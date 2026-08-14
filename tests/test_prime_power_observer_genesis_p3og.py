"""Focused laws and hostile boundaries for the isolated P3-OG pressure slice."""

from __future__ import annotations

from dataclasses import fields, replace
import logging

import pytest

import src.core.prime_power_observer_genesis_p3og_runtime as runtime_module
from src.core.prime_power_observer_genesis_p3og import (
    P3OGPressureReport, P3OGSource, PressureStatus, TransitionKind,
    deterministic_select, p3og_source, run_p3og_pressure, validate_source,
)
from src.core.prime_power_observer_genesis_p3og_source import primitive_seed
from src.core.prime_power_observer_genesis_p3og_types import (
    BoundaryState, MaintenanceControlState,
)
from src.core.prime_power_observer_genesis_p3og_validation import (
    validate_pressure_report,
)

logger = logging.getLogger(__name__)
GOOD_SEEDS = (("alpha", (0, 1, 0)), ("beta", (1, 0, 1)))
GOOD_SUFFIX = (
    TransitionKind.IDLE, TransitionKind.MAINTAIN,
    TransitionKind.IDLE, TransitionKind.ADVANCE,
)


def _source(
    *, source_instance: str = "source-1",
    seeds: tuple[tuple[str, tuple[int, ...]], ...] = GOOD_SEEDS,
    calibration: tuple[int, int] = (0, 1),
    suffix: tuple[TransitionKind, ...] = GOOD_SUFFIX,
) -> P3OGSource:
    logger.debug("test_p3og._source entry source_instance=%s", source_instance)
    result = p3og_source(
        prime=3, depth=1, source_instance_label=source_instance, seed_rows=seeds,
        calibration_inputs=calibration, maintenance_credit=2, suffix=suffix,
    )
    logger.debug("test_p3og._source exit source=%s", result.source_digest[:12])
    return result


def test_all_candidate_pressure_passes_without_observer_role_claim():
    report = run_p3og_pressure(_source())
    assert report.status is PressureStatus.PASSED
    assert report.reason == "all-candidates-passed"
    assert report.role_status is PressureStatus.OPEN
    assert report.promotions == 0
    assert len(report.candidates) == 2
    assert all(item.status is PressureStatus.PASSED for item in report.candidates)
    assert not {"token_id", "birth_core_digest"}.intersection(
        item.name for item in fields(P3OGPressureReport)
    )


def test_matched_control_coupling_accepts_both_inputs_without_digest_drift():
    """Current paired pre/post coupling semantics preserve published evidence."""
    logger.debug("test_p3og matched coupling positive entry")
    source = _source()
    seed = source.seeds[0]
    active = runtime_module._initial_state_validated(source, seed)
    controlled, _ = runtime_module._apply_maintenance_control_validated(active)
    assert runtime_module._matched_control_coupling(
        source, seed, active, controlled, source.calibration_inputs,
    ) is not None
    report = run_p3og_pressure(source)
    assert source.source_digest == (
        "0238df62dd849ecd51df3e017720237491e191c10daf9b91ca4570b54fd76010"
    )
    assert report.report_digest == (
        "6cb296c650deaf458649b0211546815490a46aa0ab8d7606362daea3fc38faf7"
    )
    assert tuple(candidate.result_digest for candidate in report.candidates) == (
        "ec20a443a486f82525b0fca69edeacae7c049a55cd8cc9c20f31b6cf01a1e620",
        "69f0a73530c5b727d6edac47390742069a50bdcf90c9513055012d7d9b079996",
    )
    logger.debug("test_p3og matched coupling positive exit")


def test_selection_has_no_nonce_and_pool_order_is_canonical():
    forward = _source(seeds=GOOD_SEEDS)
    backward = _source(seeds=tuple(reversed(GOOD_SEEDS)))
    assert forward == backward
    assert deterministic_select(forward) == deterministic_select(backward)
    assert "selector_nonce" not in {item.name for item in fields(P3OGSource)}


def test_selection_ignores_source_instance_calibration_and_suffix():
    first = _source()
    changed = _source(
        source_instance="source-2", calibration=(7, 8),
        suffix=(TransitionKind.MAINTAIN, TransitionKind.ADVANCE),
    )
    left, right = deterministic_select(first), deterministic_select(changed)
    assert left.pool_digest == right.pool_digest
    assert left.selected_index == right.selected_index
    assert left.selected_seed_digest == right.selected_seed_digest
    assert left.source_digest != right.source_digest


