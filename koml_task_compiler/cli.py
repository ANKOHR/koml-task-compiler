"""Local CLI and atomic persistence. JSON and JSONL input only."""
import argparse
import json
import os
from pathlib import Path
import tempfile
from datetime import date
from .core import TaskError, compile_records, compile_task
from .fixtures import write_fixtures
from .report import encode, render

def atomic_write(path, text):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
        os.replace(temporary, path)
    except OSError as exc:
        raise TaskError(f"WriteError: {path}: {exc}") from None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()

def parse_json(text, path, offset=0):
    try:
        return json.loads(text, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except json.JSONDecodeError as exc:
        raise TaskError(f"ParseError: {path}: line {exc.lineno + offset}: {exc.msg}") from None
    except ValueError:
        raise TaskError(f"ParseError: {path}: line {1 + offset}: non-finite number") from None

def read_input(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise TaskError(f"MissingInput: {directory}; use ktc fixtures --out <dir> or create an input directory")
    located = []
    for path in sorted(directory.iterdir()):
        if path.name in {"expectations.json", "LABEL.md"} or not path.is_file():
            continue
        if path.suffix.lower() not in {".json", ".jsonl"}:
            raise TaskError(f"SchemaError: {path}: line 1: unsupported file format; use JSON or JSONL")
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise TaskError(f"ReadError: {path}: line 1: {exc}") from None
        if path.suffix.lower() == ".jsonl":
            for number, line in enumerate(text.splitlines(), 1):
                if line.strip():
                    located.append((parse_json(line, path, number - 1), path, number))
        else:
            value = parse_json(text, path)
            if not isinstance(value, dict) or set(value) != {"synthetic", "label", "records"}:
                raise TaskError(f"SchemaError: {path}: line 1: envelope requires synthetic, label, records")
            if not isinstance(value["synthetic"], bool) or not isinstance(value["label"], str) or not isinstance(value["records"], list):
                raise TaskError(f"SchemaError: {path}: line 1: invalid envelope field")
            for record in value["records"]:
                if isinstance(record, dict) and record.get("synthetic") != value["synthetic"]:
                    raise TaskError(f"SchemaError: {path}: line 1: synthetic envelope mismatch")
                located.append((record, path, 1))
    return located

def run_input(directory, as_of):
    located = read_input(directory)
    records, sources, seen = [], [], set()
    for record, path, line in located:
        try:
            compile_task(record, as_of)
            if record["id"] in seen:
                raise TaskError("SchemaError: duplicate id " + record["id"])
            seen.add(record["id"])
        except TaskError as exc:
            raise TaskError(f"{exc}: {path}: line {line}") from None
        records.append(record)
        sources.append({"id": record["id"], "file": str(path), "line": line})
    result = compile_records(records, as_of)
    result["sources"] = sorted(sources, key=lambda item: item["id"])
    return result

def parser():
    root = argparse.ArgumentParser(description="Compile explicit natural-language objectives into formal specifications.")
    commands = root.add_subparsers(dest="command", required=True)
    fixture = commands.add_parser("fixtures", help="Generate 200 labelled synthetic records", epilog="Example: ktc fixtures --out demo")
    fixture.add_argument("--out", required=True)
    run = commands.add_parser("run", help="Compile a directory of JSON or JSONL inputs", epilog="Example: ktc run --input demo")
    run.add_argument("--input", required=True)
    run.add_argument("--results", default=".ktc-results.json")
    run.add_argument("--as-of", default="2026-09-30", help="Explicit reference date for date validation")
    report = commands.add_parser("report", help="Render computed results with provenance", epilog="Example: ktc report --format md")
    report.add_argument("--format", choices=["md", "json"], default="md")
    report.add_argument("--results", default=".ktc-results.json")
    report.add_argument("--out")
    compile_cmd = commands.add_parser("compile", help="Compile one objective", epilog='Example: ktc compile --objective "Write summary; deliverable: summary.md; accept: includes all records"')
    compile_cmd.add_argument("--objective", required=True)
    compile_cmd.add_argument("--id", default="task")
    compile_cmd.add_argument("--synthetic", action="store_true", help="Label illustrative or fixture input synthetic")
    validate = commands.add_parser("validate", help="Check directory schema and flag incomplete tasks", epilog="Example: ktc validate --input demo")
    validate.add_argument("--input", required=True)
    validate.add_argument("--as-of", default="2026-09-30")
    return root

def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if hasattr(args, "as_of"):
            try:
                if date.fromisoformat(args.as_of).isoformat() != args.as_of:
                    raise ValueError()
            except ValueError:
                raise TaskError("SchemaError: as_of must be ISO YYYY-MM-DD") from None
        if args.command == "fixtures":
            write_fixtures(Path(args.out), atomic_write)
            print("Generated 200 SYNTHETIC fixture records and hand-computed expectations.")
        elif args.command in {"run", "validate"}:
            result = run_input(args.input, args.as_of)
            if args.command == "run":
                atomic_write(args.results, encode(result))
            print(render(result, "json") if args.command == "validate" else
                  f"Computed {result['metrics']['records']} records; synthetic={result['metrics']['synthetic']}; real entered by Henry={result['metrics']['real_entered_by_Henry']}. Results: {args.results}")
        elif args.command == "compile":
            result = compile_records([{"id": args.id, "objective": args.objective,
                                      "synthetic": args.synthetic, "entered_by": "Henry"}])
            print(render(result, "json"), end="")
        else:
            path = Path(args.results)
            if not path.is_file():
                raise TaskError(f"MissingInput: {path}; run ktc run --input <dir> first")
            try:
                stored = parse_json(path.read_text(encoding="utf-8"), path)
                # Recompute from stored source records, never trust stored totals.
                result = compile_records([task["source_record"] for task in stored["tasks"]], stored["as_of"])
                result["sources"] = stored.get("sources", [])
            except (KeyError, TypeError, AttributeError):
                raise TaskError(f"SchemaError: {path}: line 1: invalid results schema") from None
            output = render(result, args.format)
            if args.out:
                atomic_write(args.out, output)
            else:
                print(output, end="")
        return 0
    except (TaskError, OSError, UnicodeError) as exc:
        # Sanitize forbidden punctuation even in OS messages and supplied paths.
        print(str(exc).replace("\u2014", "-"), file=__import__("sys").stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
