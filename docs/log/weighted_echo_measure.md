# Weighted echo measure seed

## Status

Sprint I bounded measure-like seed. This is not full measure theory; it is a finite certificate layer for weighted echo coverage, additivity, overlap obstruction, and tact pushforward rows.

## Executable files

| Surface | File | Certificate |
|---|---|---|
| Finite weighted measure rows | `src/core/shadows/weighted_measure.py` | `weighted_echo_measure` |
| Certificate hook | `src/core/certificates/weighted_measure.py` | `certify_weighted_echo_measure()` |
| Tests | `tests/shadows/test_weighted_measure.py` | 6 targeted tests |

## Canonical fixture

`weighted_echo_measure()` has three atoms:

| Atom | Tact | Weight | Normalized mass |
|---|---:|---:|---:|
| `alpha` | `warm` | `1` | `1/6` |
| `beta` | `cool` | `2` | `1/3` |
| `gamma` | `cool` | `3` | `1/2` |

Total raw weight is `6` and all event masses are exact `RatioMode` shadows.

## Rows

### Event/complement coverage

`coverage_row(measure, "alpha-beta", {alpha,beta})` records:

- event mass: `1/2`;
- complement mass: `1/2`;
- status: `covered`;
- obstruction: `none`.

### Finite additivity

`finite_additivity_row(measure, "partition", {alpha}, {beta,gamma})` records exact partition additivity:

- left mass: `1/6`;
- right mass: `5/6`;
- intersection mass: `0`;
- union mass: `1`;
- relation: `additive`.

### Overlap obstruction

`overlap_gap_card()` records the finite counterexample to naive additivity for overlapping events `{alpha,beta}` and `{beta,gamma}`.

The card relation is `blocked-naive` with obstruction `overlap-mass`; this preserves the correction term instead of silently double-counting `beta`.

### Tact pushforward

`pushforward_by_tact()` folds atoms by tact labels:

| Target tact | Source atoms | Mass |
|---|---|---:|
| `warm` | `alpha` | `1/6` |
| `cool` | `beta,gamma` | `5/6` |

Each row has status `preserved` when source and target masses match.

## Definition ledger

| ID | Meaning |
|---|---|
| `DEF-I1` | `WeightedEchoAtom` is a finite atom with nonnegative exact weight and tact label. |
| `DEF-I2` | `WeightedEchoMeasure` is a finite unique-atom measure with positive total weight. |
| `DEF-I3` | `CoverageRow` records event mass and complement mass under a finite observer. |
| `DEF-I4` | `AdditivityRow` records partition additivity or explicit overlap correction. |
| `DEF-I5` | `PushForwardRow` records mass preservation after folding atoms by tact. |
| `LEM-I1` | The canonical `{alpha,beta}` event has mass `1/2` and complement `1/2`. |
| `LEM-I2` | The canonical `{alpha}` / `{beta,gamma}` partition has union mass `1`. |
| `LEM-I3` | Folding by tact preserves warm/cool masses `1/6` and `5/6`. |
| `OBS-I1` | Overlapping events require the `overlap-mass` correction and block naive additivity. |

## Verification

After this seed, Essence/Core has 23 executable layers and the certificate suite has 30 rows. Verified on 2026-06-06: targeted weighted-measure/core/Sage/certify tests passed `23/23`; full the complete verification suite passed with pytest `363/363`, certificates `30/30`, Sage smoke ok, doctest `41/41`, and hygiene clean.
