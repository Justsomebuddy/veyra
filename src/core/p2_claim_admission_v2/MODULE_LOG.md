# Module Log — P2 Claim Admission v2

### [2.0.0] Additive meta-only registry and literal oracle
- **Type:** ✨ Feature / 🔒 Security
- **Files:** `registry.py`, `errors.py`, `resource_validation.py`, `__init__.py`,
  focused registry tests and publication integration.
- **What:** Added the exact immutable v1-plus-one registry snapshot for
  `composition-licensed-presentation-v2`, its independent literal extension
  oracle, complete semantic and nonclaim pins, strict shallow type gates, fixed
  resource limits, and a deliberately registry-only package export surface.
- **Why:** Freeze and validate the licensed-composition presentation vocabulary
  before a separate producer wave, without widening the generic P2-S v1
  calculus or casting registry/schema conformity into truth.
- **Evidence:** Exact counts `15/18/41/1/5`; registry digest
  `ba6020151518faf5eb2fa2eb22943af4c7d0abd88b393b1388f848e63dbc3eb4`;
  v1 registry and oracle pins remain exact. Ruff, formatting and byte
  compilation pass; focused registry tests pass `20/20`; broader registry,
  P2-S v1, composition-v1, packaging, path and platform regressions pass
  `133/133`; documentation references pass `2/2`; hygiene passes `1800/0`.
  Exact-head hosted and publication evidence is recorded by the pull request.
- **Module version:** new → 2.0.0
