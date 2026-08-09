# Sage seed facades for trig, linear algebra, and statistics

**Status:** executable seed facade, not package-stable Sage extension
**Date:** 2026-06-05
**Scope:** `veyra_sage` rows, notebooks, certificates, and API index

## Purpose

The calculus-depth facade made one school-topic seed visible through `veyra_sage`. This document records the next facade bundle for the already executable seed topics:

- `trigonometry-identities`
- `vectors-matrices`
- `statistics-inference`

The goal is a JSON/notebook-friendly research surface, not a full Sage category or symbolic library.

## Public facades

| Topic | Facade | Summary function | Notebook builder |
|---|---|---|---|
| Trigonometry identities | `VeyraTrigonometryIdentityLab` | `trigonometry_identity_lab_summary()` | `build_trigonometry_identity_notebook()` |
| Linear algebra seed | `VeyraLinearAlgebraLab` | `linear_algebra_seed_lab_summary()` | `build_linear_algebra_seed_notebook()` |
| Statistics inference | `VeyraStatisticsInferenceLab` | `statistics_inference_lab_summary()` | `build_statistics_inference_notebook()` |

All names are exported through `veyra_sage.all` and listed in `docs/reference/veyra_sage_api.md`.

## Row contracts

| Facade | Rows | Ready condition |
|---|---|---|
| `VeyraTrigonometryIdentityLab` | rational phase rows plus Pythagorean/sum/double/inverse cards | four coherent cards and zero unit gap |
| `VeyraLinearAlgebraLab` | matrix action row plus determinant/eigen cards | image `[2, 6]` and determinant-product card coherent |
| `VeyraStatisticsInferenceLab` | Bernoulli family, interval, hypothesis cards, uncertainty row | `p=3/4`, center `2`, uncertainty `3/64` |

Rows intentionally stringify exact ratio shadows so notebook JSON remains stable.

## Certificate hooks

`sage_certificate_suite()` now emits:

- `sage_trigonometry_identities_passed`
- `sage_linear_algebra_seed_passed`
- `sage_statistics_inference_passed`

The generated artifact summary becomes 36 notebooks, 254 cells, 123 markdown cells, and 131 code cells.

## Boundaries

This is a research-lab facade bundle. It does not claim:

- continuous trigonometric evaluation;
- inverse-trig equation solving;
- arbitrary matrix algorithms;
- statistical asymptotics or full hypothesis-test theory;
- package-stable Sage extension semantics.

Those require new theorem registries, negative-pressure tests, and package-boundary review first.


## Sprint G follow-up

2026-06-06: geometry theorem-card exports are now handled separately in `docs/log/geometry_sage_exports.md`; the current generated notebook artifact summary is 41 notebooks, 280 cells, 133 markdown cells, and 147 code cells after the likelihood geometry notebook.
