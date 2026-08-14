"""Fail-closed snapshots for P1-A realization transport v2."""

from __future__ import annotations

from dataclasses import replace
import json
import logging
from typing import NoReturn

from ..observer_core_semantics import MAX_OBSERVER_DEPTH, MAX_OBSERVER_NODES
from ..observer_core_types import Mark, ObstructionCode, PathStep
from ..observer_morphism import observer_morphism_judgment
from ..observer_morphism_types import MorphismStatus, ProjectionStep, ResponseTranslation
from ..observer_morphism_validation import (
    ObserverMorphismValidationError,
    response_kind_signature,
    snapshot_morphism_doctrine,
    snapshot_source_binding,
    snapshot_translation,
)
from ..observer_realization_types import (
    ObservationStatus,
    RealizationClosurePolicy,
    RealizationCostPolicy,
    ResponseTotalization,
)
from ..realization_transport.types import RealizationTransportReceipt
from ..realization_transport.validation import snapshot_receipt as snapshot_v1_receipt
from .digest import (
    judgment_root,
    partition_digest,
    payload_digest,
    receipt_digest,
    row_digest,
    transport_digest,
)
from .partitions import MAX_P1A_V2_PARTITION_STATES, refinement_class_map
from .types import (
    P1AEndpointPartitionLawV2,
    P1AEndpointV2,
    P1AObservationCommutingRowV2,
    P1AObservationPayloadV2,
    P1AObservationTransportV2,
    P1AOutcomeLawV2,
    P1ARealizationTransportReceiptV2,
)

logger = logging.getLogger(__name__)
P1A_TRANSPORT_VERSION = "p1-r16-p1a-observation-transport-v2"
P1A_RECEIPT_SCHEMA = "veyra.p1-r16.p1a-realization-transport-receipt.v2"
P1A_TRANSPORT_SCOPE = "finite-same-doctrine-strong-all-status-replayed-no-category-or-lifecycle-claim"
MAX_P1A_V2_ROWS = 256
MAX_P1A_V2_PAYLOAD_BYTES = 262_144
MAX_P1A_V2_TRANSPORTED_ENDPOINT_BYTES = 8_388_608
MAX_P1A_V2_SIX_STREAM_BYTES = 33_554_432
MAX_P1A_V2_RECEIPT_NODES = 65_536
MAX_P1A_V2_RECEIPT_TEXT_BYTES = 1_048_576


class P1ARealizationTransportValidationError(ValueError):
    """A v2 DTO, replay binding, law, or resource invariant failed."""


def reject(reason: str) -> NoReturn:
    """Raise the closed public validation error without payload disclosure."""
    logger.error("p1a realization transport rejected reason=%s", reason)
    raise P1ARealizationTransportValidationError(reason)


def _id(value: object, field: str) -> str:
    """Capture one exact nonempty identifier of at most 128 UTF-8 bytes."""
    logger.debug("p1a identifier entry field=%s", field)
    if type(value) is not str or not value or len(value) > 128:
        reject(f"invalid-{field}")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError:
        reject(f"invalid-{field}")
    if size > 128:
        reject(f"invalid-{field}")
    logger.debug("p1a identifier exit field=%s bytes=%d", field, size)
    return value


def _dg(value: object, field: str) -> str:
    """Capture exact lowercase SHA-256 text."""
    logger.debug("p1a digest entry field=%s", field)
    if type(value) is not str or len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        reject(f"invalid-{field}")
    logger.debug("p1a digest exit field=%s", field)
    return value


def _nat(value: object, field: str, maximum: int) -> int:
    """Capture an exact bounded natural without Boolean coercion."""
    logger.debug("p1a natural entry field=%s", field)
    if type(value) is not int or not 0 <= value <= maximum:
        reject(f"invalid-{field}")
    logger.debug("p1a natural exit field=%s value=%d", field, value)
    return value


def _text_bytes(value: object, field: str) -> int:
    """Charge one exact nonpayload string without unbounded prior encoding."""
    logger.debug("p1a text charge entry field=%s", field)
    if type(value) is not str:
        reject(f"invalid-{field}")
    if len(value) > MAX_P1A_V2_RECEIPT_TEXT_BYTES:
        reject("p1a-receipt-text-limit")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError:
        reject(f"invalid-{field}")
    if size > MAX_P1A_V2_RECEIPT_TEXT_BYTES:
        reject("p1a-receipt-text-limit")
    logger.debug("p1a text charge exit field=%s bytes=%d", field, size)
    return size


