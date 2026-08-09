"""Raw-P1-backed translation, relation, refinement, and isomorphism laws."""

from __future__ import annotations

import logging

from ..relations.types import MorphismEvidenceStatus, ProposalStatus
from .common import reject
from .digest import records_digest
from .maps import compose_maps, operational_edge_map, ready_image
from .p1_replay import map_p1_law, replay_raw_pair, witness_input_ids
from .types import (
    CompositionJudgment,
    EdgeJudgment,
    EvaluationDomainJudgment,
    IsomorphismJudgment,
    LawStatus,
    ObserverNetworkSource,
    RefinementStatus,
    RelationReplayRow,
    ResponseStatus,
)

logger = logging.getLogger(__name__)


def edge_judgment(source: ObserverNetworkSource, edge_id: str) -> EdgeJudgment:
    """Replay the committed raw P1-A/P1-A2 source and actual translation table."""
    logger.debug("edge_judgment entry edge=%s", edge_id)
    edge = next((x for x in source.translations if x.edge_id == edge_id), None)
    if edge is None:
        reject("edge-judgment-edge-missing")
    src = next((x for x in source.observers if x.observer_id == edge.source_observer_id), None)
    dst = next((x for x in source.observers if x.observer_id == edge.target_observer_id), None)
    if src is None or dst is None:
        reject("edge-judgment-endpoint-missing")
    op = operational_edge_map(source, edge_id)
    raw = replay_raw_pair(source, src.observer_id, dst.observer_id)
    input_commitments = {item.stage_commitment: item.commitment for item in source.inputs}
    relation_rows = tuple(
        RelationReplayRow(
            row.pair_index,
            input_commitments[row.left[1]],
            input_commitments[row.right[1]],
            row.fine_outcome,
            row.coarse_outcome,
            row.row_digest,
        )
        for row in raw.pairs
    )
    relation_counterexample = witness_input_ids(source, raw, "preservation")
    p1_commutes = False
    if not op.domain:
        translatable = LawStatus.VACUOUS_TYPED
        relation = preservation = domain_equal = LawStatus.NOT_ESTABLISHED
        separator = None
    else:
        translatable = LawStatus.ESTABLISHED
        relation = map_p1_law(raw.preservation)
        domain_equal = map_p1_law(raw.domain_equality)
        p1_commutes = (
            raw.forward.morphism_status is MorphismEvidenceStatus.P1A_ESTABLISHED
            and raw.forward.proposal_status is ProposalStatus.COMMUTES_ON_SCOPE
        )
        preservation = LawStatus.ESTABLISHED if _map_preserves(source, op) else LawStatus.REFUTED
        separator = (
            witness_input_ids(source, raw, "reflection") if map_p1_law(raw.reflection) is LawStatus.REFUTED else None
        )
    if all(x is LawStatus.ESTABLISHED for x in (relation, preservation, domain_equal)):
        refinement = RefinementStatus.STRICT if separator is not None else RefinementStatus.NONSTRICT
    else:
        refinement = RefinementStatus.OPEN
    identity = (
        edge_id,
        op.map_digest,
        translatable.value,
        relation.value,
        preservation.value,
        domain_equal.value,
        refinement.value,
        "" if separator is None else ":".join(separator),
        "" if relation_counterexample is None else ":".join(relation_counterexample),
        raw.judgment_digest,
        str(p1_commutes),
    )
    jid = records_digest("p3t-edge-judgment-v2", identity, tuple(x.row_digest for x in relation_rows))
    result = EdgeJudgment(
        edge_id,
        op,
        relation_rows,
        relation_counterexample,
        translatable,
        relation,
        preservation,
        domain_equal,
        refinement,
        separator,
        jid,
    )
    logger.debug("edge_judgment exit edge=%s refinement=%s", edge_id, refinement.value)
    return result


