# Jev Enterprise Decision Eval Lab

**Jev does not replace OpenAI, Claude, or Gemini. It changes where a frontier LLM is needed.**

This project evaluates TypeSafe AI's Jev as a fast, typed **decision plane** for enterprise agents. It compares Jev with generative models on decision quality, calibration, latency, cost, and confidence-gated escalation—then tests a hybrid architecture in which Jev handles routine decisions and uncertain or high-risk cases move to a stronger model or a human.

> Independent community project. Not affiliated with TypeSafe AI, OpenAI, Anthropic, or Google. Model names and prices change; verify them before drawing conclusions.

## Why this project

Most model comparisons ask which model writes the best answer. Enterprise agents often face a different question:

> **What is the safest next action, and how confident are we?**

Examples include routing a support request, selecting the next tool, approving or blocking a software change, escalating a suspicious claim, or deciding when human review is required.

Jev is designed for this bounded decision step. It receives application state and predefined criteria, then returns a typed choice and probability distribution. It does not generate a long natural-language answer.

## Jev versus frontier LLMs

| Dimension | TypeSafe Jev | OpenAI | Anthropic Claude | Google Gemini |
|---|---|---|---|---|
| Primary role | Fast typed decisions | General reasoning, generation, tools | General reasoning, long-form analysis, tools | General reasoning, multimodal work, tools |
| Output | Choice, score, or yes/no probability | Generated text or structured output | Generated text or structured output | Generated text or structured output |
| Best fit here | Routing, gates, classification, confidence policies | Complex fallback reasoning and action planning | Nuanced fallback review and policy analysis | Multimodal fallback and Google-stack workflows |
| Explanation | No rich narrative by design | Strong | Strong | Strong |
| Decision confidence | Native probability distribution | Must be requested/derived and validated | Must be requested/derived and validated | Must be requested/derived and validated |
| Expected latency/cost | Optimized for frequent small decisions | Higher for generative inference | Higher for generative inference | Higher for generative inference |
| Key limitation | Not a chatbot or deep reasoner | Expensive overkill for some routing steps | Expensive overkill for some routing steps | Expensive overkill for some routing steps |

The benchmark does **not** claim that one provider is universally better. A decision-only model and a generative model solve different parts of the system.

## Reference architecture

```text
Event / user request
        |
        v
 Policy + deterministic authorization checks
        |
        v
 Jev typed decision (choice + probabilities)
        |
        +-- confidence >= threshold and low impact --> execute bounded workflow
        |
        +-- uncertain or high impact --> OpenAI / Claude / Gemini
                                           |
                                           +--> human approval when required
```

The model never becomes the authorization boundary. Identity, permissions, transaction limits, and required human approvals remain deterministic controls.

## Enterprise scenarios

- **Agent orchestration:** choose the next tool, specialist agent, retry, or escalation path.
- **Change management:** approve, review, or block a release based on bounded evidence.
- **Fraud operations:** allow, step up identity verification, or investigate.
- **Claims triage:** straight-through processing, specialist review, or special investigation.
- **Support routing:** classify high-volume requests without paying for generated prose.
- **Evaluation:** use Jev as a low-cost first-pass judge and escalate uncertain evaluations.

Ten small synthetic cases are included for demonstration. They are not a production benchmark and contain no customer data.

## What the eval measures

| Metric | Why it matters |
|---|---|
| Accuracy and macro F1 | Overall and class-balanced decision quality |
| Brier score | Whether probabilities match outcomes |
| Expected calibration error | Whether an 80% confidence behaves like 80% correctness |
| Selective accuracy | Quality when the system accepts only confident decisions |
| Coverage | Work handled without fallback |
| Average and p95 latency | User and workflow responsiveness |
| Estimated cost | Economics at decision volume |
| Escalation rate | Operational load moved to a frontier model or human |

For high-impact use cases, also test false-negative cost, subgroup performance, distribution shift, option-label sensitivity, prompt injection, missing evidence, and abstention behavior.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q

# Offline, deterministic CI demo
decision-lab evaluate --provider mock --output results/mock.json
decision-lab report results/mock.json --output results/report.html
```

For a live provider, copy `.env.example`, export the relevant key, and run one of:

```bash
decision-lab evaluate --provider jev --output results/jev.json
decision-lab evaluate --provider openai --output results/openai.json
decision-lab evaluate --provider anthropic --output results/anthropic.json
decision-lab evaluate --provider gemini --output results/gemini.json

decision-lab report results/jev.json results/openai.json results/anthropic.json results/gemini.json
```

Live calls incur provider charges. The Jev adapter uses the System One endpoint and its `choice` question type. Provider APIs and model identifiers can change; pin validated versions for production.

## Evaluation protocol that avoids misleading claims

1. Freeze one labelled dataset before running providers.
2. Give every provider the same state, label definitions, and expected output schema.
3. Repeat runs to detect instability and option-order sensitivity.
4. Tune the confidence threshold only on a development split.
5. Report accuracy **and** calibration, latency, cost, coverage, and failure cases.
6. Separate routine cases from high-impact decisions.
7. Blind-review disagreements with domain experts.
8. Never treat generated self-confidence as calibrated without measuring it.

## Important limitations

- Typed output guarantees schema validity, not semantic correctness.
- Probability quality must be validated on your distribution.
- Option names and criteria wording can change results; test paraphrases and permutations.
- Generative providers may not expose native class probabilities; requested probabilities are not automatically calibrated.
- Pricing in code is illustrative and currently populated only for Jev. Add verified price cards before cost comparisons.
- Do not automate consequential decisions without policy controls, audit logs, and appropriate human oversight.

## Roadmap

- Confidence-threshold sweep and risk/coverage curves
- Bootstrap confidence intervals and paired significance tests
- Option-label permutation and adversarial robustness suite
- Native structured-output schemas for each generative provider
- MCP server exposing `route`, `judge`, and `escalate` tools
- HTML failure explorer with per-case disagreement analysis
- Domain packs for change risk, contact center, claims, and agent evaluation

Contributions are welcome—especially new labelled datasets, provider adapters, calibration methods, and red-team cases.

## References

- [TypeSafe AI Python SDK](https://github.com/typesafe-ai/typesafe-sdk-python)
- [OpenAI API documentation](https://platform.openai.com/docs/api-reference/responses)
- [Anthropic API documentation](https://docs.anthropic.com/en/api/messages)
- [Gemini API documentation](https://ai.google.dev/api/generate-content)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