def _charge_text(total: int, value: object, field: str) -> int:
    """Add one UTF-8 text charge and fail at the frozen aggregate ceiling."""
    logger.debug("p1a aggregate text charge entry field=%s total=%d", field, total)
    result = total + _text_bytes(value, field)
    if result > MAX_P1A_V2_RECEIPT_TEXT_BYTES:
        reject("p1a-receipt-text-limit")
    logger.debug("p1a aggregate text charge exit field=%s total=%d", field, result)
    return result


def _charge_expanded_nodes(shallow_nodes: int, decoded_nodes: int) -> int:
    """Enforce one aggregate ceiling across DTO and decoded JSON nodes."""
    logger.debug(
        "p1a expanded node charge entry shallow=%d decoded=%d",
        shallow_nodes,
        decoded_nodes,
    )
    if type(shallow_nodes) is not int or type(decoded_nodes) is not int or shallow_nodes < 0 or decoded_nodes < 0:
        reject("p1a-receipt-node-limit")
    result = shallow_nodes + decoded_nodes
    if result > MAX_P1A_V2_RECEIPT_NODES:
        reject("p1a-receipt-node-limit")
    logger.debug("p1a expanded node charge exit nodes=%d", result)
    return result


def _preflight_payload(value: object) -> tuple[int, int]:
    """Shallow-check one envelope before copying, hashing, or JSON decoding."""
    logger.debug("p1a payload preflight entry")
    if (
        type(value) is not P1AObservationPayloadV2
        or type(value.status) is not ObservationStatus
        or type(value.canonical_payload) is not bytes
        or type(value.payload_digest) is not str
    ):
        reject("p1a-payload-must-be-exact")
    size = len(value.canonical_payload)
    if size > MAX_P1A_V2_PAYLOAD_BYTES:
        reject("p1a-payload-byte-limit")
    logger.debug("p1a payload preflight exit bytes=%d", size)
    # Canonical JSON bytes have their own payload/stream ceilings.  Only the
    # envelope status and digest are nonpayload text.
    text_bytes = _text_bytes(value.status.value, "p1a-payload-status")
    text_bytes += _text_bytes(value.payload_digest, "p1a-payload-digest")
    return 4, text_bytes