def isomorphism_judgment(
    source: ObserverNetworkSource, forward: EdgeJudgment, reverse: EdgeJudgment
) -> IsomorphismJudgment:
    """Require two nonvacuous raw-backed commuting maps, exact domains, and units."""
    logger.debug("isomorphism_judgment entry forward=%s reverse=%s", forward.edge_id, reverse.edge_id)
    f_edge = next((x for x in source.translations if x.edge_id == forward.edge_id), None)
    r_edge = next((x for x in source.translations if x.edge_id == reverse.edge_id), None)
    if (
        f_edge is None
        or r_edge is None
        or (f_edge.source_observer_id, f_edge.target_observer_id)
        != (r_edge.target_observer_id, r_edge.source_observer_id)
    ):
        reject("isomorphism-edges-not-opposite")
    if not forward.operational_map.domain or not reverse.operational_map.domain:
        missing = LawStatus.NOT_ESTABLISHED
        result = IsomorphismJudgment(
            forward.edge_id,
            reverse.edge_id,
            missing,
            missing,
            missing,
            missing,
            missing,
            missing,
            records_digest("p3t-isomorphism-v2", (forward.edge_id, reverse.edge_id, missing.value), ()),
        )
        logger.debug("isomorphism_judgment exit vacuous")
        return result
    frows = dict(forward.operational_map.rows)
    rrows = dict(reverse.operational_map.rows)
    f_image = ready_image(source, f_edge.source_observer_id)
    r_image = ready_image(source, r_edge.source_observer_id)
    f_unit = (
        LawStatus.ESTABLISHED
        if set(frows) == set(f_image) and all(rrows.get(frows[x]) == x for x in f_image)
        else LawStatus.REFUTED
    )
    r_unit = (
        LawStatus.ESTABLISHED
        if set(rrows) == set(r_image) and all(frows.get(rrows[x]) == x for x in r_image)
        else LawStatus.REFUTED
    )
    fobs = next((x for x in source.observers if x.observer_id == f_edge.source_observer_id), None)
    robs = next((x for x in source.observers if x.observer_id == r_edge.source_observer_id), None)
    if fobs is None or robs is None:
        reject("isomorphism-observer-endpoint-missing")
    domains_equal = tuple((x.response.status, x.response.reason_id) for x in fobs.rows) == tuple(
        (x.response.status, x.response.reason_id) for x in robs.rows
    )
    domain_law = LawStatus.ESTABLISHED if domains_equal else LawStatus.REFUTED
    laws = (
        forward.relation_preserving,
        reverse.relation_preserving,
        forward.translation_preserving,
        reverse.translation_preserving,
        f_unit,
        r_unit,
        domain_law,
    )
    if all(x is LawStatus.ESTABLISHED for x in laws):
        status = LawStatus.ESTABLISHED
    elif any(x is LawStatus.REFUTED for x in laws):
        status = LawStatus.REFUTED
    else:
        status = LawStatus.NOT_ESTABLISHED
    jid = records_digest(
        "p3t-isomorphism-v2", (forward.edge_id, reverse.edge_id, status.value, *(x.value for x in laws)), ()
    )
    result = IsomorphismJudgment(
        forward.edge_id,
        reverse.edge_id,
        status,
        domain_law,
        f_unit,
        r_unit,
        forward.translation_preserving,
        reverse.translation_preserving,
        jid,
    )
    logger.debug("isomorphism_judgment exit status=%s", status.value)
    return result


def composition_judgment(source: ObserverNetworkSource, left: EdgeJudgment, right: EdgeJudgment) -> CompositionJudgment:
    """Separate raw A2 transitivity from full-image commuting composition."""
    logger.debug("composition_judgment entry left=%s right=%s", left.edge_id, right.edge_id)
    op = compose_maps(left.operational_map, right.operational_map)
    if not left.operational_map.domain or not right.operational_map.domain or not op.domain:
        relation = translation = LawStatus.NOT_ESTABLISHED
    else:
        actual_relation = LawStatus.ESTABLISHED
        if op.source_observer_id != op.target_observer_id:
            raw = replay_raw_pair(source, op.source_observer_id, op.target_observer_id)
            actual_relation = map_p1_law(raw.preservation)
        relation = (
            LawStatus.ESTABLISHED
            if left.relation_preserving is LawStatus.ESTABLISHED
            and right.relation_preserving is LawStatus.ESTABLISHED
            and actual_relation is LawStatus.ESTABLISHED
            else LawStatus.NOT_ESTABLISHED
        )
        translation = (
            LawStatus.ESTABLISHED
            if left.translation_preserving is LawStatus.ESTABLISHED
            and right.translation_preserving is LawStatus.ESTABLISHED
            and _map_preserves(source, op)
            else LawStatus.NOT_ESTABLISHED
        )
    jid = records_digest(
        "p3t-composition-judgment-v2", (*op.path_edge_ids, op.map_digest, relation.value, translation.value), ()
    )
    result = CompositionJudgment((left.edge_id, right.edge_id), op, relation, translation, jid)
    logger.debug("composition_judgment exit translation=%s", translation.value)
    return result


