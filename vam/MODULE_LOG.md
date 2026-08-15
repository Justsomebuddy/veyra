# VAM Module Log

### [0.1.0] VAM runtime result-invariant hardening
- **Type:** Correctness / Security
- **Files:** `intrinsic/runtime.py`, `src/diagnostics.py`, `src/highlevel.py`,
  `tests/test_vam_assertion_invariants.py`, portable admission, public docs,
  module memory and changelog
- **What:** Replaced exactly four optimization-sensitive assertions with exact
  built-in dict/bytes gates and conservative missing-diagnostic results; added
  fixed value-free entry/error/exit logs and hostile plus `python -O`
  regressions.
- **Why:** Runtime type narrowing, decoder ordering and diagnostic totality must
  not depend on whether CPython retains `assert` statements or on trusted helper
  results.
- **Module version:** absent → 0.1.0
- **Boundary:** Valid VAMI/profile/report bytes and digests, legacy VAM0/VAMD,
  Python/Rust parity, successful compilation, exports, certificate/proof status
  and claim levels are unchanged. Wider assertion and repository quality debt
  is out of scope.
- **Verification:** Focused `7/7`, broader portable VAM `320/320`, native
  Python/Rust VAMI parity `27/27` and configured portable Pytest `667/667`
  pass. Ruff lint/new-test format, byte compilation, strict target Mypy,
  Bandit B101 `0`, hygiene `1831/0` and diff checks pass; exact old-tree
  optimized discrimination exits `11`. Local package smoke remains unavailable
  only because setuptools 80.10.2 is below the declared `>=83,<84` floor. Full
  `make verify` was not run.