def _preflight_receipt(value: object) -> int:
    """Bound the complete shallow DTO graph before child replay or JSON work."""
    logger.debug("p1a receipt preflight entry")
    if type(value) is not P1ARealizationTransportReceiptV2:
        reject("p1a-receipt-must-be-exact")
    if (
        type(value.schema) is not str
        or type(value.scope) is not str
        or type(value.receipt_digest) is not str
        or type(value.transport) is not P1AObservationTransportV2
        or type(value.context_transport) is not RealizationTransportReceipt
    ):
        reject("p1a-receipt-shallow-type-drift")
    transport_nodes, text_bytes = _preflight_transport(value.transport)
    if type(value.rows) is not tuple or not 1 <= len(value.rows) <= MAX_P1A_V2_ROWS:
        reject("invalid-p1a-rows")
    nodes = 1 + transport_nodes
    for field, item in (
        ("p1a-receipt-schema", value.schema),
        ("p1a-receipt-scope", value.scope),
        ("p1a-receipt-digest", value.receipt_digest),
    ):
        text_bytes = _charge_text(text_bytes, item, field)
    six_stream_bytes = 0
    source_transported_bytes = 0
    target_transported_bytes = 0
    for row in value.rows:
        if type(row) is not P1AObservationCommutingRowV2:
            reject("p1a-row-must-be-exact")
        if (
            type(row.source_index) is not int
            or type(row.target_index) is not int
            or type(row.law) is not P1AOutcomeLawV2
            or type(row.source_input_commitment) is not str
            or type(row.target_input_commitment) is not str
            or type(row.row_digest) is not str
        ):
            reject("p1a-row-text-must-be-exact")
        payloads = (
            row.source_fine,
            row.source_transported,
            row.source_coarse,
            row.target_fine,
            row.target_transported,
            row.target_coarse,
        )
        for payload in payloads:
            added_nodes, added_text = _preflight_payload(payload)
            nodes += added_nodes
            text_bytes += added_text
            if text_bytes > MAX_P1A_V2_RECEIPT_TEXT_BYTES:
                reject("p1a-receipt-text-limit")
            six_stream_bytes += len(payload.canonical_payload)
        source_transported_bytes += len(row.source_transported.canonical_payload)
        target_transported_bytes += len(row.target_transported.canonical_payload)
        nodes += 14
        for field, item in (
            ("p1a-source-input", row.source_input_commitment),
            ("p1a-target-input", row.target_input_commitment),
            ("p1a-row-law", row.law.value),
            ("p1a-row-digest", row.row_digest),
        ):
            text_bytes = _charge_text(text_bytes, item, field)
    if six_stream_bytes > MAX_P1A_V2_SIX_STREAM_BYTES:
        reject("p1a-six-stream-byte-limit")
    if (
        source_transported_bytes > MAX_P1A_V2_TRANSPORTED_ENDPOINT_BYTES
        or target_transported_bytes > MAX_P1A_V2_TRANSPORTED_ENDPOINT_BYTES
    ):
        reject("p1a-transported-endpoint-byte-limit")
    for law in (value.source_partition_law, value.target_partition_law):
        if type(law) is not P1AEndpointPartitionLawV2:
            reject("p1a-partition-law-must-be-exact")
        if type(law.endpoint) is not P1AEndpointV2 or type(law.partition_digest) is not str:
            reject("p1a-partition-law-shallow-type-drift")
        text_bytes = _charge_text(text_bytes, law.endpoint.value, "p1a-partition-endpoint")
        text_bytes = _charge_text(text_bytes, law.partition_digest, "p1a-partition-digest")
        for partition in (
            law.fine_partition,
            law.transported_partition,
            law.coarse_partition,
            law.fine_to_coarse_class_map,
        ):
            if type(partition) is not tuple or len(partition) > MAX_P1A_V2_PARTITION_STATES:
                reject("invalid-p1a-partition")
            if any(type(item) is not int for item in partition):
                reject("invalid-p1a-partition-class")
            nodes += len(partition)
    _charge_expanded_nodes(nodes, 0)
    if text_bytes > MAX_P1A_V2_RECEIPT_TEXT_BYTES:
        reject("p1a-receipt-text-limit")
    logger.debug(
        "p1a receipt preflight exit rows=%d nodes=%d text_bytes=%d payload_bytes=%d",
        len(value.rows),
        nodes,
        text_bytes,
        six_stream_bytes,
    )
    return nodes


def _preflight_transport(value: object) -> tuple[int, int]:
    """Gate all arrow scalar and child types before any comparison or replay."""
    logger.debug("p1a transport preflight entry")
    if type(value) is not P1AObservationTransportV2:
        reject("p1a-transport-must-be-exact")
    textual = (
        ("p1a-transport-id", value.transport_id),
        ("p1a-doctrine", value.doctrine_fingerprint),
        ("p1a-binding", value.source_binding_digest),
        ("p1a-judgment", value.strong_judgment_root),
        ("p1a-source-context", value.source_context_digest),
        ("p1a-target-context", value.target_context_digest),
        ("p1a-source-witness", value.source_witness_digest),
        ("p1a-target-witness", value.target_witness_digest),
        ("p1a-context-morphism", value.context_morphism_digest),
        ("p1a-v1-receipt", value.v1_receipt_digest),
        ("p1a-transport-version", value.version),
        ("p1a-transport-scope", value.scope),
        ("p1a-transport-digest", value.transport_digest),
    )
    if (
        any(type(item) is not str for _, item in textual)
        or type(value.translation) is not ResponseTranslation
        or type(value.response_policy) is not ResponseTotalization
        or type(value.cost_policy) is not RealizationCostPolicy
        or type(value.closure_policy) is not RealizationClosurePolicy
    ):
        reject("p1a-transport-shallow-type-drift")
    translation_text = (
        ("p1a-translation-id", value.translation.translation_id),
        ("p1a-translation-doctrine", value.translation.doctrine_fingerprint),
        ("p1a-translation-binding", value.translation.source_binding_digest),
        ("p1a-fine-observer", value.translation.fine_observer_id),
        ("p1a-coarse-observer", value.translation.coarse_observer_id),
        ("p1a-translation-digest", value.translation.translation_digest),
        ("p1a-translation-scope", value.translation.scope),
    )
    if (
        any(type(item) is not str for _, item in translation_text)
        or type(value.translation.projection) is not tuple
        or len(value.translation.projection) > 128
        or any(type(item) is not ProjectionStep for item in value.translation.projection)
    ):
        reject("p1a-translation-shallow-type-drift")
    try:
        fine_kind = response_kind_signature(value.translation.fine_kind)
        coarse_kind = response_kind_signature(value.translation.coarse_kind)
    except (ObserverMorphismValidationError, TypeError, ValueError, RecursionError) as exc:
        logger.error("p1a translation kind preflight rejected")
        raise P1ARealizationTransportValidationError("p1a-translation-shallow-type-drift") from exc
    text_bytes = 0
    for field, item in textual + translation_text:
        text_bytes = _charge_text(text_bytes, item, field)
    for item in value.translation.projection:
        text_bytes = _charge_text(text_bytes, item.value, "p1a-projection-step")
    for item in fine_kind + coarse_kind:
        text_bytes = _charge_text(text_bytes, item, "p1a-response-kind")
    for field, item in (
        ("p1a-response-policy", value.response_policy.value),
        ("p1a-cost-policy", value.cost_policy.value),
        ("p1a-closure-policy", value.closure_policy.value),
    ):
        text_bytes = _charge_text(text_bytes, item, field)
    nodes = 2 + len(value.translation.projection) + len(fine_kind) + len(coarse_kind)
    logger.debug("p1a transport preflight exit nodes=%d text_bytes=%d", nodes, text_bytes)
    return nodes, text_bytes


