from pathlib import Path
from typing import Annotated

import typer

from .evaluate import load_cases, run, save, summarize
from .providers import build_provider
from .report import generate

app = typer.Typer(no_args_is_help=True)


@app.command()
def evaluate(
    provider: Annotated[str, typer.Option(help="mock, jev, openai, anthropic, or gemini")] = "mock",
    dataset: Annotated[Path, typer.Option()] = Path("datasets/enterprise_decisions.jsonl"),
    output: Annotated[Path, typer.Option()] = Path("results/run.json"),
    threshold: Annotated[float, typer.Option(min=0, max=1)] = 0.80,
) -> None:
    cases = load_cases(dataset)
    results = run(build_provider(provider), cases)
    summary = summarize(cases, results, threshold)
    save(output, cases, results, summary)
    typer.echo(summary.model_dump_json(indent=2))


@app.command()
def report(
    inputs: Annotated[list[Path], typer.Argument()],
    output: Annotated[Path, typer.Option()] = Path("results/report.html"),
) -> None:
    generate(inputs, output)
    typer.echo(f"Wrote {output}")


if __name__ == "__main__":
    app()
