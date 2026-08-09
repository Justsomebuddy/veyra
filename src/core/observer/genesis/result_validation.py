"""Fail-fast raw-source/result revalidation for P1-E1."""

from __future__ import annotations

import logging

from .native import ObserverGenesisValidationError
from .runtime import observer_genesis_judgment
from .types import (
    GenesisJudgment, GenesisOperation, GenesisOperationStatus,
    GenesisResourceLimit, GenesisResult,
    HistoricalTargetIndependence, MachineState, OEPAdmissionRecord,
    ObserverGenesisDoctrine, ObserverGenesisSource, ObserverRole,
    PhysicalInstantiation, PremiseArtifact, PremiseName, PremiseStatus,
    RecurrenceEvidence, TransitionRow, WitnessScope,
)

logger = logging.getLogger(__name__)


def _reject(reason: str) -> None:
    logger.error("observer genesis result rejected reason=%s", reason)
    raise ObserverGenesisValidationError(reason)


def _permanent(value: object) -> None:
    logger.debug("_permanent entry")
    try:
        history = value.historical_target_independence
        physical = value.physical_instantiation
        scope = value.scope
    except AttributeError:
        _reject("genesis-result-permanent-fields-missing")
    expected_scope = (
        "finite-doctrine-relative-oep-role-only"
        if type(value) is GenesisJudgment
        else "resource-refusal-no-partial-genesis-evidence"
    )
    if (
        type(history) is not HistoricalTargetIndependence
        or history is not HistoricalTargetIndependence.NOT_ESTABLISHED
        or type(physical) is not PhysicalInstantiation
        or physical is not PhysicalInstantiation.NOT_ESTABLISHED
        or type(scope) is not str or scope != expected_scope
    ):
        _reject("genesis-result-permanent-field-drift")
    logger.debug("_permanent exit")


def _resource(value: GenesisResourceLimit, expected: GenesisResourceLimit) -> None:
    logger.debug("_resource entry")
    if type(value) is not GenesisResourceLimit:
        _reject("genesis-resource-result-must-be-exact")
    try:
        enum_fields = (value.operation, value.failed_bound, value.operation_status)
        integers = (value.required_value, value.allowed_value)
        digests = (
            value.doctrine_digest, value.source_digest, value.adapter_digest,
            value.witness_digest, value.recurrence_digest, value.oep_digest,
            value.run_digest, value.refusal_digest,
        )
    except AttributeError:
        _reject("genesis-resource-result-missing-fields")
    expected_enums = (
        GenesisOperation.JUDGMENT, expected.failed_bound,
        GenesisOperationStatus.RESOURCE_LIMIT,
    )
    expected_integers = (expected.required_value, expected.allowed_value)
    expected_digests = (
        expected.doctrine_digest, expected.source_digest, expected.adapter_digest,
        expected.witness_digest, expected.recurrence_digest, expected.oep_digest,
        expected.run_digest, expected.refusal_digest,
    )
    _permanent(value)
    if (
        any(type(item) is not type(want) or item is not want for item, want in zip(enum_fields, expected_enums, strict=True))
        or any(type(item) is not int or item != want for item, want in zip(integers, expected_integers, strict=True))
        or any(type(item) is not str or item != want for item, want in zip(digests, expected_digests, strict=True))
        or hasattr(value, "premises") or hasattr(value, "trace")
    ):
        _reject("genesis-resource-result-outer-precheck-drift")
    logger.debug("_resource exit")


def _row(value: TransitionRow, expected: TransitionRow) -> None:
    logger.debug("_row entry")
    if type(value) is not TransitionRow:
        _reject("genesis-premise-transition-must-be-exact")
    try:
        fields = (
            value.control, value.residue, value.coupling, value.next_control,
            value.next_residue, value.response,
        )
    except AttributeError:
        _reject("genesis-premise-transition-missing-fields")
    wanted = (
        expected.control, expected.residue, expected.coupling,
        expected.next_control, expected.next_residue, expected.response,
    )
    if any(type(item) is not str or item != want for item, want in zip(fields, wanted, strict=True)):
        _reject("genesis-premise-transition-drift")
    logger.debug("_row exit")


def _state(value: MachineState, expected: MachineState) -> None:
    logger.debug("_state entry")
    if type(value) is not MachineState:
        _reject("genesis-premise-state-must-be-exact")
    try:
        fields = (value.control, value.residue)
    except AttributeError:
        _reject("genesis-premise-state-missing-fields")
    if (
        type(fields[0]) is not str or fields[0] != expected.control
        or type(fields[1]) is not str or fields[1] != expected.residue
    ):
        _reject("genesis-premise-state-drift")
    logger.debug("_state exit")


