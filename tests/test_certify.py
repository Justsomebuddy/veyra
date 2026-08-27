import pytest

from src import core
import src.core.all_depth_family as d3_api
import src.core.confluence_aggregate as c2_api
import src.core.translated_confluence as c3_api
import src.core.stream_completion as pomega1_api
import src.core.padic_completion as pomega2_api
import src.core.padic_completion_public as pomega2_public
import src.core.status_promotion as p2s_api
import src.core.status_promotion_public as p2s_public
import src.core.scoped_formation as c4_api
import src.core.scoped_formation_public as c4_public
import src.core.observer_actualization as e4_api
import src.core.observer_actualization_public as e4_public
from src.core.certify import certificate_suite, certificate_summary


@pytest.fixture(scope="module")
def certs():
    return certificate_suite()


def test_certificate_suite_all_passes_current_core(certs):
    summary = certificate_summary(certs)
    assert summary["total"] == 110
    assert summary["failed"] == []
    assert summary["passed"] == summary["total"]


def test_p1c2_root_exports_are_collision_safe():
    assert set(c2_api.__all__).issubset(core.__all__)
    assert all(getattr(core, name) is getattr(c2_api, name) for name in c2_api.__all__)


def test_p1d3_root_exports_are_collision_safe():
    unique = (
        "AllDepthFamilySpec", "AssumptionLedger", "FamilyHypothesis",
        "FormalFamilySource", "OracleFamilyHypothesis", "FamilyEvidenceStatus",
        "FamilyProvenance", "FamilyLaw", "FamilyNonexistence",
        "FamilyLawCounterexampleAssessment", "derive_periodic_family",
        "replay_all_depth_family", "assess_family_law_counterexample",
    )
    assert all(name in core.__all__ for name in unique)
    assert all(getattr(core, name) is getattr(d3_api, name) for name in unique)
    assert core.FamilyCompletedCarrierStatus is d3_api.CompletedCarrierStatus
    assert core.FamilyLawStatus is d3_api.LawStatus
    assert core.CompletedCarrierStatus is not core.FamilyCompletedCarrierStatus
    assert core.LawStatus is not core.FamilyLawStatus


def test_p1c3_root_exports_are_collision_safe():
    assert set(c3_api.__all__).issubset(core.__all__)
    assert all(getattr(core, name) is getattr(c3_api, name) for name in c3_api.__all__)


def test_pomega1_root_exports_are_collision_safe():
    exact = (
        "StreamCompletionValidationError", "bounded_stream_shadow",
        "formal_alphabet_presentation", "stream_alphabet_source",
        "stream_completion_judgment", "stream_completion_policy",
        "stream_completion_theorem_source", "validate_stream_completion_result",
    )
    aliases = {
        "POMEGA1_ARTIFACT_PATH": "ARTIFACT_PATH",
        "POMEGA1_ARTIFACT_SHA256": "ARTIFACT_SHA256",
        "POMEGA1_AXIOM_CLOSURE": "AXIOM_CLOSURE",
        "POMEGA1_BRIDGE_THEOREM_IDS": "BRIDGE_THEOREM_IDS",
        "POMEGA1_SCP_THEOREM_IDS": "SCP_THEOREM_IDS",
        "POMEGA1_TCB_DIGEST": "TCB_DIGEST",
        "POMEGA1_THEOREM_IDS": "THEOREM_IDS",
        "POMEGA1_TOOLCHAIN_ID": "TOOLCHAIN_ID",
        "POMEGA1_NONCLAIMS": "POMEGA1_NONCLAIMS",
        "pomega1_stream_completion_doctrine": "stream_completion_doctrine",
        "pomega1_stream_completion_ledger": "stream_completion_ledger",
        "pomega1_stream_completion_package": "stream_completion_package",
        "StreamCompletedCarrierStatus": "CompletedCarrierStatus",
        "BoundedStreamShadow": "BoundedStreamShadow",
        "StreamCompletionFailedBound": "CompletionFailedBound",
        "StreamCompletionObligationStatuses": "CompletionObligationStatuses",
        "StreamCompletionResultStatus": "CompletionResultStatus",
        "FormalAlphabetPresentation": "FormalAlphabetPresentation",
        "StreamFormalExecutionFailure": "FormalExecutionFailure",
        "StreamFormalExecutionFailureKind": "FormalExecutionFailureKind",
        "StreamLedgerRowClass": "LedgerRowClass",
        "StreamMetaphysicalTotalityStatus": "MetaphysicalTotalityStatus",
        "StreamObligationStatus": "ObligationStatus",
        "StreamPhysicalInstantiationStatus": "PhysicalInstantiationStatus",
        "StreamAlphabetSource": "StreamAlphabetSource",
        "StreamCompletionDoctrine": "StreamCompletionDoctrine",
        "StreamCompletionJudgment": "StreamCompletionJudgment",
        "StreamCompletionLedger": "StreamCompletionLedger",
        "StreamCompletionLedgerRow": "StreamCompletionLedgerRow",
        "StreamCompletionPackage": "StreamCompletionPackage",
        "StreamCompletionPolicy": "StreamCompletionPolicy",
        "StreamCompletionResourceLimit": "StreamCompletionResourceLimit",
        "StreamCompletionResult": "StreamCompletionResult",
        "StreamCompletionTheoremSource": "StreamCompletionTheoremSource",
    }
    assert all(name in core.__all__ for name in exact + tuple(aliases))
    assert all(getattr(core, name) is getattr(pomega1_api, name) for name in exact)
    assert all(getattr(core, alias) is getattr(pomega1_api, name) for alias, name in aliases.items())
    assert core.CompletedCarrierStatus is not core.StreamCompletedCarrierStatus
    assert core.CompletedCarrierStatus.__module__ == "src.core.productivity_types"


