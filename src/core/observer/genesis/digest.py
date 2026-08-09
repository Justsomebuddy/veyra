"""Counted, domain-separated commitments for P1-E1."""

from __future__ import annotations

from hashlib import sha256
import logging

from ...native_runtime import Mode
from .types import (
    FiniteObserverMachine, GenesisResourcePolicy, MachineState, ModeSpec,
    OEPAdmissionRecord, ObserverGenesisDoctrine, ObserverGenesisSource,
    PremiseName, PremiseStatus, RecurrenceEvidence, RecurrenceWitness,
    TransitionRow, WitnessScope,
)

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

def _token(digest: object, tag: bytes, value: bytes) -> None:
    logger.debug("_token entry tag=%d bytes=%d", len(tag), len(value))
    digest.update(len(tag).to_bytes(4, "big"))  # type: ignore[attr-defined]
    digest.update(tag)  # type: ignore[attr-defined]
    digest.update(len(value).to_bytes(8, "big"))  # type: ignore[attr-defined]
    digest.update(value)  # type: ignore[attr-defined]
    logger.debug("_token exit")

def tagged_digest(domain: str, fields: tuple[tuple[str, bytes], ...]) -> str:
    """Hash an exact tagged, length-prefixed, field-counted stream."""
    logger.debug("tagged_digest entry domain=%s count=%d", domain, len(fields))
    digest = sha256()
    _token(digest, b"domain", domain.encode())
    _token(digest, b"field-count", len(fields).to_bytes(8, "big"))
    for tag, value in fields:
        _token(digest, tag.encode(), value)
    result = digest.hexdigest()
    logger.debug("tagged_digest exit domain=%s", domain)
    return result

