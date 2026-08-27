"""Executable Veyra workability certificates."""
from __future__ import annotations
from fractions import Fraction
import logging
from .balance import balance_from_int, stitch_balance
from .certify_benchmark_evidence import certify_benchmark_evidence_r15
from .certify_calculus import certify_calculus_depth
from .certify_classical_benchmarks import certify_classical_benchmark_f5
from .certify_comparative_ledgers import certify_comparative_bridge_separation_ledgers
from .certify_category import certify_category_like_translation
from .certify_convergence import certify_convergence_algebra
from .certify_deduction_chain import certify_deduction_chain_f6
from .certify_foundational import certify_foundational_repair_f1_f3
from .certify_proof_core import certify_proof_carrying_core_r7
from .certify_theorem_contracts import certify_theorem_promotion_contract_r8
from .certify_intrinsic_mode import certify_intrinsic_mode_transport_r9
from .certify_intrinsic_observer_echo import certify_intrinsic_observer_echo_r13
from .certify_observer_synthesis_v2 import certify_observer_synthesis_v2_r14
from .certify_observer_descent import certify_observer_descent_r16
from .certify_observer_realization import certify_observer_realization_p1_r16
from .certify_intrinsic_vam import certify_intrinsic_vam_r12
from .certify_proof_elaboration import certify_proof_elaboration_r10
from .certify_observer_core import certify_observer_core_r11
from .certify_formal_completion import certify_formal_export_completion_x8
from .certify_formal_export import certify_formal_export_prep_x7
from .certify_geometry_visuals import certify_geometry_visual_regression_x6
from .certify_likelihood import certify_likelihood_geometry_x5
from .certify_surprise_separation import certify_surprise_separation_s1
from .certify_surprise_search import certify_surprise_search_s3
from .certify_surprise_kwise import certify_surprise_kwise_s5
from .certify_surprise_corpus import certify_surprise_corpus_s7
from .certify_surprise_debruijn import certify_surprise_debruijn_s6
from .certify_observer_gap_topology import certify_observer_gap_topology_s7
from .certify_observer_patch_atlas import certify_observer_patch_atlas_g4
from .certify_infinity_i1 import certify_observer_infinity_i1
from .certify_positive_ontology import certify_positive_ontology_p0
from .certify_observer_morphism import certify_observer_morphism_p1a
from .certify_finite_construction import certify_finite_construction_p1b
from .certify_confluence import certify_confluence_p1c1
from .certify_confluence_aggregate import certify_confluence_aggregate_p1c2
from .certify_productivity import certify_productivity_p1d1
from .certify_observer_genesis import certify_observer_genesis_p1e1
from .certify_observer_relations import certify_observer_relations_p1a2
from .certify_productivity_counterpressure import certify_productivity_counterpressure
from .certify_release_bundle import certify_d3_pomega_p2s_bundle
from .certify_translated_confluence import certify_translated_confluence_p1c3
from .certify_phase_equations import certify_phase_equation_normal_forms
from .certify_quantum_baselines import certify_quantum_baseline_q3
from .certify_quantum_gates import certify_quantum_gate_identity_q6
from .certify_quantum_obstructions import certify_quantum_error_obstruction_q7
from .certify_quantum_qft import certify_quantum_qft_period_q8
from .certify_quantum_compression import certify_quantum_circuit_compression_q9
from .certify_quantum_qec import certify_quantum_qec_echo_q5
from .certify_quantum_stabilizer import certify_quantum_stabilizer_q2
from .certify_quantum_topology import certify_quantum_topology_q4
from .certify_quantum_veyra import certify_quantum_veyra_q1
from .certify_quantum_surprise import certify_quantum_surprise_q10
from .certify_quantum_tensor import certify_quantum_tensor_q11
from .certify_real_analysis import certify_real_analysis_structure
from .certify_scale_memory import certify_scale_memory_log
from .certify_science import certify_model_diagnostics, certify_science_domain_certificates
from .certify_topology import certify_topology_echo_x4
from .certify_veyra_magic import certify_veyra_magic_m1
from .certify_vam import certify_vam_reference_v1
from .certify_weighted_measure import certify_weighted_echo_measure
from .certify_linear_algebra import certify_linear_algebra_seed
from .certify_native_number import certify_native_number_theory, certify_native_resonance_number
from .certify_native_number_theorems import certify_native_fermat_phase_n2, certify_native_number_theorem_n1
from .certify_necklace_congruence import certify_necklace_congruence_n8
from .certify_doctrinal_induction import certify_doctrinal_induction_di1
from .certify_orbit_partition import certify_orbit_partition_di2
from .certify_observer_lattice import certify_observer_lattice_tr1
from .certify_break_locus import certify_break_locus_tr2
from .certify_projection_forcing import certify_projection_forcing_tr2b
from .certify_break_locus_formula import certify_break_locus_formula_tr2c
from .certify_locus_tightness import certify_locus_tightness_tr2d
from .certify_native_runtime import certify_native_runtime_f4
from .certify_statistics import certify_statistics_inference
from .certify_statistics_concentration import certify_statistics_concentration_likelihood
from .certify_trigonometry import certify_trigonometry_identities
from .certify_transcendental import certify_transcendental_limit
from .certify_types import Certificate
from .certify_readiness import certify_essence_core, certify_proof_discipline
from .compression_algebra import compare_cost_strategies, compression_algebra_checklist, edit_resonance_profile, hierarchical_compression_tree, polynomial_factor_search
from .equation import LinearEquation, LinearForm, solve_linear
from .language import core_language_checklist, interpret_veyra
from .language_coverage import coverage_language_checklist, language_coverage_report, missed_language_coverage_rules
from .language_span import parse_veyra_spanned, span_language_checklist
from .language_span_coverage import missed_span_diagnostic_rules, span_diagnostic_coverage_checklist, span_diagnostic_coverage_report
from .language_proof import proof_language_checklist, proof_summary, trace_veyra_proof
from .language_fuzz import generated_language_mutation_report, generated_mutation_language_checklist, language_mutation_report, mutation_language_checklist, property_fuzz_language_checklist, property_language_fuzz_report
from .modes import Mode, echo_equivalent
from .order import RatioInterval, compare_ratios, interval_contains
from .polynomial import eval_polynomial, multiply_polynomials, polynomial_from_ints
from .ratio import add_ratios_raw, ratio_from_ints, ratio_shadow
from .resonance import resonance_profile
from .tact_similarity import aura_cost_map
from .weighted_resonance import weighted_resonance_profile
logger = logging.getLogger(__name__)
def certificate_suite() -> list[Certificate]:
    """Run core Veyra workability certificates."""
    logger.debug("certificate_suite entry")
    certs = [certify_echo(), certify_resonance(), certify_native_resonance_number(), certify_native_number_theory(),
        certify_native_number_theorem_n1(), certify_native_fermat_phase_n2(), certify_necklace_congruence_n8(), certify_doctrinal_induction_di1(), certify_orbit_partition_di2(), certify_observer_lattice_tr1(), certify_break_locus_tr2(), certify_projection_forcing_tr2b(), certify_break_locus_formula_tr2c(), certify_locus_tightness_tr2d(), certify_topology_echo_x4(), certify_observer_patch_atlas_g4(), certify_observer_infinity_i1(), certify_positive_ontology_p0(), certify_observer_morphism_p1a(), certify_observer_relations_p1a2(), certify_finite_construction_p1b(), certify_confluence_p1c1(), certify_confluence_aggregate_p1c2(), certify_translated_confluence_p1c3(), certify_productivity_p1d1(), certify_productivity_counterpressure(), *certify_d3_pomega_p2s_bundle(), certify_observer_genesis_p1e1(),
        certify_geometry_visual_regression_x6(), certify_formal_export_prep_x7(), certify_formal_export_completion_x8(),
        certify_quantum_veyra_q1(), certify_quantum_stabilizer_q2(), certify_quantum_topology_q4(),
        certify_quantum_qec_echo_q5(), certify_quantum_gate_identity_q6(),
        certify_quantum_error_obstruction_q7(), certify_quantum_qft_period_q8(), certify_quantum_circuit_compression_q9(), certify_quantum_surprise_q10(), certify_quantum_tensor_q11(),
        certify_quantum_baseline_q3(),
        certify_aura_weighted(),
        certify_balance(),
        certify_ratio(),
        certify_order(),
        certify_equation(),
        certify_polynomial(),
        certify_category_like_translation(),
        certify_calculus_depth(),
        certify_trigonometry_identities(),
        certify_phase_equation_normal_forms(),
        certify_linear_algebra_seed(),
        certify_statistics_inference(),
        certify_statistics_concentration_likelihood(),
        certify_likelihood_geometry_x5(), certify_surprise_separation_s1(), certify_surprise_search_s3(), certify_surprise_kwise_s5(), certify_surprise_debruijn_s6(), certify_surprise_corpus_s7(), certify_observer_gap_topology_s7(), certify_veyra_magic_m1(), certify_vam_reference_v1(),
        certify_foundational_repair_f1_f3(), certify_proof_carrying_core_r7(), certify_theorem_promotion_contract_r8(), certify_intrinsic_mode_transport_r9(), certify_proof_elaboration_r10(), certify_observer_core_r11(), certify_intrinsic_vam_r12(), certify_intrinsic_observer_echo_r13(), certify_observer_synthesis_v2_r14(), certify_observer_descent_r16(), certify_observer_realization_p1_r16(),
        certify_native_runtime_f4(), certify_classical_benchmark_f5(), certify_comparative_bridge_separation_ledgers(), certify_benchmark_evidence_r15(),
        certify_deduction_chain_f6(),
        certify_transcendental_limit(),
        certify_convergence_algebra(),
        certify_real_analysis_structure(),
        certify_weighted_echo_measure(),
        certify_science_domain_certificates(),
        certify_model_diagnostics(),
        certify_scale_memory_log(),
        certify_compression_algebra(),
        certify_language(),
        certify_language_spans(),
        certify_language_span_diagnostics(),
        certify_language_proofs(),
        certify_language_mutations(),
        certify_language_generated_mutations(),
        certify_language_property_fuzz(),
        certify_language_coverage(),
        certify_proof_discipline(),
        certify_essence_core(),
    ]
    logger.debug("certificate_suite exit count=%d passed=%d", len(certs), sum(c.passed for c in certs))
    return certs
