from __future__ import annotations

import html
import json
from pathlib import Path


def generate(result_files: list[Path], output: Path) -> None:
    runs = [json.loads(path.read_text()) for path in result_files]
    rows = "".join(
        "<tr>"
        + "".join(
            f"<td>{html.escape(str(value))}</td>"
            for value in [
                run["summary"]["provider"],
                run["summary"]["count"],
                f"{run['summary']['accuracy']:.3f}",
                f"{run['summary']['macro_f1']:.3f}",
                f"{run['summary']['brier_score']:.3f}",
                f"{run['summary']['expected_calibration_error']:.3f}",
                f"{run['summary']['avg_latency_ms']:.1f}",
                f"${run['summary']['total_cost_usd']:.6f}",
                f"{run['summary']['coverage']:.1%}",
            ]
        )
        + "</tr>"
        for run in runs
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(f"""<!doctype html><html><head><meta charset='utf-8'><title>Decision Lab</title>
<style>body{{font:16px system-ui;max-width:1100px;margin:40px auto;padding:0 20px;color:#17202a}}table{{border-collapse:collapse;width:100%}}th,td{{padding:12px;border-bottom:1px solid #ddd;text-align:right}}th:first-child,td:first-child{{text-align:left}}h1{{color:#312e81}}.note{{background:#eef2ff;padding:16px;border-radius:8px}}</style></head><body>
<h1>Enterprise Decision Eval Lab</h1><p class='note'>Measure decision quality, calibration, latency, cost and confidence-gated coverage. Do not interpret a single benchmark as universal model superiority.</p>
<table><thead><tr><th>Provider</th><th>N</th><th>Accuracy</th><th>Macro F1</th><th>Brier ↓</th><th>ECE ↓</th><th>Latency ms ↓</th><th>Cost ↓</th><th>Coverage</th></tr></thead><tbody>{rows}</tbody></table>
</body></html>""")