def _nat(value: int) -> bytes:
    logger.debug("_nat entry")
    if type(value) is not int or value < 0 or value.bit_length() > 64:
        raise ValueError("canonical natural must be an exact bounded nonnegative integer")
    logger.debug("_nat validated bits=%d", value.bit_length())
    result = value.to_bytes(max(1, (value.bit_length() + 7) // 8), "big")
    logger.debug("_nat exit bytes=%d", len(result))
    return result

def genealogy_digest(spec: ModeSpec) -> str:
    """Commit the full ordered primitive genealogy AST."""
    logger.debug("genealogy_digest entry tacts=%d", len(spec.breath.tacts))
    fields: list[tuple[str, bytes]] = [("version", spec.version.encode())]
    fields.append(("tact-count", _nat(len(spec.breath.tacts))))
    for index, tact in enumerate(spec.breath.tacts):
        prefix = f"tact-{index}"
        fields.extend((
            (f"{prefix}-start-rez", tact.start.residue.name.encode()),
            (f"{prefix}-start-mark", tact.start.mark.encode()),
            (f"{prefix}-end-rez", tact.end.residue.name.encode()),
            (f"{prefix}-end-mark", tact.end.mark.encode()),
            (f"{prefix}-mark", tact.mark.encode()),
        ))
    result = tagged_digest("veyra.p1e1.genealogy.v1", tuple(fields))
    logger.debug("genealogy_digest exit")
    return result

def replayed_mode_digest(value: Mode) -> str:
    """Commit only the freshly replayed native Mode identity."""
    logger.debug("replayed_mode_digest entry")
    fields: list[tuple[str, bytes]] = [("observer", value.observer.encode())]
    fields.append(("tact-count", _nat(len(value.breath.tacts))))
    for index, tact in enumerate(value.breath.tacts):
        prefix = f"tact-{index}"
        fields.extend((
            (f"{prefix}-start-rez", tact.start.residue.name.encode()),
            (f"{prefix}-start-mark", tact.start.mark.encode()),
            (f"{prefix}-end-rez", tact.end.residue.name.encode()),
            (f"{prefix}-end-mark", tact.end.mark.encode()),
            (f"{prefix}-mark", tact.mark.encode()),
        ))
    result = tagged_digest("veyra.p1e1.native-mode.v1", tuple(fields))
    logger.debug("replayed_mode_digest exit")
    return result

def machine_digest(value: FiniteObserverMachine) -> str:
    """Commit all ordered alphabets, initial pair, and semantic rows."""
    logger.debug("machine_digest entry rows=%d", len(value.rows))
    fields: list[tuple[str, bytes]] = [("version", value.version.encode())]
    for name, symbols in (
        ("control", value.control_states), ("residue", value.residues),
        ("coupling", value.couplings), ("response", value.responses),
    ):
        fields.append((f"{name}-count", _nat(len(symbols))))
        fields.extend((f"{name}-{i}", item.encode()) for i, item in enumerate(symbols))
    fields.extend((
        ("initial-control", value.initial_state.control.encode()),
        ("initial-residue", value.initial_state.residue.encode()),
        ("row-count", _nat(len(value.rows))),
    ))
    for index, row in enumerate(value.rows):
        prefix = f"row-{index}"
        fields.extend((
            (f"{prefix}-q", row.control.encode()),
            (f"{prefix}-r", row.residue.encode()),
            (f"{prefix}-c", row.coupling.encode()),
            (f"{prefix}-q2", row.next_control.encode()),
            (f"{prefix}-r2", row.next_residue.encode()),
            (f"{prefix}-response", row.response.encode()),
        ))
    result = tagged_digest("veyra.p1e1.machine.v1", tuple(fields))
    logger.debug("machine_digest exit")
    return result

def policy_digest(value: GenesisResourcePolicy) -> str:
    logger.debug("policy_digest entry")
    fields = (
        ("version", value.version.encode()),
        ("transition-rows", _nat(value.max_transition_rows)),
        ("reachability", _nat(value.max_reachability_checks)),
        ("continuation", _nat(value.max_continuation_steps)),
        ("return", _nat(value.max_return_word_steps)),
        ("response", _nat(value.max_response_checks)),
        ("bytes", _nat(value.max_encoded_bytes)),
    )
    result = tagged_digest("veyra.p1e1.policy.v1", fields)
    logger.debug("policy_digest exit")
    return result

def doctrine_digest(value: ObserverGenesisDoctrine) -> str:
    logger.debug("doctrine_digest entry")
    result = tagged_digest("veyra.p1e1.doctrine.v1", (
        ("version", value.version.encode()), ("id", value.doctrine_id.encode()),
        ("policy", value.policy.policy_digest.encode()),
    ))
    logger.debug("doctrine_digest exit")
    return result

def adapter_digest(adapter_id: str, native: str, machine: str) -> str:
    logger.debug("adapter_digest entry")
    result = tagged_digest("veyra.p1e1.adapter.v1", (
        ("id", adapter_id.encode()), ("native-mode", native.encode()),
        ("machine", machine.encode()),
    ))
    logger.debug("adapter_digest exit")
    return result

def source_digest(value: ObserverGenesisSource) -> str:
    logger.debug("source_digest entry")
    result = tagged_digest("veyra.p1e1.source.v1", (
        ("version", value.version.encode()),
        ("doctrine", value.doctrine_digest.encode()),
        ("genealogy", value.genealogy_digest.encode()),
        ("native-mode", value.native_mode_digest.encode()),
        ("adapter-id", value.adapter_id.encode()),
        ("adapter", value.adapter_digest.encode()),
        ("machine", value.machine_digest.encode()),
        ("closure-law", value.closure_law_id.encode()),
        ("recurrence-law", value.recurrence_law_id.encode()),
    ))
    logger.debug("source_digest exit")
    return result

def witness_digest(value: WitnessScope) -> str:
    logger.debug("witness_digest entry")
    fields = [
        ("version", value.version.encode()), ("source", value.source_digest.encode()),
        ("q", value.branch_state.control.encode()),
        ("r", value.branch_state.residue.encode()),
        ("left", value.left_coupling.encode()), ("right", value.right_coupling.encode()),
        ("h", _nat(value.persistence_horizon)), ("j", _nat(value.efficacy_index)),
        ("continuation-count", _nat(len(value.common_continuation))),
    ]
    fields.extend((f"continuation-{i}", item.encode()) for i, item in enumerate(value.common_continuation))
    result = tagged_digest("veyra.p1e1.witness.v1", tuple(fields))
    logger.debug("witness_digest exit")
    return result

def recurrence_digest(value: RecurrenceWitness) -> str:
    logger.debug("recurrence_digest entry")
    fields = [
        ("version", value.version.encode()), ("source", value.source_digest.encode()),
        ("witness", value.witness_digest.encode()),
        ("left-count", _nat(len(value.left_return_word))),
    ]
    fields.extend((f"left-{i}", item.encode()) for i, item in enumerate(value.left_return_word))
    fields.append(("right-count", _nat(len(value.right_return_word))))
    fields.extend((f"right-{i}", item.encode()) for i, item in enumerate(value.right_return_word))
    result = tagged_digest("veyra.p1e1.recurrence.v1", tuple(fields))
    logger.debug("recurrence_digest exit")
    return result

def oep_digest(value: OEPAdmissionRecord) -> str:
    logger.debug("oep_digest entry")
    result = tagged_digest("veyra.p1e1.oep.v1", (
        ("version", value.version.encode()), ("doctrine", value.doctrine_digest.encode()),
        ("principle", value.principle_id.encode()),
        ("admission", value.admission.value.encode()),
    ))
    logger.debug("oep_digest exit")
    return result

def request_digest(source: str, witness: str, recurrence: str, oep: str) -> str:
    logger.debug("request_digest entry")
    result = tagged_digest("veyra.p1e1.run.v1", (
        ("source", source.encode()), ("witness", witness.encode()),
        ("recurrence", recurrence.encode()), ("oep", oep.encode()),
    ))
    logger.debug("request_digest exit")
    return result

def evidence_digest(
    premise: PremiseName, status: PremiseStatus,
    rows: tuple[TransitionRow, ...], states: tuple[MachineState, ...],
) -> str:
    logger.debug("evidence_digest entry premise=%s", premise.value)
    fields: list[tuple[str, bytes]] = [
        ("premise", premise.value.encode()), ("status", status.value.encode()),
        ("row-count", _nat(len(rows))), ("state-count", _nat(len(states))),
    ]
    for index, row in enumerate(rows):
        prefix = f"row-{index}"
        fields.extend((
            (f"{prefix}-q", row.control.encode()),
            (f"{prefix}-r", row.residue.encode()),
            (f"{prefix}-c", row.coupling.encode()),
            (f"{prefix}-q2", row.next_control.encode()),
            (f"{prefix}-r2", row.next_residue.encode()),
            (f"{prefix}-response", row.response.encode()),
        ))
    for index, state in enumerate(states):
        fields.extend((
            (f"state-{index}-q", state.control.encode()),
            (f"state-{index}-r", state.residue.encode()),
        ))
    result = tagged_digest("veyra.p1e1.premise.v1", tuple(fields))
    logger.debug("evidence_digest exit")
    return result

def refusal_digest(run: str, bound: str, required: int, allowed: int) -> str:
    logger.debug("refusal_digest entry bound=%s", bound)
    result = tagged_digest("veyra.p1e1.refusal.v1", (
        ("run", run.encode()), ("bound", bound.encode()),
        ("required", _nat(required)), ("allowed", _nat(allowed)),
    ))
    logger.debug("refusal_digest exit")
    return result

def judgment_digest(
    run: str, premise_digests: tuple[str, ...], role: str,
) -> str:
    """Commit the ordered fresh premise ledger and doctrine-relative role."""
    logger.debug("judgment_digest entry premises=%d", len(premise_digests))
    fields: list[tuple[str, bytes]] = [
        ("run", run.encode()), ("role", role.encode()),
        ("premise-count", _nat(len(premise_digests))),
    ]
    fields.extend((f"premise-{i}", item.encode()) for i, item in enumerate(premise_digests))
    result = tagged_digest("veyra.p1e1.judgment.v1", tuple(fields))
    logger.debug("judgment_digest exit")
    return result

def encoded_request_bytes(
    source: ObserverGenesisSource, witness: WitnessScope,
    recurrence: RecurrenceEvidence, oep: OEPAdmissionRecord,
) -> int:
    """Return exact bytes for the bounded canonical request envelope."""
    logger.debug("encoded_request_bytes entry")
    recurrence_fields = (
        (*recurrence.left_return_word, *recurrence.right_return_word)
        if type(recurrence) is RecurrenceWitness else (recurrence.reason_id,)
    )
    strings = (
        source.source_digest, source.adapter_digest, witness.witness_digest,
        recurrence.recurrence_digest, oep.oep_digest,
        *witness.common_continuation, *recurrence_fields,
    )
    result = 8 + sum(4 + len(item.encode()) for item in strings)
    logger.debug("encoded_request_bytes exit bytes=%d", result)
    return result

