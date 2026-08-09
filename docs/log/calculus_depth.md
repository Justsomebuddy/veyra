# Veyra calculus-depth seed

**Date:** 2026-06-05
**Status:** executable polynomial-shadow seed, not full transcendental calculus.

## Aim

`calculus-depth` was an explicit school-to-11 gap after the Core Language v0.8 curriculum map.  This layer starts closing it by making derivative and integral rules executable over Veyra ratio-polynomial shadows.

The point is not to pretend school calculus is complete.  The point is to give the project a native acceptance surface:

```text
local linearization + product rule + chain rule + integral coherence
```

## Executable objects

Implemented in `src/core/shadows/calculus_depth.py`:

- `LocalLinearization` — first-order observer shadow at an anchor;
- `IntegralCoherence` — antiderivative interval certificate;
- `compose_polynomials()` — polynomial composition;
- `antiderivative_polynomial()` — exact zero-constant antiderivative;
- `local_linearization()` and `linearization_error()`;
- `product_rule_card()`;
- `chain_rule_card()`;
- `integral_coherence_card()`;
- `calculus_depth_checklist()`.

Every function logs entry/exit and stays in the finite ratio-polynomial layer.

## Theorem-card seeds

| Card | Claim | Success relation | Obstruction |
|---|---|---|---|
| `calculus-product-rule` | derivative of product equals `f'g + fg'` | `coherent` | `product-derivative-gap` |
| `calculus-chain-rule` | derivative of composition equals `(f'∘g)g'` | `coherent` | `chain-derivative-gap` |
| `calculus-integral-coherence` | antiderivative difference matches expected interval value | `coherent` | `integral-gap` |

## Current limits

This is still a seed:

- transcendental functions are now only finite formal seeds in `docs/log/transcendental_limit_seed.md`;
- no measure theory;
- no analytic convergence proof beyond existing finite completion seeds;
- no dedicated Sage facade yet;
- no theorem-registry stable export rows yet.

Therefore the curriculum row moves from `gap` to `seeded`, not to fully `covered`.

## Verification

Tests:

```bash
PYTHONPATH=. python3 -m pytest -q tests/shadows/test_calculus_depth.py tests/shadows/test_certify.py tests/kernel/test_essence_core.py
```

Full verification remains the complete verification suite.

## Sage facade

`veyra_sage/calculus.py` now exposes `VeyraCalculusLab`, `build_calculus_depth_notebook()`, and `calculus_depth_lab_summary()` for Sage-facing notebook smoke checks.
