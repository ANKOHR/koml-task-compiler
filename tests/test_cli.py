import json
import time
import pytest
from koml_task_compiler.cli import main, atomic_write
from koml_task_compiler.report import encode

def setup_fixture(tmp_path):
    main(["fixtures", "--out", str(tmp_path / "demo")])
    return tmp_path / "demo", tmp_path / "results.json"

def test_run_completes_on_fixture(tmp_path):
    demo, results = setup_fixture(tmp_path)
    start = time.perf_counter()
    assert main(["run", "--input", str(demo), "--results", str(results)]) == 0
    assert main(["report", "--results", str(results), "--out", str(tmp_path / "report.md")]) == 0
    assert time.perf_counter() - start < 5

def test_empty_input_renders_without_traceback(tmp_path, capsys):
    result = tmp_path / "results.json"
    assert main(["run", "--input", str(tmp_path), "--results", str(result)]) == 0
    assert main(["report", "--results", str(result)]) == 0
    assert "| records | 0 |" in capsys.readouterr().out

def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / "bad.json").write_text('{\n"records": !}', encoding="utf-8")
    assert main(["run", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert "ParseError" in error and "bad.json" in error and "line 2" in error

def test_determinism_byte_identical(tmp_path):
    demo, results = setup_fixture(tmp_path)
    command = ["run", "--input", str(demo), "--results", str(results)]
    assert main(command) == 0
    first = results.read_bytes()
    assert main(command) == 0
    assert results.read_bytes() == first
    report = tmp_path / "report.json"
    command = ["report", "--results", str(results), "--format", "json", "--out", str(report)]
    main(command)
    first = report.read_bytes()
    main(command)
    assert report.read_bytes() == first

def test_cli_smoke_all_subcommands(tmp_path):
    demo, results = setup_fixture(tmp_path)
    for command in (["run", "--input", str(demo), "--results", str(results)],
                    ["report", "--results", str(results), "--format", "json"],
                    ["validate", "--input", str(demo)],
                    ["compile", "--objective", "Write summary", "--synthetic"]):
        assert main(command) == 0
    for command in ("fixtures", "run", "report", "compile", "validate"):
        with pytest.raises(SystemExit) as exc:
            main([command, "--help"])
        assert exc.value.code == 0

def test_write_failure_no_partial_files(tmp_path, capsys):
    demo, results = setup_fixture(tmp_path)
    main(["run", "--input", str(demo), "--results", str(results)])
    before = sorted(p.name for p in tmp_path.iterdir())
    assert main(["report", "--results", str(results), "--out", str(tmp_path / "absent" / "file")]) == 2
    assert "WriteError" in capsys.readouterr().err
    assert sorted(p.name for p in tmp_path.iterdir()) == before

def test_missing_input_named_error(tmp_path, capsys):
    assert main(["run", "--input", str(tmp_path / "missing")]) == 2
    assert "MissingInput" in capsys.readouterr().err

def test_schema_drift_and_duplicate_location(tmp_path, capsys):
    record = {"id": "x", "objective": "Write", "synthetic": True}
    path = tmp_path / "records.jsonl"
    path.write_text(encode(record).replace("\n", "") + "\n" + encode(record).replace("\n", ""), encoding="utf-8")
    assert main(["validate", "--input", str(tmp_path)]) == 2
    assert "line 2" in capsys.readouterr().err
    record["unexpected"] = 1
    path.write_text(json.dumps(record), encoding="utf-8")
    assert main(["validate", "--input", str(tmp_path)]) == 2
    assert "unexpected" in capsys.readouterr().err
