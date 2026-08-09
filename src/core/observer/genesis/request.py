"""Construction and exact validation of E1 witness and admission requests."""

from __future__ import annotations

import logging

from .digest import (
    oep_digest, recurrence_digest, tagged_digest, witness_digest,
)
from .native import ObserverGenesisValidationError, exact_text, hex_digest
from .types import (
    MachineState, OEPAdmission, OEPAdmissionRecord, ObserverGenesisDoctrine,
    ObserverGenesisSource, RecurrenceEvidence, RecurrenceWitness,
    UnavailableRecurrenceEvidence, WitnessScope,
)
from .validation import snapshot_doctrine

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

WITNESS_VERSION = "p1-e1-witness-v1"

RECURRENCE_VERSION = "p1-e1-recurrence-v1"

OEP_RECORD_VERSION = "p1-e1-oep-record-v1"

OEP_PRINCIPLE_ID = "p1-e1-oep-sufficient-v1"

MAX_CONTINUATION_LENGTH = 128

MAX_RETURN_WORD_LENGTH = 256

UNAVAILABLE_RECURRENCE_REASON = "not-supplied"

def _reject(reason: str) -> None:
    logger.error("observer genesis request rejected reason=%s", reason)
    raise ObserverGenesisValidationError(reason)

def _source_shell(value: ObserverGenesisSource) -> tuple[str, tuple[str, ...]]:
    logger.debug("_source_shell entry")
    if type(value) is not ObserverGenesisSource:
        _reject("witness-source-must-be-exact")
    try:
        digest = hex_digest(value.source_digest, "witness-source-digest")
        machine = value.machine
        couplings = machine.couplings
    except AttributeError:
        _reject("witness-source-missing-fields")
    if (
        type(couplings) is not tuple
        or any(type(item) is not str for item in couplings)
        or type(machine.control_states) is not tuple
        or any(type(item) is not str for item in machine.control_states)
        or type(machine.residues) is not tuple
        or any(type(item) is not str for item in machine.residues)
    ):
        _reject("witness-source-couplings-must-be-tuple")
    logger.debug("_source_shell exit")
    return digest, couplings

def _state(value: MachineState, source: ObserverGenesisSource) -> MachineState:
    logger.debug("_state entry")
    if type(value) is not MachineState:
        _reject("witness-branch-state-must-be-exact")
    try:
        result = MachineState(
            exact_text(value.control, "witness-control"),
            exact_text(value.residue, "witness-residue"),
        )
    except AttributeError:
        _reject("witness-branch-state-missing-fields")
    if result.control not in source.machine.control_states or result.residue not in source.machine.residues:
        _reject("witness-branch-state-foreign")
    logger.debug("_state exit")
    return result

def build_witness(
    source: ObserverGenesisSource, branch_state: MachineState,
    left_coupling: str, right_coupling: str,
    common_continuation: tuple[str, ...], persistence_horizon: int,
    efficacy_index: int, version: str = WITNESS_VERSION,
) -> WitnessScope:
    """Bind the exact branch, continuation, horizon, and efficacy quantifiers."""
    logger.debug("build_witness entry")
    source_digest_value, couplings = _source_shell(source)
    if type(version) is not str or version != WITNESS_VERSION:
        _reject("unknown-witness-version")
    branch = _state(branch_state, source)
    left = exact_text(left_coupling, "left-coupling")
    right = exact_text(right_coupling, "right-coupling")
    if left == right or left not in couplings or right not in couplings:
        _reject("witness-branch-couplings-invalid")
    if type(common_continuation) is not tuple or not 1 <= len(common_continuation) <= MAX_CONTINUATION_LENGTH:
        _reject("witness-continuation-invalid")
    continuation = tuple(exact_text(item, "continuation-coupling") for item in common_continuation)
    if any(item not in couplings for item in continuation):
        _reject("witness-continuation-foreign")
    if (
        type(persistence_horizon) is not int
        or persistence_horizon != len(continuation)
        or type(efficacy_index) is not int
        or not 1 <= efficacy_index <= persistence_horizon
    ):
        _reject("witness-horizon-or-efficacy-index-invalid")
    provisional = WitnessScope(
        version, source_digest_value, branch, left, right, continuation,
        persistence_horizon, efficacy_index, "0" * 64,
    )
    result = WitnessScope(
        provisional.version, provisional.source_digest, provisional.branch_state,
        provisional.left_coupling, provisional.right_coupling,
        provisional.common_continuation, provisional.persistence_horizon,
        provisional.efficacy_index, witness_digest(provisional),
    )
    logger.debug("build_witness exit")
    return result

