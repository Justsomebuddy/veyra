"""Guarded public low-level boundaries for the P3-OG candidate machine."""

from __future__ import annotations

import logging

from .prime_power_observer_genesis_p3og_codec import bounded_int
from .prime_power_observer_genesis_p3og_machine_internal import (
    _apply_maintenance_control_validated, _branch_trace_validated,
    _couple_validated, _initial_state_validated, _transition_validated,
    _validate_state_validated,
)
from .prime_power_observer_genesis_p3og_source import validate_seed
from .prime_power_observer_genesis_p3og_types import (
    BoundaryState, BranchTrace, CandidateMachineState, CouplingReceipt, P3OGSource,
    PreCouplingMaintenanceControlReceipt, PrimitiveModeSeed, TransitionKind,
    TransitionReceipt,
)

logger = logging.getLogger(__name__)


def initial_state(source: P3OGSource, seed: PrimitiveModeSeed) -> CandidateMachineState:
    """Create initial state after validating the complete public context once."""
    logger.debug("p3og.initial_state entry")
    source, seed = validate_seed(source, seed)
    result = _initial_state_validated(source, seed)
    logger.debug("p3og.initial_state exit state=%s", result.state_digest[:12])
    return result


def apply_pre_coupling_maintenance_control(
    source: P3OGSource, seed: PrimitiveModeSeed, state: CandidateMachineState,
) -> tuple[CandidateMachineState, PreCouplingMaintenanceControlReceipt]:
    """Validate once, require the exact initial state, then disable maintenance."""
    logger.debug("p3og.apply_pre_coupling_maintenance_control entry")
    source, seed = validate_seed(source, seed)
    state = _validate_state_validated(source, seed, state)
    if state.boundary is BoundaryState.REMOVED:
        logger.error("p3og.apply_pre_coupling_maintenance_control removed boundary")
        raise ValueError("p3og-boundary-removed")
    if state != _initial_state_validated(source, seed):
        logger.error("p3og.apply_pre_coupling_maintenance_control non-initial state")
        raise ValueError("p3og-maintenance-control-not-pre-coupling")
    result = _apply_maintenance_control_validated(state)
    logger.debug(
        "p3og.apply_pre_coupling_maintenance_control exit state=%s",
        result[0].state_digest[:12],
    )
    return result


def couple(
    source: P3OGSource, seed: PrimitiveModeSeed, state: CandidateMachineState,
    input_value: int,
) -> tuple[CandidateMachineState, CouplingReceipt]:
    """Validate the public context and apply one bounded coupling."""
    logger.debug("p3og.couple entry")
    source, seed = validate_seed(source, seed)
    state = _validate_state_validated(source, seed, state)
    if state.boundary is BoundaryState.REMOVED:
        logger.error("p3og.couple rejected removed boundary")
        raise ValueError("p3og-boundary-removed")
    input_value = bounded_int(input_value, "p3og-coupling-input", 4096)
    result = _couple_validated(source, seed, state, input_value)
    logger.debug("p3og.couple exit response=%r", result[1].response)
    return result


def transition(
    source: P3OGSource, seed: PrimitiveModeSeed, state: CandidateMachineState,
    kind: TransitionKind,
) -> tuple[CandidateMachineState, TransitionReceipt]:
    """Validate the public context and apply one native transition."""
    logger.debug("p3og.transition entry")
    if type(kind) is not TransitionKind:
        logger.error("p3og.transition invalid kind")
        raise ValueError("p3og-transition-kind")
    source, seed = validate_seed(source, seed)
    state = _validate_state_validated(source, seed, state)
    if state.boundary is BoundaryState.REMOVED:
        logger.error("p3og.transition rejected removed boundary")
        raise ValueError("p3og-boundary-removed")
    result = _transition_validated(source, seed, state, kind)
    logger.debug("p3og.transition exit boundary=%s", result[0].boundary.value)
    return result


def branch_trace(
    source: P3OGSource, seed: PrimitiveModeSeed, initial: CandidateMachineState,
    input_value: int,
) -> BranchTrace:
    """Validate once, then run the complete trusted precommitted suffix."""
    logger.debug("p3og.branch_trace entry")
    source, seed = validate_seed(source, seed)
    initial = _validate_state_validated(source, seed, initial)
    if initial.boundary is BoundaryState.REMOVED:
        logger.error("p3og.branch_trace rejected removed boundary")
        raise ValueError("p3og-boundary-removed")
    input_value = bounded_int(input_value, "p3og-coupling-input", 4096)
    result = _branch_trace_validated(source, seed, initial, input_value)
    logger.debug("p3og.branch_trace exit boundary=%s", result.final_state.boundary.value)
    return result
