# Core module log

### [0.2.0] Core runtime invariant hardening
- **Type:** Correctness / Security
- **Files:** `confluence_runtime.py`, `intrinsic_observer_echo_source.py`,
  `observer_provenance.py`, `stream_completion_formal_process.py`,
  `translated_confluence_cell.py`, focused invariant tests, public docs,
  portable admission, and changelog
- **What:** Replaced exactly seven optimized-Python-sensitive assertions with
  explicit stable guards, added exact type narrowing, made the R13 verifier
  nonthrowing under hostile helpers, made missing-pipe cleanup deterministic,
  and removed raw command values from capture logs.
- **Why:** Runtime correctness, cleanup and privacy must not depend on whether
  CPython retains `assert` statements or on impossible/hostile boundary states.
- **Module version:** 0.1.0 → 0.2.0
- **Boundary:** Public C1 with both joins absent remains total `OPEN`, while a
  one-sided partial join remains invalid; valid DTOs,
  artifacts, digests, receipts, output bytes, exports, proof status and claim
  levels are unchanged. Certificate and VAM assertion debt is out of scope.
- **Hosted remediation:** The portable hostile-helper regression uses an
  uninitialized exact R13 DTO allocated without invoking its pinned Lean-backed
  producer, so portable jobs exercise the verifier boundary without requiring
  that external toolchain. Its missing-stdout test replaces the platform-
  specific process-group helper with a bounded cleanup double, proving one
  cleanup call and one reap on Windows without changing production.

### [0.1.0] Certificate producer result invariants
- **Type:** Correctness / Security
- **Files:** `certify_observer_genesis.py`, `certify_productivity.py`, focused
  invariant tests, API reference, portable admission, and changelog
- **What:** Replaced exactly 12 `assert isinstance(...)` certificate narrowing
  checks with immediate `type(value) is Expected` fail-closed guards, fixed
  value-free error logs, and stable `RuntimeError` failures.
- **Why:** Python removes assertions under `-O`, and permissive subclass checks
  allowed hostile objects to reach downstream attribute consumption.
- **Module version:** new → 0.1.0
- **Boundary:** Valid certificate outputs, DTOs, bytes, counts, digests, exports,
  proof status, and claim levels are unchanged. No other production assertion
  is part of this wave.
