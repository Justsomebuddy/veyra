# Core Language v0.8 — source-span diagnostic coverage

**Status:** implemented and fully verified.
**Layer:** after mutation coverage matrix v0.7.

## Purpose

v0.8 covers parser diagnostics themselves, not only proof outcomes. The Core
Language now verifies that bad source forms report exact expected/found tokens,
line/column positions, and caret excerpts.

This makes the language kernel usable as an editor-facing and proof-facing DSL:
errors have stable locations, not just failure strings.

## Diagnostic contract

```text
cases=7
diagnostics=7
excerpts=7
multiline=1
unexpected=0
missed=0
```

Covered cases:

- `missing-close`
- `trailing-source`
- `empty-label`
- `bad-label-char`
- `missing-name`
- `newline-close`
- `comma-hole`

## API

- `span_diagnostic_cases()` — deterministic diagnostic probes.
- `run_span_diagnostic_case(case)` — exact field check for one probe.
- `run_span_diagnostic_coverage()` — run all probes.
- `missed_span_diagnostic_rules()` — diagnostics whose exact fields missed.
- `span_diagnostic_coverage_report()` — aggregate counts.
- `span_diagnostic_coverage_checklist()` — v0.8 capability checklist.
- `span_diagnostic_rows()` — processed-table rows for `scripts/generate_tables.py`.
- `VeyraLanguageLab.span_diagnostic_summary()` — Sage-facing summary hook.

## Processed table

`scripts/generate_tables.py` now writes:

```text
data/processed/core_language_span_diagnostics.csv
```

Rows: `7`; fields: `name,source,ok,expected,found,message,line,column,has_excerpt,multiline`.

## Certificate

`certify_language_span_diagnostics()` is part of the core certificate suite.
Certificate count after this layer: `16/16`.

## Verification

Targeted command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  tests/language/test_core_language_span_coverage.py tests/language/test_core_language_coverage.py \
  tests/language/test_core_language_property_fuzz.py tests/language/test_core_language_generated_fuzz.py \
  tests/language/test_core_language_fuzz.py tests/language/test_core_language_spans.py \
  tests/shadows/test_certify.py tests/sage/test_veyra_sage_language.py tests/sage/test_veyra_sage.py
```

Targeted result: `55 passed`.
Full verification: full tests 274/274, doctest 41/41, smoke ok, certificates 16/16, text line hygiene 0 files >300.

## Next hardening

- Done in Sprint C: processed source-span diagnostic table artifact.
- Done in Sprint X1: semantic-domain coverage expanded to 7 declared shadow certificates.
- Add proof-step coverage by rule name and source span.
