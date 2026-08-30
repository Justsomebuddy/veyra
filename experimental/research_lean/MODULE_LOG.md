# Research Lean module log

### [0.3.0] Native-number ready-mode F002 carrier bridge
- **Type:** Research / anti-island formal bridge
- **Files:** `VeyraResearchNativeNumberBridge.lean`, neutral native length
  observer/helper, manifest/checker/package inventory, existing N1 hostile test
- **What:** Added a general carrier from any already-ready native Mode to its
  exact tact count, then reused stable `THM-F002` on that same `run.length`.
  The composition is isolated in Research Lean so importing arithmetic does not
  pollute the stable R4 namespace or downstream VAM proofs.
- **Evidence:** Exact Lean `4.30.0-rc2`; 63/63 source replay, 87/87 declarations
  and axiom rows; new headline closure is exactly `propext`.
- **Module version:** 0.2.0 → 0.3.0
- **Boundary:** Stable R4 IDs remain 001..007. No prime infinitude, Fermat,
  third theorem-derived layer, R8 promotion, certificate, or registry promotion.

### [0.2.0] Singleton-tact path-word realization bridge
- **Type:** Research / formal bridge
- **Files:** `VeyraResearchOneTactBridge.lean`, `manifest.json`, `README.md`,
  module memory, checker/tests, public research-count references
- **What:** Added an independently represented singleton-tact finite-word carrier
  (`List Unit`) and constructive bridges to `Nat`, unary `Recurrence`, and the
  exact R9 `IntrinsicMode` image, plus strict-native stitch/weave realization.
- **Evidence:** Exact Lean `4.30.0-rc2`, compiler commit
  `3dc1a088b6d2d8eafe25a7cd7ec7b58d731bd7cc`; 21/21 declarations compiled;
  11 axiom rows are empty and 10 depend only on `propext`.
- **Module version:** 0.1.1 → 0.2.0
- **Boundary:** The Lean carrier is the explicit singleton-generated path-word
  realization. This does not prove AX-007 excludes other tacts, establish
  general LEM-001 or arbitrary strict-Mode equivalence, or promote
  THM-001–003/W-001.

### [0.1.1] Stable proof-elaboration source renewal
- **Type:** Correctness / evidence continuity
- **Files:** `manifest.json`, `README.md`, module memory, root changelog/log
- **What:** Renewed the one `proofs/lean/VeyraProofElaboration.lean` digest from
  `5d92ed0a...f0f14d` to `52269d4c...b265f`, then recomputed the domain-separated
  base source root, proof root, and complete manifest digest. The research root
  remains exactly `9c38a3d6...e14514`.
- **Why:** PR #37 intentionally renewed two embedded R9 binding constants in
  the stable source, while PR #40's separate research inventory correctly
  rejected the stale source digest in exact-head CI.
- **Module version:** 0.1.0 → 0.1.1
- **Boundary:** No research source, declaration, statement, claim row, axiom
  closure, import, toolchain identity, stable theorem status, or checker policy
  changed.
- **Verification:** Reproduced the pre-repair checker result as `1 failed, 38
  passed`; post-repair `tests/test_check_research_lean.py` passes `39/39`.
  Static replay verifies 56/56 sources and the 48+8/65/33/65 inventories;
  targeted Ruff, PyCompile, workflow YAML, and `git diff --check` pass. Full
  `make verify` was intentionally not run.

### [0.1.0] Research Lean candidate governance
- **Type:** Security / research integration
- **Files:** `*.lean`, `manifest.json`, `README.md`, `lean-toolchain`,
  checker/tests/CI/packaging
- **What:** Bound eight sources and 65 declarations to exact digests, imports,
  33 literal headline claims, domain-separated roots, toolchain identity, and
  observed axiom closures; added fresh isolated compile and hostile policy
  tests, including the reproduced stale-object fail-open.
- **Why:** PR #40 supplied useful experiments but persistent artifacts and broad
  wording were unsuitable for the stable proof lane.
- **Module version:** new → 0.1.0
- **Status:** `INTERNAL_RESEARCH_CANDIDATE`; no stable theorem promotion.
