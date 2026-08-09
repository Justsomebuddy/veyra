"""Exact observer grammar/value replay and translation source validation."""

from __future__ import annotations

import logging

from ...observer_core_codec import decode_observer
from ...observer_core_semantics import observe
from ...observer_core_types import Blocked as P1Blocked, Ready as P1Ready
from ..morphism import ProjectionStep
from ..relations.digest import response_payload_digest
from ..relations.replay import observation_bytes
from .common import exact_digest, exact_shape, exact_text, reject
from .digest import digest, field, records_digest, response_digest, text, value_digest
from .types import (
    GrammarDescriptor,
    ObservationRow,
    ObserverSource,
    RawObserverPairSource,
    Response,
    ResponseStatus,
    TranslationRow,
    TranslationSource,
    TypedValue,
)

logger = logging.getLogger(__name__)


def _snapshot_descriptor(raw: GrammarDescriptor, canonical: bytes) -> GrammarDescriptor:
    """Validate the exact grammar source commitment against admitted P1 bytes."""
    logger.debug("snapshot descriptor entry")
    exact_shape(raw, GrammarDescriptor, "grammar-descriptor")
    exact_text(raw.grammar_id, "grammar-id")
    exact_text(raw.kind_id, "kind-id")
    if type(raw.canonical_source) is not bytes or raw.canonical_source != canonical:
        reject("grammar-canonical-source-mismatch")
    expected = digest(
        "p3t-grammar-v2",
        text("grammar", raw.grammar_id),
        text("kind", raw.kind_id),
        field("source", canonical),
    )
    if raw.commitment != expected:
        reject("grammar-commitment-mismatch")
    result = GrammarDescriptor(raw.grammar_id, raw.kind_id, bytes(canonical), expected)
    logger.debug("snapshot descriptor exit")
    return result


def snapshot_observer(raw: ObserverSource, inputs, stages, members) -> ObserverSource:
    """Validate a total table and replay every row from admitted P1 semantics."""
    logger.debug("snapshot observer entry")
    exact_shape(raw, ObserverSource, "observer")
    exact_text(raw.observer_id, "observer-id")
    exact_text(raw.input_type_id, "observer-input-type")
    if raw.observer_id not in members or type(raw.rows) is not tuple or len(raw.rows) != len(inputs):
        reject("observer-table-or-member-invalid")
    if not inputs or raw.input_type_id != inputs[0].type_id:
        reject("observer-input-type-mismatch")
    descriptor = _snapshot_descriptor(raw.grammar_descriptor, members[raw.observer_id].canonical)
    if (raw.ready_grammar_id, raw.ready_kind_id) != (descriptor.grammar_id, descriptor.kind_id):
        reject("observer-grammar-alias-mismatch")
    rows = tuple(_snapshot_observation(x) for x in raw.rows)
    if tuple(x.input_commitment for x in rows) != tuple(x.commitment for x in inputs):
        reject("observer-input-domain-not-exact")
    _replay_observer_rows(raw.observer_id, members[raw.observer_id].canonical, rows, stages)
    expected = records_digest(
        "p3t-observer-v2",
        (raw.observer_id, raw.input_type_id, descriptor.commitment),
        tuple(x.row_digest for x in rows),
    )
    if expected != raw.observer_digest:
        reject("observer-digest-mismatch")
    if not any(x.response.status is ResponseStatus.READY for x in rows):
        reject("observer-has-no-ready-witness")
    result = ObserverSource(
        raw.observer_id,
        raw.input_type_id,
        descriptor.grammar_id,
        descriptor.kind_id,
        descriptor,
        rows,
        expected,
    )
    logger.debug("snapshot observer exit id=%s", raw.observer_id)
    return result


