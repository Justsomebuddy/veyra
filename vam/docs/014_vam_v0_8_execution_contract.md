# 014 — VAM v0.8 execution-contract slice

## Status

VAM v0.8 turns several roadmap items into bounded executable artifacts:

- `vam/src/report.py` emits the canonical Python oracle report (`vam0-ref-v1`).
- `vam/native/src/runtime.rs` executes current VAM0 instruction rows and reports `pc`, registers, trace, certs, and obstructions.
- `vam/src/shell.py` lowers finite `shell(echo(...), ...)` relations without issuing shell certificates.
- `vam/src/obligation.py` transports theorem obligations as explicit non-certificate IR rows.
- `vam/src/highlevel.py` provides a tiny process/claim source seed that lowers one echo body.
- `vam/src/equivalence.py` summarizes optimizer evidence by executing original and optimized programs.

## Canonical report

`canonical_report(program, state)` is the Python oracle for cross-runtime parity. It normalizes:

- instructions;
- trace rows;
- registers;
- accepted certificates;
- obstructions;
- final program counter.

All maps are emitted in stable order and all VAM objects become `{kind, data}` rows. Rust parity tests compare the native execution report against this canonical Python report.

## Native Rust executor slice

`vam0-inspect` now performs two steps:

```text
VAM0 bytes -> frame validation -> Rust execution report
```

It supports the current instruction set:

```text
REZ NOD TACT BREATH MODE OBSERVER OBSERVE ECHO OBSTRUCT COMPRESS CERT
```

The native slice is a parity target, not a speed target. It has Python-oracle tests for success and obstruction cases, but no native optimizer, dense opcode table, GPU, FPGA, or performance claim.

## Shell lowering

Supported shell form:

```text
shell(echo(A,B,observer:o), echo(C,D,observer:p), ...)
```

where every child is a directly executable `echo` with a supported observer. v1.0 supersedes the root-as-last-child detail with a deterministic non-certificate shell carrier. A blocked child still emits an explicit `OBSTRUCT` row. Shell-level `CERT` remains disabled.

## Obligation IR

`VamObligationRow` and `VamObligationStatus` expose theorem-obligation status for transport. They are not proof terms and always carry `accepted_certificate=False`. Verified obligation rows mean finite Core obligation checks passed under the declared boundary, not that VAM proved quantified theorem semantics.

## High-level seed

The first high-level parser accepts only:

```text
process NAME { echo(EXPR,EXPR) under OBSERVER }
claim NAME := echo(EXPR,EXPR) under OBSERVER
```

The parser lowers to Core `echo(...)` and then uses the existing VAM compiler. Theorem-like syntax is explicitly unsupported in this seed.

## Optimizer equivalence summaries

`summarize_equivalence(original, optimized)` executes both programs and compares conservative observables:

- certificate claim/acceptance sequence;
- nested obstruction count;
- selected root-register evidence.

A `safe` result is bounded execution evidence for the tested programs, not a global optimizer proof.

## Verification

Focused checks:

```bash
PYTHONPATH=. pytest -q tests/vam/test_vam_report.py tests/vam/test_vam_obligation.py tests/vam/test_vam_highlevel.py \
  tests/vam/test_vam_shell.py tests/vam/test_vam_equivalence.py tests/vam/test_vam_native_executor.py
cargo test --manifest-path vam/native/Cargo.toml
```

Global acceptance remains the complete verification suite.
