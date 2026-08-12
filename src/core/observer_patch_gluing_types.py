"""Typed values for the bounded G4 exact-gluing classification."""

from __future__ import annotations

from dataclasses import dataclass

from .observer_patch_atlas import ExactGluingCriterion, Pair

QuotientBlock = tuple[int, ...]
QuotientPartition = tuple[QuotientBlock, ...]
ConflictEdge = tuple[int, int]


@dataclass(frozen=True, slots=True)
class QuotientConflictGraph:
    """Conflict graph on generated-echo quotient classes."""

    schema: str
    quotient_classes: tuple[tuple[str, ...], ...]
    edges: tuple[ConflictEdge, ...]
    complete: bool


@dataclass(frozen=True, slots=True)
class ExactGluingClassification:
    """Bounded classification of every exact global G4 gluing."""

    schema: str
    matching_family: bool
    criterion: ExactGluingCriterion
    generated_relation: frozenset[Pair]
    conflict_graph: QuotientConflictGraph
    safe_quotient_partitions: tuple[QuotientPartition, ...]
    direct_exact_gluing_count: int
    classification_holds: bool
    unique_exact_gluing: bool
    uniqueness_iff_conflict_complete: bool
    scope: str = "finite-exact-existence-and-uniqueness-no-general-sheaf-claim"


@dataclass(frozen=True, slots=True)
class DisjointSingletonNonuniqueness:
    """Two exact gluings with identical singleton restrictions."""

    classification: ExactGluingClassification
    identity_relation: frozenset[Pair]
    universal_relation: frozenset[Pair]
    both_exact: bool
    distinct: bool
