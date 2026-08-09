# Quantum Error Obstruction Q7

**Date:** 2026-07-07
**Status:** named finite error-obstruction catalog implemented; not a full quantum debugger.
**Implementation:** `src/core/quantum/error_obstructions.py`, `src/core/certificates/quantum_obstructions.py`.
**Certificate:** `quantum_error_obstruction_q7`.

## Purpose

Q7 turns the quantum-debugging TODO into explicit obstruction rows. Instead of a binary pass/fail signal, each row names the observer, expected shadow, observed shadow, and witness that explains how a finite toy circuit/code failed.

## Implemented obstruction rows

| Row | Family | Observer | Witness |
|---|---|---|---|
| `Q7-PHASE-BREAK` | phase-break | gate phase | one missing `S` means `S≠Z` while `S²=Z` |
| `Q7-INTERFERENCE-LOSS` | interference-loss | Z-distribution | `HH|0>` restores `|0>`, but `H|0>` stays split |
| `Q7-LEAKAGE` | leakage | basis support | nonzero `L` mass outside `{0,1}` |
| `Q7-NON-UNITARITY` | non-unitarity | norm | bad `DROP1` gate sends `|1>` to zero norm |
| `Q7-SYNDROME-AMBIGUITY` | syndrome-ambiguity | syndrome+correction | Q5 double-error rows share syndrome but flip logical result |
| `Q7-BRANCH-DISTINGUISHABLE` | branch-distinguishability | logical-after | Q5 split rows are recovery-equivalent but logically distinct |

## Current counts

`quantum_error_obstruction_summary()` reports:

```python
{
    "rows": 6,
    "ready": 6,
    "families": 6,
    "amplitude_rows": 4,
    "qec_rows": 2,
    "overclaims": 0,
}
```

The Q3 baseline ledger now includes `Q7-ERROR-OBS`, giving 14 current quantum baseline rows across 8 families.

## Boundary

Q7 is a finite named error-characterization ledger. It is not a full quantum debugger, not a full Hilbert-space simulator, not a proof assistant, not a compiler, and not a quantum-advantage claim. It only says these six finite failure surfaces are executable and baseline-known.

## Verification

```bash
PYTHONPATH=. python3 -m pytest -q tests/quantum/test_quantum_error_obstructions.py tests/quantum/test_quantum_baselines.py tests/shadows/test_certify.py
PYTHONPATH=. python3 scripts/certify_veyra.py
the complete verification suite
```

Expected Q7 signal: `quantum_error_obstruction_q7` passes, `quantum_baseline_q3` reports 14 rows / 8 families, and full verification reports `54/54` certificates.
