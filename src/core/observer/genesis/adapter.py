"""The sole Mode-only whole-table adapter and exact 24-row machine capture."""

from __future__ import annotations

import logging

from ...native_runtime import Mode, Nod, Rez, Tact
from .digest import machine_digest
from .native import ObserverGenesisValidationError, exact_text, hex_digest
from .types import FiniteObserverMachine, MachineState, TransitionRow

logger = logging.getLogger(__name__)
MACHINE_VERSION = "p1-e1-fixed-mode-machine-v1"
ADAPTER_ID = "p1-e1-mode-whole-table-v1"
CONTROL_STATES = ("base", "marked")
RESIDUES = ("zero", "L", "R")
COUPLINGS = ("left", "right", "tick", "reset")
RESPONSES = ("idle", "branch-L", "branch-R", "effect-L", "effect-R", "reset")


def _reject(reason: str) -> None:
    logger.error("observer genesis adapter rejected reason=%s", reason)
    raise ObserverGenesisValidationError(reason)


def _row(control: str, residue: str, coupling: str) -> TransitionRow:
    logger.debug("_row entry q=%s r=%s c=%s", control, residue, coupling)
    if coupling == "reset":
        result = TransitionRow(control, residue, coupling, "base", "zero", "reset")
    elif (control, residue, coupling) == ("base", "zero", "left"):
        result = TransitionRow(control, residue, coupling, "base", "L", "branch-L")
    elif (control, residue, coupling) == ("base", "zero", "right"):
        result = TransitionRow(control, residue, coupling, "base", "R", "branch-R")
    elif (control, residue, coupling) == ("base", "L", "tick"):
        result = TransitionRow(control, residue, coupling, "marked", "L", "effect-L")
    elif (control, residue, coupling) == ("base", "R", "tick"):
        result = TransitionRow(control, residue, coupling, "base", "R", "effect-R")
    else:
        result = TransitionRow(control, residue, coupling, control, residue, "idle")
    logger.debug("_row exit response=%s", result.response)
    return result


def _origin_mode_only(value: Mode) -> None:
    logger.debug("_origin_mode_only entry")
    if type(value) is not Mode or type(value.breath.tacts) is not tuple or len(value.breath.tacts) != 1:
        _reject("adapter-requires-exact-origin-mode")
    tact = value.breath.tacts[0]
    if (
        value.observer != "native-cycle" or type(tact) is not Tact
        or type(tact.start) is not Nod or type(tact.end) is not Nod
        or type(tact.start.residue) is not Rez or type(tact.end.residue) is not Rez
        or tact.start.residue.name != "origin" or tact.end.residue.name != "origin"
        or tact.start.mark != "origin" or tact.end.mark != "origin"
        or tact.mark != "cycle" or tact.start != tact.end
    ):
        _reject("adapter-requires-exact-origin-mode")
    logger.debug("_origin_mode_only exit")


def _derive_machine(value: Mode) -> FiniteObserverMachine:
    """Derive a fresh canonical table from only one freshly replayed Mode."""
    logger.debug("_derive_machine entry")
    _origin_mode_only(value)
    rows = tuple(
        _row(control, residue, coupling)
        for control in CONTROL_STATES
        for residue in RESIDUES
        for coupling in COUPLINGS
    )
    provisional = FiniteObserverMachine(
        MACHINE_VERSION, CONTROL_STATES, RESIDUES, COUPLINGS, RESPONSES,
        MachineState("base", "zero"), rows, "0" * 64,
    )
    result = FiniteObserverMachine(
        provisional.version, tuple(item for item in provisional.control_states),
        tuple(item for item in provisional.residues),
        tuple(item for item in provisional.couplings),
        tuple(item for item in provisional.responses),
        MachineState(provisional.initial_state.control, provisional.initial_state.residue),
        tuple(TransitionRow(
            row.control, row.residue, row.coupling, row.next_control,
            row.next_residue, row.response,
        ) for row in rows),
        machine_digest(provisional),
    )
    logger.debug("_derive_machine exit rows=%d", len(result.rows))
    return result


def _snapshot_state(value: MachineState, field: str) -> MachineState:
    logger.debug("_snapshot_state entry field=%s", field)
    if type(value) is not MachineState:
        _reject(f"{field}-must-be-exact-machine-state")
    try:
        result = MachineState(
            exact_text(value.control, f"{field}-control"),
            exact_text(value.residue, f"{field}-residue"),
        )
    except AttributeError:
        _reject(f"{field}-missing-fields")
    logger.debug("_snapshot_state exit field=%s", field)
    return result


