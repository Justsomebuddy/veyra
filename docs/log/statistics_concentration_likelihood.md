# Statistics Concentration and Likelihood Seed

**Date:** 2026-06-06
**Status:** executable finite seed.
**Implementation:** `src/core/shadows/statistics_concentration.py`, `src/core/certificates/statistics_concentration.py`.
**Certificate:** `statistics_concentration_likelihood`.

## Scope

This seed extends the finite statistics layer beyond intervals/hypotheses into guarded concentration and likelihood rows:

- Chebyshev-style mean bound `variance/(n·radius²)`;
- Hoeffding-style exponent guard `2n·radius²/width²` with exponential tail shadow deferred;
- exact Bernoulli likelihood rows `p^k(1-p)^(n-k)`;
- exact likelihood-ratio theorem card;
- finite decision rows that name true/false positive/negative outcomes.

It is a bounded row/card seed, not asymptotic statistics or complete hypothesis testing.

## Concentration rows

The Chebyshev row keeps all evidence rational.  For variance `3/16`, sample count `4`, and radius `1/2`, the bound is:

```text
(3/16) / (4·(1/2)^2) = 3/16
```

The row is `informative` when the bound is at most `1`; otherwise it is `loose` with obstruction `bound-over-one`.

The Hoeffding row records only the finite exponent guard.  For `n=4`, radius `1/2`, and width `1`, the exponent is:

```text
2·4·(1/2)^2 / 1^2 = 2
```

The exponential tail is deliberately marked `tail-exponential-shadow-deferred`.

## Likelihood geometry

For `k=3`, `n=4`, candidate `p=3/4`:

```text
(3/4)^3 · (1/4) = 27/256
```

For the baseline `p=1/2`:

```text
(1/2)^3 · (1/2) = 1/16
```

The likelihood-ratio card prefers the left row because `(27/256)/(1/16) = 27/16 > 1`.

## Decision error rows

A threshold decision row records:

- score;
- threshold;
- whether a real shift exists;
- decision `reject` / `accept`;
- outcome `true-positive`, `true-negative`, `false-positive`, or `false-negative`.

This makes false positives and false negatives explicit evidence rows rather than hidden testing caveats.

## Non-goals

- No p-values.
- No asymptotic normal approximation.
- No continuous likelihood surface.
- No claim that the Hoeffding exponential tail is fully evaluated here.
- No replacement for statistical modeling assumptions.

## Verification

```bash
PYTHONPATH=. python3 -m pytest -q tests/shadows/test_statistics_concentration.py tests/shadows/test_certify.py tests/kernel/test_essence_core.py tests/sage/test_veyra_sage_essence.py tests/sage/test_veyra_sage.py
the complete verification suite
```

Expected after this seed: active pytest `342/342`, certificates `28/28`, Sage smoke ok, doctest `41/41`, line hygiene `0` files over 300.
