# R9 — Intrinsic recurrence ↔ strict native Mode transport

**Date:** 2026-07-14
**Status:** checked narrow carrier bridge.
**Certificate:** `intrinsic_mode_transport_r9`.
**Boundary:** exact fixed-anchor unary `IntrinsicMode` image only.

## Result

R9 connects the R7 proof carrier `Veyra.Recurrence` to one explicitly defined
subset of the strict native runtime carrier:

```text
Recurrence  ≃  IntrinsicModeImage  ⊊  strict native Mode
```

It does **not** identify proof recurrence with every strict `Mode`. It also does
not reach the external labeled word `Mode`, cyclic/phase resonance, weighted or
approximate resonance, or resonance profiles.

## Canonical image

The image is intentionally rigid:

| Field | Canonical value |
|---|---|
| origin nod | residue and mark `intrinsic-origin` |
| successor tact | origin self-loop marked `intrinsic-successor` |
| observer | `native-cycle` |
| silence | empty breath anchored at the origin nod |
| pulse recurrence | unary successor-tact run with no anchor |

`encode_recurrence()` is total for every finite closed Python
`Silence | Pulse` chain and walks it iteratively, so deep valid chains do not
depend on Python recursion depth. `decode_mode()` is deliberately partial: it
accepts only the exact dataclass/container types, observer, anchor policy, and
successor tact, then re-encodes before returning `IntrinsicMode`. Foreign,
malformed, or forged modes return `NativeObstruction`.

## Structural laws

The executable path never converts the transported value to school `int`,
length arithmetic, `%`, `pow`, or `gcd`. It checks:

- decode after encode returns the original recurrence;
- encode after successful decode returns the exact native mode;
- proof silence and pulse/successor agree with strict-native zero and successor;
- recurrence stitch agrees with strict-native structural stitch;
- recurrence weave agrees with strict-native structural weave;
- the R7 unit-witness reflexive resonance survives transport.

The Python law rows are bounded regression witnesses. General statements come
from the Lean bridge below, not from enumerating samples.

## Lean theorem chain

`proofs/lean/VeyraIntrinsicRuntime.lean` mirrors the strict image's
zero/successor/stitch/weave operations. `VeyraRecurrenceModeBridge.lean` proves
the static carrier bridge; `VeyraProofModeTransport.lean` is the generated
digest-bound composite export.

| ID | Checked statement |
|---|---|
| `THM-R9-001` | every encoded breath evaluates to `.ready` as its encoded mode |
| `THM-R9-002` | `decodeMode (encodeMode r) = some r` |
| `THM-R9-003` | a successful decode characterizes the exact encoded image |
| `THM-R9-004` | `encodeMode` is injective |
| `THM-R9-005` | image stitch preserves recurrence stitch |
| `THM-R9-006` | image weave preserves recurrence weave |
| `THM-R9-007` | recurrence resonance iff intrinsic-image resonance |
| `THM-R9-008` | R7 `THM-R7-004` transports to native-image reflexivity |

The evaluator-readiness theorem is essential: the bridge targets actual strict
runtime formation semantics, not merely a similarly shaped record.

## Trust and reproducibility boundary

The R9 bridge fails closed over:

1. an immutable manifest of 16 reviewed sources: eight Python/native inputs and
   eight Lean sources, including the strict intrinsic runtime mirror;
2. a content-addressed read-only snapshot of the eight Lean files, compiled in
   dependency order without reopening the mutable originals;
3. pinned `leanprover/lean4:v4.30.0-rc2`, `-DwarningAsError=true`, and rejection
   of placeholders such as `sorry`, `admit`, `axiom`, or `unsafe`;
4. a generated export that embeds the R7 artifact digest and reviewed source
   digests;
5. independent rehash of cached status, sources, generated export, toolchain,
   diagnostics, boundary, and binding before a report is trusted.

These hashes bind the reviewed Python/native/Lean implementations. They are
source-parity evidence, **not** extraction of Python from Lean and not a proof
that arbitrary Python behavior is formalized.

## Refutation pressure

Three executable rows prevent a false bridge to the external word carrier:

| Row | Witness | Result |
|---|---|---|
| label erasure | `ab` vs `aa` | same unary image; cyclic resonance differs |
| phase erasure | `ab` in `abab` vs `baba` | offsets `(0,2)` vs `(1,3)` are lost |
| silence | empty word vs itself | intrinsic reflexivity holds; current cyclic relation rejects silent part |

Therefore `THM-R9-007/008` must never be cited as a theorem about word labels,
phase offsets, approximate matching, weights, or profiles.

## Readiness and verification

R9 adds a transport certificate, not a new Essence layer or theorem-derived
layer. Its carrier remains
`veyra.proof.recurrence-equiv-strict-intrinsic-mode.v1`; after R10 the existing
R8 contract requires bridge `veyra.lean.r10.proof-elaboration-tcb.v1`, which
source-replays into R7 and this image. It still promotes only `THM-R7-004`.
The readiness taxonomy stays exactly:

```text
layers=35; theorem-derived=1; witness-only=4; shadow=25; meta=5
execution_ready=True; proof_complete=False
```

Acceptance uses the focused transport/refutation/bridge tests, all eight Lean
theorems, manifest/snapshot/cache attacks, and the root suite:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  tests/proof/test_intrinsic_mode_transport.py \
  tests/proof/test_intrinsic_mode_refutations.py \
  tests/proof/test_intrinsic_mode_bridge.py
the complete verification suite
```

Final acceptance passed: exact manifest `16/16`, pinned Lean chain `8/8`, Rust
`12/12`, and full the complete verification suite (`pytest 1131/1131`, certificates `65/65`, Sage,
doctest `41/41`, hygiene). Changed-file Ruff and `git diff --check` were clean;
two independent final reviews found no blocker/high/medium.

R10 now supplies the checked closed recurrence proof-surface elaboration into
R7 and this image without widening R9. R11 observer/echo proof semantics is
next; arbitrary strict/word modes remain separately unproved.