def snapshot_witness(
    source: ObserverGenesisSource, value: WitnessScope,
) -> WitnessScope:
    """Rebind witness scope to the freshly replayed raw source."""
    logger.debug("snapshot_witness entry")
    if type(value) is not WitnessScope:
        _reject("witness-scope-must-be-exact")
    try:
        expected = build_witness(
            source, value.branch_state, value.left_coupling, value.right_coupling,
            value.common_continuation, value.persistence_horizon,
            value.efficacy_index, value.version,
        )
        supplied = (
            hex_digest(value.source_digest, "witness-source-digest"),
            hex_digest(value.witness_digest, "witness-digest"),
        )
    except AttributeError:
        _reject("witness-scope-missing-fields")
    if supplied != (expected.source_digest, expected.witness_digest):
        _reject("witness-scope-drift-or-transplant")
    logger.debug("snapshot_witness exit")
    return expected

def _word(value: tuple[str, ...], couplings: tuple[str, ...], field: str) -> tuple[str, ...]:
    logger.debug("_word entry field=%s", field)
    if type(value) is not tuple or not 1 <= len(value) <= MAX_RETURN_WORD_LENGTH:
        _reject(f"{field}-must-be-bounded-nonempty-tuple")
    result = tuple(exact_text(item, f"{field}-coupling") for item in value)
    if any(item not in couplings for item in result):
        _reject(f"{field}-contains-foreign-coupling")
    logger.debug("_word exit field=%s", field)
    return result

def build_recurrence(
    source: ObserverGenesisSource, witness: WitnessScope,
    left_return_word: tuple[str, ...], right_return_word: tuple[str, ...],
    version: str = RECURRENCE_VERSION,
) -> RecurrenceWitness:
    """Bind path-relevant nonempty return words to source and witness."""
    logger.debug("build_recurrence entry")
    source_digest_value, couplings = _source_shell(source)
    witness = snapshot_witness(source, witness)
    if type(version) is not str or version != RECURRENCE_VERSION:
        _reject("unknown-recurrence-version")
    left = _word(left_return_word, couplings, "left-return-word")
    right = _word(right_return_word, couplings, "right-return-word")
    if left[:1] != (witness.left_coupling,) or right[:1] != (witness.right_coupling,):
        _reject("return-word-must-start-with-branch-coupling")
    left_prefix = (witness.left_coupling,) + witness.common_continuation
    right_prefix = (witness.right_coupling,) + witness.common_continuation
    if left[:len(left_prefix)] != left_prefix or right[:len(right_prefix)] != right_prefix:
        _reject("return-word-must-traverse-exact-evidence-prefix")
    provisional = RecurrenceWitness(
        version, source_digest_value, witness.witness_digest, left, right, "0" * 64,
    )
    result = RecurrenceWitness(
        provisional.version, provisional.source_digest, provisional.witness_digest,
        provisional.left_return_word, provisional.right_return_word,
        recurrence_digest(provisional),
    )
    logger.debug("build_recurrence exit")
    return result

def build_unavailable_recurrence(
    source: ObserverGenesisSource, witness: WitnessScope,
    reason_id: str = UNAVAILABLE_RECURRENCE_REASON,
) -> UnavailableRecurrenceEvidence:
    """Bind explicit absence of recurrence evidence without semantic refutation."""
    logger.debug("build_unavailable_recurrence entry")
    source_digest_value, _ = _source_shell(source)
    witness = snapshot_witness(source, witness)
    if type(reason_id) is not str or reason_id != UNAVAILABLE_RECURRENCE_REASON:
        _reject("unknown-unavailable-recurrence-reason")
    digest = tagged_digest("veyra.p1e1.recurrence-open.v1", (
        ("version", RECURRENCE_VERSION.encode()),
        ("source", source_digest_value.encode()),
        ("witness", witness.witness_digest.encode()),
        ("reason", reason_id.encode()),
    ))
    result = UnavailableRecurrenceEvidence(
        RECURRENCE_VERSION, source_digest_value, witness.witness_digest,
        reason_id, digest,
    )
    logger.debug("build_unavailable_recurrence exit")
    return result

