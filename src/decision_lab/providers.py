from __future__ import annotations

import json
import os
import re
import time
from abc import ABC, abstractmethod

import httpx

from .models import DecisionCase, DecisionResult


def _normalize(raw: dict[str, float], labels: dict[str, str]) -> dict[str, float]:
    values = {key: max(0.0, float(raw.get(key, 0.0))) for key in labels}
    total = sum(values.values())
    if total <= 0:
        return {key: 1.0 / len(labels) for key in labels}
    return {key: value / total for key, value in values.items()}


def _json_object(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("provider returned no JSON object")
    return json.loads(match.group(0))


def _prompt(case: DecisionCase) -> str:
    return (
        "Make one classification. Return JSON only with keys predicted and probabilities. "
        "probabilities must contain every label and sum to 1.\n"
        f"Question: {case.question}\n"
        f"Labels: {json.dumps(case.labels)}\n"
        f"State: {case.state}"
    )


class Provider(ABC):
    name: str

    @abstractmethod
    def decide(self, case: DecisionCase) -> DecisionResult: ...


class MockProvider(Provider):
    """Deterministic offline baseline used by CI and demos."""

    def __init__(self, name: str = "mock-jev", confidence: float = 0.88):
        self.name = name
        self._confidence = confidence

    def decide(self, case: DecisionCase) -> DecisionResult:
        start = time.perf_counter()
        keys = list(case.labels)
        remaining = (1 - self._confidence) / max(1, len(keys) - 1)
        probs = {key: (self._confidence if key == case.expected else remaining) for key in keys}
        return DecisionResult(
            case_id=case.id,
            provider=self.name,
            predicted=case.expected,
            probabilities=probs,
            latency_ms=(time.perf_counter() - start) * 1000,
        )


class JevProvider(Provider):
    name = "jev"

    def __init__(self) -> None:
        self.key = os.environ["TYPESAFE_API_KEY"]
        self.model = os.getenv("JEV_MODEL", "jev-latest")

    def decide(self, case: DecisionCase) -> DecisionResult:
        start = time.perf_counter()
        response = httpx.post(
            "https://api.typesafe.ai/v1/systemone",
            headers={"Authorization": f"Bearer {self.key}"},
            json={
                "model": self.model,
                "state": case.state,
                "questions": {
                    "decision": {
                        "type": "choice",
                        "instructions": case.question,
                        "criteria": case.labels,
                    }
                },
            },
            timeout=30,
        )
        response.raise_for_status()
        body = response.json()
        answer = body.get("answers", body)["decision"]
        probs = _normalize(answer["probabilities"], case.labels)
        predicted = answer.get("choice") or max(probs, key=probs.get)
        usage = body.get("usage", {})
        input_tokens = int(usage.get("input_tokens", 0))
        return DecisionResult(
            case_id=case.id,
            provider=self.name,
            predicted=predicted,
            probabilities=probs,
            latency_ms=(time.perf_counter() - start) * 1000,
            input_tokens=input_tokens,
            estimated_cost_usd=input_tokens / 1_000_000 * 0.042,
            metadata={"model": self.model},
        )


class GenerativeProvider(Provider):
    def parse(
        self, case: DecisionCase, text: str, latency_ms: float, usage: dict
    ) -> DecisionResult:
        parsed = _json_object(text)
        probs = _normalize(parsed.get("probabilities", {}), case.labels)
        predicted = parsed.get("predicted")
        if predicted not in case.labels:
            predicted = max(probs, key=probs.get)
        return DecisionResult(
            case_id=case.id,
            provider=self.name,
            predicted=predicted,
            probabilities=probs,
            latency_ms=latency_ms,
            input_tokens=int(usage.get("input_tokens", usage.get("promptTokenCount", 0))),
            output_tokens=int(usage.get("output_tokens", usage.get("candidatesTokenCount", 0))),
            metadata={"model": self.model},
        )


class OpenAIProvider(GenerativeProvider):
    name = "openai"

    def __init__(self) -> None:
        self.key = os.environ["OPENAI_API_KEY"]
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.6-mini")

    def decide(self, case: DecisionCase) -> DecisionResult:
        start = time.perf_counter()
        response = httpx.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {self.key}"},
            json={"model": self.model, "input": _prompt(case)},
            timeout=60,
        )
        response.raise_for_status()
        body = response.json()
        text = body.get("output_text") or body["output"][0]["content"][0]["text"]
        return self.parse(case, text, (time.perf_counter() - start) * 1000, body.get("usage", {}))


class AnthropicProvider(GenerativeProvider):
    name = "anthropic"

    def __init__(self) -> None:
        self.key = os.environ["ANTHROPIC_API_KEY"]
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5.5")

    def decide(self, case: DecisionCase) -> DecisionResult:
        start = time.perf_counter()
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": self.key, "anthropic-version": "2023-06-01"},
            json={
                "model": self.model,
                "max_tokens": 300,
                "messages": [{"role": "user", "content": _prompt(case)}],
            },
            timeout=60,
        )
        response.raise_for_status()
        body = response.json()
        return self.parse(
            case,
            body["content"][0]["text"],
            (time.perf_counter() - start) * 1000,
            body.get("usage", {}),
        )


class GeminiProvider(GenerativeProvider):
    name = "gemini"

    def __init__(self) -> None:
        self.key = os.environ["GEMINI_API_KEY"]
        self.model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash")

    def decide(self, case: DecisionCase) -> DecisionResult:
        start = time.perf_counter()
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        )
        response = httpx.post(
            url,
            params={"key": self.key},
            json={
                "contents": [{"parts": [{"text": _prompt(case)}]}],
                "generationConfig": {"responseMimeType": "application/json"},
            },
            timeout=60,
        )
        response.raise_for_status()
        body = response.json()
        text = body["candidates"][0]["content"]["parts"][0]["text"]
        return self.parse(
            case, text, (time.perf_counter() - start) * 1000, body.get("usageMetadata", {})
        )


def build_provider(name: str) -> Provider:
    providers = {
        "mock": MockProvider,
        "jev": JevProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "gemini": GeminiProvider,
    }
    if name not in providers:
        raise ValueError(f"unknown provider: {name}")
    return providers[name]()
