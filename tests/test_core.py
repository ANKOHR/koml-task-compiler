import pytest
from koml_task_compiler.core import TaskError, compile_records, compile_task

def record(**overrides):
    return {"id": "a", "objective": "Write summary; deliverable: report.md; accept: includes all rows", "synthetic": True, **overrides}

def test_explicit_compilation():
    task = compile_task(record())
    assert task["deliverables"] == ["report.md"]
    assert task["acceptance_criteria"] == ["includes all rows"]
    assert task["status"] == "ready"

@pytest.mark.parametrize("overrides", [{"amount": -1}, {"amount": 1.5}, {"amount": True}, {"due": "2099-01-01"}, {"objective": "x" * 100001}, {"extra": 1}, {"synthetic": "true"}, {"synthetic": False}, {"objective": "bad\u2014text"}])
def test_rejects_adversarial_values(overrides):
    with pytest.raises(TaskError, match="SchemaError"):
        compile_task(record(**overrides))

def test_duplicate_ids():
    with pytest.raises(TaskError, match="duplicate id"):
        compile_records([record(), record()])

def test_handles_unicode_and_long_inputs():
    objective = "整理 café " + "a" * 90000 + r"; deliverable: C:\Users\Henry\报告.md; accept: all rows"
    assert compile_task(record(objective=objective))["status"] == "ready"

def test_unstructured_objective_requires_review():
    assert compile_task(record(objective="Build a useful tool"))["issues"] == ["missing_deliverable", "missing_acceptance"]
