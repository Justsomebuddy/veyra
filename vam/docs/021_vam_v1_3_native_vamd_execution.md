# VAM v1.3 Native VAMD Execution

## Purpose

v1.3 closes the first native dense-bytecode gap: `vam0-inspect` can now read a
`VAMD` dense frame, decode it in Rust, execute it through the existing
`vam0-ref-v1` runtime, and emit the same canonical report shape as `VAM0`.

This is still semantic parity work. It is not a speed claim, native optimizer
claim, proof-assistant bridge, GPU backend, or FPGA backend.

## Artifacts

- `native/src/main.rs` autodetects frame magic:
  - `VAM0` -> JSON-envelope decoder;
  - `VAMD` -> dense decoder;
  - unknown magic -> deterministic `magic` error row.
- `native/src/lib.rs` carries `FrameReport.magic` so the report names the real
  input frame.
- `native/src/json.rs` owns JSON rendering helpers, keeping `lib.rs` small and
  avoiding hardcoded `magic:"VAM0"` for dense frames.
- `native/src/dense.rs` now returns a `FrameReport` with `magic:"VAMD"`.
- `tests/vam/test_vam_native_vamd_executor.py` compares Rust CLI reports against
  the Python oracle: `decode_dense -> execute -> canonical_report`.

## CLI contract

The binary name remains `vam0-inspect` because the semantics profile remains
`vam0-ref-v1`:

```bash
source ~/.cargo/env
cargo run --manifest-path vam/native/Cargo.toml -- <file.vam0|file.vamd>
```

The profile field is still `vam0-ref-v1`. The frame field now distinguishes the
wire encoding:

```json
{"frame":{"magic":"VAMD","version":1,"size":123,"crc32":"..."}}
```

## Parity rule

For accepted VAMD frames, Rust and Python must agree on:

- final program counter;
- register objects;
- trace rows;
- accepted certificates;
- obstruction rows;
- frame magic/version/size/checksum metadata.

Fixture scope is deliberate: parity is checked against current finite golden
programs, not all possible future Veyra programs.

## Boundary

v1.3 does not add:

- a native optimizer;
- proof-grade equivalence;
- a bytecode compiler beyond existing Python emitters;
- performance benchmarks;
- GPU/FPGA execution;
- proof-assistant semantics.

Next safe targets are native optimizer parity and broader malformed-VAMD error
taxonomy parity, still under the same no-speed/no-proof boundary.