def _json_pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    """Reject duplicate JSON object names without a nested callback."""
    logger.debug("p1a json pairs entry items=%d", len(items))
    if len({key for key, _ in items}) != len(items):
        logger.error("p1a json duplicate key rejected")
        raise ValueError("duplicate-key")
    result = dict(items)
    logger.debug("p1a json pairs exit items=%d", len(result))
    return result


def _normalize_partition_labels(items: tuple[int, ...]) -> tuple[int, ...]:
    """Normalize labels by first occurrence for horizontal comparison."""
    logger.debug("p1a partition label normalization entry items=%d", len(items))
    classes: dict[int, int] = {}
    result = tuple(classes.setdefault(item, len(classes)) for item in items)
    logger.debug("p1a partition label normalization exit classes=%d", len(classes))
    return result


def _exact_keys(value: object, keys: frozenset[str]) -> dict[str, object]:
    """Require one exact JSON object shape."""
    logger.debug("p1a payload exact keys entry keys=%d", len(keys))
    if type(value) is not dict or frozenset(value) != keys:
        reject("p1a-payload-schema")
    logger.debug("p1a payload exact keys exit")
    return value


def _validate_recurrence_data(value: object) -> int:
    """Validate canonical closed Silence/Pulse JSON iteratively."""
    logger.debug("p1a recurrence payload validation entry")
    cursor = value
    nodes = 0
    depth = 0
    while True:
        nodes += 1
        if nodes > MAX_OBSERVER_NODES or depth > MAX_OBSERVER_DEPTH:
            reject("p1a-payload-recurrence-resource-limit")
        if type(cursor) is not dict or type(cursor.get("tag")) is not str:
            reject("p1a-payload-recurrence-schema")
        if cursor["tag"] == "silence":
            _exact_keys(cursor, frozenset({"tag"}))
            break
        if cursor["tag"] != "pulse":
            reject("p1a-payload-recurrence-schema")
        row = _exact_keys(cursor, frozenset({"tag", "tail"}))
        cursor = row["tail"]
        depth += 1
    logger.debug("p1a recurrence payload validation exit nodes=%d", nodes)
    return nodes


def _validate_response_data(value: object) -> int:
    """Validate exact bounded Recurrence/Mark/Pair response JSON iteratively."""
    logger.debug("p1a response payload validation entry")
    stack: list[tuple[object, int]] = [(value, 0)]
    nodes = 0
    while stack:
        node, depth = stack.pop()
        nodes += 1
        if nodes > MAX_OBSERVER_NODES or depth > MAX_OBSERVER_DEPTH:
            reject("p1a-payload-response-resource-limit")
        if type(node) is not dict or type(node.get("tag")) is not str:
            reject("p1a-payload-response-schema")
        tag = node["tag"]
        if tag == "pair":
            row = _exact_keys(node, frozenset({"tag", "left", "right"}))
            stack.append((row["right"], depth + 1))
            stack.append((row["left"], depth + 1))
        elif tag == "mark":
            row = _exact_keys(node, frozenset({"tag", "mark"}))
            if type(row["mark"]) is not str or row["mark"] not in {item.value for item in Mark}:
                reject("p1a-payload-mark-schema")
        elif tag == "recurrence":
            row = _exact_keys(node, frozenset({"tag", "term"}))
            nodes += _validate_recurrence_data(row["term"])
            if nodes > MAX_OBSERVER_NODES:
                reject("p1a-payload-response-resource-limit")
        else:
            reject("p1a-payload-response-schema")
    logger.debug("p1a response payload validation exit nodes=%d", nodes)
    return nodes


