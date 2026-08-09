"""Canonical complete raw-request encoding and exact byte charge for P1-C3."""

from __future__ import annotations

import logging

from .digest import frame, kind_bytes, recurrence_bytes

logger = logging.getLogger(__name__)
ENCODING_VERSION = "p1-c3-request-encoding-v1"


def _record(tag: str, fields: tuple[tuple[str, bytes], ...]) -> bytes:
    """Encode a versioned tagged record with an explicit field count."""
    logger.debug("c3 encode record entry tag=%s fields=%d", tag, len(fields))
    result = frame("record-tag", tag.encode()) + len(fields).to_bytes(8, "big")
    result += b"".join(frame(name, value) for name, value in fields)
    logger.debug("c3 encode record exit tag=%s bytes=%d", tag, len(result))
    return result


def _rows(tag: str, values: tuple[bytes, ...]) -> bytes:
    """Encode a counted ordered row family."""
    logger.debug("c3 encode rows entry tag=%s count=%d", tag, len(values))
    result = len(values).to_bytes(8, "big") + b"".join(frame(tag, item) for item in values)
    logger.debug("c3 encode rows exit tag=%s bytes=%d", tag, len(result))
    return result


def _observer(value) -> bytes:
    """Encode every validated internal-observer field."""
    logger.debug("c3 encode observer entry")
    result = _record("internal-observer-v1", (
        ("id", value.observer_id.encode()), ("canonical", value.canonical),
        ("kind", kind_bytes(value.response_kind)),
    ))
    logger.debug("c3 encode observer exit")
    return result


def _doctrine(value) -> bytes:
    """Encode the complete doctrine, including unbridged observers."""
    logger.debug("c3 encode doctrine entry observers=%d", len(value.observers))
    result = _record("observer-doctrine-v1", (
        ("id", value.doctrine_id.encode()), ("admission", value.admission_rule.encode()),
        ("metadata", _rows("metadata", tuple(item.encode() for item in value.metadata))),
        ("observers", _rows("observer", tuple(_observer(item) for item in value.observers))),
        ("version", value.version.encode()), ("fingerprint", value.fingerprint.encode()),
    ))
    logger.debug("c3 encode doctrine exit bytes=%d", len(result))
    return result


def _stage(value) -> bytes:
    """Encode a complete diagram stage and all admitted observer snapshots."""
    logger.debug("c3 encode diagram stage entry")
    result = _record("diagram-stage-v1", (
        ("id", value.stage_id.encode()), ("recurrence", recurrence_bytes(value.representative)),
        ("doctrine", value.doctrine_id.encode()),
        ("observers", _rows("observer", tuple(_observer(item) for item in value.observers))),
    ))
    logger.debug("c3 encode diagram stage exit")
    return result


def _diagram(value) -> bytes:
    """Encode every diagram member, commitment, edge, path, and protocol field."""
    logger.debug("c3 encode diagram entry")
    edges = tuple(_record("diagram-edge-v1", (
        ("id", item.edge_id.encode()), ("lower", item.lower_stage_id.encode()),
        ("upper", item.upper_stage_id.encode()),
        ("observers", _rows("observer-id", tuple(x.encode() for x in item.preserved_observer_ids))),
    )) for item in value.edges)
    paths = tuple(_record("diagram-path-v1", (
        ("id", item.path_id.encode()),
        ("edges", _rows("edge-id", tuple(x.encode() for x in item.edge_ids))),
        ("start", item.start_stage_id.encode()), ("end", item.end_stage_id.encode()),
    )) for item in value.paths)
    result = _record("finite-diagram-source-v1", (
        ("id", value.source_id.encode()), ("doctrine", value.doctrine_fingerprint.encode()),
        ("stages", _rows("stage", tuple(_stage(item) for item in value.stages))),
        ("stage-commitments", _rows("digest", tuple(x.encode() for x in value.stage_commitments))),
        ("edges", _rows("edge", edges)), ("paths", _rows("path", paths)),
        ("path-commitments", _rows("digest", tuple(x.encode() for x in value.path_commitments))),
        ("digest", value.source_digest.encode()), ("version", value.version.encode()),
        ("scope", value.scope.encode()),
    ))
    logger.debug("c3 encode diagram exit bytes=%d", len(result))
    return result


