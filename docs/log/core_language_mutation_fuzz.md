# Veyra Core Language v0.4 — Mutation/Fuzz Pressure

**Status:** executable negative-pressure layer.
**Implementation:** `src/core/language/fuzz.py`.
**Tests:** `tests/language/test_core_language_fuzz.py`.

## Purpose

The Core Language now has grammar, spans, diagnostics, and proof objects. v0.4
adds deterministic mutation pressure: bad grammar, bad typing, blocked echo, and
unknown observers are generated as a catalog and must produce the expected
proof-trace status.

The goal is simple: Veyra must never silently accept broken language forms.
Every malformed or semantically unavailable case must become `blocked` or
`unknown` with traceable evidence.

## Mutation categories

| Category | Examples | Expected |
|---|---|---|
| grammar | missing close paren, invalid char, trailing source, missing label | `blocked` parse trace |
| typing | wrong constructor child kinds | `blocked` type trace |
| inference | trace mismatch, unknown observer | `blocked` or `unknown` inference trace |

## API

| Function | Meaning |
|---|---|
| `language_mutation_cases()` | deterministic mutation catalog |
| `run_language_mutation_case(case)` | proof-trace one mutation |
| `run_language_mutations()` | run all cases |
| `language_mutation_report()` | aggregate counts |
| `mutation_language_checklist()` | v0.4 capability list |

## Current catalog

v0.4 contains 10 cases:

- 4 grammar mutations;
- 4 typing mutations;
- 2 inference mutations.

Expected aggregate:

```text
cases=10
blocked=9
unknown=1
ready=0
unexpected=0
```

The single `unknown` case is intentional: a syntactically and type-correct echo
using an observer whose semantics are not yet defined.

## Verification

Targeted command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/language/test_core_language_fuzz.py tests/language/test_core_language_proofs.py tests/language/test_core_language_spans.py tests/language/test_core_language.py tests/shadows/test_certify.py
```

Current verification: targeted `29 passed`; full suite `241 passed`; doctest 41/41; smoke ok; certificates 12/12; line hygiene 0 files >300.

## Next step

Move from deterministic catalog to generated mutation families over constructor
positions, observer names, labels, and arities; then expose this through the
Sage-facing Core Language wrapper.