def _replay_observer_rows(observer_id, canonical, rows, stages) -> None:
    """Require literal upstream P1 observation bytes and blockage digests."""
    logger.debug("replay observer rows entry observer=%s", observer_id)
    program = decode_observer(canonical)
    for row, stage in zip(rows, stages.stages):
        actual = observe(program, stage.recurrence)
        payload = observation_bytes(actual)
        upstream = response_payload_digest(payload)
        if type(actual) is P1Ready:
            if row.response.status is not ResponseStatus.READY or row.response.value.payload != payload:
                reject("observer-ready-row-not-p1-replay")
        elif type(actual) is P1Blocked:
            if row.response.status is not ResponseStatus.BLOCKED or row.response.reason_id != upstream:
                reject("observer-blocked-row-not-p1-replay")
        else:
            reject("observer-unknown-p1-response")
    logger.debug("replay observer rows exit observer=%s", observer_id)


def _snapshot_observation(raw: ObservationRow) -> ObservationRow:
    """Validate one response row and its distinct digest domain."""
    logger.debug("snapshot observation entry")
    exact_shape(raw, ObservationRow, "observation-row")
    exact_digest(raw.input_commitment, "input-commitment")
    response = _snapshot_response(raw.response)
    expected = records_digest("p3t-observation-row-v2", (raw.input_commitment,), (response.response_digest,))
    if raw.row_digest != expected:
        reject("observation-row-digest-mismatch")
    result = ObservationRow(raw.input_commitment, response, expected)
    logger.debug("snapshot observation exit")
    return result


def _snapshot_response(raw: Response) -> Response:
    """Validate Ready/Blocked; Silent syntax cannot satisfy upstream replay."""
    logger.debug("snapshot response entry")
    exact_shape(raw, Response, "response")
    if type(raw.status) is not ResponseStatus or type(raw.reason_id) is not str:
        reject("response-tag-invalid")
    if raw.status is ResponseStatus.READY:
        value = _snapshot_value(raw.value)
        if raw.reason_id:
            reject("ready-reason-not-empty")
    else:
        value = None
        if raw.value is not None:
            reject("nonready-value-present")
        exact_text(raw.reason_id, "response-reason")
    expected = response_digest(raw.status.value, "" if value is None else value.value_digest, raw.reason_id)
    if raw.response_digest != expected:
        reject("response-digest-mismatch")
    result = Response(raw.status, value, raw.reason_id, expected)
    logger.debug("snapshot response exit status=%s", raw.status.value)
    return result


def _snapshot_value(raw: TypedValue) -> TypedValue:
    """Validate one immutable typed value and exact grammar/kind identifiers."""
    logger.debug("snapshot value entry")
    exact_shape(raw, TypedValue, "typed-value")
    exact_text(raw.grammar_id, "value-grammar")
    exact_text(raw.kind_id, "value-kind")
    if type(raw.payload) is not bytes or value_digest(raw.grammar_id, raw.kind_id, raw.payload) != raw.value_digest:
        reject("value-digest-mismatch")
    result = TypedValue(raw.grammar_id, raw.kind_id, bytes(raw.payload), raw.value_digest)
    logger.debug("snapshot value exit")
    return result


def snapshot_raw_pair(raw: RawObserverPairSource, observers) -> RawObserverPairSource:
    """Validate one ordered raw P1-A2 source and optional P1-A source."""
    logger.debug("snapshot raw pair entry")
    exact_shape(raw, RawObserverPairSource, "raw-pair")
    for value, label in (
        (raw.pair_id, "pair-id"),
        (raw.source_observer_id, "pair-source"),
        (raw.target_observer_id, "pair-target"),
    ):
        exact_text(value, label)
    if raw.source_observer_id == raw.target_observer_id or raw.source_observer_id not in observers or raw.target_observer_id not in observers:
        reject("raw-pair-endpoint-invalid")
    if raw.projection is not None and (
        type(raw.projection) is not tuple
        or not raw.morphism_id
        or any(type(x) is not ProjectionStep for x in raw.projection)
    ):
        reject("raw-p1a-projection-invalid")
    if raw.projection is None and raw.morphism_id:
        reject("raw-p1a-morphism-without-projection")
    steps = () if raw.projection is None else tuple(x.value for x in raw.projection)
    expected = records_digest(
        "p3t-raw-pair-v2",
        (raw.pair_id, raw.source_observer_id, raw.target_observer_id, raw.morphism_id, *steps),
        (),
    )
    if raw.pair_digest != expected:
        reject("raw-pair-digest-mismatch")
    result = RawObserverPairSource(
        raw.pair_id,
        raw.source_observer_id,
        raw.target_observer_id,
        raw.morphism_id,
        raw.projection,
        expected,
    )
    logger.debug("snapshot raw pair exit")
    return result


