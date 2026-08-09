# 013 — Native Rust VAM0 Scaffold and Executor Slice

## Status

`vam/native/` now contains a minimal Rust crate for the first native boundary:

```text
VAM0 bytes -> Rust frame validator -> deterministic JSON metadata report
```

The binary is `vam0-inspect`. v0.7 was a frame scaffold; v0.9 adds golden-fixture parity and native unit-test coverage for current VAM0 rows.

## Current capability

The Rust crate validates:

- magic `VAM0`;
- version `1`;
- payload length;
- CRC32;
- UTF-8 JSON payload shape;
- instruction rows with `op`, `args`, and optional `line`;
- wire argument tags `int`, `reg`, and `str`.

It emits JSON with:

- `profile: vam0-ref-v1`;
- frame metadata;
- instruction count;
- opcode list;
- canonical instruction rows;
- final `pc`, registers, trace rows, accepted certs, and obstructions for executable frames.

## Profile gate

Only `vam0-ref-v1` is accepted. `f4-strict` and any other profile must be rejected until specified.

## Python oracle test

`tests/vam/test_vam_native_scaffold.py` checks frame validation and CRC rejection. `tests/vam/test_vam_native_executor.py` compares Rust execution reports with the Python `canonical_report()` oracle across the named golden fixture corpus. Native tests skip if Rust/Cargo is unavailable.

## Non-claims

This scaffold/executor slice does not yet:

- implement optimizer parity;
- implement dense opcode tables;
- claim native speed;
- claim GPU/FPGA readiness.

## Next honest milestone

The next native step is broader `vam0-ref-v1` parity:

1. add malformed execution payloads and every obstruction shape;
2. move/expand native Rust tests before `lib.rs` reaches the module size limit;
3. compare optimizer-in/out programs only when optimizer parity is explicitly in scope;
4. only then discuss performance-oriented backends.
