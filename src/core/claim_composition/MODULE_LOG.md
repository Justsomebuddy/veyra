# Claim Composition Module Log

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
