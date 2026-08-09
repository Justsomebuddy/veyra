# Quantum Gate Identity Q6

**Date:** 2026-07-07
**Status:** finite exact gate identity catalog implemented; not a full quantum compiler.
**Implementation:** `src/core/quantum/gate_identities.py`, `src/core/certificates/quantum_gates.py`.
**Certificate:** `quantum_gate_identity_q6`.

## Purpose

Q6 turns the gate-identity TODO into an executable ledger for compiler verification. It checks small exact Clifford-style identities with symbolic `Q(√2)` and complex phase amplitudes, while keeping the classical matrix/tableau baseline explicit.

## Implemented rows

| Row family | Signal |
|---|---|
| `GateIdentityRow` | exact or global-phase identity row with source/target words |
| `GateIdentityBaselineRow` | classical matrix/tableau/peephole baseline row |
| one-qubit identities | `HH=I`, `XX=I`, `ZZ=I`, `SS=Z`, `S^4=I`, `HXH=Z`, `HZH=X` |
| commutation row | `XZ = -ZX` as global-phase equivalence |
| CNOT rows | `CNOT^2=I`, control-X propagation, target-X stability |

## Current counts

`quantum_gate_identity_summary()` reports:

```python
{
    "rows": 11,
    "ready": 11,
    "exact_identities": 10,
    "phase_identities": 1,
    "cnot_rows": 3,
    "baseline_rows": 3,
    "stronger_claims": 0,
    "overclaims": 0,
}
```

The Q3 baseline ledger includes `Q6-GATE-ID`; after Q7 it also includes `Q7-ERROR-OBS`, giving 14 current quantum baseline rows.

## Boundary

This is a finite exact identity catalog for local compiler-style rewrites. It is not a general quantum compiler, not a universal Clifford tableau implementation, not a proof of circuit optimization advantage, and not a quantum speedup claim.

## Verification

```bash
PYTHONPATH=. python3 -m pytest -q tests/quantum/test_quantum_gate_identities.py tests/quantum/test_quantum_baselines.py tests/shadows/test_certify.py
the complete verification suite
```

Expected Q6 signal: `quantum_gate_identity_q6` passes and full verification reports `54/54` certificates after Q7.
