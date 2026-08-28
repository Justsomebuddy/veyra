# Module Log — P2 Claim Admission v2

### [2.1.1] Canonical codec resource closure
- **Type:** Correctness / Resource safety
- **Files:** `codec.py`, adversarial codec boundaries, document 171, module
  memory and changelog
- **What:** Applied the decoder's combined raw-authority plus decoded node/text
  charge to the exact encoder data tree before canonical JSON emission.
- **Why:** One valid near-limit typed presentation serialized successfully but
  its own decoder immediately rejected the resulting payload at the stricter
  decoded-text gate.
- **Module version:** 2.1.0 → 2.1.1
- **Boundary:** The decoder is not relaxed. Below-limit canonical bytes,
  judgments, digests, v1 surfaces, registry pins, statuses and nonclaims remain
  unchanged; over-limit encoding fails before returning a payload.

### [2.1.0] Authoritative licensed-composition presentation producer
- **Type:** ✨ Feature / 🔒 Security
- **Files:** `types.py`, `replay.py`, `schema_audit.py`, `public.py`,
  `codec.py`, `validation.py`, `log_boundary.py`, `__init__.py`, focused normal
  and adversarial tests, package/portable integration and public documentation.
- **What:** Added the full source-backed `LicensedCompositionPresentation`
  producer, reconstructing verifier and strict canonical codec. The public DTO
  retains the exact contract, license, freshly derived assessment, receipt,
  premise, descriptor, request, registry/oracle pair and two independent
  meta-only audits. Ordered receipt/validator/authority triples distinguish
  fresh native governed replay from detached external binding even when v1
  receipts and validator roots coincide. Fixed source/identifier/text/node/
  depth/JSON ceilings, exact-type callback-free immutable capture, bounded
  errors and context-local lower-log redaction fail closed before replay,
  equality or output. Results retain the captured authority snapshot, so
  concurrent mutation of caller DTOs cannot enter the judgment.
- **Why:** Complete issue #51's producer wave without widening v1 or allowing
  registry/schema conformity, caller-supplied audit material, or validator-root
  naming to become conclusion authority.
- **Evidence:** Focused, broader compatibility, portable/package, hygiene and
  independent review evidence is bound to the exact producer pull request;
  hosted clean-package evidence supplements the local toolchain boundary.
- **Module version:** 2.0.0 → 2.1.0

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
