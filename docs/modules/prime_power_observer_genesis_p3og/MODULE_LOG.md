# P3-OG Machine-Pressure Module Log

## 0.1.1 — 2026-08-14

### Matched maintenance-control coupling — fail-closed paired evidence
- **Type:** 🐛 Fix / 🔒 Security
- **Files:** `src/core/prime_power_observer_genesis_p3og_runtime.py`,
  `src/core/prime_power_observer_genesis_p3og_machine_internal.py`,
  `tests/test_prime_power_observer_genesis_p3og.py`,
  `tests/test_prime_power_observer_genesis_p3og_adversarial.py`
- **What:** Added a schema-derived semantic state projection excluding only the
  maintenance flag and state digest, then gated both calibration inputs on
  expected flags, equal responses/states, exact bounded receipt scalars, and
  exact input/state-link/receipt digests. Accepted precomputed coupling outputs
  now continue through the shared suffix helper without recoupling. Added
  baseline-byte pins plus response, semantic-state, flag, right-arm, priority,
  malformed-output, hostile-scalar, broken-link, and future-field regressions.
- **Why:** Ensure the active/control arms remain matched at the coupling
  boundary and fail narrowly as `matched-control-coupling-drift` before any
  downstream reason, including under future coupling/state refactors.
- **Module version:** 0.1.0 → 0.1.1

### Public finite-slice wording — matched-coupling boundary
- **Type:** 📝 Documentation
- **Files:** `CHANGELOG.md`,
  `docs/168_endogenous_arithmetic_observer_p3og.md`, module memory/log
- **What:** Documented the paired-coupling gate and unchanged byte/status/export/
  theorem/nonclaim boundaries without altering the facade or public schemas.
- **Why:** Keep the executable finite pressure claim and its public limitations
  synchronized.
- **Module version:** 0.1.1

## 0.1.0 — 2026-08-13

### Flat P3-OG module family — bounded candidate integration
- **Type:** ✨ Feature / 🔒 Security
- **Files:** `src/core/prime_power_observer_genesis_p3og*.py`,
  `tests/test_prime_power_observer_genesis_p3og*.py`
- **What:** Added the explicit facade, closed DTOs, canonical source/selection,
  bounded machine/runtime, fresh report validation, and focused positive and
  adversarial tests. Source seed cardinality and text character count are
  preflighted before nested traversal/encoding; canonical integers are capped
  before decimal conversion; dynamic enum/dataclass metadata is bounded before
  JSON sizing and dataclass field maps before `fields()` materialization; public
  removed-state operations fail closed while internal fixed-suffix terminal
  receipts consume the transition budget.
- **Why:** Safely transplant the reviewed P3-OG finite pressure candidate onto
  current `main` without changing root exports or promoting its open claims.
- **Module version:** initial → 0.1.0

### Public status and navigation — candidate boundary synchronization
- **Type:** 📝 Documentation
- **Files:** `CHANGELOG.md`, `THEOREMS.md`, `docs/168_endogenous_arithmetic_observer_p3og.md`,
  `docs/index.md`, `docs/reference/{api,notation-extended,theorem-registry-active}.md`,
  `docs/reference/navigation.md`,
  `docs/{151_veyra_philosophical_kernel_p2,153_prime_power_model_closure,154_six_closure_principles}.md`
- **What:** Indexed the isolated facade and proposed notation while retaining
  `INTERNAL_RESEARCH_CANDIDATE`/`OPEN` status, precise nonclaims, and all current
  documentation routes.
- **Why:** Keep code, navigation, public API inventory, and theorem-status
  language aligned without assigning stable definitions or theorem numbers.
- **Module version:** 0.1.0
