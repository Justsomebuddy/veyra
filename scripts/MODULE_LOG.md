# Scripts module log

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
