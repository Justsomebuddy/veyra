# Module Log — Strict v3 Categorical Ingestion

### [1.0.0] Byte-only categorical CSV/JSONL adapter

- **Type:** ✨ Feature / 🔒 Security
- **Files:** `__init__.py`, `types.py`, `parsing.py`, `runtime.py`,
  `../schema/canonical.py`
- **What:** Added strict bounded CSV and JSONL conversion into the existing
  canonical `ThreeWayPresentation`, with exact exports and safe diagnostics;
  removed the pre-existing schema-field value from canonical debug output.
- **Why:** Provide explicit caller-declared categorical ingestion without
  inference, repair, path access, new evidence DTOs, or stronger claims.
- **Module version:** new → 1.0.0

### [1.0.0 docs] RFC 172 missing-data sibling boundary

- **Type:** Documentation / Architecture / Compatibility
- **Files:** `docs/172_observer_v3_missing_data_policy_rfc.md`, docs indexes and
  ingestion boundary documentation; no Python source changed.
- **What:** Froze a future separate masked-missingness wrapper with explicit
  replay authority, schema/policy/receipt bindings, limits and nonclaims.
- **Why:** Prevent missing-data behavior from being added implicitly to the
  exact categorical v1 parser or returned as an authority-erasing bare v1 DTO.
- **Module version:** 1.0.0 unchanged

### [1.0.0 docs] RFC 173 continuous-data sibling boundary

- **Type:** Documentation / Architecture / Compatibility
- **Files:** `docs/173_observer_v3_continuous_data_policy_rfc.md`, docs indexes
  and ingestion boundary documentation; no Python source changed.
- **What:** Froze a future separate exact-decimal fixed-bin wrapper with
  caller-declared schema/policy/receipt bindings, replay authority, limits and
  nonclaims.
- **Why:** Prevent numeric interpretation or learned binning from being added
  implicitly to the exact categorical v1 parser or returned as an
  authority-erasing bare v1 DTO.
- **Module version:** 1.0.0 unchanged
