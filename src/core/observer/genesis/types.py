"""Closed DTOs for doctrine-relative P1-E1 observer genesis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias


class PremiseStatus(str, Enum):
    ESTABLISHED = "established"
    REFUTED = "refuted"
    OPEN = "open"


class OEPAdmission(str, Enum):
    ADMITTED = "admitted"
    NOT_ADMITTED = "not-admitted"


class ObserverRole(str, Enum):
    ESTABLISHED = "established"
    OPEN = "open"


class PremiseName(str, Enum):
    PRIMITIVE_GENEALOGY = "primitive-genealogy"
    STRUCTURAL_CLOSURE = "structural-closure"
    RECURRENT_RETURN = "recurrent-return"
    COUNTERFACTUAL_DISCRIMINATION = "counterfactual-discrimination"
    BOUNDED_PERSISTENCE = "bounded-persistence"
    RESIDUE_EFFICACY = "residue-efficacy"


class HistoricalTargetIndependence(str, Enum):
    NOT_ESTABLISHED = "not-established"


class PhysicalInstantiation(str, Enum):
    NOT_ESTABLISHED = "not-established"


class GenesisOperation(str, Enum):
    JUDGMENT = "observer-genesis-judgment"


class GenesisOperationStatus(str, Enum):
    JUDGED = "judged"
    RESOURCE_LIMIT = "resource-limit"


class GenesisResourceBound(str, Enum):
    TRANSITION_ROWS = "transition-rows"
    REACHABILITY_CHECKS = "reachability-checks"
    CONTINUATION_STEPS = "continuation-steps"
    RETURN_WORD_STEPS = "return-word-steps"
    RESPONSE_CHECKS = "response-checks"
    ENCODED_BYTES = "encoded-bytes"


@dataclass(frozen=True)
class RezSpec:
    name: str


@dataclass(frozen=True)
class NodSpec:
    residue: RezSpec
    mark: str


@dataclass(frozen=True)
class TactSpec:
    start: NodSpec
    end: NodSpec
    mark: str


@dataclass(frozen=True)
class BreathSpec:
    tacts: tuple[TactSpec, ...]


@dataclass(frozen=True)
class ModeSpec:
    version: str
    breath: BreathSpec
    genealogy_digest: str


@dataclass(frozen=True)
class MachineState:
    control: str
    residue: str


@dataclass(frozen=True)
class TransitionRow:
    control: str
    residue: str
    coupling: str
    next_control: str
    next_residue: str
    response: str


@dataclass(frozen=True)
class FiniteObserverMachine:
    version: str
    control_states: tuple[str, ...]
    residues: tuple[str, ...]
    couplings: tuple[str, ...]
    responses: tuple[str, ...]
    initial_state: MachineState
    rows: tuple[TransitionRow, ...]
    machine_digest: str


@dataclass(frozen=True)
class GenesisResourcePolicy:
    version: str
    max_transition_rows: int
    max_reachability_checks: int
    max_continuation_steps: int
    max_return_word_steps: int
    max_response_checks: int
    max_encoded_bytes: int
    policy_digest: str


@dataclass(frozen=True)
class ObserverGenesisDoctrine:
    version: str
    doctrine_id: str
    policy: GenesisResourcePolicy
    doctrine_digest: str


@dataclass(frozen=True)
class ObserverGenesisSource:
    version: str
    doctrine_digest: str
    genealogy: ModeSpec
    genealogy_digest: str
    native_mode_digest: str
    adapter_id: str
    adapter_digest: str
    machine: FiniteObserverMachine
    machine_digest: str
    closure_law_id: str
    recurrence_law_id: str
    source_digest: str


@dataclass(frozen=True)
class WitnessScope:
    version: str
    source_digest: str
    branch_state: MachineState
    left_coupling: str
    right_coupling: str
    common_continuation: tuple[str, ...]
    persistence_horizon: int
    efficacy_index: int
    witness_digest: str


@dataclass(frozen=True)
class RecurrenceWitness:
    version: str
    source_digest: str
    witness_digest: str
    left_return_word: tuple[str, ...]
    right_return_word: tuple[str, ...]
    recurrence_digest: str


@dataclass(frozen=True)
class UnavailableRecurrenceEvidence:
    version: str
    source_digest: str
    witness_digest: str
    reason_id: str
    recurrence_digest: str


RecurrenceEvidence: TypeAlias = RecurrenceWitness | UnavailableRecurrenceEvidence


@dataclass(frozen=True)
class OEPAdmissionRecord:
    version: str
    doctrine_digest: str
    principle_id: str
    admission: OEPAdmission
    oep_digest: str


@dataclass(frozen=True)
class PremiseArtifact:
    premise: PremiseName
    status: PremiseStatus
    rows: tuple[TransitionRow, ...]
    states: tuple[MachineState, ...]
    evidence_digest: str


@dataclass(frozen=True)
class GenesisJudgment:
    doctrine_digest: str
    source_digest: str
    adapter_digest: str
    witness_digest: str
    recurrence_digest: str
    oep_digest: str
    run_digest: str
    judgment_digest: str
    operation_status: GenesisOperationStatus
    premises: tuple[PremiseArtifact, ...]
    primitive_genealogy: PremiseStatus
    structural_closure: PremiseStatus
    recurrent_return: PremiseStatus
    counterfactual_discrimination: PremiseStatus
    bounded_persistence: PremiseStatus
    residue_efficacy: PremiseStatus
    observer_role_relative_to_scope: ObserverRole
    historical_target_independence: HistoricalTargetIndependence = HistoricalTargetIndependence.NOT_ESTABLISHED
    physical_instantiation: PhysicalInstantiation = PhysicalInstantiation.NOT_ESTABLISHED
    scope: str = "finite-doctrine-relative-oep-role-only"


@dataclass(frozen=True)
class GenesisResourceLimit:
    operation: GenesisOperation
    failed_bound: GenesisResourceBound
    required_value: int
    allowed_value: int
    doctrine_digest: str
    source_digest: str
    adapter_digest: str
    witness_digest: str
    recurrence_digest: str
    oep_digest: str
    run_digest: str
    refusal_digest: str
    operation_status: GenesisOperationStatus = GenesisOperationStatus.RESOURCE_LIMIT
    historical_target_independence: HistoricalTargetIndependence = HistoricalTargetIndependence.NOT_ESTABLISHED
    physical_instantiation: PhysicalInstantiation = PhysicalInstantiation.NOT_ESTABLISHED
    scope: str = "resource-refusal-no-partial-genesis-evidence"


GenesisResult: TypeAlias = GenesisJudgment | GenesisResourceLimit