def certify_echo() -> Certificate:
    """Certify observer-indexed equality replacement."""
    logger.debug("certify_echo entry")
    passed = echo_equivalent(Mode.from_word("ab"), Mode.from_word("ba"), [])
    detail = "empty observer family makes ab and ba echo-equivalent"
    result = Certificate("echo", "≈_T observer-indexed echo", passed, detail, 1)
    logger.debug("certify_echo exit result=%r", result)
    return result
def certify_resonance() -> Certificate:
    """Certify cyclic resonance beyond ordered equality."""
    logger.debug("certify_resonance entry")
    profile = resonance_profile(Mode.from_word("ab"), Mode.from_word("baba"))
    passed = profile.cyclic and not profile.ordered and 1 in profile.phase_offsets
    result = Certificate("cyclic_resonance", "phase resonance ▹_cyc", passed, str(profile.phase_offsets), 1)
    logger.debug("certify_resonance exit result=%r", result)
    return result
def certify_aura_weighted() -> Certificate:
    """Certify derived tact costs drive weighted resonance."""
    logger.debug("certify_aura_weighted entry")
    costs = aura_cost_map([Mode.from_word("abac")], ("a", "b", "c"))
    profile = weighted_resonance_profile(Mode.from_word("ab"), Mode.from_word("abac"), 0.5, costs)
    passed = profile.resonates and costs[("b", "c")] == 0.25
    result = Certificate("aura_weighted", "κ_A aura-derived weighted resonance", passed, f"b>c={costs[('b','c')]}", 1)
    logger.debug("certify_aura_weighted exit result=%r", result)
    return result
