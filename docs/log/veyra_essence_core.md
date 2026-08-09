# Veyra Essence/Core Contract

**Date:** 2026-06-03
**Status:** executable core contract v1.0.
**Implementation:** `src/core/kernel/essence.py`, `veyra_sage/essence.py`; R9 `intrinsic_mode_*`; R10 `proof_surface_*` and `proof_elaboration_*`; R11 `observer_core_*`; R13 `intrinsic_observer_echo_*`.
**Certificates:** `essence_core`, `proof_carrying_core_r7`, `theorem_promotion_contract_r8`, `intrinsic_mode_transport_r9`, `proof_elaboration_r10`, `observer_core_r11`, `intrinsic_observer_echo_r13`.

## What this closes

This layer turns the project essence from prose into a finite, testable contract.  It does not claim that Veyra has replaced all mathematics.  It says the current foundation has a stable executable spine:

- nine Essence axioms;
- thirty-six execution-ready core layers;
- six completion checks;
- a certificate verifying that the report is assembled.

Assembly readiness is not proof completeness. R13 classifies the registry as `2 theorem-derived / 4 witness-only / 25 shadow / 5 meta`; R8 contracts both promotions, R9 supplies the exact fixed-anchor unary carrier, R10 renews its closed-source bridge, R11 adds observer/echo proofs, and R13 promotes only their readiness-conditioned exact-image composition.

## Classification boundary

The nine rows below are historically named “Essence axioms,” but they form a
mixed executable policy contract: anti-default ideology, semantic/epistemic
rules, and QA governance all appear in the list. They are not nine pure
ontological postulates. `../concepts/positive_ontology_p0.md` is the canonical
provisional ontology; `reference/axioms.md` remains the operational F1 kernel.
P0 changes no current axiom, layer, certificate, Sage, notebook, or taxonomy
count merely by clarifying these levels.
The reviewed P1 contract and provisional P1 slices add no Essence row. P1-A2
establishes only exact finite-scope relation laws/classification; structural
morphisms, generability, one-fork plus declared finite-catalog confluence, pointwise productivity, and finite
OEP-relative genesis establish neither universal order, scoped formation, nor PΩ.
P1-D2 adds only two insufficiency judgments and three countermodels against exact
finite-to-universal implications; it adds no Essence row or nonexistence theorem.

## Essence axioms

1. No primitive equality: sameness is observer-indexed echo.
2. No primitive point: point is an event residue under observation.
3. No primitive segment: segment is a tremor corridor.
4. No primitive number: number is a mode, balance, or ratio shadow.
5. Observer dependence: truth status is declared relative to observer/domain.
6. Obstruction-first proof: `blocked` and `unknown` are first-class outcomes.
7. Shadow discipline: school math enters only as explicit semantic shadow.
8. Executable pressure: claims need tests, certificates, or counterexample lanes.
9. Coverage discipline: readiness needs fuzzing, coverage, and diagnostics.

## Ready core layers

