"""P1-C4 scoped formation runtime and result construction."""

from __future__ import annotations

from dataclasses import replace
import logging

from .codec import digest
from .components import expected_component_keys, replay_components
from .preflight import formation_preflight, snapshot_formation_request
from .sources import COMPONENT_ORDER
from .types import (
    FiniteScopedObjectPresentation, ScopedFormationJudgment,
    ScopedFormationResult, ScopedFormationStatus,
)

logger = logging.getLogger(__name__)


def scoped_formation_judgment(raw_rule_source, raw_scope) -> ScopedFormationResult:
    """Apply the exact allowlisted SFP after one atomic complete preflight."""
    logger.debug("scoped_formation_judgment entry")
    request = snapshot_formation_request(raw_rule_source, raw_scope)
    refusal = formation_preflight(request)
    if refusal is not None:
        logger.debug("scoped_formation_judgment exit resource-limit")
        return refusal
    g4, rows = replay_components(request.scope)
    expected = expected_component_keys(request.scope)
    actual = tuple((x.component, x.key) for x in rows)
    if actual != expected:
        logger.error("scoped_formation_judgment component coverage drift")
        raise RuntimeError("internal formation component coverage drift")
    refuted = next((x for x in rows if x.status is ScopedFormationStatus.REFUTED), None)
    opened = next((x for x in rows if x.status is ScopedFormationStatus.OPEN), None)
    winner = refuted or opened
    status = ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE if winner is None else winner.status
    presentation = _presentation(request, rows) if winner is None else None
    provisional = ScopedFormationJudgment(
        request.rule.source_digest, request.scope.scope_digest,
        request.scope.policy.policy_digest, request.run_digest,
        request.source_digests, request.scope.expected_target_commitment, g4,
        rows, expected, status, "" if winner is None else winner.obstruction,
        presentation, request.checks, request.encoded_bytes, "",
    )
    result = replace(provisional, judgment_digest=digest("c4.judgment", provisional))
    logger.debug("scoped_formation_judgment exit status=%s", status.value)
    return result


def finite_scoped_formation_rule(raw_rule_source, raw_scope) -> ScopedFormationResult:
    """Expose the named sufficient-rule application boundary."""
    logger.debug("finite_scoped_formation_rule entry")
    result = scoped_formation_judgment(raw_rule_source, raw_scope)
    logger.debug("finite_scoped_formation_rule exit type=%s", type(result).__name__)
    return result


def _presentation(request, rows) -> FiniteScopedObjectPresentation:
    """Construct a fresh positive DTO only after every row is established."""
    logger.debug("_presentation entry")
    scope = request.scope
    groups = {name: tuple(x.row_digest for x in rows if x.component == name) for name in COMPONENT_ORDER}
    order_digest = digest("c4.component-order", COMPONENT_ORDER, tuple((x.component, x.key) for x in rows))
    provisional = FiniteScopedObjectPresentation(
        scope.presentation_id, scope.target, scope.target.stage_id,
        scope.expected_target_commitment, scope.doctrine.fingerprint,
        request.rule.source_digest, scope.scope_digest,
        digest("c4.presentation.construction", groups["construction"]),
        digest("c4.presentation.support", groups["support"]),
        digest("c4.presentation.persistence", groups["persistence"]),
        digest("c4.presentation.g4", groups["g4"]),
        digest("c4.presentation.c2", groups["c2-confluence"]),
        digest("c4.presentation.refinement", groups["a2-refinement"]),
        digest("c4.presentation.survival", groups["survival"]),
        order_digest, "",
    )
    result = replace(provisional, presentation_digest=digest("c4.presentation", provisional))
    logger.debug("_presentation exit")
    return result
