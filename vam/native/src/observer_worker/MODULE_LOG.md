# Native Observer Worker Module Log

### [5.0.1] isolation_v5.rs — Truthful cgroup capability classification
- **Type:** 🐛 Fix
- **Files:** `vam/native/src/observer_worker/isolation_v5.rs`,
  `vam/native/tests/observer_worker_v5.rs`
- **What:** Existing nondelegated cgroup mounts and controller/subtree capability
  read failures now produce the explicit harness `UNAVAILABLE` report, while
  invalid limits and malformed roots remain fail-closed errors.
- **Why:** Post-merge v5 audit found that common valid-but-nondelegated host
  environments escaped the documented `PASSED`/`UNAVAILABLE` harness contract.
- **Module version:** 5.0.0 → 5.0.1