def certify_balance() -> Certificate:
    """Certify signed arithmetic via balance opposition."""
    logger.debug("certify_balance entry")
    total = stitch_balance(balance_from_int(3), balance_from_int(-2))
    passed = total.net_length == 1
    result = Certificate("balance", "arising/fading balance stitch", passed, f"net={total.net_length}", 0)
    logger.debug("certify_balance exit result=%r", result)
    return result
def certify_ratio() -> Certificate:
    """Certify fractions via balance-over-scale ratios."""
    logger.debug("certify_ratio entry")
    total = add_ratios_raw(ratio_from_ints(1, 2), ratio_from_ints(1, 3))
    passed = ratio_shadow(total) == Fraction(5, 6) and total.scale.length == 6 and total.numerator.net_length == 5
    result = Certificate("ratio", "native cross-scale balance/scale ratio", passed, f"raw={total.numerator.net_length}/{total.scale.length}", 1)
    logger.debug("certify_ratio exit result=%r", result)
    return result
def certify_order() -> Certificate:
    """Certify dominance and intervals."""
    logger.debug("certify_order entry")
    left = ratio_from_ints(1, 2)
    right = ratio_from_ints(1, 3)
    interval = RatioInterval(right, left)
    passed = compare_ratios(left, right).sign > 0 and interval_contains(interval, right)
    result = Certificate("order", "observer-relative dominance", passed, "1/2 > 1/3 and 1/3 in interval", 0)
    logger.debug("certify_order exit result=%r", result)
    return result
