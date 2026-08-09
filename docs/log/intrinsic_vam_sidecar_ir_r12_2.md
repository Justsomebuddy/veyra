# R12.2 — Intrinsic VAM Sidecar IR

**Status:** implemented typed definition and diagnostic serialization
**Schema:** `veyra.vam.intrinsic-ir.r12.2.v1`
**Scope:** exact R9 fixed-image values and the closed R11 response/outcome vocabulary
**Non-claim:** no lowering, byte codec, runtime, Lean bridge, certificate, or promotion

## 1. Purpose

Legacy VAM represents runtime shadows through permissive `VamObject.data` mappings and encodes
instructions through VAM0/VAMD. That surface cannot serve as theorem evidence: it has no exact
anchored-silence carrier and its generic shadow payload is intentionally broad.

R12.2 therefore introduces an isolated immutable sidecar:

- `vam/src/intrinsic_ir_types.py` — closed frozen types;
- `vam/src/intrinsic_ir.py` — constructors, bounded validation, and diagnostic data.

The sidecar is not imported into legacy instruction, object, optimizer, interpreter, or native
runtime modules.

## 2. Exact recurrence image

`IntrinsicAnchorIR` denotes only the R9 anchor:

```text
Nod(Rez("intrinsic-origin"), "intrinsic-origin")
```

`IntrinsicTactIR` denotes only the fixed self-loop successor tact:

```text
Tact(anchor, anchor, "intrinsic-successor")
```

`IntrinsicRecurrenceIR(tacts, anchor)` follows the exact R9 breath invariant:

| Value | `tacts` | `anchor` |
|---|---|---|
| silence | empty exact tuple | `IntrinsicAnchorIR` |
| one or more pulses | nonempty exact tuple of `IntrinsicTactIR` | `None` |

`silence_ir()` and `pulse_ir(tail)` are the safe constructors. A flat tact tuple is structural
multiplicity, not a trusted integer shadow, and avoids recursive pulse objects in the machine IR.
`crest_mark_ir()` returns only `IntrinsicMarkIR.SILENT` or `IntrinsicMarkIR.PULSE`.

## 3. Response and obstruction vocabulary

The sidecar closes the R11 shapes:

- recurrence, mark, and ordered pair response values;
- `IntrinsicReadyIR` and nonempty `IntrinsicBlockedIR`;
- `IntrinsicEchoIR`, `IntrinsicMismatchIR`, and `IntrinsicDomainBlockedIR`;
- `tail-of-silence` with outer-to-inner `apply-tail`, `apply-crest`, `pair-left`, and
  `pair-right` path steps.

Mismatch sides must be distinct and have the same derived response kind. Obstruction tuples are
exact, bounded, duplicate-free, and follow the closed R11 path grammar `pair*`, optional `crest`,
then one-or-more `tail` steps. These are structural checks only: reachability against a particular
observer/source recurrence belongs to R12.3 lowering and branding.

## 4. Fail-closed limits

| Limit | Value |
|---|---:|
| total sidecar representation nodes | 4096 |
| nesting depth | 128 |
| recurrence tacts | 2047 |
| obstructions in one result | 2048 |
| obstruction path steps | 128 |

Validation uses exact slotted frozen types rather than `isinstance`, requires exact tuples, allows
acyclic shared subtrees, rejects active cycles/hidden fields, and revalidates existing fields after
hostile mutation.

## 5. Diagnostic data is not a wire format

`intrinsic_ir_data(value)` returns deterministic JSON-compatible diagnostic data under the R12.2
schema. R12.2 deliberately adds no byte encoder, decoder, trusted digest, artifact root, or
evidence class. Canonical bytes and malformed-wire rejection belong to R12.4 after R12.3 defines
the evidence-aware lowering boundary.

Consequently this schema must not be inserted into R8 promotion contracts, R9/R11 manifests, or
the R12.1 audited bridge registry.

## 6. Legacy noninterference

The regression gate pins the pre-sidecar legacy surface:

- `VAM0` and `VAMD`, version `1`;
- opcodes `REZ..CERT` remain codes `1..11`;
- `vam0-ref-v1` remains the report profile;
- representative VAM0, VAMD, report, and opcode-row digests remain byte-exact;
- an intrinsic sidecar object is rejected as a VAM0 operand;
- no intrinsic type is added to legacy `vam.src.__all__`.

No files in legacy model/opcodes/bytecode/dense/interpreter/compiler or `vam/native` are modified.

## 7. Verification and next step

Sage 10.7 runs direct constructor, invariant, frozen/hostile-type, response/outcome, obstruction,
cycle/DAG, exact resource-boundary, and legacy digest tests. The next step is R12.3:

1. lower exact R9/R11 values into this IR;
2. raise supported IR back into the exact carriers;
3. attach R12.1 effect/evidence declarations;
4. keep legacy `Shadow.value` and `CERT` outside theorem promotion.