def snapshot_recurrence(
    source: ObserverGenesisSource, witness: WitnessScope,
    value: RecurrenceEvidence,
) -> RecurrenceEvidence:
    """Capture recurrence and reject source/witness transplants."""
    logger.debug("snapshot_recurrence entry")
    if type(value) is UnavailableRecurrenceEvidence:
        try:
            expected_open = build_unavailable_recurrence(source, witness, value.reason_id)
            supplied_open = (
                hex_digest(value.source_digest, "recurrence-source-digest"),
                hex_digest(value.witness_digest, "recurrence-witness-digest"),
                hex_digest(value.recurrence_digest, "recurrence-digest"),
            )
        except AttributeError:
            _reject("unavailable-recurrence-evidence-missing-fields")
        if supplied_open != (
            expected_open.source_digest, expected_open.witness_digest,
            expected_open.recurrence_digest,
        ) or type(value.version) is not str or value.version != RECURRENCE_VERSION:
            _reject("unavailable-recurrence-evidence-drift-or-transplant")
        logger.debug("snapshot_recurrence exit open")
        return expected_open
    if type(value) is not RecurrenceWitness:
        _reject("recurrence-witness-must-be-exact")
    try:
        expected = build_recurrence(
            source, witness, value.left_return_word, value.right_return_word,
            value.version,
        )
        supplied = (
            hex_digest(value.source_digest, "recurrence-source-digest"),
            hex_digest(value.witness_digest, "recurrence-witness-digest"),
            hex_digest(value.recurrence_digest, "recurrence-digest"),
        )
    except AttributeError:
        _reject("recurrence-witness-missing-fields")
    if supplied != (
        expected.source_digest, expected.witness_digest, expected.recurrence_digest,
    ):
        _reject("recurrence-witness-drift-or-transplant")
    logger.debug("snapshot_recurrence exit")
    return expected

def build_oep_record(
    doctrine: ObserverGenesisDoctrine, admission: OEPAdmission,
    version: str = OEP_RECORD_VERSION,
) -> OEPAdmissionRecord:
    """Build the own doctrine-bound OEP admission record."""
    logger.debug("build_oep_record entry")
    doctrine = snapshot_doctrine(doctrine)
    if type(version) is not str or version != OEP_RECORD_VERSION:
        _reject("unknown-oep-record-version")
    if type(admission) is not OEPAdmission:
        _reject("oep-admission-must-be-exact")
    provisional = OEPAdmissionRecord(
        version, doctrine.doctrine_digest, OEP_PRINCIPLE_ID, admission, "0" * 64,
    )
    result = OEPAdmissionRecord(
        provisional.version, provisional.doctrine_digest, provisional.principle_id,
        provisional.admission, oep_digest(provisional),
    )
    logger.debug("build_oep_record exit")
    return result

def snapshot_oep_record(
    doctrine: ObserverGenesisDoctrine, value: OEPAdmissionRecord,
) -> OEPAdmissionRecord:
    """Capture OEP admission and reject foreign doctrine records."""
    logger.debug("snapshot_oep_record entry")
    if type(value) is not OEPAdmissionRecord:
        _reject("oep-record-must-be-exact")
    try:
        if type(value.principle_id) is not str or value.principle_id != OEP_PRINCIPLE_ID:
            _reject("foreign-oep-principle")
        expected = build_oep_record(doctrine, value.admission, value.version)
        supplied = (
            hex_digest(value.doctrine_digest, "oep-doctrine-digest"),
            hex_digest(value.oep_digest, "oep-digest"),
        )
    except AttributeError:
        _reject("oep-record-missing-fields")
    if supplied != (expected.doctrine_digest, expected.oep_digest):
        _reject("oep-record-drift-or-transplant")
    logger.debug("snapshot_oep_record exit")
    return expected
