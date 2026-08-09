# R12.4 — Intrinsic VAMI codec and structural runtime

**Status:** implemented, bounded, Python/Rust structural parity verified
**Profile:** `veyra.vami.intrinsic-r12.4.v1`
**Depends on:** R12.2 intrinsic IR (`docs/134`), R12.3 replay receipts (`docs/135`)
**Does not add:** theorem, Lean bridge, certificate, promotion, evidence acceptance, taxonomy change

## 1. Purpose

R12.4 gives the closed R12.2 intrinsic carrier one deterministic byte form and
two independent readers:

- Python `vam.intrinsic` is the encoder and report oracle;
- Rust `vami-inspect` reads and structurally executes the same frames;
- legacy `VAM0`, `VAMD`, opcodes, `vam0-inspect`, optimizer, and certificates
  remain separate.

The frame transports **raw intrinsic IR only**. It never transports or validates
an R12.3 receipt. A valid CRC proves accidental-integrity only, not source,
observer, evidence, or reachability.

## 2. Frame

All integers are unsigned big-endian:

```text
offset  size  field
0       4     magic = "VAMI"
4       2     version = 1
6       4     payload length
10      4     IEEE CRC32(payload)
14      n     canonical binary payload
```

The payload cap is 1 MiB. Length and CRC are checked before semantic decoding.
No trailing bytes are accepted.
The Rust CLI reads at most one maximum frame plus one sentinel byte, so the
filesystem entry point cannot allocate an unbounded attacker-sized file.

## 3. Canonical payload tags

| Tag | Node | Payload |
|---:|---|---|
| 1 | anchor | none |
| 2 | tact | none |
| 3 | recurrence | `u16 tact_count`, `u8 anchor_flag` |
| 4 | raw mark | `u8` silent/pulse |
| 5 | recurrence value | recurrence node |
| 6 | mark value | mark byte |
| 7 | pair value | two response nodes |
| 8 | obstruction | code byte, `u16` path length, path bytes |
| 9 | ready | response node |
| 10 | blocked | nonzero `u16` count, tagged obstructions |
| 11 | echo | response node |
| 12 | mismatch | two same-kind unequal responses |
| 13 | domain blocked | left and right obstruction sets, total nonzero |

Tag 3 is compact: tact/anchor children are not repeated on the wire, but they
still count as semantic nodes. Re-encoding a decoded value must reproduce the
whole frame byte-for-byte.

Path bytes are:

```text
0 apply-tail
1 apply-crest
2 pair-left
3 pair-right
```

Only `pair* · crest? · tail+` is valid. Obstruction paths must be unique within
each set; left/right domain sets are independently ordered.

## 4. Shared resource contract

| Resource | Limit |
|---|---:|
| payload | 1 MiB |
| semantic nodes | 4096 |
| semantic depth | 128 |
| recurrence tacts | 2047 |
| total obstructions | 2048 |
| one obstruction path | 128 |

Python validates exact frozen R12.2 classes before encoding and again after
decoding. Rust enforces the equivalent grammar directly while reading. Both
reject unknown tags, scalar codes, malformed recurrence anchors, non-response
children, duplicate paths, invalid mismatch kinds/equality, and resource
overflow.

## 5. Structural execution report

Successful inspection returns:

```json
{
  "ok": true,
  "profile": "veyra.vami.intrinsic-r12.4.v1",
  "frame": {"magic": "VAMI", "version": 1, "size": 1, "crc32": "a505df1b"},
  "execution": {
    "status": "decoded",
    "tag": "anchor",
    "nodes": 1,
    "obstructions": 0,
    "value": {"tag": "anchor", "name": "intrinsic-origin", "mark": "intrinsic-origin"},
    "evidence_accepted": false,
    "promotion_ready": false,
    "taxonomy_changed": false
  }
}
```

`value` is exactly the R12.2 `intrinsic_ir_data(value)["value"]` shape.
Statuses are only structural:

- `blocked` for blocked/domain-blocked;
- `mismatch` for mismatch;
- `ready` for ready/echo;
- `decoded` for raw carrier/value nodes.

This runtime does not replay R7/R9 sources or execute R11 observers. Therefore
it cannot call any R12.3 raising function or manufacture a trusted receipt.

Errors are stable JSON rows:

```json
{"ok":false,"profile":"veyra.vami.intrinsic-r12.4.v1","error":{"kind":"crc32","message":"VAMI checksum mismatch"}}
```

Canonical JSON is recomputed only from exact frame bytes or an exact codec
error; caller-supplied or flag-mutated report dictionaries are rejected.

## 6. Evidence and legacy boundary

The codec rejects `TransportedIntrinsicIR`, lowering receipts/envelopes,
branded observations, legacy `VamObject`, and every other non-exact R12.2 type.
The three report booleans are always false.

R12.4 does not:

1. authenticate a frame or receipt;
2. show that an IR came from an R7/R9 source or R11 observer;
3. add `CERT`, a VAM opcode, a theorem, or an R8 promotion input;
4. alter legacy VAM0/VAMD bytes, reports, profiles, or opcode assignments.

The next slice is R12.5: a source/object/toolchain-bound formal preservation
bridge for the supported intrinsic IR and obstruction transport.

## 7. Verification

The focused Sage-environment codec/runtime parity gate passes `58/58`, all
VAM/VAMI tests pass `340/340`, and the native crate passes `19/19`. This includes all thirteen tags,
malformed/resource-boundary frames, Python/Rust success and error JSON parity,
and exact legacy pins. Adding `vami-inspect` initially made plain `cargo run`
ambiguous; `default-run = "vam0-inspect"` restores the legacy invocation.
No full repository verification, Lean, certificate, or promotion claim follows.
