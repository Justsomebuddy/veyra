"""Atomic source capture and hard-first resource preflight for P1-C3."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from ..plan import (
    build_direct_echo_transport, snapshot_fork_join_plan,
)
from ..runtime import _edge_check_count
from ..types import FiniteDiagramSource, ForkJoinPlan
from ..validation import (
    snapshot_confluence_doctrine, snapshot_finite_diagram_source,
)
from ...observer.morphism import (
    ObserverSourceBinding, snapshot_morphism_doctrine, snapshot_source_binding,
)
from ...observer.relations.preflight import (
    encoded_request_bytes, request_cost, snapshot_request,
)
from ...observer.relations.request import snapshot_stage_source
from ...observer.relations.types import RelationEvaluationSource
from ...ontology.types import ObserverDoctrine
from .bridge import snapshot_response_bridge
from .digest import digest, sequence
from .encoding import canonical_request_bytes
from .transport import (
    shallow_spec, snapshot_translated_policy, snapshot_translated_spec,
)
from .types import (
    P0P1AResponseBridgeSource, TranslatedConfluencePolicy,
    TranslatedConfluenceResourceLimit, TranslatedEchoTransportSpec,
    TranslatedResourceBound, TranslatedResourceSource,
)
from .validation import reject

logger = logging.getLogger(__name__)
HARD_CHECKS = 4096
HARD_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class TranslatedConfluenceRequest:
    """A completely captured semantics-free C3 request."""

    p0_doctrine: ObserverDoctrine
    diagram: FiniteDiagramSource
    plan: ForkJoinPlan
    p1a_doctrine: ObserverDoctrine
    p1a_source: ObserverSourceBinding
    a2_stage_source: RelationEvaluationSource
    bridge: P0P1AResponseBridgeSource
    spec: TranslatedEchoTransportSpec
    policy: TranslatedConfluencePolicy
    required_checks: int
    required_bytes: int
    a2_required_checks: int
    a2_required_bytes: int
    run_digest: str


def _history_ids(source: FiniteDiagramSource, plan: ForkJoinPlan) -> tuple[str, ...]:
    """Return every distinct stage required by both complete joined histories."""
    logger.debug("c3 preflight history_ids entry")
    if plan.left_join_path_id is None or plan.right_join_path_id is None:
        reject("translated-cell-requires-complete-separate-joins")
    paths = {row.path_id: row for row in source.paths}
    edges = {row.edge_id: row for row in source.edges}
    ordered: list[str] = []
    for first_id, second_id in (
        (plan.left_branch_path_id, plan.left_join_path_id),
        (plan.right_branch_path_id, plan.right_join_path_id),
    ):
        edge_ids = paths[first_id].edge_ids + paths[second_id].edge_ids
        ids = (edges[edge_ids[0]].lower_stage_id, *(edges[item].upper_stage_id for item in edge_ids))
        for item in ids:
            if item not in ordered:
                ordered.append(item)
    result = tuple(ordered)
    logger.debug("c3 preflight history_ids exit count=%d", len(result))
    return result


def _encoded_bytes(
    p0: ObserverDoctrine, diagram: FiniteDiagramSource, plan: ForkJoinPlan,
    p1a: ObserverDoctrine, binding: ObserverSourceBinding,
    source: RelationEvaluationSource, bridge: P0P1AResponseBridgeSource,
    spec: TranslatedEchoTransportSpec, policy: TranslatedConfluencePolicy,
) -> int:
    """Count the complete versioned canonical raw request before semantics."""
    logger.debug("c3 preflight encoded_bytes entry")
    canonical = canonical_request_bytes(
        p0, diagram, plan, p1a, binding, source, bridge, spec, policy,
    )
    result = len(canonical)
    logger.debug("c3 preflight encoded_bytes exit bytes=%d", result)
    return result


def snapshot_translated_request(
    raw_p0_doctrine: ObserverDoctrine, raw_diagram: FiniteDiagramSource,
    raw_plan: ForkJoinPlan, raw_p1a_doctrine: ObserverDoctrine,
    raw_p1a_source: ObserverSourceBinding,
    raw_a2_stage_source: RelationEvaluationSource,
    raw_bridge: P0P1AResponseBridgeSource,
    raw_spec: TranslatedEchoTransportSpec,
    raw_policy: TranslatedConfluencePolicy,
) -> TranslatedConfluenceRequest:
    """Capture all sources and derive resource charges without observe/translate."""
    logger.debug("snapshot_translated_request entry")
    p0 = snapshot_confluence_doctrine(raw_p0_doctrine)
    diagram = snapshot_finite_diagram_source(raw_diagram, p0)
    p1a = snapshot_morphism_doctrine(raw_p1a_doctrine)
    binding = snapshot_source_binding(raw_p1a_source, p1a)
    source = snapshot_stage_source(raw_a2_stage_source, p1a, binding)
    bridge = snapshot_response_bridge(p0, diagram, p1a, binding, source, raw_bridge)
    supplied_spec = shallow_spec(raw_spec)
    placeholder = build_direct_echo_transport(
        p0, (supplied_spec[4], supplied_spec[5]),
    )
    plan = snapshot_fork_join_plan(raw_plan, diagram, placeholder, p0)
    spec = snapshot_translated_spec(p0, diagram, plan, p1a, binding, source, bridge, raw_spec)
    policy = snapshot_translated_policy(raw_policy)
    required_stages = _history_ids(diagram, plan)
    bridged_stages = {row.diagram_stage_id for row in bridge.stage_rows}
    if any(item not in bridged_stages for item in required_stages):
        reject("translated-history-stage-bridge-incomplete")
    a2_request = snapshot_request(
        p1a, binding, source, spec.relation_scope, spec.morphism, None,
        spec.relation_policy,
    )[1]
    a2_checks, a2_bytes = request_cost(a2_request), encoded_request_bytes(a2_request)
    checks = (
        _edge_check_count(diagram, plan) + len(plan.alignment) + a2_checks
        + len(bridge.observer_rows) + len(bridge.stage_rows)
    )
    encoded = _encoded_bytes(
        p0, diagram, plan, p1a, binding, source, bridge, spec, policy,
    )
    run_digest = digest("p1-c3-run-v1", (
        ("sources", sequence("digest", (
            p0.fingerprint, diagram.source_digest, plan.plan_digest, p1a.fingerprint,
            binding.membership_digest, source.source_digest, bridge.bridge_digest,
            spec.spec_digest, policy.policy_digest,
        ))),
        ("checks", checks.to_bytes(8, "big")), ("bytes", encoded.to_bytes(8, "big")),
    ))
    result = TranslatedConfluenceRequest(
        p0, diagram, plan, p1a, binding, source, bridge, spec, policy,
        checks, encoded, a2_checks, a2_bytes, run_digest,
    )
    logger.debug("snapshot_translated_request exit checks=%d bytes=%d", checks, encoded)
    return result


def translated_preflight(
    request: TranslatedConfluenceRequest,
) -> TranslatedConfluenceResourceLimit | None:
    """Apply hard invariants, then byte policy, then check policy atomically."""
    logger.debug("translated_preflight entry")
    if request.required_checks > HARD_CHECKS or request.required_bytes > HARD_BYTES:
        reject("translated-confluence-hard-cap")
    failures = (
        (
            request.required_bytes > request.policy.max_bytes,
            TranslatedResourceBound.BYTES, TranslatedResourceSource.OUTER,
            request.required_bytes, request.policy.max_bytes,
        ),
        (
            request.a2_required_bytes > request.spec.relation_policy.max_encoded_bytes,
            TranslatedResourceBound.BYTES, TranslatedResourceSource.NESTED_A2,
            request.a2_required_bytes, request.spec.relation_policy.max_encoded_bytes,
        ),
        (
            request.required_checks > request.policy.max_checks,
            TranslatedResourceBound.CHECKS, TranslatedResourceSource.OUTER,
            request.required_checks, request.policy.max_checks,
        ),
        (
            request.a2_required_checks > request.spec.relation_policy.max_cost,
            TranslatedResourceBound.CHECKS, TranslatedResourceSource.NESTED_A2,
            request.a2_required_checks, request.spec.relation_policy.max_cost,
        ),
    )
    failure = next((item for item in failures if item[0]), None)
    if failure is None:
        logger.debug("translated_preflight exit admitted")
        return None
    _, failed_bound, limit_source, failed_required, failed_allowed = failure
    refusal_digest = digest("p1-c3-resource-refusal-v1", (
        ("policy", request.policy.policy_digest.encode()),
        ("run", request.run_digest.encode()),
        ("required-checks", request.required_checks.to_bytes(8, "big")),
        ("required-bytes", request.required_bytes.to_bytes(8, "big")),
        ("failed-bound", failed_bound.value.encode()),
        ("limit-source", limit_source.value.encode()),
        ("failed-required", failed_required.to_bytes(8, "big")),
        ("failed-allowed", failed_allowed.to_bytes(8, "big")),
    ))
    result = TranslatedConfluenceResourceLimit(
        request.policy.version, request.policy.policy_digest,
        request.diagram.source_digest, request.plan.plan_digest,
        request.bridge.bridge_digest, request.spec.spec_digest,
        request.required_checks, request.policy.max_checks,
        request.required_bytes, request.policy.max_bytes,
        failed_bound, limit_source, failed_required, failed_allowed,
        refusal_digest,
    )
    logger.debug(
        "translated_preflight exit refused bound=%s source=%s",
        failed_bound.value, limit_source.value,
    )
    return result
