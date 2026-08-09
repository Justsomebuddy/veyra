# Quantum Circuit Compression Q9

**Date:** 2026-07-08
**Status:** finite peephole/observer-preserving compression rows implemented; no compiler-optimality claim.
**Implementation:** `src/core/quantum/circuit_compression.py`, `src/core/certificates/quantum_compression.py`.
**Certificate:** `quantum_circuit_compression_q9`.

## Purpose

Q9 closes the circuit-compression TODO at finite scale. It records when a short circuit word can be replaced by a cheaper word under one of three finite relations:

1. exact matrix equality;
2. global-phase normalization;
3. observer-preserving echo on a declared input and observer.

## Rows

| Row | Source | Reduced | Relation | Witness |
|---|---|---|---|---|
| `Q9-REDUCE-HH` | `H,H` | `I` | exact reduction | `H² = I` |
| `Q9-REDUCE-XX` | `X,X` | `I` | exact reduction | `X² = I` |
| `Q9-REDUCE-SSSS` | `S,S,S,S` | `I` | exact reduction | `S⁴ = I` |
| `Q9-PHASE-XZ-ZX` | `X,Z` | `Z,X` | global phase | `XZ = -ZX` |
| `Q9-OBS-S-I-Z0` | `S` | `I` | observer-preserving | same `Z` shadow on `|0>` |
| `Q9-OBS-Z-I-ZPLUS` | `Z` | `I` | observer-preserving | same `Z` shadow on `|+>` |

## Baseline

Q3 now adds `Q9-CIRCUIT-COMPRESS` under `classical-compiler-peephole`. The baseline is explicit: finite matrix equality, global-phase checks, and observer-projection equality.

## Boundary

Q9 is a finite peephole ledger only. It is not a general quantum compiler, not a proof of optimal compression, not a scalable circuit optimizer, and not a quantum-advantage claim.

## Verification

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. python3 -m pytest -q tests/quantum/test_quantum_circuit_compression.py tests/quantum/test_quantum_baselines.py tests/shadows/test_certify.py
PYTHONPATH=. python3 scripts/certify_veyra.py
the complete verification suite
```

Expected Q9 signal: `quantum_circuit_compression_q9` passes, `quantum_baseline_q3` reports 16 rows / 10 families, and full verification reports `59/59` certificates after S5.
