"""Fresh BFS and scoped OEP premise derivation for P1-E1."""

from __future__ import annotations

from collections import deque
import logging

from .digest import evidence_digest
from .native import ObserverGenesisValidationError
from .types import (
    FiniteObserverMachine, MachineState, PremiseArtifact, PremiseName,
    PremiseStatus, RecurrenceEvidence, RecurrenceWitness, TransitionRow,
    WitnessScope,
)

logger = logging.getLogger(__name__)


def _table(machine: FiniteObserverMachine) -> dict[tuple[str, str, str], TransitionRow]:
    logger.debug("_table entry rows=%d", len(machine.rows))
    result = {
        (row.control, row.residue, row.coupling): row for row in machine.rows
    }
    if len(result) != len(machine.rows):
        raise ObserverGenesisValidationError("machine-table-duplicate-key")
    logger.debug("_table exit")
    return result


def _step(
    table: dict[tuple[str, str, str], TransitionRow],
    state: MachineState, coupling: str,
) -> tuple[MachineState, TransitionRow]:
    logger.debug("_step entry q=%s r=%s c=%s", state.control, state.residue, coupling)
    row = table[(state.control, state.residue, coupling)]
    result = MachineState(row.next_control, row.next_residue), TransitionRow(
        row.control, row.residue, row.coupling, row.next_control,
        row.next_residue, row.response,
    )
    logger.debug("_step exit q=%s r=%s", result[0].control, result[0].residue)
    return result


def _path(
    table: dict[tuple[str, str, str], TransitionRow], start: MachineState,
    word: tuple[str, ...],
) -> tuple[tuple[MachineState, ...], tuple[TransitionRow, ...]]:
    logger.debug("_path entry steps=%d", len(word))
    states = [MachineState(start.control, start.residue)]
    rows: list[TransitionRow] = []
    current = states[0]
    for coupling in word:
        current, row = _step(table, current, coupling)
        states.append(current)
        rows.append(row)
    result = tuple(states), tuple(rows)
    logger.debug("_path exit")
    return result


def reachable_states(machine: FiniteObserverMachine) -> tuple[MachineState, ...]:
    """Derive reachable pairs by bounded BFS in canonical coupling order."""
    logger.debug("reachable_states entry")
    table = _table(machine)
    initial = MachineState(machine.initial_state.control, machine.initial_state.residue)
    queue: deque[MachineState] = deque((initial,))
    seen = {(initial.control, initial.residue)}
    ordered = [initial]
    while queue:
        current = queue.popleft()
        for coupling in machine.couplings:
            nxt, _ = _step(table, current, coupling)
            key = (nxt.control, nxt.residue)
            if key not in seen:
                seen.add(key)
                ordered.append(nxt)
                queue.append(nxt)
    result = tuple(ordered)
    logger.debug("reachable_states exit count=%d", len(result))
    return result


def _artifact(
    premise: PremiseName, status: PremiseStatus,
    rows: tuple[TransitionRow, ...], states: tuple[MachineState, ...],
) -> PremiseArtifact:
    logger.debug("_artifact entry premise=%s status=%s", premise.value, status.value)
    fresh_rows = tuple(TransitionRow(
        row.control, row.residue, row.coupling, row.next_control,
        row.next_residue, row.response,
    ) for row in rows)
    fresh_states = tuple(MachineState(item.control, item.residue) for item in states)
    result = PremiseArtifact(
        premise, status, fresh_rows, fresh_states,
        evidence_digest(premise, status, fresh_rows, fresh_states),
    )
    logger.debug("_artifact exit premise=%s", premise.value)
    return result


def derive_premises(
    machine: FiniteObserverMachine, witness: WitnessScope,
    recurrence: RecurrenceEvidence,
) -> tuple[PremiseArtifact, ...]:
    """Freshly derive all six independent premise artifacts on one exact scope."""
    logger.debug("derive_premises entry")
    table = _table(machine)
    reachable = reachable_states(machine)
    reachable_keys = {(item.control, item.residue) for item in reachable}
    branch = MachineState(witness.branch_state.control, witness.branch_state.residue)
    left_state, left_branch_row = _step(table, branch, witness.left_coupling)
    right_state, right_branch_row = _step(table, branch, witness.right_coupling)
    left_states, left_rows = _path(
        table, left_state, witness.common_continuation,
    )
    right_states, right_rows = _path(
        table, right_state, witness.common_continuation,
    )
    if type(recurrence) is RecurrenceWitness:
        left_return_states, left_return_rows = _path(
            table, branch, recurrence.left_return_word,
        )
        right_return_states, right_return_rows = _path(
            table, branch, recurrence.right_return_word,
        )
        recurrent_status = (
            PremiseStatus.ESTABLISHED
            if left_return_states[-1] == branch and right_return_states[-1] == branch
            else PremiseStatus.REFUTED
        )
    else:
        left_return_states = right_return_states = (branch,)
        left_return_rows = right_return_rows = ()
        recurrent_status = PremiseStatus.OPEN
    all_states = (
        (branch, left_state, right_state) + left_states + right_states
        + left_return_states + right_return_states
    )
    if any((item.control, item.residue) not in reachable_keys for item in all_states):
        raise ObserverGenesisValidationError("witness-evidence-state-unreachable")
    discrimination = (
        left_state.control == right_state.control
        and left_state.residue != right_state.residue
    )
    persistence = all(
        left.residue != right.residue
        for left, right in zip(left_states, right_states, strict=True)
    )
    index = witness.efficacy_index - 1
    left_pre, right_pre = left_states[index], right_states[index]
    left_effect, right_effect = left_rows[index], right_rows[index]
    efficacy = (
        left_pre.control == right_pre.control
        and left_pre.residue != right_pre.residue
        and left_effect.coupling == right_effect.coupling
        and (
            left_effect.next_control != right_effect.next_control
            or left_effect.response != right_effect.response
        )
    )
    established = PremiseStatus.ESTABLISHED
    statuses = (
        established,
        established,
        recurrent_status,
        established if discrimination else PremiseStatus.REFUTED,
        established if persistence else PremiseStatus.REFUTED,
        established if efficacy else PremiseStatus.REFUTED,
    )
    artifacts = (
        _artifact(PremiseName.PRIMITIVE_GENEALOGY, statuses[0], (), (machine.initial_state,)),
        _artifact(PremiseName.STRUCTURAL_CLOSURE, statuses[1], (), reachable),
        _artifact(
            PremiseName.RECURRENT_RETURN, statuses[2],
            left_return_rows + right_return_rows,
            left_return_states + right_return_states,
        ),
        _artifact(
            PremiseName.COUNTERFACTUAL_DISCRIMINATION, statuses[3],
            (left_branch_row, right_branch_row), (branch, left_state, right_state),
        ),
        _artifact(
            PremiseName.BOUNDED_PERSISTENCE, statuses[4],
            (left_branch_row, right_branch_row) + left_rows + right_rows,
            left_states + right_states,
        ),
        _artifact(
            PremiseName.RESIDUE_EFFICACY, statuses[5],
            (left_effect, right_effect),
            (left_pre, right_pre, left_states[index + 1], right_states[index + 1]),
        ),
    )
    logger.debug("derive_premises exit")
    return artifacts
