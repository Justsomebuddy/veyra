"""All-candidate matched-control pressure runtime for P3-OG."""

from __future__ import annotations

import logging

from .prime_power_observer_genesis_p3og_codec import digest
from .prime_power_observer_genesis_p3og_machine_internal import (
    _apply_maintenance_control_validated, _branch_trace_validated,
    _initial_state_validated,
)
from .prime_power_observer_genesis_p3og_source import (
    _deterministic_select_validated, validate_seed, validate_source,
)
from .prime_power_observer_genesis_p3og_types import (
    BoundaryState, CandidatePressureResult, MaintenanceControlState,
    P3OGPressureReport, P3OGSource, PressureStatus, PrimitiveModeSeed,
    P3OG_NONCLAIMS,
)

logger = logging.getLogger(__name__)


def _refuted(
    source: P3OGSource, seed: PrimitiveModeSeed, reason: str,
    identity: str,
) -> CandidatePressureResult:
    """Create one explicit finite counterexample result without a capability."""
    logger.debug("p3og._refuted entry reason=%s", reason)
    fields = (
        seed.seed_digest, PressureStatus.REFUTED, reason, identity,
        None, None, None, None, None,
    )
    result = CandidatePressureResult(*fields, digest("candidate-result", *fields))
    logger.debug("p3og._refuted exit seed=%s", seed.seed_digest[:12])
    return result


def candidate_pressure(
    source: P3OGSource, seed: PrimitiveModeSeed,
) -> CandidatePressureResult:
    """Run recurrence, discrimination, retention, and maintenance-control checks."""
    logger.debug("p3og.candidate_pressure entry")
    source, seed = validate_seed(source, seed)
    result = _candidate_pressure_validated(source, seed)
    logger.debug(
        "p3og.candidate_pressure exit status=%s reason=%s",
        result.status.value, result.reason,
    )
    return result


def _candidate_pressure_validated(
    source: P3OGSource, seed: PrimitiveModeSeed,
) -> CandidatePressureResult:
    """Run one candidate after source and seed validation at the caller boundary."""
    logger.debug("p3og._candidate_pressure_validated entry")
    logger.debug("p3og.candidate_pressure seed=%s", seed.seed_digest[:12])
    identity = digest(
        "candidate-pressure-identity", source.source_digest, seed.seed_digest,
        source.source_instance_label,
    )
    if len(seed.cycle) < 3 or seed.cycle[0] != seed.cycle[-1]:
        return _refuted(source, seed, "nonrecurrent-seed", identity)
    if len(set(seed.cycle[:-1])) < 2:
        return _refuted(source, seed, "blind-seed", identity)
    active = _initial_state_validated(source, seed)
    controlled, maintenance_control = _apply_maintenance_control_validated(active)
    left, right = source.calibration_inputs
    active_left = _branch_trace_validated(source, seed, active, left)
    active_right = _branch_trace_validated(source, seed, active, right)
    control_left = _branch_trace_validated(source, seed, controlled, left)
    control_right = _branch_trace_validated(source, seed, controlled, right)
    traces = (active_left, active_right, control_left, control_right)
    reason = "passed"
    status = PressureStatus.PASSED
    if active_left.coupling.response == active_right.coupling.response:
        status, reason = PressureStatus.REFUTED, "calibration-not-discriminated"
    elif any(trace.final_state.boundary is not BoundaryState.ALIVE
             for trace in (active_left, active_right)):
        status, reason = PressureStatus.REFUTED, "active-boundary-not-maintained"
    elif (active_left.final_state.retained_residue
          == active_right.final_state.retained_residue):
        status, reason = PressureStatus.REFUTED, "residue-not-distinct"
    elif active_left.final_state.phase == active_right.final_state.phase:
        status, reason = PressureStatus.REFUTED, "retained-residue-not-efficacious"
    elif any(trace.final_state.boundary is not BoundaryState.REMOVED
             for trace in (control_left, control_right)):
        status, reason = (
            PressureStatus.REFUTED, "maintenance-control-does-not-remove-boundary",
        )
    elif any(trace.final_state.retained_residue is not None
             for trace in (control_left, control_right)):
        status, reason = (
            PressureStatus.REFUTED, "maintenance-control-does-not-clear-residue",
        )
    elif control_left.final_state.phase != control_right.final_state.phase:
        status, reason = (
            PressureStatus.REFUTED, "maintenance-control-does-not-erase-efficacy",
        )
    elif any(trace.maintenance_control is not expected for trace, expected in zip(
            traces,
            (MaintenanceControlState.ACTIVE, MaintenanceControlState.ACTIVE,
             MaintenanceControlState.DISABLED, MaintenanceControlState.DISABLED),
            strict=True)):
        status, reason = PressureStatus.REFUTED, "matched-control-drift"
    fields = (
        seed.seed_digest, status, reason, identity, maintenance_control,
        active_left, active_right, control_left, control_right,
    )
    result = CandidatePressureResult(*fields, digest("candidate-result", *fields))
    logger.debug(
        "p3og._candidate_pressure_validated exit status=%s reason=%s",
        status.value, reason,
    )
    return result


def run_p3og_pressure(source: P3OGSource) -> P3OGPressureReport:
    """Require every canonical pool candidate to pass; never cherry-pick one."""
    logger.debug("p3og.run_p3og_pressure entry")
    source = validate_source(source)
    result = _run_p3og_pressure_validated(source)
    logger.debug("p3og.run_p3og_pressure exit status=%s", result.status.value)
    return result


def _run_p3og_pressure_validated(source: P3OGSource) -> P3OGPressureReport:
    """Run the complete pressure report over one already validated source."""
    logger.debug("p3og._run_p3og_pressure_validated entry")
    selection = _deterministic_select_validated(source)
    candidates = tuple(
        _candidate_pressure_validated(source, seed) for seed in source.seeds
    )
    failed = tuple(item for item in candidates if item.status is not PressureStatus.PASSED)
    status = PressureStatus.REFUTED if failed else PressureStatus.PASSED
    reason = failed[0].reason if failed else "all-candidates-passed"
    selected = candidates[selection.selected_index]
    fields = (
        status, reason, source.source_digest, selection, candidates,
        selected.result_digest, PressureStatus.OPEN, 0, P3OG_NONCLAIMS,
    )
    result = P3OGPressureReport(*fields, digest("pressure-report", *fields))
    logger.debug("p3og._run_p3og_pressure_validated exit status=%s", status.value)
    return result
