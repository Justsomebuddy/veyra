# Scale-memory logarithm recovery

## Status

Sprint L practical logarithm seed. This layer upgrades `DEF-067` from bounded discrete-log shadow into a reusable Veyra recovery surface: logarithm is treated as hidden transition-depth recovery, not as a primitive inverse function.

The scope is finite: no generic discrete-log algorithm follows from these bounded rows.

## Executable files

| Surface | File | Certificate |
|---|---|---|
| Scale-memory log rows | `src/core/shadows/scale_memory_log.py` | `scale_memory_log` |
| Certificate hook | `src/core/certificates/scale_memory.py` | `certify_scale_memory_log()` |
| Practice script | `scripts/scale_memory_log_demo.py` | visible `[1/5]` progress + JSON summary |
| Tests | `tests/shadows/test_scale_memory_log.py` | exact/residual/cyclic/obstruction/script checks |

## Core definition

`recover_transition_depth(label, base, target, max_depth, tolerance)` searches finite depths `n` such that:

```text
base^n ≈ target
```

and returns a certificate row:

```text
candidate_depth, candidate_value, residual, tolerance, status, obstruction
```

This reframes logarithm as:

```text
log = recover_depth(tact, origin, target, observer)
```

## Practice rows

### Exact transition-depth recovery

The exact row recovers:

```text
2^5 = 32
```

Expected certificate:

| Field | Value |
|---|---:|
| status | `exact` |
| candidate depth | `5` |
| residual | `0` |
| obstruction | `none` |

### Residual log recovery

The residual row searches for the best finite depth near target `20`:

| Candidate | Value | Residual |
|---:|---:|---:|
| `2^4` | `16` | `4` |
| `2^5` | `32` | `12` |

With tolerance `4`, the certificate reports:

```text
status=approximate, candidate_depth=4, residual=4
```

### Cyclic unwrap recovery

The finite-field unwrap fixture recovers:

```text
5^17 mod 97 = 83
```

Expected certificate:

| Field | Value |
|---|---:|
| modulus | `97` |
| generator | `5` |
| target | `83` |
| candidate depth | `17` |
| status | `exact` |

This is the toy shape of a discrete-log recovery certificate: linear transition history is observed through a cyclic shadow.

### Obstruction card

The collapsed-generator card uses:

```text
1^n mod 97 = 2
```

The orbit collapses immediately, so the certificate reports:

```text
status=blocked, obstruction=cycle-collapse, cycle_length=1
```

## Script

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/scale_memory_log_demo.py
```

The script prints five progress stages and a JSON summary for exact, residual, cyclic, and obstruction recovery.

## Definition ledger

| ID | Meaning |
|---|---|
| `DEF-L1` | `TransitionDepthRow` is one finite candidate `base^n` against a target shadow. |
| `DEF-L2` | `ScaleMemoryLogCertificate` records best depth, residual, tolerance, status, and obstruction. |
| `DEF-L3` | `CyclicDepthCertificate` records finite cyclic unwrap depth or cycle/search obstruction. |
| `LEM-L1` | The exact fixture recovers depth `5` for `2^n=32`. |
| `LEM-L2` | The residual fixture chooses depth `4` for target `20` with residual `4`. |
| `LEM-L3` | The cyclic fixture recovers depth `17` for `5^n mod 97 = 83`. |
| `OBS-L1` | Generator `1` against target `2 mod 97` is blocked by `cycle-collapse`. |

## Verification

Verified on 2026-06-06: targeted scale-memory/core/Sage/certify tests passed `24/24`; full the complete verification suite passed with pytest `382/382`, certificates `33/33`, Sage smoke ok, doctest `41/41`, and hygiene clean.
