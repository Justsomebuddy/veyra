"""Closed raw constructors for the finite P3-T source."""

from __future__ import annotations

import logging

from ..morphism import ProjectionStep
from .common import exact_digest, exact_shape, exact_text, reject
from .digest import digest, field, input_digest, records_digest, response_digest, text, value_digest
from .source_aggregate import observer_network_source as observer_network_source
from .types import (
    GrammarDescriptor,
    InputSnapshot,
    ObservationRow,
    ObserverSource,
    RawObserverPairSource,
    Response,
    ResponseStatus,
    TranslationRow,
    TranslationSource,
    TriangleDemand,
    TypedValue,
)

logger = logging.getLogger(__name__)
NETWORK_VERSION = "p3-t-observer-network-v2"


def input_snapshot(input_id: str, type_id: str, payload: bytes, stage_commitment: str) -> InputSnapshot:
    """Commit canonical occurrence bytes separately from its upstream stage."""
    logger.debug("input_snapshot entry")
    exact_text(input_id, "input-id")
    exact_text(type_id, "input-type")
    if type(payload) is not bytes or len(payload) > 1_048_576:
        reject("input-payload-invalid")
    exact_digest(stage_commitment, "input-stage-commitment")
    commitment = input_digest(input_id, type_id, payload)
    result = InputSnapshot(input_id, type_id, bytes(payload), stage_commitment, commitment)
    logger.debug("input_snapshot exit id=%s", input_id)
    return result


def grammar_descriptor(grammar_id: str, kind_id: str, canonical_source: bytes) -> GrammarDescriptor:
    """Commit an exact immutable grammar descriptor and its real source bytes."""
    logger.debug("grammar_descriptor entry")
    exact_text(grammar_id, "grammar-id")
    exact_text(kind_id, "kind-id")
    if type(canonical_source) is not bytes or not canonical_source or len(canonical_source) > 1_048_576:
        reject("grammar-source-invalid")
    commitment = digest(
        "p3t-grammar-v2", text("grammar", grammar_id), text("kind", kind_id), field("source", canonical_source)
    )
    result = GrammarDescriptor(grammar_id, kind_id, bytes(canonical_source), commitment)
    logger.debug("grammar_descriptor exit")
    return result


def typed_value(grammar_id: str, kind_id: str, payload: bytes) -> TypedValue:
    """Create one immutable closed ready value."""
    logger.debug("typed_value entry")
    exact_text(grammar_id, "value-grammar")
    exact_text(kind_id, "value-kind")
    if type(payload) is not bytes or len(payload) > 1_048_576:
        reject("value-payload-invalid")
    result = TypedValue(grammar_id, kind_id, bytes(payload), value_digest(grammar_id, kind_id, payload))
    logger.debug("typed_value exit")
    return result


def ready(value: TypedValue) -> Response:
    """Create a ready response carrying exact upstream observation bytes."""
    logger.debug("ready entry")
    exact_shape(value, TypedValue, "ready-value")
    exact_digest(value.value_digest, "ready-value-digest")
    result = Response(ResponseStatus.READY, value, "", response_digest("ready", value.value_digest, ""))
    logger.debug("ready exit")
    return result


def silent(reason_id: str) -> Response:
    """Create a silent response; raw P1-A2 can never promote it."""
    logger.debug("silent entry")
    exact_text(reason_id, "silent-reason")
    result = Response(ResponseStatus.SILENT, None, reason_id, response_digest("silent", "", reason_id))
    logger.debug("silent exit")
    return result


def blocked(upstream_payload_digest: str) -> Response:
    """Create a blocked response bound to its upstream P1-A2 payload digest."""
    logger.debug("blocked entry")
    exact_digest(upstream_payload_digest, "blocked-payload-digest")
    result = Response(
        ResponseStatus.BLOCKED, None, upstream_payload_digest, response_digest("blocked", "", upstream_payload_digest)
    )
    logger.debug("blocked exit")
    return result


def observation_row(input_value: InputSnapshot, response: Response) -> ObservationRow:
    """Bind one response to one exact input occurrence."""
    logger.debug("observation_row entry")
    exact_shape(input_value, InputSnapshot, "observation-input")
    exact_shape(response, Response, "observation-response")
    exact_digest(input_value.commitment, "observation-input-commitment")
    exact_digest(response.response_digest, "observation-response-digest")
    row_id = records_digest("p3t-observation-row-v2", (input_value.commitment,), (response.response_digest,))
    result = ObservationRow(input_value.commitment, response, row_id)
    logger.debug("observation_row exit")
    return result