def certify_equation() -> Certificate:
    """Certify linear equation constraint solving."""
    logger.debug("certify_equation entry")
    eq = LinearEquation(LinearForm(ratio_from_ints(2), ratio_from_ints(3)), LinearForm(ratio_from_ints(0), ratio_from_ints(7)))
    sol = solve_linear(eq)
    passed = sol.value is not None and ratio_shadow(sol.value) == 2
    result = Certificate("equation", "linear residual obstruction solver", passed, f"status={sol.status}", 0)
    logger.debug("certify_equation exit result=%r", result)
    return result
def certify_polynomial() -> Certificate:
    """Certify polynomial schema operations."""
    logger.debug("certify_polynomial entry")
    poly = multiply_polynomials(polynomial_from_ints([1, 1]), polynomial_from_ints([-1, 1]))
    value = eval_polynomial(poly, ratio_from_ints(3))
    passed = ratio_shadow(value) == 8
    result = Certificate("polynomial", "ratio polynomial transformer schema", passed, "((x+1)(x-1))(3)=8", 0)
    logger.debug("certify_polynomial exit result=%r", result)
    return result
def certify_compression_algebra() -> Certificate:
    """Certify Sprint B edit/compression/factor/cost layer."""
    logger.debug("certify_compression_algebra entry")
    edit = edit_resonance_profile(Mode.from_word("ab"), Mode.from_word("abxab"), 1)
    tree = hierarchical_compression_tree(Mode.from_word("ababab"), 2, 0)
    factors = polynomial_factor_search(polynomial_from_ints([-1, 0, 1]), [-1, 0, 1])
    costs = compare_cost_strategies(Mode.from_word("ab"), Mode.from_word("abac"), 0.5, [Mode.from_word("abac")], ("a", "b", "c"), {("b", "c"): 0.25})
    passed = edit.resonates and edit.distance == 1 and tree.status == "split" and len(factors) == 2 and [row.profile.resonates for row in costs] == [False, True, True] and len(compression_algebra_checklist()) == 4
    result = Certificate("compression_algebra", "edit drift, compression tree, factor hits, cost-strategy comparison", passed, f"edit={edit.distance} factors={len(factors)}", 1)
    logger.debug("certify_compression_algebra exit result=%r", result)
    return result
def certify_language() -> Certificate:
    """Certify Core Language v0.1 interpreter stack."""
    logger.debug("certify_language entry")
    source = "echo(mode(breath(tact(nod:a,nod:b),tact(nod:b,nod:a))),mode(breath(tact(nod:b,nod:a),tact(nod:a,nod:b))),observer:length)"
    result = interpret_veyra(source, "logic")
    passed = result.check.status == "ready" and len(core_language_checklist()) == 9
    cert = Certificate("core_language", "grammar/type/echo/normal/interpreter stack", passed, result.normal, 1)
    logger.debug("certify_language exit result=%r", cert)
    return cert
def certify_language_spans() -> Certificate:
    """Certify Core Language v0.2 span diagnostics."""
    logger.debug("certify_language_spans entry")
    good = parse_veyra_spanned("echo(nod:a,nod:b,observer:length)")
    bad = parse_veyra_spanned("echo(nod:a,nod:b,observer:length")
    passed = good.ok and not bad.ok and len(span_language_checklist()) == 6
    detail = f"tokens={len(good.tokens)} bad_col={bad.diagnostic.span.column if bad.diagnostic else 'none'}"
    result = Certificate("core_language_spans", "token/source-span/diagnostic parser", passed, detail, 1)
    logger.debug("certify_language_spans exit result=%r", result)
    return result
def certify_language_span_diagnostics() -> Certificate:
    """Certify Core Language v0.8 source-span diagnostic coverage."""
    logger.debug("certify_language_span_diagnostics entry")
    report = span_diagnostic_coverage_report()
    missed = missed_span_diagnostic_rules()
    passed = report.cases == 7 and report.diagnostics == 7 and report.excerpts == 7 and report.multiline == 1 and report.unexpected == 0 and report.missed == 0 and not missed and len(span_diagnostic_coverage_checklist()) == 6
    detail = f"cases={report.cases} diagnostics={report.diagnostics} excerpts={report.excerpts} missed={report.missed} multiline={report.multiline}"
    result = Certificate("core_language_span_diagnostics", "source-span diagnostic coverage and missed-rule report", passed, detail, 1)
    logger.debug("certify_language_span_diagnostics exit result=%r", result)
    return result
