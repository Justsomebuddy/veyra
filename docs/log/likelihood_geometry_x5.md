# X5 — Likelihood geometry and residual families

**Date:** 2026-07-07  
**Status:** Sprint X5 closed as a finite likelihood/residual certificate layer.  
**Implementation:** `src/core/shadows/likelihood_geometry.py`, `src/core/certificates/likelihood.py`, `veyra_sage/likelihood_geometry.py`.  
**Certificate:** `likelihood_geometry_x5`.

## Claim boundary

X5 does **not** add a continuous likelihood manifold, Bayesian theory, or regression framework. It adds a finite, executable geometry of likelihood rows plus domain-specific residual-family certificates:

- likelihood geometry is a finite parameter grid;
- adjacent grid points carry exact rational slope shadows;
- peak claims are finite cards, including tie obstruction handling;
- residual-family claims are accepted or blocked per finite domain report.

This keeps statistical language inside Veyra's observer-indexed certificate discipline.

## Likelihood geometry rows

| Row | Meaning |
|---|---|
| `LikelihoodPoint` | exact finite parameter/likelihood pair from a Bernoulli row |
| `LikelihoodSegment` | adjacent parameter-grid segment with exact likelihood gap and slope |
| `LikelihoodPeakCard` | finite best candidate and peak/tie status |

Default fixture: successes `3`, trials `4`, candidate parameters `{1/4, 1/2, 3/4}`.

| Parameter | Likelihood |
|---|---|
| `1/4` | `3/256` |
| `1/2` | `1/16` |
| `3/4` | `27/256` |

Adjacent finite slopes are `13/64` and `11/64`, so the fixture has two rising segments and a unique finite peak at `p=3/4`.

## Residual-family certificates

| Domain | Status | Evidence |
|---|---|---|
| `linear-motion` | `certified` | canonical finite residual family stays inside tolerance `1` |
| `sensor-spike` | `blocked` | residual report contains `residual-outlier` |

The domain label is part of the certificate surface. A residual report is not promoted to a generic statistical theorem unless its finite domain row is accepted.

## Sage surface

`VeyraLikelihoodGeometryLab` exposes JSON-ready rows:

- `likelihood_rows()` — exact parameter/likelihood grid;
- `segment_rows()` — adjacent exact slopes;
- `peak_row()` — finite peak card;
- `residual_rows()` — domain residual-family certificates;
- `checklist()` and `summary()` — Sprint X5 acceptance surface;
- `build_likelihood_geometry_notebook()` — generated global notebook.

The generated artifact is tracked as `notebooks/generated/global/likelihood_geometry.*`. Current generated notebook inventory after X5 is `41` notebooks and `280` cells.

## Verification

```bash
PYTHONPATH=. python3 -m pytest -q tests/shadows/test_likelihood_geometry.py tests/sage/test_veyra_sage_likelihood_geometry.py tests/shadows/test_certify.py tests/sage/test_veyra_sage.py
the complete verification suite
```

Expected contract:

- `likelihood_geometry_x5` passes;
- `likelihood_geometry_summary()` reports `likelihood_points=3`, `rising_segments=2`, `blocked_domains=1`;
- `likelihood_geometry_lab_summary()` reports the same rows through the Sage facade;
- global generated notebook artifacts report `41` notebooks / `280` cells.