def observer_source(
    observer_id: str, input_type_id: str, descriptor: GrammarDescriptor, rows: tuple[ObservationRow, ...]
) -> ObserverSource:
    """Bind one exact total observer table to its grammar source."""
    logger.debug("observer_source entry")
    exact_text(observer_id, "observer-id")
    exact_text(input_type_id, "input-type")
    if (
        type(rows) is not tuple
        or len(rows) > 4096
        or any(type(x) is not ObservationRow for x in rows)
    ):
        reject("observer-constructor-shape-invalid")
    exact_shape(descriptor, GrammarDescriptor, "observer-descriptor")
    for row in rows:
        exact_shape(row, ObservationRow, "observer-row")
    exact_text(descriptor.grammar_id, "observer-grammar-id")
    exact_text(descriptor.kind_id, "observer-kind-id")
    exact_digest(descriptor.commitment, "observer-grammar-commitment")
    for row in rows:
        exact_digest(row.row_digest, "observer-row-digest")
    oid = records_digest(
        "p3t-observer-v2", (observer_id, input_type_id, descriptor.commitment), tuple(x.row_digest for x in rows)
    )
    result = ObserverSource(
        observer_id, input_type_id, descriptor.grammar_id, descriptor.kind_id, descriptor, tuple(rows), oid
    )
    logger.debug("observer_source exit id=%s rows=%d", observer_id, len(rows))
    return result


def translation_row(source_value: TypedValue, target_value: TypedValue) -> TranslationRow:
    """Create one exact typed table row."""
    logger.debug("translation_row entry")
    exact_shape(source_value, TypedValue, "translation-source-value")
    exact_shape(target_value, TypedValue, "translation-target-value")
    exact_digest(source_value.value_digest, "translation-source-value-digest")
    exact_digest(target_value.value_digest, "translation-target-value-digest")
    row_id = records_digest("p3t-translation-row-v2", (), (source_value.value_digest, target_value.value_digest))
    result = TranslationRow(source_value, target_value, row_id)
    logger.debug("translation_row exit")
    return result


def translation_source(
    edge_id: str,
    source_id: str,
    target_id: str,
    declared_domain: tuple[str, ...],
    rows: tuple[TranslationRow, ...],
    dependency_ids: tuple[str, ...],
) -> TranslationSource:
    """Bind a separately declared exact domain and one total row per value."""
    logger.debug("translation_source entry")
    for label, value in (("edge-id", edge_id), ("source-observer", source_id), ("target-observer", target_id)):
        exact_text(value, label)
    if (
        any(type(x) is not tuple for x in (declared_domain, rows, dependency_ids))
        or any(len(x) > 4096 for x in (declared_domain, rows, dependency_ids))
        or any(type(x) is not str for x in (*declared_domain, *dependency_ids))
        or any(type(x) is not TranslationRow for x in rows)
    ):
        reject("translation-constructor-shape-invalid")
    for row in rows:
        exact_shape(row, TranslationRow, "translation-row")
    for item in declared_domain:
        exact_digest(item, "translation-domain-digest")
    for item in dependency_ids:
        exact_digest(item, "translation-dependency-digest")
    for row in rows:
        exact_digest(row.row_digest, "translation-row-digest")
    tid = records_digest(
        "p3t-translation-v2",
        (edge_id, source_id, target_id, *declared_domain, *dependency_ids),
        tuple(x.row_digest for x in rows),
    )
    result = TranslationSource(
        edge_id, source_id, target_id, tuple(declared_domain), tuple(rows), tuple(dependency_ids), tid
    )
    logger.debug("translation_source exit id=%s rows=%d", edge_id, len(rows))
    return result


def raw_observer_pair_source(
    pair_id: str,
    source_id: str,
    target_id: str,
    morphism_id: str = "",
    projection: tuple[ProjectionStep, ...] | None = None,
) -> RawObserverPairSource:
    """Commit one raw P1-A2 pair request and optional raw P1-A projection."""
    logger.debug("raw_observer_pair_source entry")
    for label, value in (("pair-id", pair_id), ("source", source_id), ("target", target_id)):
        exact_text(value, label)
    if projection is not None and (
        type(projection) is not tuple
        or len(projection) > 4096
        or any(type(x) is not ProjectionStep for x in projection)
    ):
        reject("raw-pair-projection-invalid")
    if projection is not None:
        exact_text(morphism_id, "morphism-id")
    elif type(morphism_id) is not str or morphism_id:
        reject("raw-pair-morphism-invalid")
    steps = () if projection is None else tuple(object.__getattribute__(x, "_value_") for x in projection)
    pid = records_digest("p3t-raw-pair-v2", (pair_id, source_id, target_id, morphism_id, *steps), ())
    result = RawObserverPairSource(pair_id, source_id, target_id, morphism_id, projection, pid)
    logger.debug("raw_observer_pair_source exit id=%s", pair_id)
    return result


def triangle_demand(demand_id: str, direct_edge_id: str, indirect_edge_ids: tuple[str, ...]) -> TriangleDemand:
    """Demand comparison of one direct edge with one nontrivial path."""
    logger.debug("triangle_demand entry")
    exact_text(demand_id, "demand-id")
    exact_text(direct_edge_id, "direct-edge")
    if (
        type(indirect_edge_ids) is not tuple
        or len(indirect_edge_ids) < 2
        or len(indirect_edge_ids) > 4096
        or any(type(x) is not str or not x for x in indirect_edge_ids)
    ):
        reject("indirect-path-invalid")
    for item in indirect_edge_ids:
        exact_text(item, "indirect-edge")
    result = TriangleDemand(demand_id, direct_edge_id, tuple(indirect_edge_ids))
    logger.debug("triangle_demand exit id=%s", demand_id)
    return result
