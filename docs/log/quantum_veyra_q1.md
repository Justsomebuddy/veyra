# Quantum Veyra Q1

**Date:** 2026-07-07
**Status:** finite observer-indexed quantum seed implemented; not a full quantum apparatus.
**Implementation:** `src/core/quantum/veyra.py`, `src/core/certificates/quantum_veyra.py`.
**Certificate:** `quantum_veyra_q1`.

## Purpose

Q1 starts the quantum TODO layer as a bounded executable seed. It maps quantum computation into Veyra's observer discipline without claiming superiority over Hilbert-space, stabilizer, or tensor-network methods.

## Implemented vocabulary

| Quantum | Q-Veyra seed |
|---|---|
| finite state | `QMode` with exact symbolic amplitudes |
| amplitude algebra | `QAmp` over complex `Q(√2)` via `Rad2` |
| gate | `QGate` matrix transformer |
| measurement basis | `observer_distribution(mode, "Z"/"X")` |
| same distribution | `qecho(left, right, observer)` |
| obstruction | theorem-card relation `obstruction` |
| entanglement seed | `bell_state()` plus rank-one factorization obstruction |

## Theorem-card seed

`quantum_theorem_cards()` returns six finite rows:

| ID | Claim | Signal |
|---|---|---|
| `Q-HH` | `H ∘ H = I` | exact matrix identity |
| `Q-XX` | `X ∘ X = I` | exact matrix identity |
| `Q-CNOT-NORM` | CNOT preserves norm on seed states | finite norm row |
| `Q-BELL-NONFACT` | Bell seed is not product-factorable | obstruction row |
| `Q-ZX-SHADOW` | Z and X observers differ on `|0>` | distinguishability row |
| `Q-NO-CLONE` | finite no-cloning obstruction for `|+>` | linearity obstruction row |

## Boundary

This is not full quantum mechanics. Q1 has finite tensor seeds, exact Born-shadow distributions, and seed norm checks, but no general Hilbert-space simulator, no stabilizer benchmark ledger, no tensor-network comparison, and no broad formal proof artifact.

## Verification

```bash
PYTHONPATH=. python3 -m pytest -q tests/quantum/test_quantum_veyra.py tests/shadows/test_certify.py
the complete verification suite
```

Expected Q1 signal: `quantum_veyra_q1` passes and full verification reports `48/48` certificates.
