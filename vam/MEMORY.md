# VAM Module Memory

## Purpose

`vam/` contains the reference VAM text/binary runtimes, Core and tiny
high-level lowering, the isolated R12.4 intrinsic VAMI codec/runtime, and the
native Rust parity implementation. It remains a bounded finite research
machine, not a theorem prover or a promotion surface.

## Result-invariant contract

- `intrinsic/runtime.py` admits only an exact built-in rendered `dict` before
  metrics and exact built-in frame `bytes` before decoding. Both failures use
  stable `IntrinsicCodecError(kind="payload")` messages and fixed value-free
  logs.
- `src/diagnostics.py` closes a missing parser diagnostic into
  `internal.compiler_bug`; `src/highlevel.py` wraps a missing Core diagnostic
  as `core.internal.compiler_bug` while retaining successful lowering.
- Valid VAMI bytes/profile/report digests, VAM0/VAMD behavior, Python/Rust
  parity, compiler success paths and `__all__` surfaces remain unchanged.
- `tests/test_vam_assertion_invariants.py` is portable and must keep all four
  guards active under `python -O`; do not replace its explicit child checks
  with assertions.

## Working rules

- Keep intrinsic failures within the established codec taxonomy and reject
  exact-type violations before callbacks, metrics or field access on the
  rejected value, and before decoding for rejected frames.
- Logs at partially trusted boundaries must use fixed reasons and safe counts;
  do not log source text, raw values, representations, exception payloads,
  dynamic type names, frame bytes or digests.
- Preserve the separation between legacy `vam.src`, isolated `vam.intrinsic`
  and native Rust parity surfaces. Any wire/export change requires new explicit
  compatibility evidence rather than silently updating pins.
- Do not mass-format legacy VAM production files inside semantic hardening
  changes. Full `make verify` requires separate authorization; focused evidence
  must be described as focused.

## Version

Documented VAM result-invariant baseline `0.1.0` (issue #69).

## Session Notes (2026-08-15)

- Replaced exactly four optimized-away result/diagnostic assertions with
  exact pre-callback gates or conservative internal diagnostics. Added hostile,
  privacy, compatibility and optimized-Python regressions plus portable
  admission; final verification/publication remain parent-owned.
