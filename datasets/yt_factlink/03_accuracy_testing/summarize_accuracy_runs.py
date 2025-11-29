"""
Generate an HTML summary of all accuracy testing runs.
Looks for run directories under the current directory (where this script is located).
A run directory contains both `run_config.json` and `metrics.json`.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


# ---------------------------------------------------------------
# 1. Find run directories (contain run_config.json + metrics.json)
# ---------------------------------------------------------------
def find_run_dirs(root: Path) -> list[Path]:
    run_dirs = []
    for cfg_path in root.rglob("run_config.json"):
        run_dir = cfg_path.parent
        if (run_dir / "metrics.json").exists():
            run_dirs.append(run_dir)
    return run_dirs


# ---------------------------------------------------------------
# 2. Load run data into flat dicts
# ---------------------------------------------------------------
def load_run(run_dir: Path) -> dict:
    cfg = json.loads((run_dir / "run_config.json").read_text("utf-8"))
    met = json.loads((run_dir / "metrics.json").read_text("utf-8"))

    rel = run_dir.relative_to(ROOT)
    parts = rel.parts

    exp_level = parts[0] if len(parts) > 0 else None        # e.g. all_at_once / single_class
    provider_level = parts[1] if len(parts) > 1 else None   # e.g. openai / google

    overall = met.get("overall", {}) or {}

    return {
        "run_dir": str(rel),
        "timestamp": cfg.get("timestamp", ""),
        "dataset_id": cfg.get("dataset_id", ""),
        "experiment_type": cfg.get("experiment_type", ""),
        "provider": cfg.get("provider", ""),
        "model_name": cfg.get("model_name", ""),
        "data_jsonl": cfg.get("data_jsonl", ""),
        "prompt_dir": cfg.get("prompt_dir", ""),
        "exp_level": exp_level,
        "provider_level": provider_level,
        "overall_accuracy": overall.get("macro_accuracy"),
        "macro_f1": overall.get("macro_f1"),
        "failures": met.get("failures", 0),
        "per_label": met.get("per_label", {}),
    }


# ---------------------------------------------------------------
# 3. Escape HTML
# ---------------------------------------------------------------
def esc(s: str | None) -> str:
    if s is None:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# ---------------------------------------------------------------
# 4. Build HTML
# ---------------------------------------------------------------
def build_html(runs: list[dict]) -> str:
    runs = sorted(runs, key=lambda r: r["timestamp"] or "")

    # minimal CSS to keep it readable
    css = """
    body {
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        margin: 1.5rem;
        background: #111827;
        color: #e5e7eb;
    }
    h1 {
        margin-bottom: 0.5rem;
    }
    .meta {
        color: #9ca3af;
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }
    table {
        border-collapse: collapse;
        width: 100%;
    }
    th, td {
        border-bottom: 1px solid #374151;
        padding: 0.4rem 0.5rem;
        vertical-align: top;
        font-size: 0.85rem;
    }
    th {
        background: #1f2937;
        position: sticky;
        top: 0;
        z-index: 1;
    }
    tr:nth-child(even) td {
        background: #020617;
    }
    tr:nth-child(odd) td {
        background: #030712;
    }
    .badge {
        display: inline-block;
        padding: 0.1rem 0.4rem;
        border-radius: 999px;
        font-size: 0.75rem;
        background: #1d4ed8;
        color: #e5e7eb;
        white-space: nowrap;
    }
    .badge.small {
        background: #6b21a8;
    }
    .muted {
        color: #9ca3af;
        font-size: 0.8rem;
    }
    .model-cell {
        word-break: break-all;
        font-family: ui-monospace, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        font-size: 0.8rem;
    }
    .run-dir {
        font-family: ui-monospace, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        font-size: 0.75rem;
        color: #9ca3af;
    }
    details summary {
        cursor: pointer;
        font-size: 0.8rem;
        color: #93c5fd;
    }
    details {
        margin-top: 0.25rem;
    }
    .perlabel-table {
        width: 100%;
        margin-top: 0.4rem;
        border-collapse: collapse;
        table-layout: auto;
    }
    .perlabel-table th, .perlabel-table td {
        border: 1px solid #374151;
        font-size: 0.75rem;
        padding: 0.2rem 0.3rem;
        background: #020617;
    }
    .metric-good {
        color: #22c55e;
        font-weight: 500;
    }
    .metric-bad {
        color: #f97316;
        font-weight: 500;
    }
    """

    html = []
    html.append("<!DOCTYPE html>")
    html.append("<html lang='en'>")
    html.append("<head>")
    html.append("<meta charset='utf-8'/>")
    html.append("<title>Accuracy Runs Overview</title>")
    html.append("<style>")
    html.append(css)
    html.append("</style>")
    html.append("</head>")
    html.append("<body>")
    html.append("<h1>Accuracy Runs Overview</h1>")
    html.append(
        f"<div class='meta'>Total runs: {len(runs)} &mdash; one row per run. "
        "Click <em>Show per-label metrics</em> on a row to see C1–C6 details.</div>"
    )

    # Main table header
    html.append("<table>")
    html.append(
        "<tr>"
        "<th>Timestamp</th>"
        "<th>Provider</th>"
        "<th>Experiment</th>"
        "<th>Model</th>"
        "<th>Dataset / Split</th>"
        "<th>Overall Acc</th>"
        "<th>Macro F1</th>"
        "<th>Failures</th>"
        "<th>Per-label metrics</th>"
        "<th>Run Dir</th>"
        "</tr>"
    )

    for r in runs:
        acc = r["overall_accuracy"]
        f1 = r["macro_f1"]

        def fmt_metric(v: float | None) -> str:
            if isinstance(v, (int, float)):
                cls = "metric-good" if v >= 0.8 else "metric-bad"
                return f"<span class='{cls}'>{v:.3f}</span>"
            return "<span class='muted'>-</span>"

        acc_html = fmt_metric(acc)
        f1_html = fmt_metric(f1)

        # Show the exact data_jsonl path instead of dataset/split
        ds_cell = f"<span class='muted'>{esc(r['data_jsonl'])}</span>"

        # experiment badge
        exp_badge = f"<span class='badge'>{esc(r['experiment_type'] or '')}</span>"
        # provider sub-badge
        prov_badge = f"<span class='badge small'>{esc(r['provider'] or '')}</span>"

        # per-label details HTML
        per_label = r.get("per_label") or {}
        if per_label:
            pl = []
            pl.append("<details>")
            pl.append("<summary>Show per-label metrics</summary>")
            pl.append("<table class='perlabel-table'>")
            pl.append(
                "<tr>"
                "<th>Label</th>"
                "<th>Acc</th>"
                "<th>F1</th>"
                "<th>Prec</th>"
                "<th>Rec</th>"
                "<th>TP</th>"
                "<th>FP</th>"
                "<th>TN</th>"
                "<th>FN</th>"
                "</tr>"
            )
            for label_name, m in sorted(per_label.items()):
                def fm(x):
                    return f"{x:.3f}" if isinstance(x, (int, float)) else "-"

                pl.append(
                    "<tr>"
                    f"<td>{esc(label_name)}</td>"
                    f"<td>{fm(m.get('accuracy'))}</td>"
                    f"<td>{fm(m.get('f1'))}</td>"
                    f"<td>{fm(m.get('precision'))}</td>"
                    f"<td>{fm(m.get('recall'))}</td>"
                    f"<td>{m.get('tp', 0)}</td>"
                    f"<td>{m.get('fp', 0)}</td>"
                    f"<td>{m.get('tn', 0)}</td>"
                    f"<td>{m.get('fn', 0)}</td>"
                    "</tr>"
                )
            pl.append("</table>")
            pl.append("</details>")
            per_label_html = "\n".join(pl)
        else:
            per_label_html = "<span class='muted'>no per-label metrics</span>"

        html.append("<tr>")
        html.append(f"<td>{esc(r['timestamp'])}</td>")
        html.append(f"<td>{prov_badge}</td>")
        html.append(f"<td>{exp_badge}</td>")
        html.append(f"<td class='model-cell'>{esc(r['model_name'])}</td>")
        html.append(f"<td>{ds_cell}</td>")
        html.append(f"<td>{acc_html}</td>")
        html.append(f"<td>{f1_html}</td>")
        html.append(f"<td>{r['failures']}</td>")
        html.append(f"<td>{per_label_html}</td>")
        html.append(f"<td class='run-dir'>{esc(r['run_dir'])}</td>")
        html.append("</tr>")

    html.append("</table>")
    html.append("</body></html>")

    return "\n".join(html)


# ---------------------------------------------------------------
# 5. MAIN
# ---------------------------------------------------------------
def main() -> None:
    run_dirs = find_run_dirs(ROOT)
    if not run_dirs:
        print("No runs found.")
        return

    runs = [load_run(rd) for rd in run_dirs]

    html = build_html(runs)
    out_path = ROOT / "accuracy_overview.html"
    out_path.write_text(html, encoding="utf-8")
    print("Wrote:", out_path)


if __name__ == "__main__":
    main()
