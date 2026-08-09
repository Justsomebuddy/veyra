# 015 — VAM v0.9 golden parity tightening

## Status

VAM v0.9 tightens the v0.8 execution contract with a fixture corpus and stronger parity checks:

- `vam/src/fixtures.py` defines named golden fixture programs and canonical reports.
- `tests/vam/test_vam_native_executor.py` runs the Rust executor over the fixture report surface.
- `vam/native/src/lib.rs` has native unit tests for frame parsing, success JSON, and executor error surfacing.
- `vam/src/equivalence.py` adds `report-fingerprint` checks over canonical reports.
- `vam/src/obligation.py` adds a transport-only gate for obligation batches.

## Golden fixtures

Current fixture names:

- `minimal-accepted-echo-cert`;
- `bad-breath-nod-obstruction`;
- `all-instruction-kinds`;
- `shell-lowering`;
- `optimizer-duplicate-compress`.

`fixture_program(name)` returns the authored fixture program. `fixture_report_program(name)` returns the exact executable surface used for canonical report parity. This distinction matters for optimizer fixtures, where the report surface is the optimized program.

## Native parity

Native parity is still fixture-scoped, not a release-wide correctness theorem. For each fixture report program:

```text
Instruction IR -> VAM0 -> Rust report
Instruction IR -> Python canonical_report
compare pc/registers/trace/certs/obstructions
```

Rust unit tests also cover the local frame boundary and the `execution_error` JSON path when a frame decodes but executor operands are malformed.

## Equivalence tightening

`report-fingerprint` compares selected canonical-report roots, accepted certificate evidence/boundaries, and obstructions. This catches mutations that preserve the boolean accepted flag but change evidence or trust boundary.

The check is still conservative execution evidence. It is not global program equivalence and not optimizer proof.

## Obligation no-overclaim gate

`obligation_batch_is_transport_only(rows)` returns true only for non-empty batches with no accepted certificates. It makes the no-proof boundary machine-checkable for obligation transport rows.

## Remaining work

- v1.0 broadened fixture corpus for malformed payloads and current obstruction shapes;
- move native Rust tests out of crowded `lib.rs` before more native coverage;
- define optimizer parity only after a written optimizer-native contract;
- dense opcodes, GPU, FPGA, LLVM, and speed claims remain gated behind parity.

## Verification

Focused checks:

```bash
PYTHONPATH=. pytest -q tests/vam/test_vam_fixtures.py tests/vam/test_vam_native_executor.py tests/vam/test_vam_equivalence.py tests/vam/test_vam_obligation.py tests/shadows/test_certify.py
cargo fmt --manifest-path vam/native/Cargo.toml --check
cargo test --manifest-path vam/native/Cargo.toml
```

Global acceptance remains the complete verification suite.
