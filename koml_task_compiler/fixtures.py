"""Synthetic planted ground truth, enumerated without randomness."""
from .report import encode

def fixture_records():
    records = []
    for i in range(200):
        group = i // 40
        objective = "Prepare weekly operations summary"
        if group != 1:
            objective += "; deliverable: summary.md"
        if group != 2:
            objective += "; accept: includes all supplied records"
        if group == 3:
            objective += "; mystery: do the usual thing"
        if group == 4:
            objective = "Prepare weekly operations summary"
        records.append({"id": f"task-{i:03d}", "objective": objective, "synthetic": True})
    return records

def expectations():
    # Hand calculation: five groups of 40. Only group 0 is complete.
    # Groups 1 and 4 lack deliverables; groups 2 and 4 lack acceptance.
    return {"synthetic": True, "label": "SYNTHETIC hand-computed expectations",
            "metrics": {"records": 200, "ready": 40, "needs_review": 160,
                        "synthetic": 200, "real_entered_by_Henry": 0,
                        "issues": {"missing_goal": 0, "missing_deliverable": 80,
                                   "missing_acceptance": 80, "unrecognized_clause": 40}},
            "review_ids": [f"task-{i:03d}" for i in range(40, 200)]}

def write_fixtures(directory, writer):
    directory.mkdir(parents=True, exist_ok=True)
    writer(directory / "tasks.json", encode({"synthetic": True,
        "label": "SYNTHETIC fixture records", "records": fixture_records()}))
    writer(directory / "expectations.json", encode(expectations()))
    writer(directory / "LABEL.md", "<!-- SYNTHETIC -->\nAll files in this fixture directory are synthetic.\n")