def test_success_requires_every_pool_candidate_not_selected_cherry_pick():
    source = _source(seeds=((*GOOD_SEEDS, ("blind", (0, 0, 0)))))
    report = run_p3og_pressure(source)
    assert report.status is PressureStatus.REFUTED
    assert any(item.reason == "blind-seed" for item in report.candidates)
    assert any(item.status is PressureStatus.PASSED for item in report.candidates)


def test_nonrecurrent_and_blind_candidates_are_refuted_not_open():
    nonrecurrent = run_p3og_pressure(_source(seeds=(("bad", (0, 1)),)))
    blind = run_p3og_pressure(_source(seeds=(("blind", (0, 0, 0)),)))
    assert nonrecurrent.status is PressureStatus.REFUTED
    assert nonrecurrent.reason == "nonrecurrent-seed"
    assert blind.status is PressureStatus.REFUTED
    assert blind.reason == "blind-seed"


def test_exact_blind_calibration_is_refuted_not_open():
    report = run_p3og_pressure(_source(calibration=(0, 9)))
    assert report.status is PressureStatus.REFUTED
    assert report.reason == "calibration-not-discriminated"


def test_maintenance_control_uses_identical_transition_schedule():
    candidate = run_p3og_pressure(_source()).candidates[0]
    traces = (
        candidate.active_left, candidate.active_right,
        candidate.control_left, candidate.control_right,
    )
    assert all(trace is not None for trace in traces)
    schedules = {
        tuple(receipt.kind for receipt in trace.transitions)  # type: ignore[union-attr]
        for trace in traces
    }
    assert schedules == {GOOD_SUFFIX}
    assert candidate.active_left.maintenance_control is MaintenanceControlState.ACTIVE
    assert (
        candidate.control_left.maintenance_control
        is MaintenanceControlState.DISABLED
    )


def test_active_component_maintains_while_control_removes_and_erases():
    candidate = run_p3og_pressure(_source()).candidates[0]
    assert candidate.maintenance_control is not None
    assert candidate.active_left.final_state.boundary is BoundaryState.ALIVE
    assert candidate.active_right.final_state.boundary is BoundaryState.ALIVE
    assert candidate.control_left.final_state.boundary is BoundaryState.REMOVED
    assert candidate.control_right.final_state.boundary is BoundaryState.REMOVED
    assert candidate.control_left.final_state.retained_residue is None
    assert candidate.control_right.final_state.retained_residue is None
    assert candidate.control_left.final_state.phase == candidate.control_right.final_state.phase
    assert candidate.control_left.transitions[-1].before_digest != (
        candidate.control_left.transitions[-1].after_digest
    )
    assert candidate.control_left.final_state.transition_count == 1 + len(GOOD_SUFFIX)


def test_retained_residue_changes_later_active_transition():
    candidate = run_p3og_pressure(_source()).candidates[0]
    left, right = candidate.active_left, candidate.active_right
    assert left.coupling.response != right.coupling.response
    assert left.final_state.retained_residue != right.final_state.retained_residue
    assert left.final_state.phase != right.final_state.phase


def test_cycle_values_drive_responses_not_only_shape():
    report = run_p3og_pressure(_source())
    responses = {
        item.seed_digest: (
            item.active_left.coupling.response, item.active_right.coupling.response,
        ) for item in report.candidates
    }
    assert set(responses.values()) == {(0, 1), (1, 0)}


def test_missing_maintenance_refutes_active_boundary():
    report = run_p3og_pressure(_source(suffix=(
        TransitionKind.IDLE, TransitionKind.IDLE, TransitionKind.ADVANCE,
    )))
    assert report.status is PressureStatus.REFUTED
    assert report.reason == "active-boundary-not-maintained"


def test_missing_decay_refutes_maintenance_control_removal():
    report = run_p3og_pressure(_source(suffix=(
        TransitionKind.MAINTAIN, TransitionKind.ADVANCE,
    )))
    assert report.status is PressureStatus.REFUTED
    assert report.reason == "maintenance-control-does-not-remove-boundary"