def _premise_outer(
    value: PremiseArtifact, expected: PremiseArtifact,
) -> tuple[tuple[TransitionRow, ...], tuple[MachineState, ...]]:
    logger.debug("_premise_outer entry premise=%s", expected.premise.value)
    if type(value) is not PremiseArtifact:
        _reject("genesis-premise-artifact-must-be-exact")
    try:
        premise, status = value.premise, value.status
        rows, states, digest = value.rows, value.states, value.evidence_digest
    except AttributeError:
        _reject("genesis-premise-artifact-missing-fields")
    if (
        type(premise) is not PremiseName or premise is not expected.premise
        or type(status) is not PremiseStatus or status is not expected.status
        or type(digest) is not str or digest != expected.evidence_digest
        or type(rows) is not tuple or len(rows) != len(expected.rows)
        or type(states) is not tuple or len(states) != len(expected.states)
    ):
        _reject("genesis-premise-artifact-outer-precheck-drift")
    logger.debug("_premise_outer exit premise=%s", expected.premise.value)
    return rows, states


def _premise(value: PremiseArtifact, expected: PremiseArtifact) -> None:
    logger.debug("_premise entry premise=%s", expected.premise.value)
    rows, states = _premise_outer(value, expected)
    for row, wanted in zip(rows, expected.rows, strict=True):
        _row(row, wanted)
    for state, wanted in zip(states, expected.states, strict=True):
        _state(state, wanted)
    logger.debug("_premise exit premise=%s", expected.premise.value)


def _judgment(value: GenesisJudgment, expected: GenesisJudgment) -> None:
    logger.debug("_judgment entry")
    if type(value) is not GenesisJudgment:
        _reject("genesis-judgment-must-be-exact")
    try:
        digests = (
            value.doctrine_digest, value.source_digest, value.adapter_digest,
            value.witness_digest, value.recurrence_digest, value.oep_digest,
            value.run_digest, value.judgment_digest,
        )
        statuses = (
            value.primitive_genealogy, value.structural_closure,
            value.recurrent_return, value.counterfactual_discrimination,
            value.bounded_persistence, value.residue_efficacy,
        )
        operation, role, premises = (
            value.operation_status, value.observer_role_relative_to_scope,
            value.premises,
        )
    except AttributeError:
        _reject("genesis-judgment-missing-fields")
    expected_digests = (
        expected.doctrine_digest, expected.source_digest, expected.adapter_digest,
        expected.witness_digest, expected.recurrence_digest, expected.oep_digest,
        expected.run_digest, expected.judgment_digest,
    )
    expected_statuses = tuple(item.status for item in expected.premises)
    _permanent(value)
    if (
        any(type(item) is not str or item != want for item, want in zip(digests, expected_digests, strict=True))
        or any(type(item) is not PremiseStatus or item is not want for item, want in zip(statuses, expected_statuses, strict=True))
        or type(operation) is not GenesisOperationStatus
        or operation is not GenesisOperationStatus.JUDGED
        or type(role) is not ObserverRole or role is not expected.observer_role_relative_to_scope
        or type(premises) is not tuple or len(premises) != 6
    ):
        _reject("genesis-judgment-outer-precheck-drift")
    for item, wanted in zip(premises, expected.premises, strict=True):
        _premise_outer(item, wanted)
    for item, wanted in zip(premises, expected.premises, strict=True):
        _premise(item, wanted)
    logger.debug("_judgment exit")


def validate_genesis_result(
    doctrine: ObserverGenesisDoctrine, source: ObserverGenesisSource,
    witness: WitnessScope, recurrence: RecurrenceEvidence,
    oep: OEPAdmissionRecord, value: GenesisResult,
) -> GenesisResult:
    """Replay every raw input, rederive all evidence, and return a fresh result."""
    logger.debug("validate_genesis_result entry")
    expected = observer_genesis_judgment(doctrine, source, witness, recurrence, oep)
    if type(value) is not type(expected):
        _reject("genesis-result-union-variant-drift")
    if type(expected) is GenesisResourceLimit:
        _resource(value, expected)  # type: ignore[arg-type]
    else:
        _judgment(value, expected)  # type: ignore[arg-type]
    logger.debug("validate_genesis_result exit")
    return expected
