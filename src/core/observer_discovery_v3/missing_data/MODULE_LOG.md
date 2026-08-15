# Missing-Data Runtime Module Log

### [1.0.0] RFC 172 additive runtime
- **Type:** ✨ Feature / 🔒 Security
- **Files:** `types.py`, `errors.py`, `resources.py`, `policy.py`, `parsing.py`,
  `digest.py`, `runtime.py`, `codec.py`, `__init__.py`
- **What:** Added explicit categorical missing-marker policy replay, typed
  receipts, native/external authority separation and bounded canonical codec.
- **Why:** Realize accepted RFC 172 without widening strict-v3 ingestion or
  allowing equal legacy projections to mint native policy authority.
- **Module version:** new → 1.0.0

### [1.0.1] Adversarial review closure
- **Type:** 🔒 Security / 🐛 Fix / ✅ Compatibility
- **Files:** `resources.py`, `policy.py`, `digest.py`, `runtime.py`, `codec.py`,
  `parsing.py`, focused tests and fixed v1 JSON fixture
- **What:** Moved whole-policy exact type/cardinality/text/integer/node gates
  before copying and UTF-8 work; replaced bool/int-collapsing DTO equality with
  exact canonical comparison; removed dynamic type-name callbacks and digest
  log values; serialized detached validated snapshots; pinned v1 public bytes,
  roots, errors and exports.
- **Why:** Close three HIGH and three MED independent-review authority, resource,
  callback, privacy and TOCTOU findings without changing strict ingestion,
  root exports or Phase-II compatibility.
- **Module version:** 1.0.0 → 1.0.1

### [1.0.2] Final adversarial resource-boundary closure
- **Type:** 🔒 Security / 🐛 Fix
- **Files:** `resources.py`, `runtime.py`, `codec.py`, `parsing.py`, adversarial
  and codec tests, runtime documentation
- **What:** Added pre-transcoding codec caps, pre-decode physical-line scans,
  snapshot-boundary row/scalar rechecks, shallow top/rule/global-node stops and
  one shared retained policy/schema/receipt/parser/wrapper resource ledger.
- **Why:** Prevent oversized conversion, post-preflight mutation, unbounded
  structural traversal and separately passing components from exceeding the
  RFC's aggregate ceilings.
- **Module version:** 1.0.1 → 1.0.2

### [1.0.3] Aggregate text-ledger multiplicity correction
- **Type:** 🔒 Security / 🐛 Fix
- **Files:** `resources.py`, `parsing.py`, adversarial tests and runtime docs
- **What:** Charged each simultaneously retained row identity, observed scalar,
  missing fallback and target at its exact semantic/projection/wrapper
  multiplicity instead of undercounting shared values.
- **Why:** Ensure independently bounded policy and row components cannot exceed
  the aggregate 1 MiB nonpayload ceiling before canonical or digest work.
- **Module version:** 1.0.2 → 1.0.3

### [1.0.4] Direct-wrapper, codec and UTF-8 preflight closure
- **Type:** 🔒 Security / 🐛 Fix / ✅ Privacy
- **Files:** `resources.py`, `runtime.py`, `codec.py`, `parsing.py`, shared
  canonical/digest loggers, adversarial tests and runtime documentation
- **What:** Applied the shared aggregate ledger to detached structural and
  codec paths; shallow-capped every decoded list before nested traversal;
  counted exact UTF-8 bytes without allocations before policy detachment;
  removed digest values from shared exit logs; and cleared owned strict-Mypy
  suppressions/casts.
- **Why:** Close the final direct-wrapper aggregate bypass, nested codec list
  traversal, multibyte/top-text preflight and logging-claim mismatches found by
  second independent review.
- **Verification:** Missing-data 62/62, broader focused 291/291 and
  package/path/platform 46/46 pass; Ruff, strict owned Mypy 9/9, PyCompile,
  function logging 126/126, hygiene 1820/0, 24-file privacy, compatibility and
  whitespace diff gates pass. The touched shared proof codec was Ruff-formatted;
  its AST equals `HEAD` plus the single intended digest-free log call, and the
  proof-core regression lane passes 67/67.
- **Module version:** 1.0.3 → 1.0.4

### [1.0.5] Exact retained-authority text charge
- **Type:** 🔒 Security / 🐛 Fix
- **Files:** `resources.py`, `runtime.py`, adversarial tests and runtime docs
- **What:** Parameterized the shared wrapper seed by the actual receipt
  authority while retaining native replay as the source-parser default.
- **Why:** `EXTERNAL_BINDING_ONLY` is one UTF-8 byte longer than
  `NATIVE_POLICY_REPLAY`; hardcoding native authority undercounted direct
  structural/codec wrappers at the exact 1 MiB boundary.
- **Verification:** Exact-boundary regression proves native-at-limit admission
  and external +1 rejection; missing-data tests pass 63/63, broader focused
  tests pass 292/292, and the complete static/hygiene/compatibility gate passes.
- **Module version:** 1.0.4 → 1.0.5

### [1.0.6] Complete-policy and downgrade aggregate closure
- **Type:** 🔒 Security / 🐛 Fix
- **Files:** `resources.py`, `policy.py`, `runtime.py`, adversarial tests and
  runtime docs
- **What:** Combined the policy container and five actual top strings with both
  schemas/rules before retained capture; reserved the exact fixed generated
  top overhead before policy construction; and recharged a completed external
  downgrade before it can return.
- **Why:** Prevent near-limit nested policy graphs from exceeding the 1 MiB or
  node ceilings through omitted top fields, prevent construction of policies
  that capture would reject, and prevent native-at-limit downgrade from
  returning an external +1-byte over-cap wrapper.
- **Verification:** Three pre-detachment/boundary regressions pass; missing-data
  is 66/66 and the broader focused lane is 295/295.
- **Module version:** 1.0.5 → 1.0.6

### [1.0.7] Windows-safe oversized-codec test identities
- **Type:** 🐛 Fix / ✅ CI Portability
- **File:** `tests/test_observer_discovery_v3_missing_data_codec.py`
- **What:** Replaced implicit representations of four 1 MiB codec parameters
  with fixed short ASCII IDs and pinned their stable 32-character ceiling.
- **Why:** Windows rejects environment values above 32,767 characters; Pytest
  copied the implicit megabyte-scale node IDs into `PYTEST_CURRENT_TEST`,
  causing hosted setup/teardown errors despite correct production behavior.
- **Verification:** Collected node IDs are short/stable, codec tests pass 16/16
  and the complete configured portable Pytest step passes; no production
  semantics changed.
- **Module version:** 1.0.6 → 1.0.7