def _validate_obstructions(value: object) -> int:
    """Validate exact ordered nonempty bounded obstruction JSON."""
    logger.debug("p1a obstruction payload validation entry")
    if type(value) is not list or not 1 <= len(value) <= MAX_OBSERVER_NODES:
        reject("p1a-payload-obstruction-count")
    seen: set[tuple[str, ...]] = set()
    path_steps = {item.value for item in PathStep}
    codes = {item.value for item in ObstructionCode}
    nodes = 0
    for item in value:
        row = _exact_keys(item, frozenset({"code", "path"}))
        path = row["path"]
        if (
            type(row["code"]) is not str
            or row["code"] not in codes
            or type(path) is not list
            or not 1 <= len(path) <= MAX_OBSERVER_DEPTH
            or any(type(step) is not str or step not in path_steps for step in path)
            or path[-1] != PathStep.APPLY_TAIL.value
        ):
            reject("p1a-payload-obstruction-schema")
        signature = tuple(path)
        if signature in seen:
            reject("p1a-payload-duplicate-obstruction-path")
        seen.add(signature)
        nodes += 2 + len(path)
        if nodes > MAX_P1A_V2_RECEIPT_NODES:
            reject("p1a-payload-obstruction-resource-limit")
    logger.debug("p1a obstruction payload validation exit count=%d", len(value))
    return nodes


def _validate_payload_schema(data: object, status: ObservationStatus) -> int:
    """Validate the exact R11 Ready|Blocked canonical data schema."""
    logger.debug("p1a payload schema validation entry status=%s", status.value)
    if status is ObservationStatus.READY:
        row = _exact_keys(data, frozenset({"tag", "value"}))
        if row["tag"] != "ready":
            reject("p1a-payload-status-drift")
        nodes = 1 + _validate_response_data(row["value"])
    else:
        row = _exact_keys(data, frozenset({"tag", "obstructions"}))
        if row["tag"] != "blocked":
            reject("p1a-payload-status-drift")
        nodes = 1 + _validate_obstructions(row["obstructions"])
    logger.debug("p1a payload schema validation exit nodes=%d", nodes)
    return nodes


def _canonical_payload(value: object) -> tuple[P1AObservationPayloadV2, int]:
    """Snapshot one exact canonical payload after shallow resource preflight."""
    logger.debug("p1a canonical payload snapshot entry")
    _preflight_payload(value)
    raw = value.canonical_payload

    try:
        data = json.loads(raw.decode("ascii"), object_pairs_hook=_json_pairs)
        decoded_nodes = _validate_payload_schema(data, value.status)
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    except P1ARealizationTransportValidationError:
        raise
    except (UnicodeError, json.JSONDecodeError, RecursionError, TypeError, ValueError) as exc:
        logger.error("p1a canonical payload decoding rejected")
        raise P1ARealizationTransportValidationError("invalid-p1a-payload") from exc
    if canonical != raw:
        reject("p1a-payload-noncanonical")
    supplied = _dg(value.payload_digest, "p1a-payload-digest")
    expected = payload_digest(raw)
    if supplied != expected:
        reject("p1a-payload-digest-drift")
    result = P1AObservationPayloadV2(value.status, raw, expected)
    logger.debug(
        "p1a canonical payload snapshot exit status=%s bytes=%d",
        result.status.value,
        len(raw),
    )
    return result, decoded_nodes


def _normalized(value: object, count: int) -> tuple[int, ...]:
    """Capture one bounded first-occurrence-normalized partition."""
    logger.debug("p1a normalized partition snapshot entry states=%d", count)
    if type(value) is not tuple or not 1 <= count <= MAX_P1A_V2_PARTITION_STATES or len(value) != count:
        reject("invalid-p1a-partition")
    result = tuple(_nat(item, "p1a-partition-class", count - 1) for item in value)
    seen: set[int] = set()
    next_class = 0
    for item in result:
        if item not in seen:
            if item != next_class:
                reject("noncanonical-p1a-partition")
            seen.add(item)
            next_class += 1
    logger.debug("p1a normalized partition snapshot exit classes=%d", next_class)
    return result


