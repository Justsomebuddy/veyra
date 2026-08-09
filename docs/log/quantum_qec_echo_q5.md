# Quantum QEC Echo Q5

**Date:** 2026-07-07
**Status:** finite observer-indexed QEC echo layer implemented; not a fault-tolerance proof.
**Implementation:** `src/core/quantum/qec_echo.py`, `src/core/certificates/quantum_qec.py`.
**Certificate:** `quantum_qec_echo_q5`.

## Purpose

Q5 expands the Q2 repetition-code seed into explicit observer-indexed QEC echo rows. The point is not to simulate arbitrary quantum error correction; the point is to make syndrome echo, correction echo, logical distinction, and ambiguity obstruction first-class Veyra rows.

## Implemented rows

| Row family | Signal |
|---|---|
| `QECBranchRow` | logical 0/1 branches under weight 0/1/2 bit-flip errors |
| `QECObserverFamilyRow` | syndrome, recovery, logical, and diagnostic observer families |
| `QECSplitEchoRow` | same syndrome/correction echo while logical observer differs |
| `QECAmbiguityRow` | single-vs-double errors share recovery shadow but differ after correction |

## Current counts

`quantum_qec_echo_summary()` reports:

```python
{
    "branches": 14,
    "observer_families": 4,
    "single_error_corrected": 8,
    "double_error_obstructions": 6,
    "split_echo_rows": 4,
    "ambiguity_rows": 6,
    "overclaims": 0,
}
```

The Q3 baseline ledger covers Q5 with `Q5-QEC-ECHO` and `Q5-QEC-AMBIGUITY` rows; Q6 adds `Q6-GATE-ID`, and Q7 adds `Q7-ERROR-OBS`.

## Boundary

This is a finite 3-qubit repetition-code diagnostic. It is not a general stabilizer simulator, not a surface-code decoder, not a threshold/fault-tolerance theorem, not a topological-code proof, and not a quantum advantage claim.

## Verification

```bash
PYTHONPATH=. python3 -m pytest -q tests/quantum/test_quantum_qec_echo.py tests/quantum/test_quantum_baselines.py tests/shadows/test_certify.py
the complete verification suite
```

Expected Q5 signal: `quantum_qec_echo_q5` passes and full verification reports `52/52` certificates.
