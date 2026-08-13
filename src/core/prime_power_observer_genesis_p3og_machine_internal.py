"""Private operations over already validated P3-OG source, seed, and state values."""

from __future__ import annotations

import logging

from .prime_power_observer_genesis_p3og_codec import digest
from .prime_power_observer_genesis_p3og_types import (
    BoundaryState, BranchTrace, CandidateMachineState, CouplingReceipt,
    MaintenanceControlState, P3OGSource, PreCouplingMaintenanceControlReceipt,
    PrimitiveModeSeed, TransitionKind, TransitionReceipt,
)

logger = logging.getLogger(__name__)
MAX_TRANSITION_COUNT = 4096


def _state(
    run_id: str, seed_digest: str, boundary: BoundaryState,
    maintenance_control: MaintenanceControlState, phase: int, retained: int | None,
    credit: int, count: int,
) -> CandidateMachineState:
    """Construct one digest-bound internal state from trusted scalars."""
    logger.debug(
        "p3og.internal.state entry boundary=%s maintenance_control=%s",
        boundary, maintenance_control,
    )
    fields = (
        run_id, seed_digest, boundary, maintenance_control, phase, retained,
        credit, count,
    )
    result = CandidateMachineState(*fields, digest("machine-state", *fields))
    logger.debug("p3og.internal.state exit digest=%s", result.state_digest[:12])
    return result


def _validate_state_validated(
    source: P3OGSource, seed: PrimitiveModeSeed, state: CandidateMachineState,
) -> CandidateMachineState:
    """Validate state against an already validated source and canonical seed."""
    logger.debug("p3og.internal.validate_state entry")
    if type(state) is not CandidateMachineState:
        logger.error("p3og.internal.validate_state wrong state type")
        raise ValueError("p3og-state-type")
    try:
        exact_scalars = (
            type(state.run_id) is str and type(state.seed_digest) is str
            and type(state.boundary) is BoundaryState
            and type(state.maintenance_control) is MaintenanceControlState
            and type(state.phase) is int and type(state.maintenance_credit) is int
            and type(state.transition_count) is int and type(state.state_digest) is str
            and (state.retained_residue is None or type(state.retained_residue) is int)
        )
        if not exact_scalars:
            logger.error("p3og.internal.validate_state malformed scalar types")
            raise ValueError("p3og-state-malformed")
        period = len(seed.cycle) - 1
        modulus = source.prime ** (source.depth + 1)
        live_shape = (
            state.boundary is BoundaryState.ALIVE
            and 0 <= state.phase < max(period, 1)
            and 1 <= state.maintenance_credit <= source.maintenance_credit
            and (state.retained_residue is None
                 or 0 <= state.retained_residue < modulus)
        )
        removed_shape = (
            state.boundary is BoundaryState.REMOVED and state.phase == 0
            and state.retained_residue is None and state.maintenance_credit == 0
        )
        expected_run = digest("candidate-run", source.source_digest, seed.seed_digest)
        fields = (
            state.run_id, state.seed_digest, state.boundary,
            state.maintenance_control, state.phase, state.retained_residue,
            state.maintenance_credit, state.transition_count,
        )
        valid = (
            (live_shape or removed_shape)
            and 0 <= state.transition_count <= MAX_TRANSITION_COUNT
            and state.seed_digest == seed.seed_digest and state.run_id == expected_run
            and state.state_digest == digest("machine-state", *fields)
        )
    except (AttributeError, TypeError, UnicodeError, ValueError) as exc:
        logger.error("p3og.internal.validate_state malformed state=%s", exc)
        raise ValueError("p3og-state-malformed") from exc
    if not valid:
        logger.error("p3og.internal.validate_state state drift")
        raise ValueError("p3og-state-drift")
    logger.debug("p3og.internal.validate_state exit state=%s", state.state_digest[:12])
    return state


def _initial_state_validated(
    source: P3OGSource, seed: PrimitiveModeSeed,
) -> CandidateMachineState:
    """Create initial state from an already validated source and seed."""
    logger.debug("p3og.internal.initial_state entry")
    run_id = digest("candidate-run", source.source_digest, seed.seed_digest)
    result = _state(
        run_id, seed.seed_digest, BoundaryState.ALIVE, MaintenanceControlState.ACTIVE,
        0, None, source.maintenance_credit, 0,
    )
    logger.debug("p3og.internal.initial_state exit run=%s", run_id[:12])
    return result


