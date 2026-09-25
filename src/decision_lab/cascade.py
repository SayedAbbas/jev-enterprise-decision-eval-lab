from __future__ import annotations

from .models import DecisionCase, DecisionResult
from .providers import Provider


class ConfidenceCascade(Provider):
    """Accept fast decisions above the threshold; escalate uncertainty."""

    name = "confidence-cascade"

    def __init__(self, primary: Provider, fallback: Provider, threshold: float = 0.80):
        self.primary = primary
        self.fallback = fallback
        self.threshold = threshold

    def decide(self, case: DecisionCase) -> DecisionResult:
        first = self.primary.decide(case)
        if first.confidence >= self.threshold:
            first.provider = f"cascade:{self.primary.name}"
            return first
        second = self.fallback.decide(case)
        second.provider = f"cascade:{self.primary.name}->{self.fallback.name}"
        second.latency_ms += first.latency_ms
        second.estimated_cost_usd += first.estimated_cost_usd
        second.escalated = True
        second.metadata["primary_confidence"] = first.confidence
        return second