def _plan(value) -> bytes:
    """Encode complete fork/join path identities, commitments, and alignment."""
    logger.debug("c3 encode plan entry")
    alignment = tuple(_record("alignment-point-v1", (
        ("left", item.left_index.to_bytes(8, "big")),
        ("right", item.right_index.to_bytes(8, "big")),
    )) for item in value.alignment)
    result = _record("fork-join-plan-v1", (
        ("id", value.plan_id.encode()), ("diagram", value.diagram_digest.encode()),
        ("fork", value.fork_stage_commitment.encode()),
        ("left-branch", value.left_branch_path_id.encode()),
        ("right-branch", value.right_branch_path_id.encode()),
        ("left-join", b"absent" if value.left_join_path_id is None else value.left_join_path_id.encode()),
        ("right-join", b"absent" if value.right_join_path_id is None else value.right_join_path_id.encode()),
        ("join", b"absent" if value.join_stage_commitment is None else value.join_stage_commitment.encode()),
        ("alignment", _rows("point", alignment)), ("transport", value.transport_digest.encode()),
        ("digest", value.plan_digest.encode()), ("version", value.version.encode()),
        ("scope", value.scope.encode()),
    ))
    logger.debug("c3 encode plan exit bytes=%d", len(result))
    return result


def _binding(value) -> bytes:
    """Encode complete P1-A source membership, including unbridged members."""
    logger.debug("c3 encode binding entry")
    result = _record("observer-source-binding-v1", (
        ("id", value.binding_id.encode()), ("doctrine", value.doctrine_fingerprint.encode()),
        ("observer-ids", _rows("id", tuple(x.encode() for x in value.observer_ids))),
        ("observer-digests", _rows("digest", tuple(x.encode() for x in value.observer_digests))),
        ("membership", value.membership_digest.encode()), ("scope", value.scope.encode()),
    ))
    logger.debug("c3 encode binding exit bytes=%d", len(result))
    return result


def _a2_source(value) -> bytes:
    """Encode every A2 stage recurrence and source protocol field."""
    logger.debug("c3 encode a2 source entry")
    stages = tuple(_record("relation-stage-v1", (
        ("id", item.stage_id.encode()), ("recurrence", recurrence_bytes(item.recurrence)),
        ("commitment", item.commitment.encode()),
    )) for item in value.stages)
    result = _record("relation-evaluation-source-v1", (
        ("doctrine", value.doctrine_fingerprint.encode()),
        ("stages", _rows("stage", stages)),
        ("order", _rows("digest", tuple(x.encode() for x in value.ordered_commitments))),
        ("binding", value.observer_source_digest.encode()),
        ("version", value.version.encode()), ("digest", value.source_digest.encode()),
    ))
    logger.debug("c3 encode a2 source exit bytes=%d", len(result))
    return result


def _bridge(value) -> bytes:
    """Encode every exact observer/stage bridge field and protocol marker."""
    logger.debug("c3 encode bridge entry")
    observers = tuple(_record("observer-bridge-row-v1", (
        ("p0-id", item.diagram_observer_id.encode()), ("p1a-id", item.p1a_observer_id.encode()),
        ("canonical", item.canonical_observer), ("kind", item.response_kind_digest.encode()),
        ("p0-membership", item.diagram_membership_digest.encode()),
        ("p1a-membership", item.p1a_membership_digest.encode()),
        ("digest", item.row_digest.encode()),
    )) for item in value.observer_rows)
    stages = tuple(_record("stage-bridge-row-v1", (
        ("p0-id", item.diagram_stage_id.encode()),
        ("p0-commitment", item.diagram_stage_commitment.encode()),
        ("recurrence", recurrence_bytes(item.recurrence)),
        ("recurrence-digest", item.recurrence_digest.encode()),
        ("a2-id", item.relation_stage_id.encode()),
        ("a2-commitment", item.relation_stage_commitment.encode()),
        ("digest", item.row_digest.encode()),
    )) for item in value.stage_rows)
    result = _record("p0-p1a-response-bridge-v1", (
        ("p0", value.p0_doctrine_fingerprint.encode()), ("diagram", value.diagram_digest.encode()),
        ("p1a", value.p1a_doctrine_fingerprint.encode()),
        ("binding", value.p1a_observer_source_digest.encode()),
        ("a2-source", value.a2_stage_source_digest.encode()),
        ("observers", _rows("row", observers)), ("stages", _rows("row", stages)),
        ("a2-order", _rows("digest", tuple(x.encode() for x in value.a2_ordered_commitments))),
        ("digest", value.bridge_digest.encode()), ("version", value.version.encode()),
        ("scope", value.scope.encode()),
    ))
    logger.debug("c3 encode bridge exit bytes=%d", len(result))
    return result


