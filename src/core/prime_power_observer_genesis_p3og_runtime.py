"""All-candidate matched-control pressure runtime for P3-OG."""

from __future__ import annotations

from dataclasses import fields
import logging

from .prime_power_observer_genesis_p3og_codec import MAX_CODEC_INT_BITS, digest
from .prime_power_observer_genesis_p3og_machine_internal import (
    _apply_maintenance_control_validated, _branch_trace_from_coupling_validated,
    _couple_validated, _initial_state_validated, _validate_state_validated,
)
from .prime_power_observer_genesis_p3og_source import (
    _deterministic_select_validated, validate_seed, validate_source,
)
from .prime_power_observer_genesis_p3og_types import (
    BoundaryState, CandidateMachineState, CandidatePressureResult,
    CouplingReceipt, MaintenanceControlState, P3OGPressureReport, P3OGSource,
    PressureStatus, PrimitiveModeSeed, P3OG_NONCLAIMS,
)

logger = logging.getLogger(__name__)
_MATCHED_STATE_EXCLUSIONS = frozenset({"maintenance_control", "state_digest"})


def _matched_state_projection(
    state: CandidateMachineState,
) -> tuple[tuple[str, object], ...]:
    """Project every semantic state field except the control flag and digest."""
    logger.debug("p3og._matched_state_projection entry type=%s", type(state).__name__)
    state_fields = fields(state)
    excluded = {field.name for field in state_fields if field.name in _MATCHED_STATE_EXCLUSIONS}
    if excluded != _MATCHED_STATE_EXCLUSIONS:
        logger.error("p3og._matched_state_projection incompatible state schema")
        raise ValueError("p3og-matched-control-state-schema")
    result = tuple(
        (field.name, getattr(state, field.name))
        for field in state_fields
        if field.name not in _MATCHED_STATE_EXCLUSIONS
    )
    logger.debug("p3og._matched_state_projection exit fields=%d", len(result))
    return result


def _valid_coupling_receipt_scalars(receipt: CouplingReceipt) -> bool:
    """Preflight exact bounded receipt scalars before comparisons or hashing."""
    logger.debug("p3og._valid_coupling_receipt_scalars entry")
    digests = (
        receipt.before_digest, receipt.after_digest, receipt.receipt_digest,
    )
    valid = (
        type(receipt.input_value) is int
        and receipt.input_value.bit_length() <= MAX_CODEC_INT_BITS
        and (
            receipt.response is None
            or (
                type(receipt.response) is int
                and receipt.response.bit_length() <= MAX_CODEC_INT_BITS
            )
        )
        and all(
            type(value) is str
            and len(value) == 64
            and all(character in "0123456789abcdef" for character in value)
            for value in digests
        )
    )
    logger.debug("p3og._valid_coupling_receipt_scalars exit valid=%s", valid)
    return valid


def _matched_control_coupling(
    source: P3OGSource, seed: PrimitiveModeSeed,
    active: CandidateMachineState, controlled: CandidateMachineState,
    inputs: tuple[int, int],
) -> tuple[
    tuple[CandidateMachineState, CouplingReceipt,
          CandidateMachineState, CouplingReceipt], ...
] | None:
    """Check matched pre/post coupling semantics for both calibration inputs."""
    logger.debug("p3og._matched_control_coupling entry inputs=%d", len(inputs))
    if (
        type(active) is not CandidateMachineState
        or type(controlled) is not CandidateMachineState
    ):
        logger.error("p3og._matched_control_coupling malformed pre-coupling state")
        return None
    try:
        _validate_state_validated(source, seed, active)
        _validate_state_validated(source, seed, controlled)
        pre_matched = (
            active.maintenance_control is MaintenanceControlState.ACTIVE
            and controlled.maintenance_control is MaintenanceControlState.DISABLED
            and _matched_state_projection(active)
            == _matched_state_projection(controlled)
        )
    except ValueError as exc:
        logger.error("p3og._matched_control_coupling invalid pre-state=%s", exc)
        return None
    if not pre_matched:
        logger.error("p3og._matched_control_coupling pre-coupling drift")
        return None
    probes = []
    for input_value in inputs:
        try:
            active_output = _couple_validated(source, seed, active, input_value)
            controlled_output = _couple_validated(
                source, seed, controlled, input_value,
            )
        except ValueError as exc:
            logger.error("p3og._matched_control_coupling rejected probe=%s", exc)
            return None
        if (
            type(active_output) is not tuple or len(active_output) != 2
            or type(controlled_output) is not tuple or len(controlled_output) != 2
            or type(active_output[0]) is not CandidateMachineState
            or type(active_output[1]) is not CouplingReceipt
            or type(controlled_output[0]) is not CandidateMachineState
            or type(controlled_output[1]) is not CouplingReceipt
        ):
            logger.error("p3og._matched_control_coupling malformed probe output")
            return None
        active_after, active_receipt = active_output
        controlled_after, controlled_receipt = controlled_output
        if not (
            _valid_coupling_receipt_scalars(active_receipt)
            and _valid_coupling_receipt_scalars(controlled_receipt)
        ):
            logger.error("p3og._matched_control_coupling malformed receipt scalars")
            return None
        try:
            _validate_state_validated(source, seed, active_after)
            _validate_state_validated(source, seed, controlled_after)
        except ValueError as exc:
            logger.error("p3og._matched_control_coupling invalid state=%s", exc)
            return None
        row_matched = (
            active_after.maintenance_control is MaintenanceControlState.ACTIVE
            and controlled_after.maintenance_control is MaintenanceControlState.DISABLED
            and _matched_state_projection(active_after)
            == _matched_state_projection(controlled_after)
            and active_receipt.input_value == input_value
            and controlled_receipt.input_value == input_value
            and active_receipt.response == controlled_receipt.response
            and active_receipt.before_digest == active.state_digest
            and controlled_receipt.before_digest == controlled.state_digest
            and active_receipt.after_digest == active_after.state_digest
            and controlled_receipt.after_digest == controlled_after.state_digest
            and active_receipt.receipt_digest == digest(
                "coupling", active_receipt.input_value,
                active_receipt.before_digest, active_receipt.after_digest,
                active_receipt.response,
            )
            and controlled_receipt.receipt_digest == digest(
                "coupling", controlled_receipt.input_value,
                controlled_receipt.before_digest, controlled_receipt.after_digest,
                controlled_receipt.response,
            )
        )
        if not row_matched:
            logger.error("p3og._matched_control_coupling row drift")
            return None
        probes.append(
            (active_after, active_receipt, controlled_after, controlled_receipt),
        )
    result = tuple(probes)
    logger.debug("p3og._matched_control_coupling exit rows=%d", len(result))
    return result


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
    coupling_probes = _matched_control_coupling(
        source, seed, active, controlled, (left, right),
    )
    if coupling_probes is None:
        return _refuted(source, seed, "matched-control-coupling-drift", identity)
    left_probe, right_probe = coupling_probes
    active_left = _branch_trace_from_coupling_validated(
        source, seed, active, left_probe[0], left_probe[1],
    )
    control_left = _branch_trace_from_coupling_validated(
        source, seed, controlled, left_probe[2], left_probe[3],
    )
    active_right = _branch_trace_from_coupling_validated(
        source, seed, active, right_probe[0], right_probe[1],
    )
    control_right = _branch_trace_from_coupling_validated(
        source, seed, controlled, right_probe[2], right_probe[3],
    )
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
