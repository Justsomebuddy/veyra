"""Central capability classification for the complete public test suite."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)

PINNED_LEAN_TESTS = frozenset(
    {
        "test_all_depth_family_p1d3.py",
        "test_all_depth_family_p1d3_adversarial.py",
        "test_all_depth_family_p1d3_certificate.py",
        "test_all_depth_family_p1d3_counterexamples.py",
        "test_benchmark_derivations.py",
        "test_certify.py",
        "test_certify_padic_local_realization.py",
        "test_certify_prime_power_observer_actualization.py",
        "test_certify_prime_power_reduction_network.py",
        "test_certify_vam_optimizer.py",
        "test_certify_intrinsic_vam.py",
        "test_classical_benchmarks.py",
        "test_comparative_bridge_ledger.py",
        "test_comparative_ledgers_certificate.py",
        "test_deduction_chain.py",
        "test_essence_core.py",
        "test_formal_bridge.py",
        "test_formal_export_binomial_symmetry.py",
        "test_formal_export_completion.py",
        "test_formal_export_geometry_wave.py",
        "test_formal_export_prep.py",
        "test_formal_export_probability_independence.py",
        "test_formal_export_probability_union.py",
        "test_formal_export_remaining_completion.py",
        "test_formal_export_variance_shift.py",
        "test_generated_confluence_p3c1_certificate.py",
        "test_generated_confluence_p3c1.py",
        "test_generated_confluence_p3c1_adversarial.py",
        "test_infinity_i1_certificate.py",
        "test_intrinsic_mode_bridge.py",
        "test_intrinsic_observer_echo_evidence.py",
        "test_intrinsic_observer_echo_formal_bridge.py",
        "test_intrinsic_observer_echo_lean.py",
        "test_intrinsic_observer_echo_source.py",
        "test_intrinsic_observer_echo_theorem.py",
        "test_intrinsic_vam_formal_bridge.py",
        "test_intrinsic_vam_formal_semantics.py",
        "test_layer_derivations.py",
        "test_layer_theorem_contracts.py",
        "test_native_formal_bridge.py",
        "test_native_number_theorems.py",
        "test_observer_core_bridge.py",
        "test_observer_descent_formal.py",
        "test_observer_patch_atlas_certificate.py",
        "test_observer_synthesis_parity.py",
        "test_observer_v3_lineage.py",
        "test_padic_completion_pomega2.py",
        "test_padic_completion_pomega2_adversarial.py",
        "test_padic_completion_pomega2_formal.py",
        "test_padic_family_introduction_p3n1.py",
        "test_padic_family_introduction_p3n1_adversarial.py",
        "test_padic_family_introduction_p3n1_formal.py",
        "test_padic_local_realization_p3n3n4.py",
        "test_padic_local_realization_p3n3n4_adversarial.py",
        "test_padic_local_realization_p3n3n4_formal.py",
        "test_prime_power_information_witness_n6w.py",
        "test_prime_power_observer_actualization_p3n0.py",
        "test_prime_power_observer_actualization_p3n0_history_rows.py",
        "test_prime_power_observer_actualization_p3n0_public_hostile.py",
        "test_prime_power_observer_actualization_p3n0_result_hostile.py",
        "test_prime_power_productive_bridge_p3a1b.py",
        "test_prime_power_productive_bridge_p3a1b_adversarial.py",
        "test_prime_power_productive_bridge_p3a1b_formal.py",
        "test_prime_power_reduction_network_p3n2.py",
        "test_prime_power_reduction_network_p3n2_adversarial.py",
        "test_prime_power_reduction_network_p3n2_formal.py",
        "test_prime_power_unbounded_p3n6_hardening.py",
        "test_prime_power_unbounded_p3n6_positive.py",
        "test_prime_power_unbounded_p3n6_sources.py",
        "test_productivity_counterpressure_p1d2.py",
        "test_productivity_counterpressure_p1d2_adversarial.py",
        "test_productivity_counterpressure_p1d2_certificate.py",
        "test_proof_core_bridge.py",
        "test_proof_elaboration_artifact.py",
        "test_proof_elaboration_bridge.py",
        "test_quantum_tensor_formal.py",
        "test_shadow_effects.py",
        "test_stream_completion_pomega1.py",
        "test_stream_completion_pomega1_adversarial.py",
        "test_stream_completion_pomega1_certificate.py",
        "test_structural_separation_ledger.py",
        "test_transport_coherence_p3c2.py",
        "test_transport_coherence_p3c2_adversarial.py",
        "test_transport_coherence_p3c2_formal.py",
        "test_vam_optimizer_formal_bridge.py",
        "test_vam_optimizer_proofs.py",
        "test_veyra_magic.py",
        "test_veyra_sage_essence.py",
    }
)

NATIVE_RUST_TESTS = frozenset(
    {
        "test_vam_benchmark_publication.py",
        "test_vam_native_boundaries.py",
        "test_vam_native_dense.py",
        "test_vam_native_emit_optimized_vam0.py",
        "test_vam_native_error_taxonomy.py",
        "test_vam_native_executor.py",
        "test_vam_native_optimizer.py",
        "test_vam_native_optimizer_expansion.py",
        "test_vam_native_optimizer_generated.py",
        "test_vam_native_optimizer_metamorphic.py",
        "test_vam_native_parity_expansion.py",
        "test_vam_native_scaffold.py",
        "test_vam_native_vamd_boundaries.py",
        "test_vam_native_vamd_executor.py",
        "test_vam_quantified_theorem.py",
        "test_vami_runtime_parity.py",
    }
)

LINUX_HARDENING_TESTS = frozenset(
    {
        "test_claim_composition_adversarial.py",
        "test_observer_discovery_v3_closed_worker.py",
        "test_observer_discovery_v3_governed_evaluation.py",
        "test_observer_discovery_v3_observer_transport.py",
        "test_observer_synthesis_v2_pipeline.py",
        "test_observer_synthesis_v2_receipt_worker.py",
        "test_observer_synthesis_v2_receipt_worker_hardening.py",
        "test_observer_synthesis_v2_receipt_worker_trust.py",
        "test_observer_synthesis_v2_trial_worker.py",
        "test_observer_synthesis_v2_trial_worker_hardening.py",
        "test_observer_synthesis_v2_worker.py",
        "test_observer_synthesis_v2_worker_hardening.py",
    }
)


def capability_markers_for(path: Path) -> tuple[str, ...]:
    """Return explicit external capability markers for one test module."""
    logger.debug("capability_markers_for entry path=%s", path)
    name = path.name
    markers: list[str] = []
    if name in PINNED_LEAN_TESTS:
        markers.extend(("requires_posix_file_locks", "requires_linux_hardening", "requires_pinned_lean"))
    if name in NATIVE_RUST_TESTS:
        markers.append("requires_native_rust")
    if name in LINUX_HARDENING_TESTS:
        markers.append("requires_linux_hardening")
    result = tuple(dict.fromkeys(markers))
    logger.debug("capability_markers_for exit markers=%r", result)
    return result


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Attach capability metadata without skipping or changing full-lane tests."""
    logger.debug("pytest_collection_modifyitems entry items=%d", len(items))
    marked = 0
    for item in items:
        for marker in capability_markers_for(Path(str(item.path))):
            item.add_marker(getattr(pytest.mark, marker))
            marked += 1
    logger.debug("pytest_collection_modifyitems exit marker_applications=%d", marked)
