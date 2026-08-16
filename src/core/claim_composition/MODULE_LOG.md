# Claim Composition Module Log

### [1.0.2] `protocol.py` — strict local-source admission
- **Type:** Correctness / Security
- **File:** `protocol.py`
- **Lines:** local receipt construction and fresh replay
- **What:** Added one logged strict-leaf profile gate requiring exact `LOCAL`
  quantification and no component-contract identity before constructing a
  `LocalClaimReceipt`.
- **Why:** An aggregate exact-conjunction contract could previously be
  relabeled as local and re-enter composition, making target identity depend
  on nested bracketing rather than the documented flat N-ary source family.
- **Module version:** 1.0.1 → 1.0.2
- **Boundary:** Policy A semantic-component deduplication and occurrence-exact
  v1/P2 evidence remain unchanged. No ancestry inference, recursive flattening,
  trust, independence, truth, stronger wording or promotion is added.
- **Verification:** Focused composition/P2 `109/109`, portable Pytest `703/703`,
  package metadata `31/31`, Ruff lint, compile, import-skipped strict target
  Mypy, module Bandit `0`, repository hygiene `1836/0`, exact pins and diff
  checks pass. An exact-HEAD discriminator admits aggregate re-entry while the
  changed tree rejects it with the named reason. Exact-HEAD and changed-tree
  Ruff-format classification is the same two inherited files. Local package
  smoke stops at the known setuptools `80.10.2 < >=83,<84` floor. Full `make
  verify` was not run. Independent final review: GO `0/0/0/0`.

### [1.0.1] `protocol.py` — semantic component-set derivation
- **Type:** Correctness / Compatibility
- **File:** `protocol.py`
- **Lines:** exact-conjunction producer/obstruction derivation and private
  component helper
- **What:** Added one shared sorted-unique semantic contract-digest helper and
  used it in both target construction and exact-license validation.
- **Why:** Two distinct established receipts may bind the same semantic
  contract; the target is set-valued while receipt/validator/authority evidence
  remains occurrence-valued.
- **Module version:** absent → 1.0.1
- **Boundary:** Canonical sources, receipt roots, validator roots, license,
  assessment, composition receipt, P2 authority, codecs/schemas/domains/exports
  and distinct-contract pins are unchanged. No agreement, independence, trust,
  authority upgrade or promotion follows.
- **Verification:** Focused `22/22`, broader relevant `116/116`, package
  metadata `30/30`, exact v1/v2 pin, strict target Mypy, Bandit `0`, Ruff lint,
  compile, hygiene, privacy and protected-surface checks pass. Full
  `make verify` was not run.