def path_laws(source: ObserverNetworkSource, op, parent_edges: tuple[EdgeJudgment, ...]) -> tuple[LawStatus, LawStatus]:
    """Derive arbitrary finite-path relation and translation laws from all parents."""
    logger.debug("path_laws entry edges=%d", len(parent_edges))
    if not op.domain or any(x.refinement is RefinementStatus.OPEN for x in parent_edges):
        result = (LawStatus.NOT_ESTABLISHED, LawStatus.NOT_ESTABLISHED)
    else:
        relation = LawStatus.ESTABLISHED
        if op.source_observer_id != op.target_observer_id:
            raw = replay_raw_pair(source, op.source_observer_id, op.target_observer_id)
            relation = map_p1_law(raw.preservation)
        translation = (
            LawStatus.ESTABLISHED
            if all(x.translation_preserving is LawStatus.ESTABLISHED for x in parent_edges)
            and _map_preserves(source, op)
            else LawStatus.NOT_ESTABLISHED
        )
        result = (relation, translation)
    logger.debug("path_laws exit relation=%s translation=%s", result[0].value, result[1].value)
    return result


def raw_pair_witnesses(source: ObserverNetworkSource, source_id: str, target_id: str):
    """Return raw A2 preservation/reflection facts and exact witnesses."""
    logger.debug("raw_pair_witnesses entry")
    raw = replay_raw_pair(source, source_id, target_id)
    result = (
        map_p1_law(raw.preservation),
        map_p1_law(raw.reflection),
        witness_input_ids(source, raw, "preservation"),
        witness_input_ids(source, raw, "reflection"),
    )
    logger.debug("raw_pair_witnesses exit")
    return result


def _map_preserves(source: ObserverNetworkSource, op) -> bool:
    """Replay one derived map against every ready occurrence; nonready stays nonready."""
    logger.debug("map_preserves entry")
    src = next((x for x in source.observers if x.observer_id == op.source_observer_id), None)
    dst = next((x for x in source.observers if x.observer_id == op.target_observer_id), None)
    if src is None or dst is None:
        reject("map-preservation-endpoint-missing")
    table = dict(op.rows)
    image = ready_image(source, src.observer_id)
    result = (
        bool(op.domain)
        and set(image) <= set(op.domain)
        and all(
            row.response.status is not ResponseStatus.READY
            or (
                dst.rows[i].response.status is ResponseStatus.READY
                and table[row.response.value.value_digest] == dst.rows[i].response.value.value_digest
            )
            for i, row in enumerate(src.rows)
        )
    )
    logger.debug("map_preserves exit result=%s", result)
    return result


def evaluation_domain_judgment(source: ObserverNetworkSource, observer_id: str) -> EvaluationDomainJudgment:
    """Retain every full tagged response without coercing blockage or silence."""
    logger.debug("evaluation_domain_judgment entry observer=%s", observer_id)
    observer = next((x for x in source.observers if x.observer_id == observer_id), None)
    if observer is None:
        reject("evaluation-domain-observer-missing")
    inputs = tuple(x.input_commitment for x in observer.rows)
    statuses = tuple(x.response.status for x in observer.rows)
    responses = tuple(x.response.response_digest for x in observer.rows)
    ready_inputs = tuple(x.input_commitment for x in observer.rows if x.response.status is ResponseStatus.READY)
    jid = records_digest(
        "p3t-evaluation-domain-v2", (observer_id, *(x.value for x in statuses)), inputs + responses + ready_inputs
    )
    result = EvaluationDomainJudgment(observer_id, inputs, statuses, responses, ready_inputs, jid)
    logger.debug("evaluation_domain_judgment exit observer=%s", observer_id)
    return result
