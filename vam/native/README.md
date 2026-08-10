# VAM native backend

Native backend work lives here, but the first milestone is semantic parity, not
speed.


## Current parity slice

This directory contains a Rust crate with `vam0-inspect`. It validates VAM0/VAMD magic/version/length/CRC, decodes the current JSON or dense instruction payload, executes current `vam0-ref-v1` rows, and emits deterministic JSON reports. Python remains the oracle. v1.3 adds CLI VAMD execution/report parity; v1.5 extends bounded optimizer parity across observer alias, duplicate `COMPRESS`, idempotent `COMPRESS`, and dead-shadow pruning. v1.6 accepts VAMD only at the decoded semantic report boundary. v1.7 emits optimized VAM0 frames only for VAM0 input plus exact `observer-alias-v1`. v1.8/v1.9 add witness, proof-obligation, and metamorphic regression evidence around those boundaries; VAMD optimized-frame emission remains blocked. Performance work remains future work.

Run manually:

```bash
cargo run --manifest-path vam/native/Cargo.toml -- <file.vam0|file.vamd>
cargo run --manifest-path vam/native/Cargo.toml -- --optimize observer-alias-v1 <file.vam0>
cargo run --manifest-path vam/native/Cargo.toml -- --optimize observer-alias-v1 <file.vamd>  # report-only boundary
cargo run --manifest-path vam/native/Cargo.toml -- --optimize observer-alias-v1 --emit-optimized-vam0 out.vam0 <file.vam0>
```

`cargo` must be on `PATH`; no home-directory layout is assumed. The repository
pins Rust `1.95.0` through `rust-toolchain.toml` for reproduced checks and
declares `rust-version = "1.83"` as the crate MSRV. The compatibility lane
selects exact Rust 1.83.0. Run the portable native gate on Linux, macOS, or
Windows with:

```bash
cd vam/native
cargo fmt --all -- --check
cargo test --locked
```

## Current feasible path

The target remains Rust `vam0-ref-v1` parity:

```text
VAM0/VAMD bytes -> Rust decoder -> Rust interpreter -> canonical trace/certs
```

It must keep matching the Python reference stack for VAM0 v1, VAMD golden fixtures, and any enabled native optimizer slice before LLVM, GPU, FPGA, or speed-focused work is allowed.

## Required contract

- Profile is explicit: `vam0-ref-v1` now; `f4-strict` is future-gated and must be
  rejected until specified.
- ABI boundary is immutable VAM0/VAMD frame bytes in, canonical JSON report or
  deterministic error row out.
- Oracle is Python reference output: same decoded instructions, trace rows, certificates, obstructions, and decode failures.
- v0.9 adds golden fixture parity plus small Rust unit tests; coverage is still fixture-scoped.
- v1.2 adds VAMD parser scaffold coverage; v1.3 adds CLI execution/report parity for VAMD; v1.4/v1.5 add bounded optimizer parity; v1.6 accepts VAMD optimizer input as decoded-IR report-only parity; v1.7 emits optimized VAM0 artifacts only from VAM0 input; v1.8/v1.9 add bounded witness/obligation/metamorphic regression checks and keep VAMD optimized-frame emission out of scope.
- GPU/FPGA work is blocked until Rust parity is green and deterministic fallback
  comparisons exist.
- No speedup claim exists until parity and benchmark gates are documented.

See `../docs/010_native_backend_feasibility.md` for the detailed feasibility
path, semantics profiles, ABI/frame contract, oracle plan, later hardware gates,
and no-speedup boundary.
