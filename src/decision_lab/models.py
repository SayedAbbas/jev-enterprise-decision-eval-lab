from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field, model_validator


class DecisionCase(BaseModel):
    id: str
    use_case: str
    state: str
    question: str
    labels: dict[str, str]
    expected: str
    high_impact: bool = False

    @model_validator(mode="after")
    def expected_is_valid(self) -> DecisionCase:
        if self.expected not in self.labels:
            raise ValueError("expected must be one of labels")
        return self


@dataclass
class DecisionResult:
    case_id: str
    provider: str
    predicted: str
    probabilities: dict[str, float]
    latency_ms: float
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    escalated: bool = False
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def confidence(self) -> float:
        return max(self.probabilities.values(), default=0.0)


class RunSummary(BaseModel):
    provider: str
    count: int
    accuracy: float
    macro_f1: float
    brier_score: float
    expected_calibration_error: float
    avg_latency_ms: float
    p95_latency_ms: float
    total_cost_usd: float
    coverage: float = Field(description="Fraction accepted without escalation")
    selective_accuracy: float = Field(description="Accuracy on accepted decisions")
