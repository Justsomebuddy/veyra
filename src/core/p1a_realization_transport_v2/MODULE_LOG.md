# P1-A Realization Transport V2 Module Log

### [2.0.1] Validation/runtime — Close hostile preflight and public errors

- **Type:** 🔒 Security / 🐛 Fix
- **Files:** `observation.py`, `partitions.py`, `validation.py`, `runtime.py`,
  `composition.py`, `public.py`, `log_boundary.py`,
  `tests/test_p1a_realization_transport_v2_limits.py`
- **What:** Added shallow exact/resource gates before comparisons and JSON,
  exact bounded R11 payload-schema validation, full STRONG-judgment replay,
  embedded-v1 graph/row/root binding, authoritative partition carriers,
  pre-construction six-stream charging, one combined shallow/decoded node cap,
  complete nonpayload UTF-8 charging, a non-disclosing local outcome encoder,
  a transient thread-local redaction boundary for reachable value-bearing
  lower replay logs installed before pre-existing audit filters,
  filter/factory restoration checks, and fixed public exception normalization.
- **Why:** Hostile DTO fields, malformed canonical JSON, detached v1 children,
  and lower-layer exceptions must not bypass or escape the sibling boundary.
- **Verification:** Focused normal/adversarial/compatibility/limits matrix
  `94/94`; Ruff, format, PyCompile, and diff checks pass. Hosted gates are
  recorded in the publishing PR; no full `make verify` claim.
- **Module version:** 2.0.0 → 2.0.1

### [2.0.0] p1a_realization_transport_v2 — All-status same-doctrine sibling

- **Type:** ✨ Feature / 🔒 Security
- **Files:** `types.py`, `digest.py`, `observation.py`, `partitions.py`,
  `validation.py`, `runtime.py`, `composition.py`, `public.py`, `__init__.py`
- **What:** Added exact sibling DTOs and roots, full `Ready|Blocked` projection,
  independent source/target replay, six-payload commuting rows, endpoint
  partitions/refinement maps, embedded-v1 verification, authoritative receipt
  reconstruction, fresh identity/composition, fixed safe logs, and explicit
  row/payload/aggregate/node/text ceilings.
- **Why:** RFC 169 requires a separately versioned all-status P1-A square;
  widening v1 or inferring a selected ready value from discarded blocked data
  would create false transport evidence.
- **Verification:** Normal, adversarial, compatibility, v1 regression,
  packaging, portable, hygiene, format, byte-compilation, and diff gates are
  recorded in the publishing PR; no full `make verify` claim.
- **Module version:** absent → 2.0.0
