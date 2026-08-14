"""Finite exact payload partitions and vertical refinement laws."""

from __future__ import annotations
import logging
from .digest import partition_digest
from .types import P1AEndpointPartitionLawV2, P1AEndpointV2, P1AObservationPayloadV2

logger = logging.getLogger(__name__)
MAX_P1A_V2_PARTITION_STATES = 256


def _reject(reason: str) -> None:
    """Raise one bounded partition error without logging payload data."""
    logger.error("p1a v2 partition rejected reason=%s", reason)
    raise ValueError(reason)


def _normalized_partition(value: object) -> tuple[int, ...]:
    """Validate one nonempty first-occurrence-normalized bounded partition."""
    logger.debug("p1a v2 normalized partition entry")
    if type(value) is not tuple or not 1 <= len(value) <= MAX_P1A_V2_PARTITION_STATES:
        _reject("p1a-partition-carrier")
    result: tuple[int, ...] = value
    seen: set[int] = set()
    next_class = 0
    for item in result:
        if type(item) is not int or not 0 <= item < len(result):
            _reject("p1a-partition-class")
        if item not in seen:
            if item != next_class:
                _reject("p1a-partition-noncanonical")
            seen.add(item)
            next_class += 1
    logger.debug("p1a v2 normalized partition exit classes=%d", next_class)
    return result


def normalize_payload_partition(values: tuple[P1AObservationPayloadV2, ...]) -> tuple[int, ...]:
    """Normalize exact canonical payload bytes by first occurrence."""
    logger.debug("normalize_payload_partition entry")
    if type(values) is not tuple or not 1 <= len(values) <= MAX_P1A_V2_PARTITION_STATES:
        _reject("p1a-payload-partition-carrier")
    logger.debug("normalize_payload_partition bounded values=%d", len(values))
    classes: dict[bytes, int] = {}
    out = []
    for value in values:
        if type(value) is not P1AObservationPayloadV2 or type(value.canonical_payload) is not bytes:
            _reject("p1a-payload-partition-value")
        key = value.canonical_payload
        if key not in classes:
            classes[key] = len(classes)
        out.append(classes[key])
    result = tuple(out)
    logger.debug("normalize_payload_partition exit classes=%d", len(classes))
    return result


def refinement_class_map(fine: tuple[int, ...], coarse: tuple[int, ...]) -> tuple[int, ...]:
    """Return the unique fine-class to coarse-class map, or reject."""
    logger.debug("refinement_class_map entry")
    fine = _normalized_partition(fine)
    coarse = _normalized_partition(coarse)
    if len(fine) != len(coarse):
        _reject("p1a-partition-carrier")
    mapping = [-1] * (1 + max(fine))
    for f, c in zip(fine, coarse, strict=True):
        if mapping[f] == -1:
            mapping[f] = c
        elif mapping[f] != c:
            _reject("p1a-fine-does-not-refine-coarse")
    result = tuple(mapping)
    logger.debug("refinement_class_map exit classes=%d", len(result))
    return result


def endpoint_partition_law(
    endpoint: P1AEndpointV2,
    fine_values: tuple[P1AObservationPayloadV2, ...],
    transported_values: tuple[P1AObservationPayloadV2, ...],
    coarse_values: tuple[P1AObservationPayloadV2, ...],
) -> P1AEndpointPartitionLawV2:
    """Reconstruct one endpoint's transported/coarse equality and refinement."""
    if type(endpoint) is not P1AEndpointV2:
        _reject("p1a-endpoint-type")
    logger.debug("endpoint_partition_law entry endpoint=%s", endpoint.value)
    fine = normalize_payload_partition(fine_values)
    transported = normalize_payload_partition(transported_values)
    coarse = normalize_payload_partition(coarse_values)
    if transported != coarse:
        _reject("p1a-transported-coarse-partition-mismatch")
    mapping = refinement_class_map(fine, coarse)
    provisional = P1AEndpointPartitionLawV2(endpoint, fine, transported, coarse, mapping, "0" * 64)
    result = P1AEndpointPartitionLawV2(endpoint, fine, transported, coarse, mapping, partition_digest(provisional))
    logger.debug("endpoint_partition_law exit endpoint=%s", endpoint.value)
    return result
