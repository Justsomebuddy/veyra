# Core Language v0.7 — coverage matrix and missed-rule report

**Status:** implemented and fully verified.
**Layer:** after property-fuzz/shrinker v0.6.

## Purpose

v0.7 joins all negative-pressure layers into one coverage matrix. The language
lab can now answer: which mutation families are covered, how many examples each
family owns, which statuses appear, and whether an expected rule family is
missing entirely.

This is the first coverage contract for the Veyra language kernel.

## Inputs

The matrix merges three sources:

- fixed v0.4 catalog: grammar, typing, inference;
- generated v0.5 families: arity, constructor, observer, label;
- property v0.6 families: property-arity, property-constructor,
  property-observer, property-label.

## Coverage contract

```text
families=11
cases=54
blocked=48
unknown=6
ready=0
unexpected=0
missed=0
shrink_witnesses=24
```

Expected family order:

```text
grammar, typing, inference,
arity, constructor, observer, label,
property-arity, property-constructor, property-observer, property-label
```

## API

- `language_coverage_matrix()` — per-family rows.
- `language_coverage_report()` — aggregate coverage counts.
- `missed_language_coverage_rules()` — expected families with zero cases.
- `coverage_language_checklist()` — v0.7 capability checklist.
- `language_coverage_rows()` — processed-table rows for `scripts/generate_tables.py`.
- `VeyraLanguageLab.coverage_summary()` — Sage-facing summary hook.

## Processed table

`scripts/generate_tables.py` now writes:

```text
data/processed/core_language_coverage_matrix.csv
```

Rows: `11`; fields: `family,cases,blocked,unknown,ready,unexpected,covered`.

## Certificate

`certify_language_coverage()` is part of the core certificate suite.
Certificate count after this layer: `15/15`.

## Verification

Targeted command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  tests/language/test_core_language_coverage.py tests/language/test_core_language_property_fuzz.py \
  tests/language/test_core_language_generated_fuzz.py tests/language/test_core_language_fuzz.py \
  tests/shadows/test_certify.py tests/sage/test_veyra_sage_language.py tests/sage/test_veyra_sage.py
```

Targeted result: `42 passed`.
Full verification: full tests 267/267, doctest 41/41, smoke ok, certificates 15/15, text line hygiene 0 files >300.

## Next hardening

- Done in Sprint C: processed coverage matrix table artifact.
- Done in v0.8: source-span coverage over parser diagnostics.
- Done in Sprint X1: semantic-domain coverage expanded to 7 declared shadow certificates.