def certify_language_proofs() -> Certificate:
    """Certify Core Language v0.3 proof objects."""
    logger.debug("certify_language_proofs entry")
    trace = trace_veyra_proof("echo(nod:a,nod:b,observer:kind)")
    summary = proof_summary(trace)
    passed = trace.parse_ok and trace.final_check.status == "ready" and summary.steps >= 4 and len(proof_language_checklist()) == 7
    detail = f"steps={summary.steps} ready={summary.ready} blocked={summary.blocked}"
    result = Certificate("core_language_proofs", "rule/source-span/status proof objects", passed, detail, 1)
    logger.debug("certify_language_proofs exit result=%r", result)
    return result
def certify_language_mutations() -> Certificate:
    """Certify Core Language v0.4 mutation pressure."""
    logger.debug("certify_language_mutations entry")
    report = language_mutation_report()
    passed = report.cases == 10 and report.blocked == 9 and report.unknown == 1 and report.unexpected == 0 and len(mutation_language_checklist()) == 6
    detail = f"cases={report.cases} blocked={report.blocked} unknown={report.unknown} unexpected={report.unexpected}"
    result = Certificate("core_language_mutations", "generated grammar/type/inference mutation pressure", passed, detail, 1)
    logger.debug("certify_language_mutations exit result=%r", result)
    return result
def certify_language_generated_mutations() -> Certificate:
    """Certify Core Language v0.5 generated mutation families."""
    logger.debug("certify_language_generated_mutations entry")
    report = generated_language_mutation_report()
    passed = report.families == 4 and report.cases == 20 and report.blocked == 18 and report.unknown == 2 and report.ready == 0 and report.unexpected == 0 and len(generated_mutation_language_checklist()) == 6
    detail = f"families={report.families} cases={report.cases} blocked={report.blocked} unknown={report.unknown} unexpected={report.unexpected}"
    result = Certificate("core_language_generated_mutations", "generated arity/constructor/observer/label mutation families", passed, detail, 1)
    logger.debug("certify_language_generated_mutations exit result=%r", result)
    return result
def certify_language_property_fuzz() -> Certificate:
    """Certify Core Language v0.6 deterministic property fuzzing."""
    logger.debug("certify_language_property_fuzz entry")
    report = property_language_fuzz_report()
    passed = report.seed == 613 and report.families == 4 and report.cases == 24 and report.blocked == 21 and report.unknown == 3 and report.ready == 0 and report.unexpected == 0 and report.shrunk == 24 and len(property_fuzz_language_checklist()) == 6
    detail = f"seed={report.seed} cases={report.cases} blocked={report.blocked} unknown={report.unknown} shrunk={report.shrunk} unexpected={report.unexpected}"
    result = Certificate("core_language_property_fuzz", "seeded property mutation fuzzing with shrinker", passed, detail, 1)
    logger.debug("certify_language_property_fuzz exit result=%r", result)
    return result
def certify_language_coverage() -> Certificate:
    """Certify Core Language v0.7 coverage matrix."""
    logger.debug("certify_language_coverage entry")
    report = language_coverage_report()
    missed = missed_language_coverage_rules()
    passed = report.families == 11 and report.cases == 54 and report.blocked == 48 and report.unknown == 6 and report.ready == 0 and report.unexpected == 0 and report.missed == 0 and report.shrink_witnesses == 24 and not missed and len(coverage_language_checklist()) == 6
    detail = f"families={report.families} cases={report.cases} missed={report.missed} unexpected={report.unexpected} shrink={report.shrink_witnesses}"
    result = Certificate("core_language_coverage", "mutation coverage matrix and missed-rule report", passed, detail, 1)
    logger.debug("certify_language_coverage exit result=%r", result)
    return result
def certificate_summary(certs: list[Certificate]) -> dict[str, object]:
    """Return compact certificate summary."""
    logger.debug("certificate_summary entry count=%d", len(certs))
    result = {"total": len(certs), "passed": sum(item.passed for item in certs), "failed": [item.name for item in certs if not item.passed], "min_level": min((item.level for item in certs), default=0)}
    logger.debug("certificate_summary exit result=%r", result)
    return result