def snapshot_translation(raw: TranslationSource, observers, pairs) -> TranslationSource:
    """Validate declared T_fg, total rows, grammars, and raw P1-A closure."""
    logger.debug("snapshot translation entry")
    exact_shape(raw, TranslationSource, "translation")
    for value, label in (
        (raw.edge_id, "edge-id"),
        (raw.source_observer_id, "translation-source"),
        (raw.target_observer_id, "translation-target"),
    ):
        exact_text(value, label)
    pair = pairs.get((raw.source_observer_id, raw.target_observer_id))
    if pair is None:
        reject("translation-missing-raw-p1a2-source")
    if any(type(x) is not tuple for x in (raw.declared_domain, raw.rows, raw.dependency_ids)):
        reject("translation-container-invalid")
    rows = tuple(_snapshot_translation_row(x) for x in raw.rows)
    if tuple(x.source_value.value_digest for x in rows) != raw.declared_domain or len(set(raw.declared_domain)) != len(raw.declared_domain):
        reject("translation-declared-domain-row-mismatch")
    source, target = observers[raw.source_observer_id], observers[raw.target_observer_id]
    dependencies = (source.grammar_descriptor.commitment, target.grammar_descriptor.commitment)
    if raw.dependency_ids != dependencies:
        reject("translation-dependency-closure-invalid")
    _validate_translation_values(rows, source, target)
    expected = records_digest(
        "p3t-translation-v2",
        (raw.edge_id, raw.source_observer_id, raw.target_observer_id, *raw.declared_domain, *dependencies),
        tuple(x.row_digest for x in rows),
    )
    if raw.translation_digest != expected:
        reject("translation-digest-mismatch")
    result = TranslationSource(
        raw.edge_id,
        raw.source_observer_id,
        raw.target_observer_id,
        raw.declared_domain,
        rows,
        dependencies,
        expected,
    )
    logger.debug("snapshot translation exit id=%s", raw.edge_id)
    return result


def _validate_translation_values(rows, source, target) -> None:
    """Require correct grammar sources and reachable operational outputs."""
    logger.debug("validate translation values entry rows=%d", len(rows))
    if any(
        (x.source_value.grammar_id, x.source_value.kind_id) != (source.ready_grammar_id, source.ready_kind_id)
        or (x.target_value.grammar_id, x.target_value.kind_id) != (target.ready_grammar_id, target.ready_kind_id)
        for x in rows
    ):
        reject("translation-grammar-kind-mismatch")
    source_image = {x.response.value.value_digest for x in source.rows if x.response.status is ResponseStatus.READY}
    target_image = {x.response.value.value_digest for x in target.rows if x.response.status is ResponseStatus.READY}
    if any(x.source_value.value_digest in source_image and x.target_value.value_digest not in target_image for x in rows):
        reject("operational-output-not-reachable")
    logger.debug("validate translation values exit")


def _snapshot_translation_row(raw: TranslationRow) -> TranslationRow:
    """Validate one actual table row."""
    logger.debug("snapshot translation row entry")
    exact_shape(raw, TranslationRow, "translation-row")
    source = _snapshot_value(raw.source_value)
    target = _snapshot_value(raw.target_value)
    expected = records_digest("p3t-translation-row-v2", (), (source.value_digest, target.value_digest))
    if raw.row_digest != expected:
        reject("translation-row-digest-mismatch")
    result = TranslationRow(source, target, expected)
    logger.debug("snapshot translation row exit")
    return result
