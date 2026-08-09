# Veyra Sage Core Language Wrapper

**Status:** executable Sage-facing bridge.
**Implementation:** `veyra_sage/language.py`.
**Tests:** `tests/sage/test_veyra_sage_language.py`.

## Purpose

Core Language v0.1–v0.5 lives in `src/core`. This layer exposes it through the
Sage laboratory facade so notebooks, certificates, and Sage-style studies can
use the language interpreter, proof traces, and mutation pressure without
importing internal core modules directly.

## API

| Artifact | Meaning |
|---|---|
| `VeyraLanguageLab` | facade over interpreter, proof trace, fixed mutation report, and generated-family report |
| `VeyraLanguageResult` | JSON-ready interpretation row |
| `VeyraLanguageTraceRow` | JSON-ready compact proof-trace row |
| `build_language_lab_notebook()` | notebook artifact for wrapper smoke |
| `language_lab_summary()` | default wrapper capability summary |
| `generated_family_summary()` | generated arity/constructor/observer/label mutation-family counts |

## Contract

The default lab uses the `logic` semantic domain.

Expected summary:

```python
{
    "domain": "logic",
    "ready_status": "ready",
    "blocked_status": "blocked",
    "mutation_cases": 10,
    "mutation_unexpected": 0,
    "family_cases": 20,
    "family_unexpected": 0,
}
```

The notebook contract is six cells: two markdown cells and four code cells.

## Why this matters

This closes the last immediate Core Language TODO. The Veyra Sage lab can now
surface:

- language interpretation;
- proof-trace summaries;
- mutation/fuzz reports;
- generated mutation-family reports;
- notebook smoke artifacts;
- certificate checks.

That means future Sage notebooks can test the language kernel itself, not only
school theorem cards and ratio/mode objects.

## Verification

Targeted command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/sage/test_veyra_sage_language.py tests/sage/test_veyra_sage.py
```

Current verification: targeted `55 passed` with span/coverage/property/generated/fixed suite; full suite `274 passed`; doctest 41/41; smoke ok; certificates 16/16; text line hygiene 0 files >300.
