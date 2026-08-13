# Observer Synthesis Module Log

### [v5 hardening] Represented tasks and truthful prune frontier
- **Type:** 🐛 Fix
- **Files:** `vam/native/src/observer_synthesis/discovery_benchmark_v5.rs`,
  `vam/native/src/observer_synthesis/synthesis_v5.rs`,
  `vam/native/src/observer_synthesis/synthesis_winner_v5.rs`,
  `vam/native/src/observer_synthesis/prune_verifier_v5.rs`,
  `vam/native/tests/observer_synthesis_v5.rs`
- **What:** Bound a nonidentity represented-state permutation for the recovery
  calibration row; evaluated all same-cost alternatives; restricted pruning to
  a strictly higher-cost suffix; independently reconstructed both semantics in
  the verifier; renewed the affected V5 family/run digests.
- **Why:** Post-merge V5 audit found that recovery duplicated hidden-affine
  semantics and that inspected same-cost rows were mislabeled as pruned.
- **Compatibility:** V1–V4 contracts and bytes remain unchanged.