def test_pomega2_root_exports_are_collision_safe():
    assert len(pomega2_public.__all__) == len(set(pomega2_public.__all__))
    assert set(pomega2_public.__all__).issubset(core.__all__)
    assert all(getattr(core, name) is getattr(pomega2_public, name) for name in pomega2_public.__all__)
    assert core.POMEGA2_ARTIFACT_SHA256 == pomega2_api.ARTIFACT_SHA256
    assert core.POMEGA2_CANONICAL_OPS_ID == pomega2_api.CANONICAL_OPS_ID
    assert core.Pomega2CompletedCarrierStatus is pomega2_api.PadicCompletedCarrierStatus
    assert core.Pomega2CompletedCarrierStatus is not core.StreamCompletedCarrierStatus


def test_p2s_root_exports_are_collision_safe():
    assert len(p2s_public.__all__) == len(set(p2s_public.__all__))
    assert len(core.__all__) == len(set(core.__all__))
    assert set(p2s_public.__all__).issubset(core.__all__)
    assert all(getattr(core, name) is getattr(p2s_public, name) for name in p2s_public.__all__)
    assert core.P2SJudgmentKind is p2s_api.JudgmentKind
    assert core.P2SEvidenceStatus is p2s_api.EvidenceStatus
    assert core.P2SResourceBound is p2s_api.ResourceBound
    assert core.P2SPremiseArtifact is p2s_api.PremiseArtifact
    assert core.ResourceBound is not core.P2SResourceBound
    assert core.PremiseArtifact is not core.P2SPremiseArtifact
    registry = core.p2s_promotion_registry()
    assert len(registry.domains) == 15
    assert len(registry.rules) == 17
    assert len(registry.premise_projections) == 40
    assert len(registry.index_projections) == 1
    assert core.P2S_LITERAL_ORACLE_DIGEST == (
        "2cbe0f2f1f1025696b947c73e32196f230e7748c77c030543d2292a34585875a"
    )


def test_p1c4_root_exports_are_collision_safe():
    assert len(c4_public.__all__) == len(set(c4_public.__all__))
    assert len(core.__all__) == len(set(core.__all__))
    assert set(c4_public.__all__).issubset(core.__all__)
    assert all(getattr(core, name) is getattr(c4_public, name) for name in c4_public.__all__)
    assert core.C4ScopedFormationStatus is c4_api.ScopedFormationStatus
    assert core.C4FormationPolicy is c4_api.FormationPolicy
    assert core.C4ScopedFormationResult is c4_api.ScopedFormationResult
    assert core.C4FiniteScopedObjectPresentation is c4_api.FiniteScopedObjectPresentation
    assert core.C4FormationPolicy is not core.ConfluenceAggregatePolicy


def test_p1e4_root_exports_are_collision_safe():
    assert len(e4_public.__all__) == len(set(e4_public.__all__))
    assert len(core.__all__) == len(set(core.__all__))
    assert set(e4_public.__all__).issubset(core.__all__)
    assert all(getattr(core, name) is getattr(e4_public, name) for name in e4_public.__all__)
    assert core.E4ActualizationStatus is e4_api.ActualizationStatus
    assert core.E4HistoricalObserverSource is e4_api.HistoricalObserverSource
    assert core.E4ActualizationResourceBound is e4_api.ActualizationResourceBound
    assert core.E4PhysicalInstantiation is not core.PhysicalInstantiation


