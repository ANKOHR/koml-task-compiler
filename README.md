# KOML Task Compiler

A local, CPU-only Python CLI that turns natural-language objectives with explicit clauses into formal JSON task specifications. No model calls, network calls, inference, database, or GPU packages. Ordinary prose is retained as a goal and missing requirements are flagged for review.

Hypothesis: deterministic parsing can reliably preserve explicit requirements and identify structurally incomplete task specifications. It cannot reliably understand arbitrary prose or establish whether an acceptance criterion is meaningful. The measured synthetic outcome tests the former claim only.

## Quickstart

Python 3.10 or newer and setuptools are required. From the repository root, using already installed local build tooling:

```powershell
python -m pip install --no-deps --no-build-isolation --no-index -e .
ktc fixtures --out demo
ktc run --input demo
ktc report --format md
python -m pytest -q
```

The generated set contains 200 labelled synthetic records. For the smallest hand-written five-record example, run `ktc run --input examples` then `ktc report --format md`. It has 2 ready tasks and 3 needing review. The example is synthetic, not Henry's real trial data. Runtime evidence is recorded in EVIDENCE.md. No time or money savings have been measured.

## Input format

A directory contains UTF-8 JSON envelopes or JSONL records. JSON requires exactly `synthetic`, `label`, and `records` at the top level. The envelope's boolean synthetic flag must match each record. JSON does not support header comments: a label field carries the synthetic notice inside the file. JSONL contains one record per nonblank line, each with its own synthetic flag. Other formats are rejected with a named schema error, rather than silently ignored. `expectations.json` and `LABEL.md` are reserved fixture metadata names, never compiled. Keep results outside the input directory.

```json
{
  "synthetic": true,
  "label": "SYNTHETIC illustrative input",
  "records": [
    {
      "id": "task-1",
      "objective": "Write summary; deliverable: summary.md; accept: includes all rows; constraint: local files only; input: records.json",
      "synthetic": true
    }
  ]
}
```

To supply Henry's own real data, enter it by hand, set envelope and record `synthetic` to false, and add `entered_by: "Henry"` to every record. This is a declaration, not independently verified provenance. Trial data and results are private local files and are not shipped.

Required record fields: `id`, `objective` (nonblank strings, at most 100000 characters), and `synthetic` (boolean). Optional fields: `owner`, `entered_by` (nonblank text), `due` (ISO calendar date), and `amount` (integer minor units from 0 to 1000000000000). Amount is retained as source metadata, not aggregated or treated as savings. Unknown fields fail validation. Duplicate IDs fail the entire run. Unicode and Windows paths are preserved. U+2014 is rejected to maintain the no em dash output policy.

The first semicolon-delimited segment is the goal. Subsequent clauses use case-insensitive labels `deliverable:`, `accept:`, `constraint:`, or `input:`. Repeated clauses form lists in original order. A semicolon cannot occur inside a clause value. Unrecognized nonblank segments are retained and flagged. Blank segments are ignored. Missing goal, deliverable or acceptance and unrecognized clauses yield `needs_review`; otherwise the task is `ready`. Ready means structural completeness only, not feasibility, quality, correctness or a runnable acceptance test. The tool never invents an owner, deadline, dependency, criterion or deliverable.

Future due dates are rejected relative to `--as-of`, whose fixed default is 2026-09-30. This restrictive historical-record policy is explicit; pass a later reference date to compile later snapshots. Identical inputs, paths, flags and reference dates produce byte-identical results. No randomness or seed is used. Sources include filename, record ID and line; JSON envelope schema locations use line 1 while JSON parse errors and JSONL records use actual lines.

## Subcommands