| Layer | Role | Anchor |
|---|---|---|
| echo | observer-indexed sameness replacement | `echo` |
| resonance | cyclic/phase relation beyond ordered equality | `cyclic_resonance` |
| intrinsic-resonance | proof-carrying inductive weave witness | `proof_carrying_core_r7` |
| intrinsic-observer-echo | proof-carrying readiness-conditioned intrinsic observer echo | `intrinsic_observer_echo_r13` |
| native-number | cycle-echo primitive counts and rank comparisons | `native_resonance_number` |
| aura-weight | derived tact defect costs | `aura_weighted` |
| balance | signed arithmetic via arising/fading stitch | `balance` |
| ratio-order | fractions, order, intervals | `ratio+order` |
| equation | linear residual obstruction solving | `equation` |
| polynomial | ratio-polynomial transformer schema | `polynomial` |
| calculus-depth | local linearization, derivative rules, integral coherence | `calculus_depth` |
| trigonometry-identities | rational unit phase and sum/double/inverse cards | `trigonometry_identities` |
| phase-equations | rational phase equation rows and inverse obstruction cards | `phase_equation_normal_forms` |
| linear-algebra | vector/matrix action, determinant and eigen shadows | `linear_algebra_seed` |
| statistics-inference | distribution families, intervals, hypotheses, uncertainty seeds | `statistics_inference` |
| statistics-concentration | finite concentration, likelihood, and decision-error rows | `statistics_concentration_likelihood` |
| transcendental-limit | finite exp/log series and alternating tail envelopes | `transcendental_limit` |
| convergence-algebra | Cauchy tails, majorants, nested intervals, radius guards | `convergence_algebra` |
| real-analysis-structure | finite modulus, refinement stability, jump obstruction | `real_analysis_structure` |
| weighted-echo-measure | finite weighted coverage, additivity, and tact pushforwards | `weighted_echo_measure` |
| science-domain-certificates | finite conservation, flow, diffusion, and obstruction rows | `science_domain_certificates` |
| model-diagnostics | finite residuals, fit reports, comparisons, and anomaly obstructions | `model_diagnostics` |
| scale-memory-log | transition-depth recovery, residual logs, cyclic unwraps, and obstructions | `scale_memory_log` |
| compression-algebra | edit drift, compression trees, factors, cost strategies | `compression_algebra` |
| language | grammar/type/echo/normal/interpreter | `core_language` |
| proof-pressure | proof traces, fuzz, coverage | `core_language_proofs+coverage` |
| diagnostics | parser source-span diagnostics | `core_language_spans+span_diagnostics` |
| proof-discipline | rule/span/domain/model/export coverage | `proof_discipline` |
| category-like | finite object/morphism/invariant/universal-shadow rows | `category_like_translation_x3` |
| topology-echo | finite deformation-invariant echo rows | `topology_echo_x4` |
| likelihood-geometry | finite likelihood geometry and residual-family certificates | `likelihood_geometry_x5` |
| foundational-kernel | unified axioms, theorem objects, and formal proof bridge | `foundational_repair_f1_f3` |
| native-runtime | behavior-first rez/nod/tact/breath/mode objects | `native_runtime_f4` |
| classical-benchmark | paired classical proof versus Veyra artifact ledger | `classical_benchmark_f5` |
| native-number-theorem | Euclid-style product-plus-one finite native Mode-length derivation | `native_number_theorem_n1` |
| deduction-chain | executable derived/observer/shadow/blocked proof-row ledger | `deduction_chain_f6` |

## API

```python
from src.core.kernel.essence import essence_report

report = essence_report()
assert report.summary() == {
    "axioms": 9,
    "layers": 36,
    "executable_layers": 36,
    "missing": 0,
    "checklist": 6,
    "core_ready": True,
    "execution_ready": True,
    "proof_complete": False,
    "theorem_derived": 2,
    "witness_only": 4,
    "shadow": 25,
    "meta": 5,
}
```

Sage-facing access:

```python
from veyra_sage.all import VeyraEssenceLab
lab = VeyraEssenceLab()
lab.summary()
lab.axiom_rows()
lab.layer_rows()
```

## Interpretation

The core is now an executable language of analysis:

- if we introduce a new primitive, it must fit the axiom/layer report;
- if we import a school concept, it must appear as a shadow, not as native truth;
- if a claim is beautiful but untested, it stays conjecture/heuristic/aesthetic signal;
- if a claim fails, the failure becomes data through obstruction and refutation rows.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/kernel/test_essence_core.py tests/sage/test_veyra_sage_essence.py tests/shadows/test_certify.py tests/sage/test_veyra_sage.py
python3 scripts/certify_veyra.py
python3 scripts/sage_smoke.py
```

R7 requires replay/soundness; R8 contracts promotion; R9 requires exact image transport. R10 additionally requires captured-source/de Bruijn replay, R7/R9 artifact binding, used-support, `THM-R10-001..005`, 37 reviewed sources, ten stages, nine reviewed fresh oleans, and source/object/runtime continuity over all 2,365 traced Lean userspace inputs. R11 adds the closed observer/echo artifact; R13 composes it with R12 through a separate 25-source, 11-stage, 10-object bridge; see docs 123–127 and 139.

Expected contract signals:

- Essence summary: `axioms=9`, `layers=36`, `execution_ready=True`, `proof_complete=False`.
- Certificates: R13 brought the suite to 72 and taxonomy to `2/4/25/5`; immutable I1-77 passed its own full gate. Later bounded P0/P1 certificates now reach registry `86` outside that snapshot, but add no Essence layer, Sage export, theorem taxonomy, or R8 promotion.
- Sage smoke: `sage_essence_passed=True`.

## Next

R13 promotes one conservative readiness-conditioned intrinsic observer-echo layer while retaining exact obstruction paths and nonreflection. R14 now supplies a separate bounded finite synthesis audit over the exact 1,565-term R11 grammar; it does not prove general synthesis or support minimality. Python parsing remains TCB, and cyclic/phase resonance plus broad `echo` remain outside the theorem.
