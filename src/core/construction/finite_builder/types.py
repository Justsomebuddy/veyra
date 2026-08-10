"""Exact immutable DTOs for provisional P1-B finite replay."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from ...positive_ontology_types import OntologyStage


@dataclass(frozen=True)
class SeedRef:
    """Reference one exactly admitted recurrence seed."""

    seed_id: str


@dataclass(frozen=True)
class PulseStep:
    """Add one Pulse to a finite builder result."""

    child: "FiniteBuilderExpr"


FiniteBuilderExpr: TypeAlias = SeedRef | PulseStep


class ReplayStatus(str, Enum):
    """Fresh replay outcome."""

    REPLAYED = "replayed"


class FormalGenerability(str, Enum):
    """Only the finite formal construction result."""

    GENERABLE = "generable"
    TARGET_MISMATCH = "target-mismatch"


class OnticGenesis(str, Enum):
    """P1-B cannot establish ontic genesis."""

    NOT_ESTABLISHED = "not-established"


class TargetIndependence(str, Enum):
    """A digest cannot establish target-independent selection."""

    NOT_ESTABLISHED = "not-established"


class ScopedObjectFormation(str, Enum):
    """Scoped-object formation remains unavailable before P1-C."""

    OPEN = "open"


@dataclass(frozen=True)
class FiniteRecurrenceSeed:
    """One fresh-snapshot recurrence seed and its commitment."""

    seed_id: str
    canonical: bytes
    seed_digest: str
    scope: str = "admitted-finite-recurrence-seed"


@dataclass(frozen=True)
class FiniteBuilderProgram:
    """Closed target-free syntax plus its intended finite stage shell."""

    builder_id: str
    output_stage_id: str
    observer_ids: tuple[str, ...]
    canonical: bytes
    referenced_seed_ids: tuple[str, ...]
    program_digest: str
    scope: str = "closed-target-free-finite-recurrence-builder"


@dataclass(frozen=True)
class ConstructionSourceBinding:
    """Immutable membership, never chronology or target independence."""

    binding_id: str
    doctrine_fingerprint: str
    program: FiniteBuilderProgram
    seeds: tuple[FiniteRecurrenceSeed, ...]
    membership_digest: str
    scope: str = "immutability-membership-not-chronology-or-target-independence"


@dataclass(frozen=True)
class ReplayArtifact:
    """Fresh replayed stage with deterministic semantic commitments."""

    source_binding_digest: str
    stage: OntologyStage
    stage_commitment: str
    recurrence_commitment: str
    trace_digest: str
    builder_nodes: int
    pulse_depth: int
    status: ReplayStatus = ReplayStatus.REPLAYED
    scope: str = "fresh-finite-replay"


@dataclass(frozen=True)
class FiniteConstructionJudgment:
    """Formal generability plus hard nonclaim boundaries."""

    doctrine_fingerprint: str
    source_binding_digest: str
    target_stage_id: str
    target_commitment: str
    replay: ReplayArtifact
    formal_generability: FormalGenerability
    obstruction: str
    ontic_genesis: OnticGenesis = OnticGenesis.NOT_ESTABLISHED
    target_independence: TargetIndependence = TargetIndependence.NOT_ESTABLISHED
    scoped_object: ScopedObjectFormation = ScopedObjectFormation.OPEN
    scope: str = "provisional-p1b-formal-finite-generability"


_LEGACY_MODULE = "src.core.finite_builder_types"
for _legacy_type in (
    SeedRef,
    PulseStep,
    ReplayStatus,
    FormalGenerability,
    OnticGenesis,
    TargetIndependence,
    ScopedObjectFormation,
    FiniteRecurrenceSeed,
    FiniteBuilderProgram,
    ConstructionSourceBinding,
    ReplayArtifact,
    FiniteConstructionJudgment,
):
    _legacy_type.__module__ = _LEGACY_MODULE
del _legacy_type, _LEGACY_MODULE
