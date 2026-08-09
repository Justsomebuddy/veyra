"""Bounded shallow raw envelope validation before E1 semantic replay."""

from __future__ import annotations

import logging

from .adapter import (
    ADAPTER_ID, CONTROL_STATES, COUPLINGS, MACHINE_VERSION, RESIDUES, RESPONSES,
)
from .digest import adapter_digest, source_digest
from .native import (
    GENEALOGY_VERSION, MAX_GENEALOGY_TACTS, ObserverGenesisValidationError,
    hex_digest,
)
from .types import (
    BreathSpec, FiniteObserverMachine, MachineState, ModeSpec,
    ObserverGenesisDoctrine, ObserverGenesisSource,
)
from .validation import (
    CLOSURE_LAW_ID, RECURRENCE_LAW_ID, SOURCE_VERSION,
)

logger = logging.getLogger(__name__)


def _reject(reason: str) -> None:
    logger.error("observer genesis envelope rejected reason=%s", reason)
    raise ObserverGenesisValidationError(reason)


def _exact_alphabet(value: object, expected: tuple[str, ...]) -> bool:
    logger.debug("_exact_alphabet entry")
    result = (
        type(value) is tuple and len(value) == len(expected)
        and all(type(item) is str and item == want for item, want in zip(value, expected, strict=True))
    )
    logger.debug("_exact_alphabet exit result=%s", result)
    return result


def snapshot_source_envelope(
    doctrine: ObserverGenesisDoctrine, value: ObserverGenesisSource,
) -> ObserverGenesisSource:
    """Bind bounded outer raw fields without adapter/table/genealogy traversal."""
    logger.debug("snapshot_source_envelope entry")
    if type(value) is not ObserverGenesisSource:
        _reject("observer-genesis-source-must-be-exact")
    try:
        genealogy, machine = value.genealogy, value.machine
        if (
            type(value.version) is not str or value.version != SOURCE_VERSION
            or type(genealogy) is not ModeSpec
            or type(genealogy.version) is not str or genealogy.version != GENEALOGY_VERSION
            or type(genealogy.breath) is not BreathSpec
            or type(genealogy.breath.tacts) is not tuple
            or not 1 <= len(genealogy.breath.tacts) <= MAX_GENEALOGY_TACTS
            or type(machine) is not FiniteObserverMachine
            or type(machine.version) is not str or machine.version != MACHINE_VERSION
            or not _exact_alphabet(machine.control_states, CONTROL_STATES)
            or not _exact_alphabet(machine.residues, RESIDUES)
            or not _exact_alphabet(machine.couplings, COUPLINGS)
            or not _exact_alphabet(machine.responses, RESPONSES)
            or type(machine.initial_state) is not MachineState
            or type(machine.initial_state.control) is not str
            or machine.initial_state.control != "base"
            or type(machine.initial_state.residue) is not str
            or machine.initial_state.residue != "zero"
            or type(machine.rows) is not tuple or len(machine.rows) != 24
            or type(value.adapter_id) is not str or value.adapter_id != ADAPTER_ID
            or type(value.closure_law_id) is not str
            or value.closure_law_id != CLOSURE_LAW_ID
            or type(value.recurrence_law_id) is not str
            or value.recurrence_law_id != RECURRENCE_LAW_ID
        ):
            _reject("observer-genesis-source-envelope-shape-drift")
        supplied = (
            hex_digest(value.doctrine_digest, "envelope-doctrine-digest"),
            hex_digest(genealogy.genealogy_digest, "envelope-nested-genealogy-digest"),
            hex_digest(value.genealogy_digest, "envelope-genealogy-digest"),
            hex_digest(value.native_mode_digest, "envelope-native-mode-digest"),
            hex_digest(value.adapter_digest, "envelope-adapter-digest"),
            hex_digest(machine.machine_digest, "envelope-nested-machine-digest"),
            hex_digest(value.machine_digest, "envelope-machine-digest"),
            hex_digest(value.source_digest, "envelope-source-digest"),
        )
    except AttributeError:
        _reject("observer-genesis-source-envelope-missing-fields")
    if (
        supplied[0] != doctrine.doctrine_digest
        or supplied[1] != supplied[2] or supplied[5] != supplied[6]
    ):
        _reject("observer-genesis-source-envelope-transplant")
    expected_adapter = adapter_digest(value.adapter_id, supplied[3], supplied[6])
    provisional = ObserverGenesisSource(
        value.version, supplied[0], genealogy, supplied[2], supplied[3],
        value.adapter_id, expected_adapter, machine, supplied[6],
        value.closure_law_id, value.recurrence_law_id, "0" * 64,
    )
    expected_source = source_digest(provisional)
    if supplied[4] != expected_adapter or supplied[7] != expected_source:
        _reject("observer-genesis-source-envelope-digest-drift")
    result = ObserverGenesisSource(
        provisional.version, provisional.doctrine_digest, provisional.genealogy,
        provisional.genealogy_digest, provisional.native_mode_digest,
        provisional.adapter_id, provisional.adapter_digest, provisional.machine,
        provisional.machine_digest, provisional.closure_law_id,
        provisional.recurrence_law_id, expected_source,
    )
    logger.debug("snapshot_source_envelope exit")
    return result