def _apply_maintenance_control_validated(
    state: CandidateMachineState,
) -> tuple[CandidateMachineState, PreCouplingMaintenanceControlReceipt]:
    """Disable maintenance on a validated active state before coupling."""
    logger.debug("p3og.internal.apply_maintenance_control entry")
    if state.boundary is BoundaryState.REMOVED:
        logger.error("p3og.internal.apply_maintenance_control removed boundary")
        raise ValueError("p3og-boundary-removed")
    if state.maintenance_control is not MaintenanceControlState.ACTIVE:
        logger.error("p3og.internal.apply_maintenance_control invalid state")
        raise ValueError("p3og-maintenance-control-state")
    unchanged = digest(
        "maintenance-control-unchanged", state.run_id, state.seed_digest,
        state.boundary, state.phase, state.retained_residue,
        state.maintenance_credit, state.transition_count,
    )
    disabled = _state(
        state.run_id, state.seed_digest, state.boundary,
        MaintenanceControlState.DISABLED, state.phase, state.retained_residue,
        state.maintenance_credit, state.transition_count,
    )
    receipt = PreCouplingMaintenanceControlReceipt(
        state.state_digest, disabled.state_digest, unchanged,
        digest(
            "maintenance-control", state.state_digest, disabled.state_digest,
            unchanged,
        ),
    )
    logger.debug(
        "p3og.internal.apply_maintenance_control exit state=%s",
        disabled.state_digest[:12],
    )
    return disabled, receipt


def _couple_validated(
    source: P3OGSource, seed: PrimitiveModeSeed, state: CandidateMachineState,
    input_value: int,
) -> tuple[CandidateMachineState, CouplingReceipt]:
    """Apply coupling to already validated values."""
    logger.debug("p3og.internal.couple entry input_bits=%d", input_value.bit_length())
    if state.boundary is BoundaryState.REMOVED:
        logger.error("p3og.internal.couple removed boundary")
        raise ValueError("p3og-boundary-removed")
    if state.transition_count >= MAX_TRANSITION_COUNT:
        logger.error("p3og.internal.couple transition budget exhausted")
        raise ValueError("p3og-transition-budget")
    period = len(seed.cycle) - 1
    residue = input_value % (source.prime ** (source.depth + 1))
    response = seed.cycle[residue % period]
    after = _state(
        state.run_id, state.seed_digest, state.boundary,
        state.maintenance_control, state.phase, residue,
        state.maintenance_credit, state.transition_count + 1,
    )
    receipt = CouplingReceipt(
        input_value, state.state_digest, after.state_digest, response,
        digest("coupling", input_value, state.state_digest, after.state_digest, response),
    )
    logger.debug("p3og.internal.couple exit response=%r", response)
    return after, receipt


def _transition_validated(
    source: P3OGSource, seed: PrimitiveModeSeed, state: CandidateMachineState,
    kind: TransitionKind,
) -> tuple[CandidateMachineState, TransitionReceipt]:
    """Apply one trusted schedule transition to a trusted state."""
    logger.debug("p3og.internal.transition entry kind=%s", kind.value)
    if state.transition_count >= MAX_TRANSITION_COUNT:
        logger.error("p3og.internal.transition budget exhausted")
        raise ValueError("p3og-transition-budget")
    if state.boundary is BoundaryState.REMOVED:
        # Internal complete-schedule traces retain terminal steps as distinct,
        # budget-consuming no-ops. Public operations reject removed states.
        after = _state(
            state.run_id, state.seed_digest, state.boundary,
            state.maintenance_control, state.phase, state.retained_residue,
            state.maintenance_credit, state.transition_count + 1,
        )
    elif kind is TransitionKind.ADVANCE:
        period = len(seed.cycle) - 1
        step = 1 if state.retained_residue is None else 1 + state.retained_residue
        after = _state(
            state.run_id, state.seed_digest, state.boundary,
            state.maintenance_control, (state.phase + step) % period,
            state.retained_residue, state.maintenance_credit,
            state.transition_count + 1,
        )
    elif kind is TransitionKind.MAINTAIN:
        credit = (
            source.maintenance_credit
            if state.maintenance_control is MaintenanceControlState.ACTIVE
            else state.maintenance_credit
        )
        after = _state(
            state.run_id, state.seed_digest, state.boundary,
            state.maintenance_control, state.phase, state.retained_residue,
            credit, state.transition_count + 1,
        )
    else:
        credit = state.maintenance_credit - 1
        alive = credit > 0
        after = _state(
            state.run_id, state.seed_digest,
            BoundaryState.ALIVE if alive else BoundaryState.REMOVED,
            state.maintenance_control, state.phase if alive else 0,
            state.retained_residue if alive else None, max(credit, 0),
            state.transition_count + 1,
        )
    receipt = TransitionReceipt(
        kind, state.state_digest, after.state_digest, None,
        digest("transition", kind, state.state_digest, after.state_digest),
    )
    logger.debug("p3og.internal.transition exit boundary=%s", after.boundary.value)
    return after, receipt


def _branch_trace_validated(
    source: P3OGSource, seed: PrimitiveModeSeed, initial: CandidateMachineState,
    input_value: int,
) -> BranchTrace:
    """Run a trace over already validated source, seed, state, and input."""
    logger.debug("p3og.internal.branch_trace entry")
    state, coupling_receipt = _couple_validated(source, seed, initial, input_value)
    receipts = []
    for kind in source.suffix:
        state, receipt = _transition_validated(source, seed, state, kind)
        receipts.append(receipt)
    fields = (
        input_value, initial.maintenance_control, coupling_receipt, tuple(receipts),
        state,
    )
    result = BranchTrace(*fields, digest("branch-trace", *fields))
    logger.debug("p3og.internal.branch_trace exit boundary=%s", state.boundary.value)
    return result
