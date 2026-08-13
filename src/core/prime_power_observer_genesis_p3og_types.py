"""Closed types for the isolated P3-OG machine-pressure experiment."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PressureStatus(str, Enum):
    """Status of implemented finite checks, not an observer-role judgment."""

    PASSED = "passed-implemented-pressure"
    REFUTED = "refuted-implemented-pressure"
    OPEN = "open-unimplemented-obligation"


class BoundaryState(str, Enum):
    """Internal boundary state of a candidate machine."""

    ALIVE = "alive"
    REMOVED = "removed"


class MaintenanceControlState(str, Enum):
    """State of the predeclared internal maintenance component."""

    ACTIVE = "active"
    DISABLED = "disabled"


class TransitionKind(str, Enum):
    """Allowed native transition kinds in a shared schedule."""

    ADVANCE = "advance"
    MAINTAIN = "maintain"
    IDLE = "idle"


@dataclass(frozen=True)
class PrimitiveModeSeed:
    """Bounded raw cycle seed; not yet a primitive Veyra genealogy."""

    label: str
    cycle: tuple[int, ...]
    seed_digest: str


@dataclass(frozen=True)
class P3OGSource:
    """Complete finite machine source; no outcome or target fields."""

    version: str
    prime: int
    depth: int
    source_instance_label: str
    seeds: tuple[PrimitiveModeSeed, ...]
    calibration_inputs: tuple[int, int]
    maintenance_credit: int
    suffix: tuple[TransitionKind, ...]
    doctrine_label: str
    source_digest: str


@dataclass(frozen=True)
class DeterministicSelectionReceipt:
    """Canonical pool selection; no chronology or consumed-attempt claim."""

    source_digest: str
    pool_digest: str
    selected_index: int
    selected_seed_digest: str
    rule_id: str
    receipt_digest: str


@dataclass(frozen=True)
class CandidateMachineState:
    """Finite internal state carrying an arithmetic residue."""

    run_id: str
    seed_digest: str
    boundary: BoundaryState
    maintenance_control: MaintenanceControlState
    phase: int
    retained_residue: int | None
    maintenance_credit: int
    transition_count: int
    state_digest: str


@dataclass(frozen=True)
class TransitionReceipt:
    """Digest-bound evidence for one native state transition."""

    kind: TransitionKind
    before_digest: str
    after_digest: str
    response: int | None
    receipt_digest: str


@dataclass(frozen=True)
class CouplingReceipt:
    """Digest-bound evidence for one arithmetic coupling transition."""

    input_value: int
    before_digest: str
    after_digest: str
    response: int | None
    receipt_digest: str


@dataclass(frozen=True)
class PreCouplingMaintenanceControlReceipt:
    """Pre-coupling control change affecting only the maintenance component."""

    enabled_state_digest: str
    disabled_state_digest: str
    unchanged_fields_digest: str
    receipt_digest: str


@dataclass(frozen=True)
class BranchTrace:
    """Complete bound trace for one input under one component state."""

    input_value: int
    maintenance_control: MaintenanceControlState
    coupling: CouplingReceipt
    transitions: tuple[TransitionReceipt, ...]
    final_state: CandidateMachineState
    trace_digest: str


@dataclass(frozen=True)
class CandidatePressureResult:
    """Implemented checks for one canonical candidate."""

    seed_digest: str
    status: PressureStatus
    reason: str
    candidate_pressure_identity_digest: str
    maintenance_control: PreCouplingMaintenanceControlReceipt | None
    active_left: BranchTrace | None
    active_right: BranchTrace | None
    control_left: BranchTrace | None
    control_right: BranchTrace | None
    result_digest: str


@dataclass(frozen=True)
class P3OGPressureReport:
    """Pressure report with no observer-role, birth, or token capability."""

    status: PressureStatus
    reason: str
    source_digest: str
    selection: DeterministicSelectionReceipt
    candidates: tuple[CandidatePressureResult, ...]
    selected_candidate_result_digest: str
    role_status: PressureStatus
    promotions: int
    nonclaims: tuple[str, ...]
    report_digest: str


P3OG_NONCLAIMS = (
    "criterion-blind-historical-selection",
    "consumed-one-shot-capability",
    "primitive-rez-nod-tact-breath-genealogy",
    "exact-n1-n2-p3t-arithmetic-bridge",
    "doctrine-admission",
    "first-closure-or-history-dag",
    "endogenous-observer-role",
    "n0-or-hap-lift",
    "formal-theorem",
    "physical-birth-or-consciousness",
    "absolute-observerhood-or-object-adoption",
    "prime-power-carrier-or-completed-infinity",
)