def snapshot_partition_law(value: object, endpoint: P1AEndpointV2) -> P1AEndpointPartitionLawV2:
    """Snapshot one exact endpoint equality/refinement law."""
    logger.debug("p1a partition law snapshot entry endpoint=%s", endpoint.value)
    if type(value) is not P1AEndpointPartitionLawV2:
        reject("p1a-partition-law-must-be-exact")
    if type(value.endpoint) is not P1AEndpointV2:
        reject("p1a-partition-endpoint-drift")
    if value.endpoint is not endpoint:
        reject("p1a-partition-law-must-be-exact")
    if type(value.fine_partition) is not tuple:
        reject("invalid-p1a-partition")
    count = len(value.fine_partition)
    fine = _normalized(value.fine_partition, count)
    transported = _normalized(value.transported_partition, count)
    coarse = _normalized(value.coarse_partition, count)
    if transported != coarse:
        reject("p1a-transported-coarse-partition-mismatch")
    try:
        expected_map = refinement_class_map(fine, coarse)
    except (TypeError, ValueError, RecursionError) as exc:
        logger.error("p1a partition refinement rejected")
        raise P1ARealizationTransportValidationError("p1a-fine-does-not-refine-coarse") from exc
    if type(value.fine_to_coarse_class_map) is not tuple:
        reject("p1a-refinement-map-drift")
    supplied_map = tuple(_nat(item, "p1a-refinement-class", count - 1) for item in value.fine_to_coarse_class_map)
    if supplied_map != expected_map:
        reject("p1a-refinement-map-drift")
    provisional = P1AEndpointPartitionLawV2(endpoint, fine, transported, coarse, expected_map, "0" * 64)
    expected = partition_digest(provisional)
    if _dg(value.partition_digest, "p1a-partition-digest") != expected:
        reject("p1a-partition-digest-drift")
    result = replace(provisional, partition_digest=expected)
    logger.debug("p1a partition law snapshot exit endpoint=%s", endpoint.value)
    return result


def snapshot_transport(value: object, doctrine, binding) -> P1AObservationTransportV2:
    """Snapshot an arrow and reconstruct its complete fresh STRONG judgment."""
    logger.debug("p1a transport snapshot entry")
    _preflight_transport(value)
    transport_id = _id(value.transport_id, "p1a-transport-id")
    try:
        trusted_doctrine = snapshot_morphism_doctrine(doctrine)
        trusted_binding = snapshot_source_binding(binding, trusted_doctrine)
        translation = snapshot_translation(value.translation, trusted_doctrine, trusted_binding)
        judgment = observer_morphism_judgment(
            trusted_doctrine,
            trusted_binding,
            translation.translation_id,
            translation.fine_observer_id,
            translation.coarse_observer_id,
            translation.projection,
        )
    except (ObserverMorphismValidationError, TypeError, ValueError, RecursionError) as exc:
        logger.error("p1a transport judgment reconstruction rejected")
        raise P1ARealizationTransportValidationError("p1a-transport-judgment-invalid") from exc
    if (
        judgment.status is not MorphismStatus.STRONG
        or judgment.translation is None
        or judgment.translation != translation
        or judgment.obstruction
        or not judgment.information_factorizes_on_comparison
        or not judgment.coarse_domain_in_fine_domain
        or not judgment.witness_checked
    ):
        reject("p1a-strong-judgment-required")
    supplied_doctrine = _dg(value.doctrine_fingerprint, "p1a-doctrine")
    supplied_binding = _dg(value.source_binding_digest, "p1a-binding")
    if supplied_doctrine != trusted_doctrine.fingerprint or supplied_binding != trusted_binding.membership_digest:
        reject("p1a-transport-binding-drift")
    expected_judgment_root = judgment_root(judgment)
    if _dg(value.strong_judgment_root, "p1a-judgment") != expected_judgment_root:
        reject("p1a-strong-judgment-root-drift")
    digests = tuple(
        _dg(item, f"p1a-{name}")
        for name, item in (
            ("source-context", value.source_context_digest),
            ("target-context", value.target_context_digest),
            ("source-witness", value.source_witness_digest),
            ("target-witness", value.target_witness_digest),
            ("context-morphism", value.context_morphism_digest),
            ("v1-receipt", value.v1_receipt_digest),
        )
    )
    if (
        type(value.response_policy) is not ResponseTotalization
        or type(value.cost_policy) is not RealizationCostPolicy
        or type(value.closure_policy) is not RealizationClosurePolicy
    ):
        reject("p1a-transport-policy-drift")
    version = _id(value.version, "p1a-transport-version")
    scope = _id(value.scope, "p1a-transport-scope")
    if version != P1A_TRANSPORT_VERSION or scope != P1A_TRANSPORT_SCOPE:
        reject("p1a-transport-version-or-scope-drift")
    provisional = P1AObservationTransportV2(
        transport_id,
        trusted_doctrine.fingerprint,
        trusted_binding.membership_digest,
        expected_judgment_root,
        translation,
        *digests,
        value.response_policy,
        value.cost_policy,
        value.closure_policy,
        version,
        scope,
        "0" * 64,
    )
    expected = transport_digest(provisional)
    if _dg(value.transport_digest, "p1a-transport-digest") != expected:
        reject("p1a-transport-digest-drift")
    result = replace(provisional, transport_digest=expected)
    logger.debug("p1a transport snapshot exit digest=%s", expected[:12])
    return result