def test_certificate_items_name_veyra_methods(certs):
    methods = {item.name: item.method for item in certs}
    passed = {item.name: item.passed for item in certs}
    assert "≈_T" in methods["echo"]
    assert "▹_cyc" in methods["cyclic_resonance"]
    assert "cycle-echo" in methods["native_resonance_number"]
    assert "factor/lift" in methods["native_number_theory_x2"]
    assert "Euclid-style" in methods["native_number_theorem_n1"]
    assert "Fermat phase" in methods["native_fermat_phase_n2"]
    assert "deformation-invariant" in methods["topology_echo_x4"]
    assert "finite observer-patch exact gluing" in methods["observer_patch_atlas_g4"]
    assert "classical p-adic residue shadows" in methods["observer_infinity_i1"]
    assert "provisional bounded fixed-family pressure" in methods["positive_ontology_p0"]
    assert "no completed admission or translation" in methods["positive_ontology_p0"]
    assert "structural R11 factorization" in methods["observer_morphism_p1a"]
    assert "confirmed nonempty comparison domains" in methods["observer_morphism_p1a"]
    assert "no constructibility" in methods["observer_morphism_p1a"]
    assert passed["observer_morphism_p1a"] is True
    assert "closed SeedRef/PulseStep" in methods["finite_construction_p1b"]
    assert "formal generability only" in methods["finite_construction_p1b"]
    assert "not ontic genesis" in methods["finite_construction_p1b"]
    assert passed["finite_construction_p1b"] is True
    assert "direct-echo one-fork" in methods["confluence_p1c1"]
    assert "no aggregation" in methods["confluence_p1c1"]
    assert passed["confluence_p1c1"] is True
    assert "declared global finite catalogs" in methods["confluence_aggregate_p1c2"]
    assert "no generated-path universe" in methods["confluence_aggregate_p1c2"]
    assert passed["confluence_aggregate_p1c2"] is True
    assert "exact byte-and-kind P0/P1-A bridge" in methods["translated_confluence_p1c3"]
    assert "asymmetric every-occurrence translation" in methods["translated_confluence_p1c3"]
    assert passed["translated_confluence_p1c3"] is True
    assert "completed Stream(Fin N) relative to exact SCP doctrine and ledger" in methods["stream_completion_pomega1"]
    assert passed["stream_completion_pomega1"] is True
    assert "pinned Lean PPCP" in methods["padic_completion_pomega2"] and passed["padic_completion_pomega2"]
    assert "integer to exact prime-power compatible all-depth residue family" in methods["padic_family_introduction_p3n1"]
    assert passed["padic_family_introduction_p3n1"] is True
    assert "one exact P1-bound finite translation network" in methods["observer_network_p3t"] and passed["observer_network_p3t"]
    assert "closed integer residue process commutes" in methods["prime_power_productive_bridge_p3a1b"] and passed["prime_power_productive_bridge_p3a1b"]
    assert "exact finite setoid transports" in methods["transport_coherence_p3c2"] and passed["transport_coherence_p3c2"]
    assert "meta-validation boundaries" in methods["status_promotion_p2s"]
    assert passed["status_promotion_p2s"] is True
    assert "raw P1-B/G4/C2/A2/C3 replay" in methods["scoped_formation_p1c4"]
    assert passed["scoped_formation_p1c4"] is True
    assert "finite history-relative HAP" in methods["observer_actualization_p1e4"]
    assert passed["observer_actualization_p1e4"] is True
    assert "structurally guarded pointwise finite construction" in methods["productivity_p1d1"]
    assert "no extensional all-depth family" in methods["productivity_p1d1"]
    assert passed["productivity_p1d1"] is True
    assert "Mode-only exact 24-row adapter" in methods["observer_genesis_p1e1"]
    assert "no E2/R11 shadow" in methods["observer_genesis_p1e1"]
    assert passed["observer_genesis_p1e1"] is True
    assert "complete ordered Cartesian replay" in methods["observer_relations_p1a2"]
    assert "no universal order" in methods["observer_relations_p1a2"]
    assert passed["observer_relations_p1a2"] is True
    assert "finite evidence insufficiency" in methods["productivity_counterpressure_p1d2"]
    assert passed["productivity_counterpressure_p1d2"] is True
    assert "periodic family" in methods["all_depth_family_p1d3"]
    assert passed["all_depth_family_p1d3"] is True
    assert passed["observer_patch_atlas_g4"] is True
    assert "visual scene" in methods["geometry_visual_regression_x6"]
    assert "export-prep" in methods["formal_export_prep_x7"]
    assert "checked Lean proof artifact" in methods["formal_export_completion_x8"]
    assert "Q-Veyra" in methods["quantum_veyra_q1"]
    assert "stabilizer" in methods["quantum_stabilizer_q2"]
    assert "baselines" in methods["quantum_baseline_q3"]
    assert "topological Veyra-qubit" in methods["quantum_topology_q4"]
    assert "QEC echo" in methods["quantum_qec_echo_q5"]
    assert "gate identity" in methods["quantum_gate_identity_q6"]
    assert "error obstruction" in methods["quantum_error_obstruction_q7"]
    assert "QFT_4" in methods["quantum_qft_period_q8"]
    assert "compression" in methods["quantum_circuit_compression_q9"]
    assert "compression tree" in methods["compression_algebra"]
    assert "κ_A" in methods["aura_weighted"]
    assert "obstruction" in methods["equation"]
    assert "universal-shadow" in methods["category_like_translation_x3"]
    assert "integral coherence" in methods["calculus_depth"]
    assert "sum/double/inverse" in methods["trigonometry_identities"]
    assert "inverse obstruction" in methods["phase_equation_normal_forms"]
    assert "determinant" in methods["linear_algebra_seed"]
    assert "hypothesis" in methods["statistics_inference"]
    assert "false-positive" in methods["statistics_concentration_likelihood"]
    assert "residual family" in methods["likelihood_geometry_x5"]
    assert "observer-gap separation" in methods["surprise_separation_s1"]
    assert passed["surprise_separation_s1"] is True
    assert "expanded-baseline" in methods["surprise_search_s3"]
    assert passed["surprise_search_s3"] is True
    assert "3-wise" in methods["surprise_kwise_s5"]
    assert passed["surprise_kwise_s5"] is True
    assert "de Bruijn" in methods["surprise_debruijn_s6"]
    assert passed["surprise_debruijn_s6"] is True
    assert "separation corpus" in methods["surprise_corpus_s7"]
    assert passed["surprise_corpus_s7"] is True
    assert "topological-order separation" in methods["observer_gap_topology_s7"]
    assert passed["observer_gap_topology_s7"] is True
    assert "without full tomography" in methods["quantum_surprise_q10"]
    assert passed["quantum_surprise_q10"] is True
    assert "Born-rule" in methods["quantum_tensor_q11"]
    assert passed["quantum_tensor_q11"] is True
    assert "evidence ledger" in methods["benchmark_evidence_r15"]
    assert passed["benchmark_evidence_r15"] is True
    assert "observer-synthesis" in methods["veyra_magic_m1"]
    assert passed["veyra_magic_m1"] is True
    assert "conservative optimizer" in methods["vam_reference_v1"]
    assert "proof-obligation ledger" in methods["vam_reference_v1"]
    assert "optimizer 7-local-law bridge" in methods["vam_reference_v1"]
    assert "pre/post witness" in methods["vam_reference_v1"]
    assert passed["vam_reference_v1"] is True
    assert "alternating tail" in methods["transcendental_limit"]
    assert "Cauchy tails" in methods["convergence_algebra"]
    assert "refinement" in methods["real_analysis_structure"]
    assert "weighted echo measure" in methods["weighted_echo_measure"]
    assert "network flow" in methods["science_domain_certificates"]
    assert "baseline comparison" in methods["model_diagnostics"]
    assert "transition-depth" in methods["scale_memory_log"]
    assert "property" in methods["core_language_property_fuzz"]
    assert "coverage" in methods["core_language_coverage"]
    assert "source-span" in methods["core_language_span_diagnostics"]
    assert "stable-export" in methods["proof_discipline"]
    assert "formal proof bridge" in methods["foundational_repair_f1_f3"] or "checked Lean bridge" in methods["foundational_repair_f1_f3"]
    assert "fixed-anchor structural codec" in methods["intrinsic_mode_transport_r9"]
    assert passed["intrinsic_mode_transport_r9"] is True
    assert "source-replayed surface proof" in methods["proof_elaboration_r10"]
    assert passed["proof_elaboration_r10"] is True
    assert "closed observer artifact" in methods["observer_core_r11"]
    assert passed["observer_core_r11"] is True
    assert "four-lane intrinsic IR/VAMI replay" in methods["intrinsic_vam_r12"]
    assert passed["intrinsic_vam_r12"] is True
    assert "guarded Lean bridge" in methods["intrinsic_observer_echo_r13"]
    assert passed["intrinsic_observer_echo_r13"] is True
    assert "finite executable five-plus-one" in methods["observer_synthesis_v2_r14"]
    assert passed["observer_synthesis_v2_r14"] is True
    assert "residual-chain balance" in methods["observer_descent_r16"]
    assert "best-lower-approximation" in next(
        item.detail for item in certs if item.name == "observer_descent_r16"
    )
    assert passed["observer_descent_r16"] is True
    assert "context-relative" in methods["observer_realization_p1_r16"]
    assert "exact-verification=pass" in next(
        item.detail for item in certs if item.name == "observer_realization_p1_r16"
    )
    assert passed["observer_realization_p1_r16"] is True
    assert "native rez/nod/tact/breath/mode" in methods["native_runtime_f4"]
    assert "classical-vs-Veyra" in methods["classical_benchmark_f5"]
    assert "deduction-chain" in methods["deduction_chain_f6"]
    assert "readiness contract" in methods["essence_core"]