def _alphabet(value: tuple[str, ...], expected: tuple[str, ...], field: str) -> tuple[str, ...]:
    logger.debug("_alphabet entry field=%s", field)
    if type(value) is not tuple or len(value) != len(expected):
        _reject(f"finite-machine-{field}-alphabet-shape-drift")
    result = tuple(exact_text(item, f"machine-{field}-symbol") for item in value)
    if any(item != want for item, want in zip(result, expected, strict=True)):
        _reject(f"finite-machine-{field}-alphabet-order-drift")
    logger.debug("_alphabet exit field=%s", field)
    return result


def snapshot_transition(value: TransitionRow) -> TransitionRow:
    """Capture one exact typed transition row."""
    logger.debug("snapshot_transition entry")
    if type(value) is not TransitionRow:
        _reject("transition-row-must-be-exact")
    try:
        values = (
            exact_text(value.control, "transition-control"),
            exact_text(value.residue, "transition-residue"),
            exact_text(value.coupling, "transition-coupling"),
            exact_text(value.next_control, "transition-next-control"),
            exact_text(value.next_residue, "transition-next-residue"),
            exact_text(value.response, "transition-response"),
        )
    except AttributeError:
        _reject("transition-row-missing-fields")
    result = TransitionRow(*values)
    logger.debug("snapshot_transition exit")
    return result


def snapshot_machine(value: FiniteObserverMachine) -> FiniteObserverMachine:
    """Deep-capture exact total-table semantics and reject order/key drift."""
    logger.debug("snapshot_machine entry")
    if type(value) is not FiniteObserverMachine:
        _reject("finite-machine-must-be-exact")
    try:
        version = exact_text(value.version, "machine-version")
        alphabets = (
            _alphabet(value.control_states, CONTROL_STATES, "control"),
            _alphabet(value.residues, RESIDUES, "residue"),
            _alphabet(value.couplings, COUPLINGS, "coupling"),
            _alphabet(value.responses, RESPONSES, "response"),
        )
        initial = _snapshot_state(value.initial_state, "machine-initial")
        raw_rows, supplied = value.rows, hex_digest(value.machine_digest, "machine-digest")
    except AttributeError:
        _reject("finite-machine-missing-fields")
    if version != MACHINE_VERSION:
        _reject("finite-machine-ordered-alphabet-drift")
    if (
        initial.control != "base" or initial.residue != "zero"
        or type(raw_rows) is not tuple or len(raw_rows) != 24
    ):
        _reject("finite-machine-initial-or-row-count-drift")
    rows = tuple(snapshot_transition(row) for row in raw_rows)
    expected_keys = tuple(
        (q, r, c) for q in CONTROL_STATES for r in RESIDUES for c in COUPLINGS
    )
    actual_keys = tuple((row.control, row.residue, row.coupling) for row in rows)
    if actual_keys != expected_keys:
        _reject("finite-machine-key-coverage-or-order-drift")
    for row in rows:
        if (
            row.next_control not in CONTROL_STATES or row.next_residue not in RESIDUES
            or row.response not in RESPONSES
        ):
            _reject("finite-machine-foreign-result")
    provisional = FiniteObserverMachine(
        version, alphabets[0], alphabets[1], alphabets[2], alphabets[3],
        initial, rows, "0" * 64,
    )
    expected_digest = machine_digest(provisional)
    if supplied != expected_digest:
        _reject("finite-machine-digest-drift")
    result = FiniteObserverMachine(
        provisional.version, provisional.control_states, provisional.residues,
        provisional.couplings, provisional.responses, provisional.initial_state,
        provisional.rows, expected_digest,
    )
    logger.debug("snapshot_machine exit")
    return result


def compare_with_derived(captured: FiniteObserverMachine, derived: FiniteObserverMachine) -> None:
    """Compare all semantic fields explicitly, not only a digest."""
    logger.debug("compare_with_derived entry")
    if (
        captured.version != derived.version
        or captured.control_states != derived.control_states
        or captured.residues != derived.residues
        or captured.couplings != derived.couplings
        or captured.responses != derived.responses
        or captured.initial_state != derived.initial_state
        or captured.rows != derived.rows
    ):
        _reject("captured-machine-not-whole-table-adapter-output")
    logger.debug("compare_with_derived exit")
