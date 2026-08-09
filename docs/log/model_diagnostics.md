# Model diagnostics seed

## Status

Sprint K bounded model-diagnostics seed. This is not a general theory of model selection; it is a finite certificate layer for residual rows, aggregate fit reports, baseline comparison, and anomaly obstruction.

## Executable files

| Surface | File | Certificate |
|---|---|---|
| Finite model diagnostics | `src/core/shadows/model_diagnostics.py` | `model_diagnostics` |
| Certificate hook | `src/core/certificates/science.py` | `certify_model_diagnostics()` |
| Tests | `tests/shadows/test_model_diagnostics.py` | 6 targeted tests |

## Rows

### Residual row

`residual_row(ModelObservation("p1", 9/4, 2), 1/2)` records:

- signed residual: `1/4`;
- absolute residual: `1/4`;
- status: `within-band`;
- obstruction: `none`.

### Fit report

`model_fit_report("candidate", canonical_model_observations(), 1/2)` aggregates three finite observations:

- total absolute error: `1/2`;
- max absolute error: `1/4`;
- status: `fit`.

### Baseline comparison

`compare_model_reports("candidate-vs-baseline", candidate, baseline)` compares total absolute error:

| Model | Total absolute error |
|---|---:|
| candidate | `1/2` |
| baseline | `5/2` |

The comparison status is `improved` only because the candidate has lower finite error.

### Anomaly obstruction

`anomaly_obstruction_card()` records observation `5` against prediction `2` with tolerance `1`:

- residual: `3`;
- relation: `blocked`;
- obstruction: `residual-outlier`.

## Definition ledger

| ID | Meaning |
|---|---|
| `DEF-K1` | `ModelObservation` is one exact observed/predicted model point. |
| `DEF-K2` | `ResidualRow` records signed residual, absolute residual, tolerance, and obstruction. |
| `DEF-K3` | `ModelFitReport` aggregates finite residual rows by total and maximum absolute error. |
| `DEF-K4` | `ModelComparisonRow` compares candidate and baseline total absolute errors. |
| `LEM-K1` | The canonical candidate has total absolute error `1/2` and max error `1/4`. |
| `LEM-K2` | The canonical baseline has total absolute error `5/2`, so the candidate is improved. |
| `OBS-K1` | The spike fixture is blocked by `residual-outlier`. |

## Verification

After this seed, Essence/Core has 25 executable layers and the certificate suite has 32 rows. Verified on 2026-06-06: targeted model/core/Sage/certify tests passed `23/23`; full the complete verification suite passed with pytest `375/375`, certificates `32/32`, Sage smoke ok, doctest `41/41`, and hygiene clean.
