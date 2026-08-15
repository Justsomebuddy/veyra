# Core module log

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
