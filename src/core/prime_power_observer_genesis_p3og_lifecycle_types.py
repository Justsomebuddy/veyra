"""Closed DTOs for authority-free bounded P3-OG formation replay."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .prime_power_observer_genesis_p3og_types import DeterministicSelectionReceipt


class FormationBoundary(str, Enum):
    """Boundary state of the isolated lifecycle machine."""

    UNFORMED = "unformed"
    ALIVE = "alive"


class FirstClosureStatus(str, Enum):
    """Scoped finite-word status, not an observer-role judgment."""

    WITNESSED = "witnessed-bounded-first-closure"
    REFUTED = "refuted-bounded-first-closure"


@dataclass(frozen=True)
class P3OGFormationSource:
    """Outcome-free source for one selected finite formation word."""

    version: str
    pressure_source_digest: str
    selection: DeterministicSelectionReceipt
    selected_seed_digest: str
    formation_word: tuple[int, ...]
    closure_rule_id: str
    source_digest: str


@dataclass(frozen=True)
class FormationState:
    """Native lifecycle state derived only from the committed word."""

    run_id: str
    formation_source_digest: str
    seed_digest: str
    boundary: FormationBoundary
    cursor: int
    current_symbol: int
    tick_count: int
    state_digest: str


@dataclass(frozen=True)
class FormationTickReceipt:
    """One digest-linked native tick in the linear formation genealogy."""

    tick_index: int
    observed_symbol: int
    before_state_digest: str
    after_state_digest: str
    became_alive: bool
    receipt_digest: str


@dataclass(frozen=True)
class P3OGFirstClosureEvidence:
    """Authority-free evidence for one bounded least-return replay."""

    version: str
    formation_source_digest: str
    initial_state: FormationState
    ticks: tuple[FormationTickReceipt, ...]
    final_state: FormationState
    first_closure_index: int | None
    pressure_entry_state_digest: str | None
    status: FirstClosureStatus
    reason: str
    genealogy_digest: str
    promotions: int
    nonclaims: tuple[str, ...]
    evidence_digest: str


P3OG_LIFECYCLE_NONCLAIMS = (
    "criterion-blind-historical-selection",
    "consumed-one-shot-capability",
    "primitive-rez-nod-tact-breath-genealogy",
    "exact-n1-n2-p3t-arithmetic-bridge",
    "typed-history-dag-or-full-def-og-003",
    "doctrine-admission",
    "endogenous-observer-role",
    "birth-core-or-historical-token",
    "post-formation-ablation-or-same-token-efficacy",
    "n0-or-hap-lift",
    "formal-theorem-or-certificate",
    "physical-birth-or-consciousness",
    "absolute-observerhood-or-object-adoption",
    "universal-observer-genesis",
    "prime-power-carrier-or-completed-infinity",
)
