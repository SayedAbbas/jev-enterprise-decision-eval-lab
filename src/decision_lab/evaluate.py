from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

from .models import DecisionCase, DecisionResult, RunSummary
from .providers import Provider


def load_cases(path: Path) -> list[DecisionCase]:
    return [
        DecisionCase.model_validate_json(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def run(provider: Provider, cases: list[DecisionCase]) -> list[DecisionResult]:
    results: list[DecisionResult] = []
    for case in cases:
        try:
            results.append(provider.decide(case))
        except Exception as exc:  # noqa: BLE001 - preserve the rest of a benchmark run
            results.append(
                DecisionResult(
                    case_id=case.id,
                    provider=provider.name,
                    predicted="error",
                    probabilities={},
                    latency_ms=0,
                    error=str(exc),
                )
            )
    return results


def _f1(cases: dict[str, DecisionCase], results: list[DecisionResult]) -> float:
    # Macro-average labels that have ground-truth support. A label present only as a
    # distractor should not make a perfectly correct run appear worse.
    labels = sorted({cases[result.case_id].expected for result in results})
    scores = []
    for label in labels:
        tp = sum(r.predicted == label and cases[r.case_id].expected == label for r in results)
        fp = sum(r.predicted == label and cases[r.case_id].expected != label for r in results)
        fn = sum(r.predicted != label and cases[r.case_id].expected == label for r in results)
        scores.append(2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0)
    return statistics.mean(scores) if scores else 0


def _ece(cases: dict[str, DecisionCase], results: list[DecisionResult], bins: int = 10) -> float:
    total = len(results)
    error = 0.0
    for index in range(bins):
        low, high = index / bins, (index + 1) / bins
        bucket = [
            r
            for r in results
            if low <= r.confidence <= high and (index == bins - 1 or r.confidence < high)
        ]
        if bucket:
            accuracy = statistics.mean(r.predicted == cases[r.case_id].expected for r in bucket)
            confidence = statistics.mean(r.confidence for r in bucket)
            error += len(bucket) / total * abs(accuracy - confidence)
    return error


def summarize(
    cases: list[DecisionCase], results: list[DecisionResult], threshold: float
) -> RunSummary:
    valid = [r for r in results if not r.error]
    by_id = {case.id: case for case in cases}
    accepted = [r for r in valid if r.confidence >= threshold and not r.escalated]
    brier_terms = []
    for result in valid:
        case = by_id[result.case_id]
        brier_terms.append(
            sum(
                (result.probabilities.get(label, 0) - (label == case.expected)) ** 2
                for label in case.labels
            )
        )
    latencies = sorted(r.latency_ms for r in valid)
    p95_index = max(0, math.ceil(len(latencies) * 0.95) - 1)
    return RunSummary(
        provider=valid[0].provider if valid else "unknown",
        count=len(valid),
        accuracy=statistics.mean(r.predicted == by_id[r.case_id].expected for r in valid)
        if valid
        else 0,
        macro_f1=_f1(by_id, valid),
        brier_score=statistics.mean(brier_terms) if brier_terms else 0,
        expected_calibration_error=_ece(by_id, valid) if valid else 0,
        avg_latency_ms=statistics.mean(latencies) if latencies else 0,
        p95_latency_ms=latencies[p95_index] if latencies else 0,
        total_cost_usd=sum(r.estimated_cost_usd for r in valid),
        coverage=len(accepted) / len(valid) if valid else 0,
        selective_accuracy=statistics.mean(
            r.predicted == by_id[r.case_id].expected for r in accepted
        )
        if accepted
        else 0,
    )


def save(
    path: Path, cases: list[DecisionCase], results: list[DecisionResult], summary: RunSummary
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": summary.model_dump(),
        "cases": [c.model_dump() for c in cases],
        "results": [r.__dict__ | {"confidence": r.confidence} for r in results],
    }
    path.write_text(json.dumps(payload, indent=2))
