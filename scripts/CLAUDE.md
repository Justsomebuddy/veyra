# Scripts module memory

Version: **0.2.0**. Scope: maintained command-line verifiers, generators,
portable checks, and bounded research explorers.

## Contracts

- `generate_tables.py` and `generate_notebooks.py` produce deterministic,
  manifest-bound artifacts. Changes must compare complete generated trees at
  identical logical output paths, including manifest bytes.
- `check_lean_sources.py` and `check_research_lean.py` compile pinned Lean
  inventories with bounded parallelism. The research checker must keep its
  fresh-snapshot, exact-manifest, source-rehash, and no-persistent-cache
  boundaries.
- Explorer CLIs are public research tools. Preserve argument/help behavior and
  exit status when applying mechanical changes.
- Scripts print explicit stages and final error counts. Functional changes add
  entry/error/exit logging through the existing project logger; secrets,
  source bodies, raw environment values, and full sensitive digests do not
  belong in logs.
- Maintained handwritten files target at most 1,000 lines. The largest current
  script, `check_research_lean.py`, remains below that target after formatting.

## Session Notes (2026-08-15)

- Private `_trusted_git.py` now owns the exact package/hygiene inventory and
  ignore queries. It admits only fixed absolute installation paths, validates
  executable/ancestor metadata before and after execution, scrubs PATH and
  Git/loader overrides while preserving HOME/XDG global-exclude semantics, and
  uses fixed value-free failures. This is narrow path hardening, not binary,
  ACL, repository-race, or all-subprocess attestation.

- Portable verification now admits the seven-position core runtime invariant
  regression, including hostile helper, optimized-Python, process cleanup and
  log-privacy checks. This is inventory admission only; portable stage order,
  timeout, environment, package and logging behavior are unchanged.

- Portable verification now admits the certificate-result invariant regression
  covering all 12 observer-genesis/productivity producer positions and two
  optimized-Python process checks. This is test admission only; the portable
  runner's stage ordering, timeout, logging, and package behavior are unchanged.

- Issue #63 bounds the first repository formatting wave to exactly 21
  previously unformatted scripts: nine verifier/build/generator tools and 12
  explorer CLIs. Ruff formatting is AST-identical, all explorer help streams
  and exits are unchanged, and regenerated 12-table and 83-notebook trees are
  byte-identical including manifests. No script semantics or logging changed.
- This bounded wave does not clear or reclassify the remaining repository-wide
  Ruff, Mypy, or Bandit debt and is not comprehensive `make verify` evidence.
- The real-Sage G4 verifier passes 1,275/1,275 assignments. The broader
  `sage_smoke.py --require-sage` remains red at the inherited content-bound
  `r10-reviewed-tcb-drift` / `layer-theorem-bridge-rejected` boundary; replay
  from the committed pre-format tree has the same exit and stable reasons.
