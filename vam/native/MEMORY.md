# VAM Native Module

## Purpose

This crate implements the bounded native VAM codecs, inspectors, observer
workers, replay tools, and synthesis experiments used by the Python and Rust
verification lanes.

## Build and Test Contract

- `Cargo.lock` is authoritative; repository verification invokes Cargo 1.95.0
  with `--locked`, while the crate retains its declared Rust 1.83 compatibility
  floor.
- `CARGO_TARGET_DIR` may be absolute or relative.  Test helpers must ask
  `cargo metadata` for the effective target directory rather than reconstruct
  it from the manifest directory.
- Tests that execute a built binary use Cargo's reported `compiler-artifact`
  executable path, require the artifact to exist, and verify that it remains
  beneath the metadata target root.
- CLI protocol tests execute the artifact directly after a session-scoped
  build so compiler diagnostics cannot contaminate the CLI's stderr contract.

## Version

Native crate `0.1.0`; documented test/build integration baseline `0.1.0`.
