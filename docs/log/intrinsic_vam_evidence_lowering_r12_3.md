# R12.3 — Evidence-Aware Intrinsic VAM Lowering

**Status:** implemented finite executable transport
**Schema:** `veyra.intrinsic-vam.transport.r12.3.v1`
**Scope:** exact R7 recurrence, verified R9 intrinsic image, replayed R11 observation/echo
**Non-claim:** no authentication, reflection, general proof, byte codec, runtime, Lean, certificate, or promotion

## 1. Purpose

R12.2 defines diagnostic intrinsic IR but deliberately supplies no trusted route into it. R12.3
adds that route without treating legacy VAM shadows or caller-supplied outcomes as evidence.

The implementation is split into four bounded modules:

- `intrinsic_vam_lowering_types.py` — closed lane, receipt, and bundle types;
- `intrinsic_vam_values.py` — exact value conversions; raw R11 outcome conversion is module-local;
- `intrinsic_vam_receipts.py` — fixed finite-evidence rows and canonical receipt validation;
- `intrinsic_vam_lowering.py` — public source-replaying lowering and raising operations.

No R9, R11, R12.1, R12.2, legacy VAM, Lean, certificate, or promotion source is modified.

## 2. Closed lanes

| Lane | Semantic source | Provenance | Source digests | Public computation |
|---|---|---|---:|---|
| `r7-recurrence` | R7 recurrence | R7 | 1 | exact recurrence → recurrence IR |
| `r9-intrinsic-mode` | R9 intrinsic image | R9 | 1 | verified wrapper → recurrence IR |
| `r11-branded-observation` | R11 response | R7 or R9 | 1 | `observe()` then `brand_observation()` |
| `r11-echo-outcome` | R11 response | R7 or R9, equal on both sides | 2 ordered | `echo()` |

R7 accepts exact `Silence`/`Pulse` only. R9 accepts an exact `IntrinsicMode` only after
`verify_intrinsic_mode()`. R11 accepts either source form, recovers its recurrence and provenance,
and then runs the reviewed R11 evaluator. Raw `Ready`, `Blocked`, `Echo`, `Mismatch`, and
`DomainBlocked` values are not public lowering inputs.

## 3. Receipt contract

Every `TransportedIntrinsicIR` carries a frozen exact `IntrinsicLoweringReceipt` binding:

- schema, lane, semantic source, provenance, and intrinsic target;
- exactly one capability: `preserves`;
- exactly `EXECUTABLE_WITNESS` with `FINITE` scope;
- one lane-specific audited evidence ID and boundary;
- one or two ordered canonical source digests;
- observer, response-kind, and payload digests for R11 lanes;
- the complete R12.2 diagnostic IR digest;
- all preceding fields in one composite binding digest;
- `promotion_ready=False`.

R7/R9 receipts require empty observer/kind fields. R11 receipts require lowercase 64-hex values.
Digest tuple cardinality is fixed per lane. Unknown lanes, type confusion, subclasses, lists in
place of tuples, uppercase/non-hex digests, duplicate/extra capabilities, and any field drift fail
closed.

The hash is mutation evidence and canonical identity, not authentication.
`intrinsic_transport_envelope_data()` therefore emits `verification="unverified-envelope"` and
`evidence_accepted=False`; structural serialization never establishes reachability. Only a public
`raise_*` path consumes a receipt after replaying its complete expected context.

## 4. Replay before raising

Every public `raise_*` function requires the expected source, and R11 functions additionally
require the observer and ordered sources. Raising follows this sequence:

1. recompute the complete lowering from those expected inputs;
2. validate both exact transport bundles;
3. compare canonical bundle data, including IR and receipt;
4. discard the attacker-owned bundle and convert only the freshly recomputed expected IR.

`raise_r11_observation()` returns a newly created and verified `BrandedObservation`.
`raise_r11_echo()` returns the exact replay-matched three-way R11 outcome.

Consequences:

- an R7 receipt cannot be transplanted into the identical R9 IR lane;
- the same crest mark under different source recurrences cannot share a receipt;
- equal payloads under different observers cannot share a receipt;
- echo source order is bound even when both observations yield the same mark;
- structurally equal separately allocated sources remain accepted;
- replacing the IR while keeping the receipt is rejected.

## 5. Resource and legacy boundaries

R7/R9 recurrence IR admits at most 2,047 tacts. R11 retains its stricter 128-depth,
2,048-node observer/recurrence limits and its exact obstruction limits. R12.2 then validates the
produced sidecar under its own 4,096-node, 128-depth boundary before any receipt is published.

Legacy `VamObject("Shadow", ...)`, `VamObject("Echo", ...)`, and
`VamObject("Certificate", ...)` remain valid finite runtime records on their old surface, but are
not R12.3 sources, bundles, evidence, or receipts. R12.3 does not add intrinsic classes to
`vam.src.__all__`, add opcodes, or reinterpret `CERT`.

## 6. Evidence boundary

R12.3 establishes bounded executable preservation only. It does not establish:

- reflection, injectivity of every response lane, or equivalence;
- outcome reachability from receipt validation without replay;
- a general kernel proof or formal bridge;
- entry into the R8 promotion contract;
- a theorem/layer/taxonomy change;
- a byte codec, Python/Rust runtime parity, or native execution.

Those remain assigned to R12.4–R12.6 and R13.

## 7. Verification

Focused Sage 10.7 tests cover exact R7/R9 round trips, all R11 outcome forms, R7/R9 provenance,
same-payload source and observer separation, every receipt field, hostile scalar/tuple subclasses,
immutable lane rows, recomputed same-row and evidence-escalation hashes, ordered sources, raw
outcome/IR rejection, resource overflow, and legacy Shadow/Echo/Certificate isolation.

Current local evidence:

- focused R12.3: `54/54`;
- R12.1–R12.3 plus adjacent R9/R11/legacy VAM slice: `269/269`;
- changed-file Ruff and `git diff --check`: pass.

Full serial the complete verification suite, R12.4 codec/runtime parity, R12.5 Lean bridge, and R12.6
certificate/Sage integration remain open release gates.
