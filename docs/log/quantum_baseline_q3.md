# Quantum Baseline Q3

**Date:** 2026-07-08
**Status:** baseline ledger for current Q1/Q2/Q4/Q5/Q6/Q7/Q8/Q9 rows implemented; no quantum advantage claim.
**Implementation:** `src/core/quantum/baselines.py`, `src/core/certificates/quantum_baselines.py`.
**Certificate:** `quantum_baseline_q3`.

## Purpose

Q3 adds the missing anti-overclaim comparison layer for the quantum track. Every current finite Q-Veyra row is paired with a known classical, tensor-product, stabilizer-tableau, coding-theory, topology, matrix, debugging, Fourier-analysis, or compiler-peephole baseline.

## Baseline families

| Family | Covered rows |
|---|---|
| classical linear algebra | `Q-HH`, `Q-XX`, `Q-CNOT-NORM`, `Q-NO-CLONE` |
| tensor product | `Q-BELL-NONFACT` |
| classical probability | `Q-ZX-SHADOW` |
| stabilizer tableau | `Q2-SYNDROME`, `Q2-ECHO-SPLIT` |
| classical coding theory | `Q2-DOUBLE-ERROR`, `Q5-QEC-AMBIGUITY` |
| graph topology | `Q4-TOPO-ECHO` |
| QEC observer echo | `Q5-QEC-ECHO` via stabilizer-tableau baseline |
| compiler matrix identities | `Q6-GATE-ID` |
| named debugging obstructions | `Q7-ERROR-OBS` |
| period/Fourier shadows | `Q8-QFT-PERIOD` |
| circuit compression | `Q9-CIRCUIT-COMPRESS` |

## Current counts

`quantum_baseline_summary()` reports 16 benchmarked rows, 10 baseline families, 6 Q1 rows, 3 Q2 rows, 1 Q4 row, 2 Q5 rows, 1 Q6 row, 1 Q7 row, 1 Q8 row, 1 Q9 row, zero stronger claims, and zero overclaims.

## Boundary

This ledger says the current Q-Veyra rows are baseline-known and auditably comparable. It does not say Veyra is faster, more complete, a full simulator, or a quantum proof assistant. Future quantum rows must enter this ledger before any broader apparatus claim.

## Verification

```bash
PYTHONPATH=. python3 -m pytest -q tests/quantum/test_quantum_baselines.py tests/shadows/test_certify.py
the complete verification suite
```

Expected Q3 signal: `quantum_baseline_q3` passes and full verification reports `59/59` certificates after S5/Q9.
