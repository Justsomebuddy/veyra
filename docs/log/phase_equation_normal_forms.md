# Phase Equation Normal Forms Seed

**Date:** 2026-06-06
**Status:** executable finite seed.
**Implementation:** `src/core/numbers/phase_equations.py`, `src/core/certificates/phase_equations.py`.
**Certificate:** `phase_equation_normal_forms`.

## Scope

This seed adds a bounded rational phase dictionary for equation-shaped trigonometry requests:

- coordinate rows for `cos θ = r` and `sin θ = r`;
- full pair rows for `(cos θ, sin θ) = (a,b)`;
- theorem cards that distinguish resolved finite basis hits from blocked requests;
- inverse-phase obstruction cards for requests that are not unit phases or are outside the dictionary.

It is an inverse-trig/equation normal-form seed, not a full `arcsin`/`arccos` implementation.

## Finite basis

The current dictionary is intentionally small:

| Label | cos | sin | Role |
|---|---:|---:|---|
| `id` | `1` | `0` | identity phase |
| `a` | `3/5` | `4/5` | Pythagorean phase |
| `-a` | `3/5` | `-4/5` | conjugate phase |
| `b` | `5/13` | `12/13` | second Pythagorean phase |
| `-b` | `5/13` | `-12/13` | conjugate phase |
| `neg` | `-1` | `0` | negative identity shadow |

## Row behavior

`phase_coordinate_row("cos", 3/5)` resolves to `a` and `-a` because both share the same cosine shadow.

`phase_pair_row(3/5, 4/5)` resolves uniquely to `a`.

`phase_pair_row(2, 0)` is blocked with `unit-gap`, because `2² + 0² != 1`.

`phase_pair_row(0, 1)` is blocked with `basis-gap`, because it is a unit phase but not in the finite dictionary.

## Certificate checks

The certificate requires:

1. coordinate row match for `cos θ = 3/5`;
2. pair normal form for `(3/5, 4/5)`;
3. accepted normal-form theorem card;
4. rejected inverse-phase cards for `unit-gap` and `basis-gap`;
5. the four-item D5 checklist.

## Non-goals

- No transcendental angle values.
- No complete inverse-trigonometric solving.
- No continuous circle parameterization.
- No claim that the finite dictionary is complete.

## Verification

```bash
PYTHONPATH=. python3 -m pytest -q tests/numbers/test_phase_equations.py tests/shadows/test_certify.py tests/kernel/test_essence_core.py tests/sage/test_veyra_sage_essence.py tests/sage/test_veyra_sage.py
the complete verification suite
```

Expected after this seed: active pytest `337/337`, certificates `27/27`, Sage smoke ok, doctest `41/41`, line hygiene `0` files over 300.