def _v1_row_binding(
    v1: RealizationTransportReceipt,
    transport: P1AObservationTransportV2,
    rows: tuple[P1AObservationCommutingRowV2, ...],
) -> None:
    """Bind v2 rows to the exact embedded v1 graph and horizontal rows."""
    logger.debug("p1a v1 row binding entry rows=%d", len(rows))
    graph = v1.morphism.state_index_map
    if len(rows) != len(graph) or len(v1.recurrence_rows) != len(graph):
        reject("p1a-v1-row-count-drift")
    evaluations = {(row.observer_id, row.source_index): row for row in v1.evaluation_rows}
    if len(evaluations) != len(v1.evaluation_rows):
        reject("p1a-v1-duplicate-evaluation")
    fine_id = transport.translation.fine_observer_id
    coarse_id = transport.translation.coarse_observer_id
    for ordinal, (row, target_index, recurrence) in enumerate(zip(rows, graph, v1.recurrence_rows, strict=True)):
        if (
            row.source_index != ordinal
            or row.target_index != target_index
            or recurrence.source_index != ordinal
            or recurrence.target_index != target_index
            or row.source_input_commitment != recurrence.source_input_commitment
            or row.target_input_commitment != recurrence.target_input_commitment
        ):
            reject("p1a-v1-graph-or-recurrence-row-drift")
        fine = evaluations.get((fine_id, ordinal))
        coarse = evaluations.get((coarse_id, ordinal))
        if fine is None or coarse is None:
            reject("p1a-v1-evaluation-row-missing")
        if (
            fine.target_index != target_index
            or coarse.target_index != target_index
            or fine.status is not row.source_fine.status
            or coarse.status is not row.source_coarse.status
            or fine.payload_digest != row.source_fine.payload_digest
            or coarse.payload_digest != row.source_coarse.payload_digest
        ):
            reject("p1a-v1-evaluation-row-drift")
        if (
            row.source_fine != row.target_fine
            or row.source_coarse != row.target_coarse
            or row.source_transported != row.source_coarse
            or row.target_transported != row.target_coarse
        ):
            reject("p1a-four-vertex-payload-law-drift")
    logger.debug("p1a v1 row binding exit rows=%d", len(rows))


