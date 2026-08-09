# Formal Export Preparation X7

**Date:** 2026-07-07
**Status:** export-prep ledger shipped; no new theorem is claimed formalized.
**Implementation:** `src/core/formal/prep.py`, `src/core/certificates/formal_export.py`.
**Certificate:** `formal_export_prep_x7`.

## Purpose

X7 turns the stable-export gate into an auditable preparation ledger. It separates two things that must not be conflated:

1. already checked tiny Lean bridge rows (`THM-F001`, `THM-F002`);
2. stable theorem-card candidates that are only ready for later Lean/Coq export work.

## Rows

`FormalExportPrepRow` records:

| Field | Meaning |
|---|---|
| `theorem_id` / `title` | theorem-card or bridge identifier |
| `source` | Sage hook or bridge file path |
| `backend` | `Lean`, `Lean-prep`, or `Coq-prep` |
| `dependencies` | registry dependencies for theorem cards |
| `source_status` | e.g. `bridge-file` or `stable-card-only` |
| `export_status` | `checked` for existing bridges, `prep-ready` for candidates |
| `formalized` | true only for already checked bridge rows |
| `boundary` | explicit non-claim text |

## Current counts

- checked bridge rows: `2` (`THM-F001`, `THM-F002`);
- stable theorem-card candidates: `19`;
- candidate rows marked formalized: `0`;
- completed-formalization claims among candidates: `0`.

## Boundary

X7 itself does not generate Lean/Coq code for the 19 cards. X8 separately promotes all nineteen: the prior fifteen plus four closed A004–A006/C002 fixtures; the X7 ledger remains the prep gate.

`THM-F003` remains Python-certified only, and `THM-G001` remains a finite native geometry row until separately exported.

## Verification

```bash
PYTHONPATH=. python3 -m pytest -q tests/formal/test_formal_export_prep.py tests/shadows/test_certify.py
```

Expected X7 signals:

- `formal_export_prep_x7` certificate passes;
- `formal_export_prep_summary()` reports `checked_bridges=2`, `candidate_rows=19`, and `candidate_formalized=0`;
- full suite reports `46/46` certificates after X7; later formal-completion work keeps X8 as one certificate while increasing completed rows.
