"""Pure compilation with explicit clauses, never inferred requirements."""
import re
from datetime import date

MAX_TEXT = 100000
FIELDS = {"id", "objective", "synthetic", "owner", "due", "amount", "entered_by"}
CLAUSES = {"deliverable", "accept", "constraint", "input"}

class TaskError(ValueError):
    """Named input failure safe to show to an operator."""

def validate(record, as_of):
    if not isinstance(record, dict):
        raise TaskError("SchemaError: record must be an object")
    extra = set(record) - FIELDS
    if extra:
        raise TaskError("SchemaError: unknown field " + sorted(extra)[0])
    for field in ("id", "objective"):
        value = record.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > MAX_TEXT:
            raise TaskError(f"SchemaError: {field} must be nonempty text of at most {MAX_TEXT} characters")
    if not isinstance(record.get("synthetic"), bool):
        raise TaskError("SchemaError: synthetic must be a boolean")
    if not record["synthetic"] and record.get("entered_by") != "Henry":
        raise TaskError("SchemaError: entered_by must be Henry for real inputs")
    for field in ("owner", "entered_by"):
        if field in record and (not isinstance(record[field], str) or not record[field].strip() or len(record[field]) > MAX_TEXT):
            raise TaskError(f"SchemaError: invalid {field}")
    if "amount" in record:
        value = record["amount"]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 10**12:
            raise TaskError("SchemaError: amount must be integer minor units between 0 and 1000000000000")
    if "due" in record:
        try:
            parsed = date.fromisoformat(record["due"])
            if parsed.isoformat() != record["due"] or parsed > date.fromisoformat(as_of):
                raise ValueError()
        except (ValueError, TypeError):
            raise TaskError("SchemaError: due must be ISO date on or before as_of") from None
    if any("\u2014" in value for value in record.values() if isinstance(value, str)):
        raise TaskError("SchemaError: text contains forbidden U+2014")

def compile_task(record, as_of="2026-09-30"):
    validate(record, as_of)
    parts = record["objective"].split(";")
    goal = parts[0].strip()
    clauses = {key: [] for key in sorted(CLAUSES)}
    unresolved = []
    for part in parts[1:]:
        match = re.fullmatch(r"\s*(deliverable|accept|constraint|input)\s*:\s*(.+?)\s*", part, re.I | re.S)
        if match:
            clauses[match[1].lower()].append(match[2])
        elif part.strip():
            unresolved.append(part.strip())
    issues = []
    if not goal:
        issues.append("missing_goal")
    if not clauses["deliverable"]:
        issues.append("missing_deliverable")
    if not clauses["accept"]:
        issues.append("missing_acceptance")
    if unresolved:
        issues.append("unrecognized_clause")
    return {"id": record["id"], "goal": goal, "deliverables": clauses["deliverable"],
            "acceptance_criteria": clauses["accept"], "constraints": clauses["constraint"],
            "inputs": clauses["input"], "unresolved_clauses": unresolved,
            "issues": issues, "status": "needs_review" if issues else "ready",
            "synthetic": record["synthetic"], "source_record": dict(record),
            "owner": record.get("owner"), "due": record.get("due"),
            "interpretation": "Explicit clauses only; ready means structurally complete, not semantically verified."}

def compile_records(records, as_of="2026-09-30"):
    tasks, seen = [], set()
    for record in records:
        task = compile_task(record, as_of)
        if task["id"] in seen:
            raise TaskError("SchemaError: duplicate id " + task["id"])
        seen.add(task["id"])
        tasks.append(task)
    tasks.sort(key=lambda task: task["id"])
    issues = {name: sum(name in t["issues"] for t in tasks) for name in
              ("missing_goal", "missing_deliverable", "missing_acceptance", "unrecognized_clause")}
    return {"schema_version": 1, "as_of": as_of, "tasks": tasks,
            "metrics": {"records": len(tasks), "ready": sum(t["status"] == "ready" for t in tasks),
                        "needs_review": sum(t["status"] == "needs_review" for t in tasks),
                        "synthetic": sum(t["synthetic"] for t in tasks),
                        "real_entered_by_Henry": sum(not t["synthetic"] for t in tasks),
                        "issues": issues},
            "savings": {"status": "unmeasured", "time_saved": None, "money_saved": None,
                        "note": "No baseline supplied; hypothetical savings are not measured or reported."}}