def test_report_binds_complete_transition_and_final_state_evidence():
    candidate = run_p3og_pressure(_source()).candidates[0]
    for trace in (
        candidate.active_left, candidate.active_right,
        candidate.control_left, candidate.control_right,
    ):
        assert trace.trace_digest
        assert trace.coupling.receipt_digest
        assert len(trace.transitions) == len(GOOD_SUFFIX)
        assert all(receipt.receipt_digest for receipt in trace.transitions)
        assert trace.final_state.state_digest


def test_replay_is_fresh_drift_check_not_authentication():
    source = _source()
    report = run_p3og_pressure(source)
    replay = validate_pressure_report(source, report)
    assert replay == report
    assert replay is not report
    assert replay.selection is not report.selection


def test_source_and_nested_result_splicing_are_rejected():
    source = _source()
    report = run_p3og_pressure(source)
    with pytest.raises(ValueError, match="p3og-source-drift"):
        validate_source(replace(source, depth=2))
    with pytest.raises(ValueError, match="p3og-report-drift"):
        validate_pressure_report(source, replace(report, promotions=1))
    foreign = run_p3og_pressure(_source(source_instance="other"))
    with pytest.raises(ValueError, match="p3og-report-drift"):
        validate_pressure_report(source, foreign)


def test_duplicate_pool_rows_and_labels_are_rejected():
    with pytest.raises(ValueError, match="p3og-seed-duplicate"):
        _source(seeds=(GOOD_SEEDS[0], GOOD_SEEDS[0]))
    with pytest.raises(ValueError, match="p3og-seed-label-duplicate"):
        _source(seeds=(("same", (0, 1, 0)), ("same", (1, 0, 1))))


@pytest.mark.parametrize("prime", [0, 1, 4, 9, True, 2**127 - 1])
def test_invalid_prime_scope_is_bounded_and_rejected(prime):
    with pytest.raises(ValueError, match="p3og-arithmetic-scope"):
        p3og_source(
            prime=prime, depth=1, source_instance_label="source",
            seed_rows=GOOD_SEEDS,
            calibration_inputs=(0, 1), maintenance_credit=2, suffix=GOOD_SUFFIX,
        )


@pytest.mark.parametrize("field,value,reason", [
    ("source_instance_label", "x" * 129, "p3og-source-instance-label"),
    ("doctrine_label", "", "p3og-doctrine-label"),
    ("calibration_inputs", (0, 1 << 4097), "p3og-calibration"),
    ("maintenance_credit", 0, "p3og-maintenance-credit"),
])
def test_resource_envelope_rejects_oversized_or_empty_values(field, value, reason):
    kwargs = dict(
        prime=3, depth=1, source_instance_label="source", seed_rows=GOOD_SEEDS,
        calibration_inputs=(0, 1), maintenance_credit=2, suffix=GOOD_SUFFIX,
        doctrine_label="P3-OG-pressure-v2",
    )
    kwargs[field] = value
    with pytest.raises(ValueError, match=reason):
        p3og_source(**kwargs)


def test_malformed_seed_containers_and_unicode_are_typed_errors():
    with pytest.raises(ValueError, match="p3og-seed-rows"):
        p3og_source(
            prime=3, depth=1, source_instance_label="source",
            seed_rows=list(GOOD_SEEDS),
            calibration_inputs=(0, 1), maintenance_credit=2, suffix=GOOD_SUFFIX,
        )
    with pytest.raises(ValueError, match="p3og-seed-label"):
        primitive_seed("\ud800", (0, 1, 0))


def test_uninitialized_and_malformed_nested_dtos_fail_typed():
    with pytest.raises(ValueError, match="p3og-source-malformed"):
        validate_source(object.__new__(P3OGSource))
    source = _source()
    with pytest.raises(ValueError, match="p3og-source-malformed"):
        validate_source(replace(source, seeds=(object(),)))
    with pytest.raises(ValueError, match="p3og-report-malformed"):
        validate_pressure_report(source, object.__new__(P3OGPressureReport))


def test_nonclaims_keep_role_history_formalism_and_infinity_open():
    report = run_p3og_pressure(_source())
    required = {
        "criterion-blind-historical-selection", "consumed-one-shot-capability",
        "exact-n1-n2-p3t-arithmetic-bridge", "doctrine-admission",
        "first-closure-or-history-dag", "endogenous-observer-role",
        "n0-or-hap-lift", "formal-theorem",
        "prime-power-carrier-or-completed-infinity",
    }
    assert required.issubset(report.nonclaims)
