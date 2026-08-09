"""Adversarial boundaries for the hardened P3-OG pressure implementation."""

from __future__ import annotations

from dataclasses import fields, make_dataclass, replace
import logging

import pytest

import src.core.prime_power_observer_genesis_p3og as facade
import src.core.prime_power_observer_genesis_p3og_source as source_module
from src.core.prime_power_observer_genesis_p3og import (
    CandidatePressureResult, P3OGPressureReport, P3OGSource, PrimitiveModeSeed,
    TransitionKind, p3og_source, run_p3og_pressure, validate_pressure_report,
    validate_source,
)
from src.core.prime_power_observer_genesis_p3og_codec import canonical_bytes
from src.core.prime_power_observer_genesis_p3og_machine import (
    apply_pre_coupling_maintenance_control, couple, initial_state, transition,
)
from src.core.prime_power_observer_genesis_p3og_runtime import candidate_pressure
from src.core.prime_power_observer_genesis_p3og_source import validate_seed

logger = logging.getLogger(__name__)
SUFFIX = (
    TransitionKind.IDLE, TransitionKind.MAINTAIN,
    TransitionKind.IDLE, TransitionKind.ADVANCE,
)
SEEDS = (("alpha", (0, 1, 0)), ("beta", (1, 0, 1)))


class ExplosiveEquality:
    """Hostile field that must be rejected before equality dispatch."""

    def __eq__(self, other: object) -> bool:
        logger.error("test_p3og.ExplosiveEquality equality was invoked other=%r", other)
        raise RuntimeError("hostile equality invoked")


def _source(source_instance: str = "source-1"):
    """Build the small canonical adversarial fixture."""
    logger.debug(
        "test_p3og_adversarial._source entry source_instance=%s", source_instance,
    )
    result = p3og_source(
        prime=3, depth=1, source_instance_label=source_instance, seed_rows=SEEDS,
        calibration_inputs=(0, 1), maintenance_credit=2, suffix=SUFFIX,
    )
    logger.debug("test_p3og_adversarial._source exit source=%s", result.source_digest[:12])
    return result


@pytest.mark.parametrize("field", ["promotions", "nonclaims", "report_digest"])
def test_replay_rejects_hostile_equality_fields_without_dispatch(field):
    logger.debug("test_p3og hostile equality entry field=%s", field)
    source = _source()
    forged = replace(run_p3og_pressure(source), **{field: ExplosiveEquality()})
    with pytest.raises(ValueError, match="p3og-report-malformed"):
        validate_pressure_report(source, forged)
    logger.debug("test_p3og hostile equality exit field=%s", field)


def test_replay_returns_fresh_recomputed_evidence():
    logger.debug("test_p3og fresh replay entry")
    source = _source()
    report = run_p3og_pressure(source)
    replay = validate_pressure_report(source, report)
    assert replay == report
    assert replay is not report
    assert replay.selection is not report.selection
    assert replay.candidates is not report.candidates
    logger.debug("test_p3og fresh replay exit")


def test_source_and_seed_reject_hostile_equality_without_dispatch():
    logger.debug("test_p3og hostile source entry")
    source = _source()
    forged_source = replace(source, source_digest=ExplosiveEquality())
    with pytest.raises(ValueError, match="p3og-source-malformed"):
        validate_source(forged_source)
    forged_seed = PrimitiveModeSeed("alpha", (0, 1, 0), ExplosiveEquality())
    with pytest.raises(ValueError, match="p3og-seed-malformed"):
        validate_seed(source, forged_seed)
    uninitialized = object.__new__(P3OGSource)
    with pytest.raises(ValueError, match="p3og-source-malformed"):
        validate_source(uninitialized)
    logger.debug("test_p3og hostile source exit")


