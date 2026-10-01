import json
from koml_task_compiler.fixtures import fixture_records, expectations, write_fixtures
from koml_task_compiler.core import compile_records
from koml_task_compiler.cli import atomic_write

def test_fixtures_labelled_synthetic(tmp_path):
    write_fixtures(tmp_path, atomic_write)
    for name in ("tasks.json", "expectations.json"):
        value = json.loads((tmp_path / name).read_text())
        assert value["synthetic"] is True
        assert "SYNTHETIC" in value["label"]
    assert all(r["synthetic"] for r in fixture_records())
    assert "<!-- SYNTHETIC -->" in (tmp_path / "LABEL.md").read_text()

def test_fixture_ground_truth_matches_hand_computed():
    assert compile_records(fixture_records())["metrics"] == expectations()["metrics"]

def test_corrupted_fixture_changes_computed_figures():
    records = fixture_records()
    records[0]["objective"] = "Incomplete objective"
    result = compile_records(records)
    assert result["metrics"]["ready"] == 39
    assert result["metrics"]["issues"]["missing_acceptance"] == 81
