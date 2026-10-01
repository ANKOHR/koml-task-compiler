"""Deterministic reports with measured counts and explicit provenance."""
import json

def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"

def render(result, format="md"):
    metrics = result["metrics"]
    banner = (f"PROVENANCE: {metrics['synthetic']} synthetic fixture records; "
              f"{metrics['real_entered_by_Henry']} real records declared entered by Henry. "
              "Declarations come from input fields, not independent verification.")
    if format == "json":
        return encode({**result, "provenance_banner": banner})
    lines = ["# KOML Task Compiler report", "", banner, "",
             "Counts below are computed from explicit input records.", "",
             "| Metric | Count |", "| --- | ---: |"]
    for name in ("records", "ready", "needs_review", "synthetic", "real_entered_by_Henry"):
        lines.append(f"| {name} | {metrics[name]} |")
    for name, count in sorted(metrics["issues"].items()):
        lines.append(f"| {name} | {count} |")
    lines += ["", "Ready means explicit goal, deliverable and acceptance clauses are present.",
              "It does not establish correctness, feasibility or executable acceptance tests.",
              "", "Savings: unmeasured. No baseline supplied. Hypothetical savings are not reported.",
              "", "## Traceable specifications", ""]
    for task in result["tasks"]:
        lines += ["```json", encode(task).rstrip(), "```", ""]
    return "\n".join(lines) + "\n"
