# Quantum QFT Period Shadows Q8

**Date:** 2026-07-08
**Status:** finite `QFT_4` period-shadow rows implemented; not Shor-scale period finding.
**Implementation:** `src/core/quantum/qft_period.py`, `src/core/certificates/quantum_qft.py`.
**Certificate:** `quantum_qft_period_q8`.

## Purpose

Q8 implements the TODO line:

```text
period -> phase orbit -> resonance -> measurement shadow
```

The layer uses an exact four-point QFT over phases `1, i, -1, -i`. It maps finite coset-period states to frequency-support shadows, records offset phase echo, and names a false-period obstruction.

## Implemented rows

| Row | Signal |
|---|---|
| `Q8-PERIOD-1-OFFSET-0` | uniform period-1 support maps to frequency `0` |
| `Q8-PERIOD-2-OFFSET-0` | support `{0,2}` maps to frequencies `0,2` |
| `Q8-PERIOD-4-OFFSET-0` | basis support `{0}` maps to all four frequencies |
| `Q8-OFFSET-ECHO` | period-2 offsets have same measurement distribution but different phase amplitudes |
| `Q8-PERIOD-OBSTRUCT` | adjacent support `{0,1}` falsely claimed as period 2 leaks to odd frequencies |

## Current counts

`quantum_qft_period_summary()` reports:

```python
{
    "period_rows": 3,
    "ready_period_rows": 3,
    "offset_echo_rows": 1,
    "obstruction_rows": 1,
    "frequency_hits": 3,
    "overclaims": 0,
}
```

The Q3 baseline ledger now includes `Q8-QFT-PERIOD`, giving 15 current quantum baseline rows across 9 families.

## Boundary

Q8 is finite `N=4` Fourier arithmetic only. It is not Shor's algorithm, not scalable period finding, not a full QFT library, not a simulator, and not a quantum-advantage claim.

## Verification

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. python3 -m pytest -q tests/quantum/test_quantum_qft_period.py tests/quantum/test_quantum_baselines.py tests/shadows/test_certify.py
PYTHONPATH=. python3 scripts/certify_veyra.py
the complete verification suite
```

Expected Q8 signal: `quantum_qft_period_q8` passes, `quantum_baseline_q3` reports 15 rows / 9 families, and full verification reports `57/57` certificates.
