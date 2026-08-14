# P3-OG Machine-Pressure Module Log

## 0.2.1 — 2026-08-14

### Raw-cycle versus operational semantics — explicit nonclaim regression
- **Type:** 🐛 Fix / 📝 Documentation
- **Files:** `tests/test_prime_power_observer_genesis_p3og_lifecycle.py`,
  `docs/168_endogenous_arithmetic_observer_p3og.md`, active registry,
  API/index/changelog and module memory
- **What:** Pinned `(0,1,0)` versus `(0,1,2)`: all 41 tested low-level coupling
  responses and fixed-schedule semantic state transitions agree after
  source/seed identity is excluded, while the full-word lifecycle judgments are
  respectively witnessed and refuted. The complete pressure runtime remains
  distinct and rejects the second word at its explicit terminal-recurrence
  gate. Documented the pressure-entry digest as identity/replay binding, not
  operational representation invariance.
- **Why:** Close issue #46's valid semantic-boundary gap before any future role
  consumer can misread raw-cycle v1 evidence as a machine-semantic property.
- **Verification:** Focused P3-OG tests pass `121/121`; package/path policy tests
  pass `26/26`; Ruff, formatting, PyCompile, hygiene `1756/0`, diff and
  non-echoing publication-safety gates pass. The portable pytest stage passes;
  local package smoke remains `UNAVAILABLE` because setuptools 80.10.2 is below
  the declared `>=83,<84` build floor, so hosted CI must supply that clean gate.
  Independent final review is GO with blocker/high/medium/low `0/0/0/0`. Full
  `make verify` was not run.
- **Module version:** 0.2.0 → 0.2.1

## 0.2.0 — 2026-08-14

### Raw-cycle first-return pressure — authority-free bounded genealogy analogue
- **Type:** ✨ Feature / 🔒 Security
- **Files:** `src/core/prime_power_observer_genesis_p3og_lifecycle*.py`,
  `tests/test_prime_power_observer_genesis_p3og_lifecycle*.py`
- **What:** Added a separate versioned lifecycle facade whose native ticks read
  only the exact committed seed cycle, start from `UNFORMED`, bind continuous
  state/receipt chains, stop at the least return after genuine departure,
  bind the lifecycle source to the deterministic selected-seed receipt, and
  validate by fresh exact replay. Digest-consistent cursors after an earlier
  first closure are unreachable and rejected. Passing evidence binds only the
  existing operational pressure-entry digest.
- **Why:** Supply the first bounded pre-token formation-pressure seam requested
  by issue #39 without changing the existing machine report bytes or pretending
  that a linear raw-cycle replay is historical observer genesis.
- **Module version:** 0.1.1 → 0.2.0

### Public status synchronization — preserve the historical boundary
- **Type:** 📝 Documentation
- **Files:** `CHANGELOG.md`, `THEOREMS.md`, doc 168, API/navigation/index,
  active registry, P2/prime-power/closure summaries, module memory/log
- **What:** Documented the executable least-first-return analogue while keeping
  full DEF-OG-003, typed history, role, token, admission, HAP/N0 lift, theorem,
  certificate and promotions explicitly absent or `OPEN`.
- **Why:** Prevent bounded native replay from being misreported as a historical
  formation judgment or observer actualization.
- **Module version:** 0.2.0

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
