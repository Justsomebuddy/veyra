# Scripts module log

### [0.2.1] Canonical late-directory sdist admission
- **Type:** Bug fix / portability
- **Files:** `scripts/package_smoke.py`, `scripts/verify_portable.py`,
  `tests/test_package_smoke_archive.py`, `tests/test_package_metadata.py`,
  `docs/174_python_quality_baseline.md`, `scripts/CLAUDE.md`,
  `scripts/MODULE_LOG.md`, `CHANGELOG.md`
- **What:** Allowed a canonical directory entry to follow files that already
  established it as an implicit archive ancestor, and admitted the adversarial
  archive regression to the hosted portable test inventory.
- **Why:** Valid source distributions may order explicit directory records
  after their children; rejecting that safe ordering made the smoke verifier
  less portable than the archive policy it documents.
- **Module version:** 0.2.0 → 0.2.1
- **Boundary:** Exact duplicate paths, files at implicit ancestor paths,
  case/NFC spelling aliases, file ancestors, unsafe member types, size/count
  limits, pre-validation extraction and `tarfile.data_filter` policy are
  unchanged.

### [0.2.0] Private trusted Git executable boundary
- **Type:** Security / portability
- **Files:** `scripts/_trusted_git.py`, `scripts/package_smoke.py`,
  `scripts/project_hygiene.py`, `scripts/verify_portable.py`,
  `tests/test_trusted_git.py`, `tests/test_package_metadata.py`,
  `docs/178_trusted_git_executable.md`, `docs/index.md`, `CHANGELOG.md`
- **What:** Routed the three production fixed-name Git calls through two
  private operations backed by fixed absolute candidates, POSIX ownership/mode
  or Windows reparse-point admission, executable/ancestor identity replay,
  isolated process settings, bounded byte capture, and a case-insensitive
  environment scrub. Added portable adversarial and consumer regressions.
- **Why:** Remove production Bandit B607 executable-path ambiguity without
  suppressions or changing source inventory and global-exclude semantics.
- **Module version:** 0.1.2 → 0.2.0
- **Boundary:** No public package export, registry/PATH resolution, checksum or
  signature pin, Windows ACL claim, atomic fd-exec, Git index race claim, broad
  subprocess refactor, proof-status change, or full `make verify` claim.

### [0.1.2] Portable core-runtime invariant admission
- **Type:** Test / portability
- **Files:** `scripts/verify_portable.py`, `tests/test_package_metadata.py`
- **What:** Added the exact core assertion-invariant regression module to the
  hosted OS-neutral Pytest inventory and pinned that membership in metadata.
- **Why:** Exercise hostile type/helper gates, optimized-Python behavior,
  process cleanup and fixed log privacy on every supported hosted platform.
- **Module version:** 0.1.1 → 0.1.2
- **Boundary:** No portable stage, timeout, environment, package or logging
  behavior changed.

### [0.1.1] Portable certificate-result invariant admission
- **Type:** Test / portability
- **Files:** `scripts/verify_portable.py`, `tests/test_package_metadata.py`
- **What:** Added the exact certificate-result invariant regression module to
  the hosted OS-neutral Pytest inventory and pinned that membership in package
  metadata tests.
- **Why:** Ensure hostile-subclass and `python -O` fail-closed behavior runs on
  every supported hosted platform.
- **Module version:** 0.1.0 → 0.1.1
- **Boundary:** No portable stage, timeout, environment, package, or logging
  behavior changed.

### [0.1.0] Bounded Ruff formatting baseline
- **Type:** Style / maintainability
- **Files:** 21 explicitly scoped verifier, generator, and explorer Python
  scripts; `scripts/CLAUDE.md`; `scripts/MODULE_LOG.md`; root changelog
- **What:** Applied the configured Ruff formatter without changing the parsed
  AST of any script. The wave covers nine verifier/build/generator tools and 12
  explorer CLIs; the other seven already-formatted scripts remain untouched.
- **Why:** Retire one reviewed, reversible portion of the historical 985-file
  Ruff-format debt without a repository-wide rewrite.
- **Module version:** new → 0.1.0
- **Boundary:** No function, argument, default, output, artifact, proof policy,
  claim status, or logging behavior changed.
- **Verification:** AST identity passed for 21/21 files; all 12 explorer
  `--help` stdout/stderr/exit triples are exact; regenerated table artifacts
  are byte-identical for 12/12 files and generated notebooks for 83/83 files,
  both including their manifests. Focused tests pass 129/129; both Lean
  checkers pass (48 stable sources and 56 manifest-bound sources plus 65
  declaration/axiom rows); Ruff, PyCompile, real-Sage G4 1,275/1,275, runtime
  demos, hygiene, privacy, and diff checks pass. The available real-Sage smoke
  remains red at pre-existing content-bound TCB drift, with the same exit and
  stable reasons from committed pre-format `HEAD`; full `make verify` was
  intentionally not run.
