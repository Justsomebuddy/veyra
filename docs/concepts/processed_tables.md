# Processed Tables

## 1. Purpose

Veyra is now both a theory seed and a small experimental system. Processed tables make the experiments reproducible.

Generated artifacts live in:

`data/processed/`

## 2. Artifact types

**DEF-040 — Processed table artifact.**

A processed table artifact is a CSV or JSON file generated from the current Veyra Core code with explicit parameters.

Current artifact families:

1. `spectrum_*.csv` — resonance spectrum rows for a chosen whole mode.
2. `compression_*.csv` — compression scores for the same candidate space.
3. `prime_variants_*.csv` — numeric/ordered/cyclic/resonance prime profiles.
4. `counterexamples_*.json` — echo splits, stitch commutators, and weave incompatibilities.
5. `phase_resonance_*.csv` — ordered/cyclic phase resonance rows.
6. `approx_resonance_*.csv` — bounded-defect near-resonance rows.
7. `cyclic_weave_*.csv` — ordered/cyclic weave comparison rows.
8. `tact_aura_costs_*.csv` — context-derived tact similarity and cost rows.
9. `weighted_resonance_*.csv` — severity-weighted near-resonance rows.
10. `core_language_coverage_matrix.csv` — Core Language mutation coverage rows.
11. `core_language_span_diagnostics.csv` — exact parser diagnostic/source-span rows.
12. `manifest.json` — parameter and file summary for the generation run.

## 3. Default generation

```bash
python3 scripts/generate_tables.py \
  --whole abac \
  --alphabet abc \
  --max-part-len 2 \
  --max-mode-len 4 \
  --max-defects 1 \
  --weighted-budget 0.5
```

## 4. Interpretation

Tables are not proofs. They are finite evidence and counterexample search surfaces.

A table row may support a conjecture, refute a careless claim, or suggest a better definition. Any theorem must still enter `THEOREMS.md` and proof/refutation process.

## 5. Hygiene rule

Whenever a generated table changes because definitions changed, update:

- `CHANGELOG.md` when behavior or interpretation is user-visible,
- relevant docs or theorem registry if meanings changed.
