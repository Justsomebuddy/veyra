# Quantum Stabilizer Q2

**Date:** 2026-07-07
**Status:** finite syndrome/logical observer layer implemented; not a full stabilizer formalism.
**Implementation:** `src/core/quantum/stabilizer.py`, `src/core/certificates/quantum_stabilizer.py`.
**Certificate:** `quantum_stabilizer_q2`.

## Purpose

Q2 extends Q1 from finite gates and Born-shadow observers into a small stabilizer/QEC diagnostic layer. The model is the 3-qubit repetition code over computational basis rows.

## Implemented rows

| Row family | Signal |
|---|---|
| `PauliRow` | finite `X_i ∘ X_i = I` involution rows |
| `SyndromeRow` | `Z0Z1`, `Z1Z2` syndrome signs and single-error correction |
| `StabilizerEchoRow` | same syndrome observer but different logical observer |
| `LogicalObstructionRow` | double-error rows that defeat single-error correction |

## Current counts

`quantum_stabilizer_summary()` reports:

```python
{
    "pauli_rows": 3,
    "syndrome_rows": 8,
    "single_error_corrected": 8,
    "echo_split_rows": 4,
    "logical_obstructions": 3,
    "overclaims": 0,
}
```

## Boundary

This is a finite repetition-code observer model. It is not a general Clifford simulator, not a full stabilizer tableau, not a fault-tolerance proof, and not a quantum advantage claim. The value is the Veyra-style split between syndrome echo and logical distinguishability.

## Verification

```bash
PYTHONPATH=. python3 -m pytest -q tests/quantum/test_quantum_stabilizer.py tests/shadows/test_certify.py
the complete verification suite
```

Expected Q2 signal: `quantum_stabilizer_q2` passes and full verification reports `49/49` certificates.
