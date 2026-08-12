"""Exact status spaces and rows for structural comparison ledgers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ComparativeBridgeStatus(str, Enum):
    """Allowed states for a proposed or established structural bridge."""

    KNOWN_ANALOGUE = "KNOWN_ANALOGUE"
    CANDIDATE_BRIDGE = "CANDIDATE_BRIDGE"
    REDUCED = "REDUCED"
    OPEN = "OPEN"


class StructuralSeparationStatus(str, Enum):
    """Allowed states for a proposed or established predicate separation."""

    CANDIDATE_SEPARATION = "CANDIDATE_SEPARATION"
    STRICTLY_SEPARATED = "STRICTLY_SEPARATED"
    OPEN = "OPEN"


@dataclass(frozen=True, slots=True)
class ComparativeEvidenceRef:
    """One typed repository evidence reference, not a portable receipt."""

    evidence_id: str
    kind: str
    location: str
    checked: bool


@dataclass(frozen=True, slots=True)
class ComparativeBridgeRow:
    """One exact structural correspondence or explicitly open bridge."""

    schema: str
    bridge_id: str
    veyra_construct: str
    comparison_formalism: str
    status: ComparativeBridgeStatus
    scope: str
    correspondence: tuple[str, ...]
    preservation: str
    reflection: str
    extra_structure: str
    evidence: tuple[ComparativeEvidenceRef, ...]
    boundary: str


@dataclass(frozen=True, slots=True)
class StructuralSeparationRow:
    """One exact predicate separation or explicitly unresolved candidate."""

    schema: str
    separation_id: str
    left_predicate: str
    right_predicate: str
    status: StructuralSeparationStatus
    scope: str
    witness: str
    evidence: tuple[ComparativeEvidenceRef, ...]
    boundary: str
