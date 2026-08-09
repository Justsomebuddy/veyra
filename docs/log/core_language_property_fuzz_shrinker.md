# Core Language v0.6 — property fuzz and shrinker

**Status:** implemented and fully verified.
**Layer:** after generated mutation families v0.5.

## Purpose

v0.5 generated fixed families. v0.6 adds a deterministic property-fuzz loop:
for a seed and count, Veyra builds many structured bad/edge programs, runs them
through proof tracing, and shrinks each case to a minimal representative.

This is not random chaos. It is reproducible pressure against language laws.

## Default contract

```text
seed=613
families=4
cases=24
blocked=21
unknown=3
ready=0
unexpected=0
shrunk=24
```

Families:

- `property-arity` — bad arity must block.
- `property-constructor` — wrong constructor nesting must block.
- `property-observer` — unknown observers stay unknown; known mismatches block.
- `property-label` — bad labels must block before silent interpretation.

## Shrinker rule

Every generated case maps to a minimal family representative:

| Family | Shrink target |
|---|---|
| arity | `tact()` |
| constructor | `mode(nod:a)` |
| unknown observer | `echo(nod:a,nod:b,observer:aura)` |
| blocked observer | `echo(nod:a,nod:b,observer:trace)` |
| label | `nod:!` |

The shrinker is deterministic: the same failing class always contracts to the
same small obstruction witness.

## API

- `property_language_mutation_cases(seed=613, count=24)`
- `run_property_language_fuzz(seed=613, count=24)`
- `shrink_language_mutation_case(case)`
- `property_language_fuzz_report(seed=613, count=24)`
- `property_fuzz_language_checklist()`
- `VeyraLanguageLab.property_fuzz_summary()`

## Certificate

`certify_language_property_fuzz()` is part of the core certificate suite.
Certificate count after this layer: `14/14`.

## Verification

Targeted command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  tests/language/test_core_language_property_fuzz.py \
  tests/language/test_core_language_generated_fuzz.py tests/language/test_core_language_fuzz.py \
  tests/shadows/test_certify.py tests/sage/test_veyra_sage_language.py tests/sage/test_veyra_sage.py
```

Targeted result: `35 passed`.
Full verification: full tests 260/260, doctest 41/41, smoke ok, certificates 14/14, text line hygiene 0 files >300.

## Next hardening

- Done in v0.7: coverage matrix with missed-rule reporting.
- Add notebook tables that display generated examples and shrink witnesses.
- Later: integrate true property minimization when Veyra gets richer syntax.
