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
