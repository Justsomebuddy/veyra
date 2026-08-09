"""Deterministic P1-A2 law aggregation and finite-scope classification."""

from __future__ import annotations

import logging

from .types import (
    CoverageStatus, DomainWitness, LawStatus, LossStatus,
    MorphismEvidenceStatus, PairOutcome, ProposalStatus, RelationClass,
    RelationPairRow, RelationRunStatus, RelationWitness, StageObservationRow,
    TranslationAssessment,
)

logger = logging.getLogger(__name__)


def preservation_law(
    rows: tuple[RelationPairRow, ...],
) -> tuple[LawStatus, RelationWitness | None]:
    """Aggregate fine-ECHO implies coarse-ECHO with mismatch precedence."""
    logger.debug("preservation_law entry rows=%d", len(rows))
    opened = False
    for row in rows:
        if row.fine_outcome is PairOutcome.ECHO and row.coarse_outcome is PairOutcome.MISMATCH:
            witness = _witness(row)
            logger.debug("preservation_law exit refuted index=%d", row.pair_index)
            return LawStatus.REFUTED, witness
        if row.fine_outcome is PairOutcome.BLOCKED or (
            row.fine_outcome is PairOutcome.ECHO
            and row.coarse_outcome is PairOutcome.BLOCKED
        ):
            opened = True
    result = LawStatus.OPEN if opened else LawStatus.ESTABLISHED
    logger.debug("preservation_law exit status=%s", result.value)
    return result, None


def reflection_law(
    rows: tuple[RelationPairRow, ...],
) -> tuple[LawStatus, RelationWitness | None]:
    """Aggregate coarse-ECHO implies fine-ECHO with mismatch precedence."""
    logger.debug("reflection_law entry rows=%d", len(rows))
    opened = False
    for row in rows:
        if row.coarse_outcome is PairOutcome.ECHO and row.fine_outcome is PairOutcome.MISMATCH:
            witness = _witness(row)
            logger.debug("reflection_law exit refuted index=%d", row.pair_index)
            return LawStatus.REFUTED, witness
        if row.coarse_outcome is PairOutcome.BLOCKED or (
            row.coarse_outcome is PairOutcome.ECHO
            and row.fine_outcome is PairOutcome.BLOCKED
        ):
            opened = True
    result = LawStatus.OPEN if opened else LawStatus.ESTABLISHED
    logger.debug("reflection_law exit status=%s", result.value)
    return result, None


def domain_equality_law(
    rows: tuple[StageObservationRow, ...],
) -> tuple[LawStatus, DomainWitness | None]:
    """Compare exact ready domains stage-by-stage, including both-blocked rows."""
    logger.debug("domain_equality_law entry rows=%d", len(rows))
    for index, row in enumerate(rows):
        if (row.fine_status is RelationRunStatus.READY) != (
            row.coarse_status is RelationRunStatus.READY
        ):
            witness = DomainWitness(
                index, row.stage, row.fine_status, row.coarse_status, row.row_digest,
            )
            logger.debug("domain_equality_law exit refuted index=%d", index)
            return LawStatus.REFUTED, witness
    logger.debug("domain_equality_law exit established")
    return LawStatus.ESTABLISHED, None


def relation_classification(
    preservation: LawStatus, reflection: LawStatus,
    domain_equality: LawStatus,
) -> RelationClass:
    """Derive one class only from the three independent relation laws."""
    logger.debug("relation_classification entry")
    if preservation is LawStatus.REFUTED and reflection is LawStatus.REFUTED:
        result = RelationClass.INCOMPARABLE_ON_SCOPE
    elif domain_equality is not LawStatus.ESTABLISHED:
        result = RelationClass.OPEN
    elif preservation is LawStatus.ESTABLISHED and reflection is LawStatus.ESTABLISHED:
        result = RelationClass.EQUIVALENT_ON_SCOPE
    elif preservation is LawStatus.ESTABLISHED and reflection is LawStatus.REFUTED:
        result = RelationClass.STRICT_REFINEMENT_ON_SCOPE
    elif reflection is LawStatus.ESTABLISHED and preservation is LawStatus.REFUTED:
        result = RelationClass.STRICT_COARSENING_ON_SCOPE
    else:
        result = RelationClass.OPEN
    logger.debug("relation_classification exit class=%s", result.value)
    return result


def coverage_status(rows: tuple[StageObservationRow, ...]) -> CoverageStatus:
    """Report whether both observers were ready on every exact stage."""
    logger.debug("relation coverage_status entry rows=%d", len(rows))
    result = (
        CoverageStatus.COMPLETE
        if all(
            row.fine_status is RelationRunStatus.READY
            and row.coarse_status is RelationRunStatus.READY
            for row in rows
        )
        else CoverageStatus.PARTIAL_BLOCKED
    )
    logger.debug("relation coverage_status exit status=%s", result.value)
    return result


def information_loss_status(
    forward: TranslationAssessment, preservation: LawStatus,
    reflection: LawStatus, domain_equality: LawStatus,
) -> LossStatus:
    """Classify loss only from established P1-A replay plus complete triangles."""
    logger.debug("information_loss_status entry")
    structural = (
        forward.morphism_status is MorphismEvidenceStatus.P1A_ESTABLISHED
        and forward.proposal_status is ProposalStatus.COMMUTES_ON_SCOPE
        and preservation is LawStatus.ESTABLISHED
        and domain_equality is LawStatus.ESTABLISHED
    )
    if structural and reflection is LawStatus.REFUTED:
        result = LossStatus.LOSSY_ON_SCOPE
    elif structural and reflection is LawStatus.ESTABLISHED:
        result = LossStatus.LOSSLESS_ON_SCOPE
    else:
        result = LossStatus.NOT_ESTABLISHED
    logger.debug("information_loss_status exit status=%s", result.value)
    return result


def _witness(row: RelationPairRow) -> RelationWitness:
    """Copy the first exact replayed counterexample row binding."""
    logger.debug("relation witness entry index=%d", row.pair_index)
    result = RelationWitness(row.pair_index, row.row_digest, row.left, row.right)
    logger.debug("relation witness exit index=%d", row.pair_index)
    return result