- `ktc fixtures --out demo`: generate labelled synthetic inputs and independent hand-computed expectations.
- `ktc run --input demo --results .ktc-results.json --as-of 2026-09-30`: compile records, preserve their source data and save computed results atomically.
- `ktc report --format md|json --results .ktc-results.json --out report.md`: render provenance, exact counts and traceable specifications. Omit `--out` for stdout. Reports recompute counts from stored source records.
- `ktc compile --objective "Write summary; deliverable: summary.md; accept: all rows included" --synthetic`: compile one illustrative objective. Without `--synthetic`, the CLI records the operator's declaration that this is Henry's real input.
- `ktc validate --input demo --as-of 2026-09-30`: validate schema and print counts and structural issues without saving results. Incomplete tasks are valid input, so they do not cause a nonzero exit.

Every command has `--help` with an example. Exit codes: 0 success, 2 named input or write error. Malformed JSON reports ParseError with filename and line. Missing files report MissingInput with a usage hint. Schema drift reports SchemaError with offending field and source location. Failed report replacement reports WriteError; temporary files are removed and an existing destination is preserved. Individual fixture files are atomic, but the multi-file generation operation is not transactional.

## Architecture

```text
Local JSON / JSONL -> cli.read_input -> core.validate
                                       -> core.compile_task
                                       -> core.compile_records
                                       -> atomic results JSON
Stored source records -> core recomputation -> report.render -> stdout / atomic file
fixtures -> labelled tasks + independent expectations
```

The core has no I/O. CLI owns parsing and persistence. Fixture expectations are not read by the compiler or report. Counts of issues overlap: a task can lack both deliverable and acceptance, so issue totals are not a partition. Ready plus needs_review always equals records; synthetic plus declared real always equals records.

## Honesty boundary and fixture policy

All figures are computed from supplied inputs. No prediction, discovery, estimated savings or inferred requirements are presented as measured. Savings remain null and unmeasured because no baseline measurement is available. Illustrative examples are synthetic. Reports carry a provenance banner even for empty inputs or single-objective compilation. JSON fixtures carry `synthetic: true` and a synthetic label; Markdown fixture metadata carries a synthetic header comment. Every generated record carries its own flag. JSON syntax forbids comments, so JSON labelling uses fields instead. The 200 cases are five planted groups of 40: complete, missing deliverable, missing acceptance, unrecognized clause, and missing both. Expected counts are 40 ready, 160 needing review, 80 missing deliverables, 80 missing acceptance, 40 unrecognized clauses, zero missing goals. Ground-truth corruption changes computed figures.

## Acceptance and failure modes

Tests pin explicit-clause extraction, planted review IDs, exact counts, zero false positives on the planted set, empty inputs, malformed input, schema drift, duplicates, negative amounts, future dates, oversized values, Unicode, long strings, Windows paths, deterministic bytes, provenance, hypothetical labels, and atomic write failure. Synthetic accuracy does not demonstrate general natural-language understanding or utility in real use. Unstructured prose, ambiguous criteria and unsupported clause forms require human review. An operator must hand-check semantic quality before delegating tasks.

## Two-week improvement hook and verdict

Start the evidence window on the first real run, not the build date. In a private local trial log record run date, actual usage, sample size, and hand-checked mismatches in explicit goal, deliverables, acceptance, constraints and review flags. The primary metric is task error rate: tasks with at least one mismatch divided by hand-checked tasks. Zero samples means unmeasured, never zero error. After 14 days, if error exceeds 10 percent, fix the most frequent failure cause and retest or kill with a recorded reason. If there was no actual use, kill with the reason recorded. Measure savings only with timed comparable baseline work and compiler plus review work; none are claimed by this build.

Verdict is pending the real-use evidence window. Record date, sample size, measured error rate, actual usage and rationale in VERDICT.md. Expand if it earns daily use or revenue; integrate if it substantially overlaps a sibling; commercialise if a buyer would pay as-is; maintain as portfolio evidence otherwise; kill if unused or unable to meet acceptance criteria. No premature commercial or adoption claim is made. Publishing is performed by a separate verification step; this build performs no external calls.