def _spec(value) -> bytes:
    """Encode every public spec and nested raw morphism/scope/policy field."""
    logger.debug("c3 encode spec entry")
    morphism = _record("morphism-replay-spec-v1", (
        ("id", value.morphism.morphism_id.encode()),
        ("fine", value.morphism.fine_observer_id.encode()),
        ("coarse", value.morphism.coarse_observer_id.encode()),
        ("projection", _rows("step", tuple(x.value.encode() for x in value.morphism.projection))),
    ))
    scope = value.relation_scope
    scope_bytes = _record("observer-relation-scope-v1", (
        ("doctrine", scope.doctrine_fingerprint.encode()),
        ("binding", scope.observer_source_digest.encode()),
        ("source", scope.stage_source_digest.encode()), ("fine", scope.fine_observer_id.encode()),
        ("coarse", scope.coarse_observer_id.encode()),
        ("stages", _rows("stage", tuple(_rows("key", tuple(x.encode() for x in key)) for key in scope.stages))),
        ("pairs", _rows("pair", tuple(_rows("key", tuple(x.encode() for key in pair for x in key)) for pair in scope.ordered_pairs))),
        ("mode", scope.mode.value.encode()), ("digest", scope.scope_digest.encode()),
    ))
    policy = value.relation_policy
    nested_policy = _record("relation-resource-policy-v1", (
        ("version", policy.version.encode()), ("checks", policy.max_cost.to_bytes(8, "big")),
        ("bytes", policy.max_encoded_bytes.to_bytes(8, "big")),
        ("digest", policy.policy_digest.encode()),
    ))
    result = _record("translated-echo-transport-spec-v1", (
        ("id", value.spec_id.encode()), ("bridge", value.bridge_digest.encode()),
        ("plan", value.plan_digest.encode()), ("direction", value.direction.value.encode()),
        ("diagram-fine", value.diagram_fine_observer_id.encode()),
        ("diagram-coarse", value.diagram_coarse_observer_id.encode()),
        ("p1a-fine", value.p1a_fine_observer_id.encode()),
        ("p1a-coarse", value.p1a_coarse_observer_id.encode()),
        ("morphism", morphism), ("relation-scope", scope_bytes),
        ("relation-policy", nested_policy),
        ("preservation", value.required_preservation.value.encode()),
        ("domain", value.required_domain_equality.value.encode()),
        ("class", value.required_class.value.encode()),
        ("loss", b"absent" if value.required_loss is None else value.required_loss.value.encode()),
        ("digest", value.spec_digest.encode()), ("version", value.version.encode()),
        ("mode", value.mode.value.encode()), ("scope", value.scope.encode()),
    ))
    logger.debug("c3 encode spec exit bytes=%d", len(result))
    return result


def canonical_request_bytes(p0, diagram, plan, p1a, binding, source, bridge, spec, policy) -> bytes:
    """Encode all nine validated raw request structures exactly once in argument order."""
    logger.debug("canonical_request_bytes entry")
    outer_policy = _record("translated-confluence-policy-v1", (
        ("version", policy.version.encode()), ("checks", policy.max_checks.to_bytes(8, "big")),
        ("bytes", policy.max_bytes.to_bytes(8, "big")), ("digest", policy.policy_digest.encode()),
    ))
    result = _record("translated-confluence-request-v1", (
        ("encoding-version", ENCODING_VERSION.encode()), ("p0-doctrine", _doctrine(p0)),
        ("diagram", _diagram(diagram)), ("plan", _plan(plan)),
        ("p1a-doctrine", _doctrine(p1a)), ("p1a-binding", _binding(binding)),
        ("a2-source", _a2_source(source)), ("bridge", _bridge(bridge)),
        ("spec", _spec(spec)), ("outer-policy", outer_policy),
    ))
    logger.debug("canonical_request_bytes exit bytes=%d", len(result))
    return result
