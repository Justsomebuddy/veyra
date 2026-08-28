# VAM Native Module Log

### [0.1.0] test_vam_native_vamd_boundaries.py — Cargo-aware session CLI fixture
- **Type:** 🐛 Fix / ⚡ Performance
- **Files:** `tests/test_vam_native_vamd_boundaries.py`, `vam/native/MEMORY.md`
- **What:** Build `vam0-inspect` once per pytest session with pinned Cargo
  1.95.0 and `--locked`, resolve the effective target through `cargo metadata`,
  select Cargo's exact executable artifact, and run malformed-frame cases
  directly with clean stderr. Added positive external-target selection plus
  missing/escaped-artifact rejection regressions.
- **Why:** Repeated `cargo run` calls were noisy and slow, while hardcoding
  `vam/native/target` would regress absolute and relative
  `CARGO_TARGET_DIR` support.
- **Verification:** VAMD boundary tests `12/12` with a real relative external
  target, including mocked locked-command and missing/escaped-artifact
  regressions; targeted Ruff, byte-compilation, and diff checks pass.
- **Module version:** absent → 0.1.0
