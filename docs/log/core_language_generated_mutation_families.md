# Core Language v0.5 — generated mutation families

**Status:** implemented and fully verified.
**Layer:** after fixed mutation catalog v0.4, before randomized/property fuzzing.

## Purpose

Veyra v0.4 had 10 fixed negative cases. v0.5 turns that into deterministic
families: the lab can sweep classes of malformed or semantically unavailable
language forms and demand a proof-trace outcome.

A generated mutation is not a random string. It is a structured probe with:

- a family name,
- a source expression,
- an expected status (`blocked` or `unknown`),
- proof-trace execution through the same parser/type/inference stack.

## Implemented families

| Family | Cases | Expected surface |
|---|---:|---|
| `arity` | 8 | wrong constructor/relation arity blocks |
| `constructor` | 4 | wrong constructor nesting blocks |
| `observer` | 4 | unsupported observers become unknown; known mismatches block |
| `label` | 4 | invalid atom labels block at parse/lex boundary |

Aggregate contract:

```text
families=4
cases=20
blocked=18
unknown=2
ready=0
unexpected=0
```

## API

- `generated_language_mutation_cases()` — returns all generated cases.
- `run_generated_language_mutations()` — executes proof traces for every case.
- `generated_language_mutation_report()` — returns aggregate counts.
- `generated_mutation_language_checklist()` — v0.5 capability checklist.
- `VeyraLanguageLab.generated_family_summary()` — Sage-facing summary hook.

## Certificate

`certify_language_generated_mutations()` is now part of `certificate_suite()`.
Certificate summary: `13/13` passing.

## Verification

Current targeted command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  tests/language/test_core_language_generated_fuzz.py \
  tests/language/test_core_language_fuzz.py tests/shadows/test_certify.py \
  tests/sage/test_veyra_sage_language.py tests/sage/test_veyra_sage.py
```

Targeted result: `28 passed`.
Full verification: full tests 253/253, doctest 41/41, smoke ok, certificates 13/13, text line hygiene 0 files >300.

## Next hardening

- Done in v0.6: deterministic property-fuzz generator with shrinking.
- Add coverage metrics over grammar constructors and observer semantics.
- Add Sage notebook cells that display family tables, not only aggregate asserts.
