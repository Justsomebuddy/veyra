# Real-analysis structure seed

## Status

Sprint H bounded real-analysis seed. This is not full real analysis; it is a finite certificate layer that makes modulus, refinement, and discontinuity-obstruction rows executable.

## Executable files

| Surface | File | Certificate |
|---|---|---|
| Finite real-analysis rows | `src/core/shadows/real_analysis_structure.py` | `real_analysis_structure` |
| Certificate hook | `src/core/certificates/real_analysis.py` | `certify_real_analysis_structure()` |
| Tests | `tests/shadows/test_real_analysis_structure.py` | 5 targeted tests |

## Rows

### Finite modulus grid

`finite_modulus_certificate()` checks all finite grid pairs with input distance below a declared radius.

Stable fixture:

- rule: `x ↦ x²`;
- grid: `{0, 1/4, 1/2, 3/4, 1}`;
- input radius: `1/4`;
- output tolerance: `1/2`;
- checked pairs: `4`;
- max output drift: `7/16`;
- status: `stable`.

This is a finite uniform-continuity shadow, not a universal proof for all real inputs.

### Derivative refinement stability

`derivative_refinement_certificate()` compares symmetric difference quotients across step refinements.

Stable fixture:

- rule: `x ↦ x²`;
- anchor: `2`;
- steps: `1`, `1/2`, `1/4`;
- quotient values: `4`, `4`, `4`;
- status: `stable`.

### Area refinement stability

`area_refinement_certificate()` compares midpoint Riemann rows across slice refinements.

Stable fixture:

- rule: identity;
- interval: `[0,1]`;
- slices: `2`, `4`, `8`;
- values: `1/2`, `1/2`, `1/2`;
- status: `stable`.

### Jump obstruction

`jump_obstruction_card()` records a sampled discontinuity counterexample.

Stable fixture:

- rule: `0` below zero, `1` otherwise;
- anchor: `0`;
- radius: `1`;
- tolerance: `0`;
- relation: `blocked`;
- obstruction: `echo-jump`.

## Definition ledger

| ID | Meaning |
|---|---|
| `DEF-H1` | `FiniteModulusCertificate` is a finite grid epsilon/modulus witness. |
| `DEF-H2` | `RefinementStabilityCertificate` records whether derivative/area refinements have bounded adjacent gaps. |
| `DEF-H3` | `JumpObstruction` is a finite sampled counterexample to no-jump continuity. |
| `LEM-H1` | On the fixture grid, square-rule output drift under input radius `1/4` is bounded by `7/16 ≤ 1/2`. |
| `LEM-H2` | The square-rule symmetric quotient at anchor `2` is refinement-stable for steps `1,1/2,1/4`. |
| `LEM-H3` | The midpoint identity-area row on `[0,1]` is refinement-stable for slices `2,4,8`. |

## Verification

After this seed, Essence/Core has 22 executable layers and the certificate suite has 29 rows. Verified on 2026-06-06: pytest `357/357`, certificates `29/29`, Sage smoke ok, doctest `41/41`, and hygiene clean.
