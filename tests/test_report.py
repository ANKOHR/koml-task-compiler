import json
from koml_task_compiler.core import compile_records
from koml_task_compiler.fixtures import fixture_records, expectations
from koml_task_compiler.report import render

def test_report_matches_ground_truth_exact():
    assert json.loads(render(compile_records(fixture_records()), "json"))["metrics"] == expectations()["metrics"]

def test_report_zero_false_positives():
    tasks = compile_records(fixture_records())["tasks"]
    actual = [t["id"] for t in tasks if t["status"] == "needs_review"]
    assert actual == expectations()["review_ids"]

def test_report_carries_provenance_banner():
    result = compile_records(fixture_records())
    for format in ("md", "json"):
        assert "PROVENANCE: 200 synthetic fixture records; 0 real" in render(result, format)

def test_hypothetical_figures_labelled():
    result = compile_records([])
    assert result["savings"]["time_saved"] is None
    for format in ("md", "json"):
        text = render(result, format).lower()
        assert "hypothetical" in text and "unmeasured" in text

def test_no_em_dashes_in_outputs():
    for format in ("md", "json"):
        assert "\u2014" not in render(compile_records(fixture_records()), format)
