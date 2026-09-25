from pathlib import Path

from decision_lab.cascade import ConfidenceCascade
from decision_lab.evaluate import load_cases, run, summarize
from decision_lab.providers import MockProvider

DATASET = Path("datasets/enterprise_decisions.jsonl")


def test_dataset_and_metrics() -> None:
    cases = load_cases(DATASET)
    results = run(MockProvider(confidence=0.88), cases)
    summary = summarize(cases, results, threshold=0.8)
    assert len(cases) == 10
    assert summary.accuracy == 1.0
    assert summary.coverage == 1.0
    assert summary.brier_score < 0.03


def test_low_confidence_escalates() -> None:
    case = load_cases(DATASET)[0]
    cascade = ConfidenceCascade(
        primary=MockProvider("fast", confidence=0.55),
        fallback=MockProvider("reasoner", confidence=0.95),
        threshold=0.8,
    )
    result = cascade.decide(case)
    assert result.escalated is True
    assert result.predicted == case.expected
    assert result.metadata["primary_confidence"] == 0.55


def test_high_confidence_stays_on_fast_path() -> None:
    case = load_cases(DATASET)[0]
    cascade = ConfidenceCascade(
        primary=MockProvider("fast", confidence=0.90),
        fallback=MockProvider("reasoner", confidence=0.95),
        threshold=0.8,
    )
    result = cascade.decide(case)
    assert result.escalated is False
    assert result.provider == "cascade:fast"
