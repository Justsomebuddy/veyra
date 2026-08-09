"""Executable level-1 certificate for P1-C3 typed translated confluence."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..confluence import (
    diagram_edge, diagram_path, direct_echo_transport, finite_diagram_source,
    fork_join_plan,
)
from ..confluence.types import AlignmentPoint, ConfluenceStatus
from ..observer_core_kernel import crest_observer
from ..observer_core_types import Input, Pair
from ..observer.morphism import (
    ProjectionStep, observer_source_binding, p1a_observer_morphism_doctrine,
)
from ..observer.relations.core import (
    ComparisonMode, LossStatus, RelationClass, morphism_replay_spec,
    observer_relation_scope, relation_evaluation_source, relation_resource_policy,
)
from ..ontology.core import internal_observer, ontology_stage
from ..ontology.doctrine import observer_doctrine
from ..proof_core_types import Pulse, Silence
from ..confluence.translated.core import (
    TranslatedConfluenceJudgment, TranslatedConfluenceResourceLimit,
    TranslationDirection, p0_p1a_response_bridge,
    translated_confluence_judgment, translated_confluence_policy,
    translated_echo_transport_spec, validate_translated_confluence_result,
)

logger = logging.getLogger(__name__)


def _recurrence(depth: int):
    """Construct one exact finite recurrence with bounded work."""
    logger.debug("c3 certificate recurrence entry depth=%d", depth)
    value = Silence()
    for _ in range(depth):
        value = Pulse(value)
    logger.debug("c3 certificate recurrence exit depth=%d", depth)
    return value


def _fixture():
    """Build one raw-source strict-refinement translated fork."""
    logger.debug("c3 certificate fixture entry")
    crest = crest_observer()
    p0 = observer_doctrine(
        "C3-certificate", "closed-r11-c3", ("finite", "translated"),
        (
            internal_observer("diagram-fine", Pair(crest, Input())),
            internal_observer("diagram-coarse", crest),
        ), version="p1-c3-certificate-p0-v1",
    )
    recurrences = (
        ("fork", _recurrence(1)), ("left", _recurrence(1)),
        ("right", _recurrence(2)), ("join", _recurrence(1)),
    )
    stages = tuple(ontology_stage(name, term, p0, 2) for name, term in recurrences)
    edges = (
        diagram_edge("fl", "fork", "left", ("diagram-coarse",)),
        diagram_edge("fr", "fork", "right", ("diagram-coarse",)),
        diagram_edge("lj", "left", "join", ("diagram-coarse",)),
        diagram_edge("rj", "right", "join", ("diagram-coarse",)),
    )
    paths = (
        diagram_path("lb", ("fl",), "fork", "left"),
        diagram_path("rb", ("fr",), "fork", "right"),
        diagram_path("ljp", ("lj",), "left", "join"),
        diagram_path("rjp", ("rj",), "right", "join"),
    )
    diagram = finite_diagram_source(p0, "c3-certificate", stages, edges, paths)
    direct = direct_echo_transport(p0, ("diagram-fine", "diagram-coarse"))
    plan = fork_join_plan(
        p0, diagram, "c3-certificate-plan", "lb", "rb", "ljp", "rjp",
        (AlignmentPoint(0, 0), AlignmentPoint(1, 1), AlignmentPoint(2, 2)), direct,
    )
    p1a = p1a_observer_morphism_doctrine()
    binding = observer_source_binding(
        p1a, "c3-certificate-binding", ("coarse-crest", "fine-total"),
    )
    source = relation_evaluation_source(p1a, binding, recurrences)
    keys = tuple((row.stage_id, row.commitment) for row in source.stages)
    scope = observer_relation_scope(
        p1a, binding, source, "fine-total", "coarse-crest", keys,
        ComparisonMode.WITH_P1A_REPLAY,
    )
    morphism = morphism_replay_spec(
        "c3-certificate-morphism", "fine-total", "coarse-crest",
        (ProjectionStep.LEFT,),
    )
    bridge = p0_p1a_response_bridge(p0, diagram, p1a, binding, source)
    spec = translated_echo_transport_spec(
        p0, diagram, plan, p1a, binding, source, bridge, "c3-certificate-spec",
        TranslationDirection.LEFT_FINE_TO_RIGHT_COARSE,
        "diagram-fine", "diagram-coarse", morphism, scope,
        relation_resource_policy(), RelationClass.STRICT_REFINEMENT_ON_SCOPE,
        LossStatus.LOSSY_ON_SCOPE,
    )
    logger.debug("c3 certificate fixture exit")
    return p0, diagram, plan, p1a, binding, source, bridge, spec


def certify_translated_confluence_p1c3() -> Certificate:
    """Certify one finite asymmetric raw-replayed translated cell and refusal."""
    logger.debug("certify_translated_confluence_p1c3 entry")
    fixture = _fixture()
    policy = translated_confluence_policy()
    first = translated_confluence_judgment(*fixture, policy)
    second = validate_translated_confluence_result(*fixture, policy, first)
    refused = translated_confluence_judgment(
        *fixture, translated_confluence_policy(max_checks=1, max_bytes=1),
    )
    passed = (
        type(first) is TranslatedConfluenceJudgment
        and type(second) is TranslatedConfluenceJudgment
        and first is not second and first.judgment_digest == second.judgment_digest
        and first.status is ConfluenceStatus.ESTABLISHED
        and first.relation_class is RelationClass.STRICT_REFINEMENT_ON_SCOPE
        and first.information_loss is LossStatus.LOSSY_ON_SCOPE
        and first.transport_cell is not None
        and len(first.transport_cell.response_rows) == 3
        and all(row.status is ConfluenceStatus.ESTABLISHED
                for row in first.transport_cell.response_rows)
        and type(refused) is TranslatedConfluenceResourceLimit
        and not hasattr(refused, "transport_cell")
    )
    method = (
        "exact byte-and-kind P0/P1-A bridge, raw strong P1-A and complete A2 replay, "
        "asymmetric every-occurrence translation, atomic hard-first preflight, and fresh revalidation"
    )
    detail = (
        "one finite typed translated cell only; no observer identity, reverse map, "
        "catalog confluence, object formation, all-depth family, completed carrier, or promotion"
    )
    result = Certificate("translated_confluence_p1c3", method, passed, detail, 1)
    logger.debug("certify_translated_confluence_p1c3 exit passed=%s", passed)
    return result
