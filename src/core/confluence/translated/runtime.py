"""Fresh A2-gated occurrence-complete translated confluence replay."""

from __future__ import annotations

from dataclasses import replace
import logging

from ..runtime import _check_persistence
from ..types import ConfluenceObstruction, ConfluenceStatus
from ...observer.morphism import MorphismStatus, observer_morphism_judgment
from ...observer.relations.types import RelationResourceLimit
from ...observer.relations.runtime import observer_relation_judgment
from ...observer.relations.types import (
    CoverageStatus, MorphismEvidenceStatus, ObserverRelationJudgment,
    ProposalStatus,
)
from .cell import build_translated_cell
from .digest import digest, sequence
from .preflight import (
    TranslatedConfluenceRequest, snapshot_translated_request, translated_preflight,
)
from .types import (
    P0P1AResponseBridgeSource, TranslatedConfluenceJudgment,
    TranslatedConfluencePolicy, TranslatedConfluenceResult,
    TranslatedEchoTransportSpec, TranslatedTransport2CellArtifact,
)

logger = logging.getLogger(__name__)


def _a2_gate(
    request: TranslatedConfluenceRequest, result: ObserverRelationJudgment,
    morphism_status: MorphismStatus,
) -> str | None:
    """Return the first exact unsatisfied structural/relation requirement."""
    logger.debug("c3 a2_gate entry")
    forward = result.forward
    checks = (
        (morphism_status is MorphismStatus.STRONG, "p1a-morphism-not-strong"),
        (forward.morphism_status is MorphismEvidenceStatus.P1A_ESTABLISHED,
         "a2-p1a-replay-not-established"),
        (forward.proposal_status is ProposalStatus.COMMUTES_ON_SCOPE,
         "a2-triangles-not-commuting"),
        (all(row.status is ProposalStatus.COMMUTES_ON_SCOPE for row in forward.triangles),
         "a2-triangle-coverage-not-ready"),
        (result.coverage is CoverageStatus.COMPLETE, "a2-coverage-partial"),
        (result.preservation is request.spec.required_preservation,
         "a2-preservation-requirement-failed"),
        (result.domain_equality is request.spec.required_domain_equality,
         "a2-domain-equality-requirement-failed"),
        (result.classification is request.spec.required_class,
         "a2-relation-class-requirement-failed"),
        (request.spec.required_loss is None
         or result.information_loss is request.spec.required_loss,
         "a2-loss-requirement-failed"),
    )
    result_reason = next((reason for passed, reason in checks if not passed), None)
    logger.debug("c3 a2_gate exit ready=%s", result_reason is None)
    return result_reason


def _open_judgment(
    request: TranslatedConfluenceRequest, a2: ObserverRelationJudgment,
    reason: str,
) -> TranslatedConfluenceJudgment:
    """Return an explicit nonpromoting OPEN result for an unmet replay gate."""
    logger.debug("c3 open_judgment entry reason=%s", reason)
    obstruction = ConfluenceObstruction(
        "translated-prerequisite", 0, request.spec.p1a_fine_observer_id, reason,
    )
    result = _judgment(request, a2, None, obstruction, ConfluenceStatus.OPEN)
    logger.debug("c3 open_judgment exit")
    return result


def _judgment(
    request: TranslatedConfluenceRequest, a2: ObserverRelationJudgment,
    cell: TranslatedTransport2CellArtifact | None,
    obstruction: ConfluenceObstruction | None, status: ConfluenceStatus,
) -> TranslatedConfluenceJudgment:
    """Commit one result after all semantic work is complete."""
    logger.debug("c3 judgment assemble entry status=%s", status.value)
    provisional = TranslatedConfluenceJudgment(
        request.p0_doctrine.fingerprint, request.diagram.source_digest,
        request.plan.plan_digest, request.p1a_doctrine.fingerprint,
        request.p1a_source.membership_digest, request.a2_stage_source.source_digest,
        request.bridge.bridge_digest, request.spec.spec_digest,
        request.policy.policy_digest, request.spec.relation_scope.scope_digest,
        a2.judgment_digest, a2.preservation, a2.domain_equality,
        a2.classification, a2.information_loss, request.spec.direction,
        status, cell, obstruction, request.required_checks,
        request.run_digest, "",
    )
    judgment_digest = digest("p1-c3-judgment-v1", (
        ("run", request.run_digest.encode()), ("a2", a2.judgment_digest.encode()),
        ("status", status.value.encode()),
        ("cell", ("absent" if cell is None else cell.trace_digest).encode()),
        ("obstruction", ("absent" if obstruction is None else obstruction.outcome).encode()),
        ("nonclaims", sequence("nonclaim", provisional.nonclaims)),
    ))
    result = replace(provisional, judgment_digest=judgment_digest)
    logger.debug("c3 judgment assemble exit")
    return result


def translated_confluence_judgment(
    p0_doctrine, diagram, plan, p1a_doctrine, p1a_source, a2_stage_source,
    bridge: P0P1AResponseBridgeSource, transport: TranslatedEchoTransportSpec,
    policy: TranslatedConfluencePolicy | None = None,
) -> TranslatedConfluenceResult:
    """Replay one raw-source, A2-gated, asymmetric translated finite cell."""
    logger.debug("translated_confluence_judgment entry")
    from .transport import translated_confluence_policy
    selected = translated_confluence_policy() if policy is None else policy
    request = snapshot_translated_request(
        p0_doctrine, diagram, plan, p1a_doctrine, p1a_source,
        a2_stage_source, bridge, transport, selected,
    )
    refusal = translated_preflight(request)
    if refusal is not None:
        logger.debug("translated_confluence_judgment exit resource-limit")
        return refusal
    morphism = observer_morphism_judgment(
        request.p1a_doctrine, request.p1a_source, request.spec.morphism.morphism_id,
        request.spec.morphism.fine_observer_id,
        request.spec.morphism.coarse_observer_id,
        request.spec.morphism.projection,
    )
    a2 = observer_relation_judgment(
        request.p1a_doctrine, request.p1a_source, request.a2_stage_source,
        request.spec.relation_scope, request.spec.morphism, None,
        request.spec.relation_policy,
    )
    if type(a2) is RelationResourceLimit:
        logger.error("c3 nested resource refusal after atomic preflight")
        raise RuntimeError("translated-confluence-nested-preflight-drift")
    if type(a2) is not ObserverRelationJudgment:
        raise RuntimeError("translated-confluence-a2-variant-drift")
    gate = _a2_gate(request, a2, morphism.status)
    if gate is not None or morphism.translation is None:
        result = _open_judgment(request, a2, gate or "p1a-translation-unavailable")
        logger.debug("translated_confluence_judgment exit open-prerequisite")
        return result
    cell = build_translated_cell(request, morphism.translation, a2.judgment_digest)
    mismatches, openings = _check_persistence(request.diagram, request.plan)
    cell_bad = cell.first_obstruction if cell.status is ConfluenceStatus.REFUTED else None
    cell_open = cell.first_obstruction if cell.status is ConfluenceStatus.OPEN else None
    mismatch = mismatches[0] if mismatches else cell_bad
    opening = openings[0] if openings else cell_open
    status = ConfluenceStatus.REFUTED if mismatch else (
        ConfluenceStatus.OPEN if opening else ConfluenceStatus.ESTABLISHED
    )
    result = _judgment(request, a2, cell, mismatch or opening, status)
    logger.debug("translated_confluence_judgment exit status=%s", status.value)
    return result
