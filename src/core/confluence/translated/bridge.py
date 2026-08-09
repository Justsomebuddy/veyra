"""Exact P0-to-P1-A observer and stage bridge for P1-C3."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import logging

from ..types import FiniteDiagramSource
from ..validation import (
    ConfluenceValidationError, snapshot_confluence_doctrine,
    snapshot_finite_diagram_source,
)
from ...observer.morphism import (
    ObserverMorphismValidationError, ObserverSourceBinding,
    snapshot_source_binding, snapshot_morphism_doctrine,
)
from ...observer.relations.request import snapshot_stage_source
from ...observer.relations.types import RelationEvaluationSource
from ...observer.relations.validation import (
    ObserverRelationValidationError, snapshot_recurrence,
)
from ...ontology.doctrine import stage_commitment
from ...ontology.types import ObserverDoctrine
from .digest import digest, frame, kind_bytes, recurrence_bytes, sequence
from .types import (
    ObserverProgramBridgeRow, P0P1AResponseBridgeSource, StageInputBridgeRow,
)
from .validation import TranslatedConfluenceValidationError, hex_digest, reject

logger = logging.getLogger(__name__)
BRIDGE_VERSION = "p1-c3-bridge-v1"
BRIDGE_SCOPE = "exact-byte-kind-and-recurrence-source-bridge"


def _snapshot_sources(
    raw_p0_doctrine: ObserverDoctrine, raw_diagram: FiniteDiagramSource,
    raw_p1a_doctrine: ObserverDoctrine, raw_p1a_source: ObserverSourceBinding,
    raw_a2_stage_source: RelationEvaluationSource,
) -> tuple[ObserverDoctrine, FiniteDiagramSource, ObserverDoctrine, ObserverSourceBinding, RelationEvaluationSource]:
    """Capture every lower source while normalizing only validation failures."""
    logger.debug("c3 bridge snapshot_sources entry")
    try:
        p0 = snapshot_confluence_doctrine(raw_p0_doctrine)
        diagram = snapshot_finite_diagram_source(raw_diagram, p0)
        p1a = snapshot_morphism_doctrine(raw_p1a_doctrine)
        binding = snapshot_source_binding(raw_p1a_source, p1a)
        stages = snapshot_stage_source(raw_a2_stage_source, p1a, binding)
    except (ConfluenceValidationError, ObserverMorphismValidationError,
            ObserverRelationValidationError) as exc:
        logger.error("c3 bridge lower source rejected")
        raise TranslatedConfluenceValidationError("invalid-c3-bridge-source") from exc
    logger.debug("c3 bridge snapshot_sources exit")
    return p0, diagram, p1a, binding, stages


def _p0_membership(doctrine: ObserverDoctrine) -> str:
    """Commit the exact ordered P0 observer family used by the diagram."""
    logger.debug("c3 p0_membership entry")
    result = digest("p1-c3-p0-membership-v1", (
        ("doctrine", doctrine.fingerprint.encode()),
        ("ids", sequence("observer", tuple(row.observer_id for row in doctrine.observers))),
        ("programs", len(doctrine.observers).to_bytes(8, "big") + b"".join(
            frame("program", row.canonical) for row in doctrine.observers
        )),
    ))
    logger.debug("c3 p0_membership exit")
    return result


def _observer_rows(
    p0: ObserverDoctrine, p1a: ObserverDoctrine, binding: ObserverSourceBinding,
) -> tuple[ObserverProgramBridgeRow, ...]:
    """Infer only unique byte-identical and kind-identical observer mappings."""
    logger.debug("c3 observer_rows entry")
    members = {row.observer_id: row for row in p1a.observers if row.observer_id in binding.observer_ids}
    p0_membership = _p0_membership(p0)
    rows: list[ObserverProgramBridgeRow] = []
    used: set[str] = set()
    for left in p0.observers:
        matches = tuple(
            right for right in members.values()
            if right.canonical == left.canonical and right.response_kind == left.response_kind
        )
        if len(matches) > 1:
            reject("ambiguous-observer-program-bridge")
        if not matches:
            continue
        right = matches[0]
        if right.observer_id in used:
            reject("duplicate-p1a-observer-program-bridge")
        used.add(right.observer_id)
        kind_digest = sha256(kind_bytes(left.response_kind)).hexdigest()
        row_digest = digest("p1-c3-observer-bridge-row-v1", (
            ("p0-id", left.observer_id.encode()), ("p1a-id", right.observer_id.encode()),
            ("program", left.canonical), ("kind", kind_digest.encode()),
            ("p0-membership", p0_membership.encode()),
            ("p1a-membership", binding.membership_digest.encode()),
        ))
        rows.append(ObserverProgramBridgeRow(
            left.observer_id, right.observer_id, bytes(left.canonical), kind_digest,
            p0_membership, binding.membership_digest, row_digest,
        ))
    if not rows:
        reject("empty-observer-program-bridge")
    result = tuple(rows)
    logger.debug("c3 observer_rows exit rows=%d", len(result))
    return result


def _stage_rows(
    diagram: FiniteDiagramSource, source: RelationEvaluationSource,
) -> tuple[StageInputBridgeRow, ...]:
    """Infer exact same-ID, same-recurrence diagram-to-A2 stage bindings."""
    logger.debug("c3 stage_rows entry")
    relation = {row.stage_id: row for row in source.stages}
    rows: list[StageInputBridgeRow] = []
    for stage in diagram.stages:
        right = relation.get(stage.stage_id)
        if right is None:
            continue
        left_bytes, right_bytes = recurrence_bytes(stage.representative), recurrence_bytes(right.recurrence)
        if left_bytes != right_bytes:
            reject("same-stage-id-different-recurrence")
        recurrence_digest = sha256(left_bytes).hexdigest()
        left_commitment = stage_commitment(stage)
        row_digest = digest("p1-c3-stage-bridge-row-v1", (
            ("p0-id", stage.stage_id.encode()), ("p0-commitment", left_commitment.encode()),
            ("recurrence", recurrence_digest.encode()), ("a2-id", right.stage_id.encode()),
            ("a2-commitment", right.commitment.encode()),
        ))
        rows.append(StageInputBridgeRow(
            stage.stage_id, left_commitment, stage.representative,
            recurrence_digest, right.stage_id, right.commitment, row_digest,
        ))
    if not 1 <= len(rows) <= 32:
        reject("stage-program-bridge-count")
    result = tuple(rows)
    logger.debug("c3 stage_rows exit rows=%d", len(result))
    return result


def p0_p1a_response_bridge(
    raw_p0_doctrine: ObserverDoctrine, raw_diagram: FiniteDiagramSource,
    raw_p1a_doctrine: ObserverDoctrine, raw_p1a_source: ObserverSourceBinding,
    raw_a2_stage_source: RelationEvaluationSource,
) -> P0P1AResponseBridgeSource:
    """Build a response-free exact bridge solely from raw lower sources."""
    logger.debug("p0_p1a_response_bridge entry")
    p0, diagram, p1a, binding, source = _snapshot_sources(
        raw_p0_doctrine, raw_diagram, raw_p1a_doctrine,
        raw_p1a_source, raw_a2_stage_source,
    )
    observers, stages = _observer_rows(p0, p1a, binding), _stage_rows(diagram, source)
    bridge_digest = digest("p1-c3-response-bridge-v1", (
        ("version", BRIDGE_VERSION.encode()), ("scope", BRIDGE_SCOPE.encode()),
        ("p0", p0.fingerprint.encode()), ("diagram", diagram.source_digest.encode()),
        ("p1a", p1a.fingerprint.encode()), ("binding", binding.membership_digest.encode()),
        ("a2-source", source.source_digest.encode()),
        ("observer-rows", sequence("row", tuple(row.row_digest for row in observers))),
        ("stage-rows", sequence("row", tuple(row.row_digest for row in stages))),
        ("a2-order", sequence("commitment", source.ordered_commitments)),
    ))
    result = P0P1AResponseBridgeSource(
        p0.fingerprint, diagram.source_digest, p1a.fingerprint,
        binding.membership_digest, source.source_digest, observers, stages,
        source.ordered_commitments, bridge_digest,
    )
    logger.debug("p0_p1a_response_bridge exit observers=%d stages=%d", len(observers), len(stages))
    return result


def snapshot_response_bridge(
    raw_p0_doctrine: ObserverDoctrine, raw_diagram: FiniteDiagramSource,
    raw_p1a_doctrine: ObserverDoctrine, raw_p1a_source: ObserverSourceBinding,
    raw_a2_stage_source: RelationEvaluationSource, value: P0P1AResponseBridgeSource,
) -> P0P1AResponseBridgeSource:
    """Freshly reconstruct and exact-compare a supplied bridge artifact."""
    logger.debug("snapshot_response_bridge entry")
    supplied = shallow_bridge(value)
    expected = p0_p1a_response_bridge(
        raw_p0_doctrine, raw_diagram, raw_p1a_doctrine,
        raw_p1a_source, raw_a2_stage_source,
    )
    compare_bridge(supplied, expected)
    logger.debug("snapshot_response_bridge exit")
    return expected

@dataclass(frozen=True, slots=True)
class _BridgeSnapshot:
    outer: tuple[str, ...]
    observers: tuple[tuple[object, ...], ...]
    stages: tuple[tuple[object, ...], ...]
    order: tuple[str, ...]


def _fields(value: object, names: tuple[str, ...], reason: str) -> tuple[object, ...]:
    """Read declared fields without property dispatch on an exact DTO."""
    logger.debug("c3 bridge fields entry reason=%s", reason)
    try:
        result = tuple(object.__getattribute__(value, name) for name in names)
    except AttributeError:
        reject(reason)
    logger.debug("c3 bridge fields exit count=%d", len(result))
    return result


def _observer(value: object) -> tuple[object, ...]:
    """Capture one exact bridge observer row using primitive-only fields."""
    logger.debug("c3 bridge observer shallow entry")
    if type(value) is not ObserverProgramBridgeRow:
        reject("observer-program-bridge-row-must-be-exact")
    names = ObserverProgramBridgeRow.__slots__
    row = _fields(value, names, "observer-program-bridge-row-missing-fields")
    if (
        any(type(item) is not str for item in (row[0], row[1], *row[3:]))
        or type(row[2]) is not bytes
    ):
        reject("observer-program-bridge-row-field-type")
    for index in (3, 4, 5, 6):
        hex_digest(row[index], "observer-program-bridge-row-digest")
    logger.debug("c3 bridge observer shallow exit")
    return row


def _stage(value: object) -> tuple[object, ...]:
    """Capture one exact stage row and safely snapshot its recurrence."""
    logger.debug("c3 bridge stage shallow entry")
    if type(value) is not StageInputBridgeRow:
        reject("stage-input-bridge-row-must-be-exact")
    row = _fields(value, StageInputBridgeRow.__slots__, "stage-input-bridge-row-missing-fields")
    if any(type(row[index]) is not str for index in (0, 1, 3, 4, 5, 6)):
        reject("stage-input-bridge-row-field-type")
    for index in (1, 3, 5, 6):
        hex_digest(row[index], "stage-input-bridge-row-digest")
    try:
        _, canonical = snapshot_recurrence(row[2])
    except (TypeError, ValueError) as exc:
        logger.error("c3 bridge stage recurrence rejected")
        raise TranslatedConfluenceValidationError(
            "invalid-stage-input-bridge-recurrence"
        ) from exc
    result = (row[0], row[1], canonical, *row[3:])
    logger.debug("c3 bridge stage shallow exit")
    return result


def shallow_bridge(value: object) -> _BridgeSnapshot:
    """Reject hollow/subclass/huge/container drift before reconstruction."""
    logger.debug("c3 shallow_bridge entry")
    if type(value) is not P0P1AResponseBridgeSource:
        reject("response-bridge-must-be-exact")
    names = P0P1AResponseBridgeSource.__slots__
    raw = _fields(value, names, "response-bridge-missing-fields")
    observers, stages, order = raw[5], raw[6], raw[7]
    if (
        type(observers) is not tuple or not 1 <= len(observers) <= 64
        or type(stages) is not tuple or not 1 <= len(stages) <= 32
        or type(order) is not tuple or not 1 <= len(order) <= 32
    ):
        reject("response-bridge-container-or-length")
    outer = (*raw[:5], raw[8], raw[9], raw[10])
    if any(type(item) is not str for item in outer):
        reject("response-bridge-field-type")
    for item in (*outer[:5], outer[5]):
        hex_digest(item, "response-bridge-digest")
    if any(type(item) is not str for item in order):
        reject("response-bridge-order-field-type")
    for item in order:
        hex_digest(item, "response-bridge-order-digest")
    result = _BridgeSnapshot(
        outer, tuple(_observer(item) for item in observers),
        tuple(_stage(item) for item in stages), tuple(order),
    )
    logger.debug("c3 shallow_bridge exit observers=%d stages=%d", len(observers), len(stages))
    return result


def compare_bridge(snapshot: _BridgeSnapshot, expected: P0P1AResponseBridgeSource) -> None:
    """Compare only captured primitive/canonical values to a fresh bridge."""
    logger.debug("c3 compare_bridge entry")
    expected_outer = (
        expected.p0_doctrine_fingerprint, expected.diagram_digest,
        expected.p1a_doctrine_fingerprint, expected.p1a_observer_source_digest,
        expected.a2_stage_source_digest, expected.bridge_digest,
        expected.version, expected.scope,
    )
    if snapshot.outer != expected_outer or snapshot.order != expected.a2_ordered_commitments:
        reject("response-bridge-drift")
    if len(snapshot.observers) != len(expected.observer_rows) or len(snapshot.stages) != len(expected.stage_rows):
        reject("response-bridge-drift")
    for supplied, wanted in zip(snapshot.observers, expected.observer_rows, strict=True):
        expected_row = tuple(object.__getattribute__(wanted, name) for name in wanted.__slots__)
        if supplied != expected_row:
            reject("observer-program-bridge-row-drift")
    for supplied, wanted in zip(snapshot.stages, expected.stage_rows, strict=True):
        expected_row = (
            wanted.diagram_stage_id, wanted.diagram_stage_commitment,
            snapshot_recurrence(wanted.recurrence)[1], wanted.recurrence_digest,
            wanted.relation_stage_id, wanted.relation_stage_commitment, wanted.row_digest,
        )
        if supplied != expected_row:
            reject("stage-input-bridge-row-drift")
    logger.debug("c3 compare_bridge exit")