def test_cross_source_and_forged_state_are_rejected():
    logger.debug("test_p3og state provenance entry")
    first, second = _source("first"), _source("second")
    seed = first.seeds[0]
    state = initial_state(first, seed)
    second_seed = next(item for item in second.seeds if item.seed_digest == seed.seed_digest)
    with pytest.raises(ValueError, match="p3og-state-drift"):
        couple(second, second_seed, state, 0)
    with pytest.raises(ValueError, match="p3og-state-drift"):
        transition(first, seed, replace(state, phase=1), TransitionKind.ADVANCE)
    logger.debug("test_p3og state provenance exit")


def test_maintenance_control_requires_valid_source_bound_state():
    logger.debug("test_p3og maintenance control provenance entry")
    source = _source()
    seed = source.seeds[0]
    state = initial_state(source, seed)
    controlled, receipt = apply_pre_coupling_maintenance_control(source, seed, state)
    assert controlled.state_digest == receipt.disabled_state_digest
    with pytest.raises(ValueError, match="p3og-state-drift"):
        apply_pre_coupling_maintenance_control(
            source, seed, replace(state, state_digest="0" * 64),
        )
    logger.debug("test_p3og maintenance control provenance exit")


@pytest.mark.parametrize(
    "operation,reason",
    [
        ("couple-type", "p3og-coupling-input"),
        ("couple-size", "p3og-coupling-input"),
        ("transition-kind", "p3og-transition-kind"),
        ("candidate-seed", "p3og-seed-type"),
    ],
)
def test_public_helpers_fail_with_typed_errors(operation, reason):
    logger.debug("test_p3og typed helper entry operation=%s", operation)
    source = _source()
    seed = source.seeds[0]
    state = initial_state(source, seed)
    with pytest.raises(ValueError, match=reason):
        if operation == "couple-type":
            couple(source, seed, state, "bad")
        elif operation == "couple-size":
            couple(source, seed, state, 1 << 4097)
        elif operation == "transition-kind":
            transition(source, seed, state, "bad")
        else:
            candidate_pressure(source, object())
    logger.debug("test_p3og typed helper exit operation=%s", operation)


def test_facade_exports_are_explicit_and_include_replay_validation():
    logger.debug("test_p3og facade exports entry")
    assert set(facade.__all__) == {
        "CandidatePressureResult", "DeterministicSelectionReceipt",
        "P3OG_NONCLAIMS", "P3OGPressureReport", "P3OGSource", "PressureStatus",
        "PrimitiveModeSeed", "TransitionKind", "deterministic_select",
        "p3og_source", "run_p3og_pressure", "validate_pressure_report",
        "validate_source",
    }
    assert all(hasattr(facade, name) for name in facade.__all__)
    logger.debug("test_p3og facade exports exit")


def test_root_package_does_not_promote_candidate_surface():
    logger.debug("test_p3og root non-export entry")
    import src.core as root_core

    assert not hasattr(root_core, "run_p3og_pressure")
    logger.debug("test_p3og root non-export exit")


def test_high_level_dto_fields_name_only_implemented_pressure_semantics():
    logger.debug("test_p3og DTO field contract entry")
    assert tuple(field.name for field in fields(P3OGSource))[3] == "source_instance_label"
    assert tuple(field.name for field in fields(CandidatePressureResult))[2:9] == (
        "reason", "candidate_pressure_identity_digest", "maintenance_control",
        "active_left", "active_right", "control_left", "control_right",
    )
    assert tuple(field.name for field in fields(P3OGPressureReport))[5] == (
        "selected_candidate_result_digest"
    )
    logger.debug("test_p3og DTO field contract exit")


