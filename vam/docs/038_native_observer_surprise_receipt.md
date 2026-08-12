# Native zero-vs-positive observer-surprise receipt

**Status:** one bounded Rust calibration and replayable receipt.  
**Implementation:** `vam/native/src/observer_synthesis/{benchmark,receipt}.rs`.

## Fixed benchmark

The benchmark uses the closed unary recurrence values `{0,1,2}` and target
partition `{0}` versus `{1,2}`. It runs the exact existing 1,565-row R14.1
catalog and two fixed training obligations; it adds no observer primitive.

The surface observer `Input` produces three response classes, satisfies one of
two obligations, and gives no class saving. The first synthesized winner is the
already pinned ordinal-1 `Crest(Input)`: it produces two classes, satisfies both
obligations, and saves one redundant response class.

```text
surface hits/classes/saving = 1 / 3 / 0
hidden  hits/classes/saving = 2 / 2 / 1
fit gap / class saving      = 1 / 1
benchmark digest            = 2002a7f81d09a1ffd1e7ddcb063baa96b50b99b38443c1b51d285b8d2d395bdc
```

This is a finite quotient calibration: changing observer makes the declared
target partition simpler. It is not BM-F009, DEF-194 promotion, hidden-variable
discovery, general synthesis, minimality, holdout validity, or a theorem.

## Canonical receipt

`NativeObserverSurpriseReceiptV1` binds benchmark, catalog, training, limits,
trace, surface/hidden observer identities, exact winner bytes/digest/rank,
integer-only scores, active cases, the complete CEGIS counter ledger, and explicit
`wall_clock_enforced=false` / `process_as_enforced=false` custody.

The default receipt digest is
`b7bbfdfdfbf33fc1bae1cd58ec7da126d88b90558552bddccd59f1ba48cb9547`.
Replay reconstructs the benchmark, catalog, cases, run, and witness under the
receipt's exact counter limits and then exact-compares every field. Rebound
semantic tampering and raw digest tampering fail closed. An `Incomplete`,
`Exhausted`, or `Invalid` run cannot mint this receipt.

Canonical receipt bytes are deterministic and suitable for a future signature
envelope, but this slice does not sign them and does not call in-process
execution isolated. `VEYRA_NATIVE_DEBUG` emits only static lifecycle/error
labels; it never logs recurrence payloads, canonical bytes, digests, or receipt
contents.

## Focused verification

```bash
cargo fmt --manifest-path vam/native/Cargo.toml --all -- --check
cargo check --manifest-path vam/native/Cargo.toml --locked
cargo test --manifest-path vam/native/Cargo.toml --locked observer_surprise
```

The public tests cover deterministic construction, replay, the pinned digest
and score, and cutoff-to-`Incomplete` receipt refusal. Unit tests additionally
mutate semantic fields and the receipt digest. This does not replace the Python
observer-synthesis oracle or its stronger process-isolated custody contracts.

`tests/fixtures/observer_synthesis_python_rust_v1.json` is the shared bounded
identity vector. Python and Rust independently check its catalog count, total
canonical bytes, catalog digest, and the exact ordinal/cost/depth/canonical
bytes/digest of `Crest(Input)`. The fixture deliberately excludes Rust-only
benchmark and receipt roots: matching the common identity layer is not a claim
that the implementations have identical custody or receipt semantics.
