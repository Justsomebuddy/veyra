# Veyra convergence algebra seed

**Date:** 2026-06-06
**Status:** executable finite convergence seed, not full real analysis

## Aim

This layer strengthens the previous finite transcendental/limit seed with a reusable convergence surface:

```text
Cauchy tail + majorant bound + nested interval shrinkage + radius guard
```

The goal is to make convergence claims explicit, bounded, and falsifiable before any stronger real-analysis or analytic-continuation work.

## Executable objects

Implemented in `src/core/shadows/convergence_algebra.py`:

- `CauchyTailCertificate` — finite tail diameter under a rational tolerance observer;
- `MajorantBound` — observed-vs-bound row;
- `NestedIntervalCertificate` — finite nested interval and width-shrink row;
- `RadiusGuard` — finite domain/radius row for series points;
- theorem cards for Cauchy tails, majorants, nested intervals, and radius guards;
- `convergence_algebra_checklist()`.

## Canonical witness

| Row | Exact result |
|---|---|
| Cauchy tail on `1, 3/2, 7/4, 15/8, 31/16` with tail `3` | max distance `3/16 <= 1/2` |
| Majorant row | observed `3/16 <= 1/4` |
| Nested intervals | final width `1/4` |
| Radius guard for `log1p` point `1/2` | inside radius `1` |

## Certificate

`src/core/certificates/convergence.py` adds `convergence_algebra` to the executable certificate suite.
Essence/Core now records 19 executable layers.

## Limits

This seed does not claim:

- complete metric-space theory;
- construction of all real numbers;
- infinite proof by default;
- analytic continuation;
- automatic convergence for arbitrary series.

Every claim remains finite, exact, and observer-bounded.

## Verification

```bash
PYTHONPATH=. python3 -m pytest -q tests/shadows/test_convergence_algebra.py tests/shadows/test_certify.py tests/kernel/test_essence_core.py
the complete verification suite
```