def _splice_report(report, target: str):
    """Create one exact-type nested splice without relying on hostile equality."""
    logger.debug("test_p3og nested splice entry target=%s", target)
    if target == "selection":
        result = replace(
            report, selection=replace(report.selection, pool_digest="0" * 64),
        )
    elif target == "selected-result-link":
        result = replace(report, selected_candidate_result_digest="0" * 64)
    else:
        candidate = report.candidates[0]
        if target == "candidate":
            changed = replace(candidate, reason="spliced")
        elif target == "maintenance-control":
            control = replace(candidate.maintenance_control, receipt_digest="0" * 64)
            changed = replace(candidate, maintenance_control=control)
        else:
            trace = candidate.active_left
            if target == "coupling":
                trace = replace(
                    trace, coupling=replace(trace.coupling, receipt_digest="0" * 64),
                )
            elif target == "transition":
                transition_receipts = (
                    replace(trace.transitions[0], receipt_digest="0" * 64),
                    *trace.transitions[1:],
                )
                trace = replace(trace, transitions=transition_receipts)
            else:
                trace = replace(
                    trace,
                    final_state=replace(trace.final_state, state_digest="0" * 64),
                )
            changed = replace(candidate, active_left=trace)
        result = replace(report, candidates=(changed, *report.candidates[1:]))
    logger.debug("test_p3og nested splice exit target=%s", target)
    return result


@pytest.mark.parametrize(
    "target",
    [
        "selection", "candidate", "maintenance-control", "coupling",
        "transition", "final-state", "selected-result-link",
    ],
)
def test_replay_rejects_exact_type_nested_splices(target):
    logger.debug("test_p3og nested rejection entry target=%s", target)
    source = _source()
    report = run_p3og_pressure(source)
    with pytest.raises(ValueError, match="p3og-report-drift"):
        validate_pressure_report(source, _splice_report(report, target))
    logger.debug("test_p3og nested rejection exit target=%s", target)


def test_codec_binds_module_identity_for_equal_qualnames():
    logger.debug("test_p3og codec identity entry")
    left_type = make_dataclass("SameRecord", [("value", int)])
    right_type = make_dataclass("SameRecord", [("value", int)])
    left_type.__module__, right_type.__module__ = "p3og.left", "p3og.right"
    assert canonical_bytes(left_type(1)) != canonical_bytes(right_type(1))
    logger.debug("test_p3og codec identity exit")


def test_codec_rejects_excessive_depth_and_container_width():
    logger.debug("test_p3og codec resource entry")
    deep: object = 0
    for _ in range(26):
        deep = (deep,)
    with pytest.raises(ValueError, match="p3og-codec-resource"):
        canonical_bytes(deep)
    with pytest.raises(ValueError, match="p3og-codec-resource"):
        canonical_bytes(tuple(range(257)))
    logger.debug("test_p3og codec resource exit")


def test_maximum_accepted_source_run_and_replay_validate_in_constant_passes(
    monkeypatch,
):
    logger.debug("test_p3og maximum source entry candidates=64 suffix=64")
    prime = 2**31 - 1
    scalar = 2**30
    rows = tuple(
        (f"seed-{index}", (scalar + index, scalar + index + 1, scalar + index))
        for index in range(64)
    )
    original_is_prime = source_module._is_prime
    prime_checks = []

    def counted_is_prime(value: int) -> bool:
        logger.debug("test_p3og counted primality entry value=%d", value)
        prime_checks.append(value)
        result = original_is_prime(value)
        logger.debug("test_p3og counted primality exit result=%s", result)
        return result

    monkeypatch.setattr(source_module, "_is_prime", counted_is_prime)
    source = p3og_source(
        prime=prime, depth=16, source_instance_label="maximum-envelope",
        seed_rows=rows,
        calibration_inputs=(2**4095 - 1, -(2**4095) + 1), maintenance_credit=64,
        suffix=(TransitionKind.MAINTAIN,) * 64,
    )
    prime_checks.clear()
    report = run_p3og_pressure(source)
    replay = validate_pressure_report(source, report)
    assert len(report.candidates) == 64
    assert all(
        candidate.active_left is not None
        and len(candidate.active_left.transitions) == 64
        for candidate in report.candidates
    )
    assert replay == report and replay is not report
    assert prime_checks == [prime, prime]
    logger.debug(
        "test_p3og maximum source exit status=%s prime_checks=%d",
        report.status.value, len(prime_checks),
    )
