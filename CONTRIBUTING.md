# Contributing

Thank you for helping improve the Jev Enterprise Decision Eval Lab.

## Start with an issue

Please comment on the issue you want to work on and briefly describe your proposed approach. Keep the first pull request focused; larger ideas can be split into follow-up work.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ruff check .
pytest -q
decision-lab evaluate --provider mock --output results/mock.json
```

Live provider tests are optional and must never expose API keys. CI must remain runnable without paid APIs or network credentials.

## Pull-request expectations

- Link the issue in the pull-request description.
- Add or update tests for behavior changes.
- Keep synthetic datasets free of customer, employee, incident, medical, financial, or other sensitive data.
- Document new environment variables and provider assumptions.
- Report limitations and failure cases; do not claim universal model superiority.
- Preserve deterministic authorization and required human approval outside the model.
- Ensure `ruff check .` and `pytest -q` pass before requesting review.

## Evaluation integrity

Use frozen labelled data, compare providers on equivalent inputs and schemas, and report accuracy together with calibration, latency, cost, coverage, and high-confidence errors. Tune thresholds on a development split rather than the final test set.

By contributing, you agree that your contribution is provided under this repository's MIT License.