def snapshot_receipt(
    value: object,
    doctrine,
    binding,
    *,
    source_count: int | None = None,
    target_count: int | None = None,
) -> P1ARealizationTransportReceiptV2:
    """Snapshot the complete bounded receipt and all embedded child evidence."""
    logger.debug("snapshot p1a v2 receipt entry")
    shallow_nodes = _preflight_receipt(value)
    schema = _id(value.schema, "p1a-receipt-schema")
    scope = _id(value.scope, "p1a-receipt-scope")
    if schema != P1A_RECEIPT_SCHEMA or scope != P1A_TRANSPORT_SCOPE:
        reject("p1a-receipt-schema-or-scope-drift")
    if type(value.context_transport) is not RealizationTransportReceipt:
        reject("p1a-v1-receipt-must-be-exact")
    try:
        transport = snapshot_transport(value.transport, doctrine, binding)
        v1 = snapshot_v1_receipt(value.context_transport)
    except P1ARealizationTransportValidationError:
        raise
    except (TypeError, ValueError, RecursionError) as exc:
        logger.error("p1a embedded child snapshot rejected")
        raise P1ARealizationTransportValidationError("p1a-child-invalid") from exc
    if (
        v1.doctrine_fingerprint != transport.doctrine_fingerprint
        or v1.source_context_digest != transport.source_context_digest
        or v1.target_context_digest != transport.target_context_digest
        or v1.source_witness_digest != transport.source_witness_digest
        or v1.target_witness_digest != transport.target_witness_digest
        or v1.receipt_digest != transport.v1_receipt_digest
        or v1.morphism.morphism_digest != transport.context_morphism_digest
    ):
        reject("p1a-v1-root-drift")
    rows: list[P1AObservationCommutingRowV2] = []
    decoded_nodes = 0
    for ordinal, row in enumerate(value.rows):
        source_index = _nat(row.source_index, "p1a-source-index", 255)
        target_index = _nat(row.target_index, "p1a-target-index", 255)
        if source_index != ordinal or type(row.law) is not P1AOutcomeLawV2:
            reject("p1a-row-order-or-type-drift")
        captured = tuple(
            _canonical_payload(item)
            for item in (
                row.source_fine,
                row.source_transported,
                row.source_coarse,
                row.target_fine,
                row.target_transported,
                row.target_coarse,
            )
        )
        payloads = tuple(item[0] for item in captured)
        decoded_nodes += sum(item[1] for item in captured)
        _charge_expanded_nodes(shallow_nodes, decoded_nodes)
        statuses = {item.status for item in payloads}
        expected_law = (
            P1AOutcomeLawV2.READY_COMMUTES_EXACT
            if statuses == {ObservationStatus.READY}
            else P1AOutcomeLawV2.BLOCKED_COMMUTES_EXACT
            if statuses == {ObservationStatus.BLOCKED}
            else None
        )
        if row.law is not expected_law:
            reject("p1a-row-status-law-drift")
        provisional = P1AObservationCommutingRowV2(
            source_index,
            target_index,
            _dg(row.source_input_commitment, "p1a-source-input"),
            _dg(row.target_input_commitment, "p1a-target-input"),
            *payloads,
            row.law,
            "0" * 64,
        )
        expected = row_digest(provisional)
        if _dg(row.row_digest, "p1a-row-digest") != expected:
            reject("p1a-row-digest-drift")
        rows.append(replace(provisional, row_digest=expected))
    frozen = tuple(rows)
    _v1_row_binding(v1, transport, frozen)
    source = snapshot_partition_law(value.source_partition_law, P1AEndpointV2.SOURCE)
    target = snapshot_partition_law(value.target_partition_law, P1AEndpointV2.TARGET)
    if source_count is not None:
        _nat(source_count, "p1a-source-count", MAX_P1A_V2_ROWS)
    if target_count is not None:
        _nat(target_count, "p1a-target-count", MAX_P1A_V2_ROWS)
    if len(source.fine_partition) != len(frozen) or (
        source_count is not None and len(source.fine_partition) != source_count
    ):
        reject("p1a-source-partition-carrier-drift")
    if target_count is not None and len(target.fine_partition) != target_count:
        reject("p1a-target-partition-carrier-drift")
    graph = v1.morphism.state_index_map
    if any(index >= len(target.fine_partition) for index in graph):
        reject("p1a-target-partition-carrier-drift")
    pulled_fine = tuple(target.fine_partition[index] for index in graph)
    pulled_coarse = tuple(target.coarse_partition[index] for index in graph)

    if source.fine_partition != _normalize_partition_labels(
        pulled_fine
    ) or source.coarse_partition != _normalize_partition_labels(pulled_coarse):
        reject("p1a-horizontal-partition-law-failed")
    expected = receipt_digest(schema, transport, frozen, source, target, scope)
    if _dg(value.receipt_digest, "p1a-receipt-digest") != expected:
        reject("p1a-receipt-digest-drift")
    result = P1ARealizationTransportReceiptV2(
        schema,
        transport,
        v1,
        frozen,
        source,
        target,
        expected,
        scope,
    )
    logger.debug("snapshot p1a v2 receipt exit rows=%d digest=%s", len(frozen), expected[:12])
    return result
