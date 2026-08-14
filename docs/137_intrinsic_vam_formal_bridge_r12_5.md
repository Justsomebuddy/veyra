# R12.5 — Formal intrinsic-VAM bridge

**Status:** checked preservation bridge; non-promotional
**Date:** 2026-07-29
**Lean:** `leanprover/lean4:v4.30.0-rc2`
**Evidence:** `formal-bridge / general`
**Capability:** `preserves`

## Purpose

R12.5 checks that the supported R7/R9 recurrence image and the R11
observer/echo semantics survive lowering into the exact R12.2 intrinsic IR.
It is the formal link that R12.4 intentionally did not provide.

The domain is deliberately narrow:

```text
bounded valid R12.2/R12.3 lowering image
  <- exact R7 recurrence / R9 intrinsic-mode image
  <- closed R11 observer and echo semantics
```

Arbitrary raw IR, malformed IR, VAMI bytes, legacy VAM values, and attacker
supplied R12.3 receipts are outside the theorem domain.
Public `THM-R12-001..009` correspondence is explicitly restricted by the
Python-aligned ceilings: 2,047 recurrence tacts; 2,048 observer/response or
obstruction nodes; 4,096 intrinsic nodes; and depth/path 128. The internal
universal lemmas remain mathematical helpers and are not bridge evidence.

## Lean semantic mirror

`proofs/lean/VeyraIntrinsicVamBridge.lean` independently defines:

- exact intrinsic anchor, tact, recurrence, mark, path, obstruction, response,
  observation, and echo-outcome types;
- validity, lowering, partial raising, and recurrence realization;
- a partial intrinsic primitive/observer evaluator;
- intrinsic observation and echo evaluation.

The module is 300 lines and contains no `sorry`, `admit`, `axiom`, or `unsafe`.

## Checked laws

| ID | Lean theorem | Exact claim |
|---|---|---|
| THM-R12-001 | `lower_recurrence_preserves_image` | lowered recurrence realizes to the R9 breath |
| THM-R12-002 | `decode_lower_recurrence` | decoding a lowered recurrence returns its R7 source |
| THM-R12-003 | `lower_recurrence_injective` | recurrence lowering is injective on the supported image |
| THM-R12-004 | `prefix_obstruction_transport` | obstruction-path prefixing commutes with lowering |
| THM-R12-005 | `runPrimitive_transport` | tail/crest evaluation transports |
| THM-R12-006 | `runObserver_transport` | bounded closed R11 observers transport when the lowered result stays admissible |
| THM-R12-007 | `observe_transport` | bounded R11 recurrence observation transports |
| THM-R12-008 | `echo_transport` | bounded echo/mismatch/domain-blocked outcomes transport |
| THM-R12-009 | `tail_silence_obstruction_transport` | `tail(silence)` keeps the exact `[applyTail]` obstruction |

These are preservation laws. They do not prove equivalence for arbitrary raw
IR or reflection from every intrinsic value.

## Bound evidence

The public bridge binds:

- the independently verified R11 report and binding;
- 28 ordered reviewed source/export digests;
- nine reviewed fresh `.olean` records;
- a ten-stage content-addressed snapshot;
- exact Lean binary and version;
- the 2,365-file, 522,231,408-byte userspace Lean runtime closure;
- the unchanged R12.1 registry digest;
- one immutable R12.5 `preserves / formal-bridge / general` effect row.

Current checked identifiers:

| Item | Digest |
|---|---|
| R11 binding | `79039a32670ea305a70129e80d6299eae0f2428393f2f28018b74ccbdbc8701f` |
| R12.1 registry | `6a62bf002948aa8f8acf30c8c3d01cfc5f1a3a87e97dbcdd6bb66e378210be41` |
| R12.5 effect | `c9685e9cff5d201e86043aa0ba707aa5c98a42f502e5a9265fa0926b7f42560e` |
| R12.5 snapshot | `4f8d887ea3cd4366cbfa26a2447f6738edf51b7997a11619f5d40edb2b1bff6e` |
| R12.5 report binding | `201d8ae00224556c45a3a795c58aca025204bcdd8354e08ad05926f16c2ae802` |

Local manifest/effect/snapshot shapes are rejected before inherited R11 work.
Source bytes are captured from immutable canonical origin rows, compiled in a
fresh object chain, and rehashed during independent report verification.

## Public API

```python
from src.core.intrinsic_vam_formal_bridge import (
    intrinsic_vam_formal_bridge_data,
    intrinsic_vam_formal_bridge_report,
    verify_intrinsic_vam_formal_bridge_report,
)

report = intrinsic_vam_formal_bridge_report()
assert report.status == "checked"
assert verify_intrinsic_vam_formal_bridge_report(report)
data = intrinsic_vam_formal_bridge_data(report)
assert data["capability"] == "preserves"
assert data["promotion_ready"] is False
```

Serialization exposes evidence; it does not promote or authenticate unrelated
inputs.

## Verification

```bash
python -m pytest -q \
  tests/test_intrinsic_vam_formal_semantics.py \
  tests/test_intrinsic_vam_formal_bridge.py
```

The acceptance suite covers direct pinned Lean compilation, exact theorem IDs,
source/export mutation, manifest order/type/origin attacks, R11 rejection,
report-field mutation, hostile subclasses, effect escalation, and explicit
non-promotion. Final focused result: `8/8`.

## Non-claims

R12.5 does **not**:

- extract the Python or Rust implementation from Lean;
- prove VAMI framing, CRC, parser, malformed-input, or resource-limit logic;
- authenticate R12.3 receipts;
- prove arbitrary raw-IR reflection, equivalence, or legacy VAM semantics;
- add a certificate or Sage facade;
- renew an R8 promotion contract;
- alter the R12.1 registry, layer taxonomy, or `proof_complete`.

Those exclusions are part of the bound report boundary. R12.6 may add one
certificate and Sage facade only after replaying this bridge without weakening
them.
