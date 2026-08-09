"""Public exact surface for P1-E1 primitive-rooted observer genesis."""

from __future__ import annotations

import logging

from .adapter import ADAPTER_ID
from .native import (
    GENEALOGY_VERSION, ObserverGenesisValidationError, build_mode_spec,
    origin_mode_spec,
)
from .request import (
    OEP_PRINCIPLE_ID, build_oep_record, build_recurrence,
    build_unavailable_recurrence, build_witness,
)
from .result_validation import validate_genesis_result
from .runtime import observer_genesis_judgment
from .types import (
    BreathSpec, FiniteObserverMachine, GenesisResourcePolicy, MachineState,
    ModeSpec, NodSpec, OEPAdmission, OEPAdmissionRecord,
    ObserverGenesisDoctrine, ObserverGenesisSource, RecurrenceWitness, RezSpec,
    TactSpec, UnavailableRecurrenceEvidence, WitnessScope,
)
from .validation import (
    CLOSURE_LAW_ID, RECURRENCE_LAW_ID, build_doctrine,
    build_resource_policy, build_source, derive_fixed_machine,
)

logger = logging.getLogger(__name__)


def genesis_resource_policy(
    max_transition_rows: int = 24, max_reachability_checks: int = 24,
    max_continuation_steps: int = 128, max_return_word_steps: int = 256,
    max_response_checks: int = 130, max_encoded_bytes: int = 16_384,
) -> GenesisResourcePolicy:
    """Build explicit E1 operational preflight limits."""
    logger.debug("genesis_resource_policy entry")
    result = build_resource_policy(
        max_transition_rows, max_reachability_checks, max_continuation_steps,
        max_return_word_steps, max_response_checks, max_encoded_bytes,
    )
    logger.debug("genesis_resource_policy exit")
    return result


def observer_genesis_doctrine(
    policy: GenesisResourcePolicy,
) -> ObserverGenesisDoctrine:
    """Build the own E1 Observer Emergence Principle doctrine."""
    logger.debug("observer_genesis_doctrine entry")
    result = build_doctrine(policy)
    logger.debug("observer_genesis_doctrine exit")
    return result


def mode_genealogy(breath: BreathSpec) -> ModeSpec:
    """Build the strict versioned primitive genealogy AST root."""
    logger.debug("mode_genealogy entry")
    result = build_mode_spec(breath)
    logger.debug("mode_genealogy exit")
    return result


def observer_genesis_source(
    doctrine: ObserverGenesisDoctrine, genealogy: ModeSpec,
    adapter_id: str, machine: FiniteObserverMachine,
) -> ObserverGenesisSource:
    """Bind doctrine, raw genealogy, and exact fresh whole-table adapter output."""
    logger.debug("observer_genesis_source entry")
    result = build_source(doctrine, genealogy, adapter_id, machine)
    logger.debug("observer_genesis_source exit")
    return result


def witness_scope(
    source: ObserverGenesisSource, branch_state: MachineState,
    left_coupling: str, right_coupling: str,
    common_continuation: tuple[str, ...], persistence_horizon: int,
    efficacy_index: int,
) -> WitnessScope:
    """Fix the exact discrimination, persistence, and efficacy scope."""
    logger.debug("witness_scope entry")
    result = build_witness(
        source, branch_state, left_coupling, right_coupling,
        common_continuation, persistence_horizon, efficacy_index,
    )
    logger.debug("witness_scope exit")
    return result


def recurrence_witness(
    source: ObserverGenesisSource, witness: WitnessScope,
    left_return_word: tuple[str, ...], right_return_word: tuple[str, ...],
) -> RecurrenceWitness:
    """Bind both path-relevant return words to source and witness."""
    logger.debug("recurrence_witness entry")
    result = build_recurrence(
        source, witness, left_return_word, right_return_word,
    )
    logger.debug("recurrence_witness exit")
    return result


def unavailable_recurrence(
    source: ObserverGenesisSource, witness: WitnessScope,
) -> UnavailableRecurrenceEvidence:
    """Bind explicit unavailable recurrence evidence as OPEN, never REFUTED."""
    logger.debug("unavailable_recurrence entry")
    result = build_unavailable_recurrence(source, witness)
    logger.debug("unavailable_recurrence exit")
    return result


def oep_admission_record(
    doctrine: ObserverGenesisDoctrine, admission: OEPAdmission,
) -> OEPAdmissionRecord:
    """Build an explicit doctrine-bound OEP admission record."""
    logger.debug("oep_admission_record entry")
    result = build_oep_record(doctrine, admission)
    logger.debug("oep_admission_record exit")
    return result


__all__ = [
    "ADAPTER_ID", "CLOSURE_LAW_ID", "GENEALOGY_VERSION",
    "OEP_PRINCIPLE_ID", "RECURRENCE_LAW_ID", "derive_fixed_machine",
    "genesis_resource_policy", "mode_genealogy", "observer_genesis_doctrine",
    "observer_genesis_judgment", "observer_genesis_source",
    "oep_admission_record", "origin_mode_spec", "recurrence_witness",
    "unavailable_recurrence", "validate_genesis_result", "witness_scope",
    "ObserverGenesisValidationError",
    "RezSpec", "NodSpec", "TactSpec", "BreathSpec",
]
