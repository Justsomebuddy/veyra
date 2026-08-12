# VAM native backend

Native backend work lives here, but the first milestone is semantic parity, not
speed.


## Current parity slice

This directory contains a Rust crate with `vam0-inspect`. It validates VAM0/VAMD magic/version/length/CRC, decodes the current JSON or dense instruction payload, executes current `vam0-ref-v1` rows, and emits deterministic JSON reports. Python remains the oracle. v1.3 adds CLI VAMD execution/report parity; v1.5 extends bounded optimizer parity across observer alias, duplicate `COMPRESS`, idempotent `COMPRESS`, and dead-shadow pruning. v1.6 accepts VAMD only at the decoded semantic report boundary. v1.7 emits optimized VAM0 frames only for VAM0 input plus exact `observer-alias-v1`. v1.8/v1.9 add witness, proof-obligation, and metamorphic regression evidence around those boundaries; VAMD optimized-frame emission remains blocked. The separate `vam_native::observer_synthesis` library surface now reproduces the closed R11 AST, exact R14.1 catalog and deterministic default R14.3b calibration without changing CLI/backend dispatch. Performance work remains future work.

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

## Native observer-synthesis calibration

`vam_native::observer_synthesis` supplies a dependency-free, closed finite
surface:

- typed `Input`, `Tail`, `Crest`, and ordered `Pair` observers;
- Python-byte-identical canonical observer JSON and SHA-256 identities;
- exact R14.1 cost/depth enumeration with pinned strata
  `1/3/8/27/104/358/1064`, 1,565 candidates, 488,550 retained bytes, and the
  published catalog digest;
- finite unary-recurrence `observe`/`echo` semantics with explicit
  `tail-of-silence` paths;
- monotone candidate/byte/evaluation/output precharges and deterministic
  train-only CEGIS;
- the exact default calibration winner `Crest(Input)` at ordinal 1 and a
  native-domain-separated counter-only trace binding.

Set `VEYRA_NATIVE_DEBUG=1` to emit bounded observer-synthesis lifecycle,
rejection, cutoff, and terminal-state diagnostics to stderr. Diagnostics are
off by default and never include observer payloads, canonical bytes, or
digests.

This base catalog/CEGIS surface is an opt-in Rust library shadow. It has no CLI,
worker isolation, wall-clock/address-space enforcement, train/holdout trial
suite, statistical discovery, or default-backend dispatch. Its finite winner
is a finite Python-identity calibration, not novelty, general synthesis, superiority, or a
speed result. Because wall-clock and process-address-space limits are not
enforced here, its limits binding explicitly records both as unenforced and its
trace cannot reuse the stronger Python worker trace root. See
`../docs/037_native_observer_synthesis_core.md`.

A bounded receipt layer adds one fixed zero-vs-positive quotient
benchmark and `NativeObserverSurpriseReceiptV1`. `Input` has three response
classes and zero saving; the pinned `Crest(Input)` winner has two classes and
one saving while satisfying both fixed obligations. The receipt freshly
replays the existing catalog/CEGIS path and retains the explicitly unenforced
wall-clock/process-AS flags. It is not BM-F009, general discovery, holdout
evidence, a signed artifact, or a backend promotion. See
`../docs/038_native_observer_surprise_receipt.md`.

The next bounded layer keeps the grammar fixed and adds an atomic four-member
benchmark suite: an identity mixture is found by `Crest(Input)`, balanced-
marginal XOR exhausts the exact catalog, a shifted mixture is repaired by the
costlier `Crest(Tail(Input))`, and a fixed permutation exhausts the catalog.
Two explicit transport rows first test the source witness unchanged and only
then record target re-synthesis. This is finite representation-sensitivity
evidence, not invariance, general impossibility, BM-F009, or hidden-variable
discovery. See `../docs/039_native_observer_benchmark_family.md`.

Observer synthesis v2 preserves the entire legacy catalog and canonical-byte
contract while adding a separately identified `Parity` grammar profile. It
enumerates 120 shift/permutation representations, provides a complete
obligation-result survey for that family, and searches transform/observer pairs by a
deterministic total-cost order. The fixed `vam-observer-worker` adds Linux
RLIMIT CPU/address-space/core custody, parent wall timeout and process-group
kill/reap; portable VORP packages bind exact worker request/receipt bytes with
external-key HMAC-SHA256 and fresh execution replay. This is bounded shared-key
authentication, not a public signature, sandbox, general representation law,
or proof of implementation correctness. See
`../docs/040_native_observer_synthesis_v2.md`.

Observer synthesis v3 layers an append-only profile registry, a typed finite
transport DSL with bounded recursive composition and derived
bijection/injection/loss classes, and a direct typed transport × observer search
whose stable-bucket implementation is checked against an independent exhaustive
oracle. It adds an integer observer-gap laboratory and atomic
normalize/transport/observer/explanation/aggregate evidence over the unchanged
v1/v2 profiles. VOR2 authenticates either the legacy worker or canonical v3
pipeline payload under external HMAC/Ed25519 trust while preserving VORP v1.
Worker-v2 states distinguish enforced, available, unavailable, unsupported and
failed controls. The worker-v3 parent marks all descriptors above stderr
close-on-exec and its fixed child audits the post-exec table. The child remains
custody-pending; its parent adds bounded output, wall-time and process-group
custody only after exact fresh pipeline replay. Strict mode blocks rather than turning missing
cgroup/seccomp/namespace controls into a sandbox claim.
See `../docs/041_native_observer_synthesis_v3.md`.

Observer synthesis v4 adds contract-stabilization vectors, a deterministic
finite representation survey, and joint
representation/transport/observer/explanation search whose optimized terminal
must agree semantically with a separately implemented exhaustive reference path
over the same catalog and primitive semantics. Worker-v4 adds
truthful `baseline`, `isolated`, and `strict` Linux profiles with namespace,
seccomp, and delegated cgroup-v2 readback; its private mount namespace does not
hide the host filesystem tree. VOR4 signs bounded manifests, derived registry
roots, an optional worker-policy binding, and an independently signed VOR2
pipeline payload, then verifies them without producer state and freshly replays
the exact pipeline. The accompanying Lean file is an abstract finite model, not
a verification of Rust, Linux custody, or Ed25519. See
`../docs/042_native_observer_synthesis_v4.md`.

Observer synthesis v5 appends a separately rooted 2,048-row affine
parity/reflection grammar and deterministic synthetic calibration family.
Proof-carrying branch-and-bound binds admitted lower bounds and the pruned
suffix, while a separate exhaustive implementation checks bounded terminals.
Worker-v5 adds fail-closed closed-rootfs/delegated-cgroup custody with
parent/child readback and cleanup. VOR5 threshold-authenticates exact
request/result/pruning/manifests under an external rotation policy and replays
the proof without producer state. These remain catalog/task/cost/host-relative
engineering results. See `../docs/043_native_observer_synthesis_v5.md`.

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
