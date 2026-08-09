"""Iterative hostile-safe replay validation for P3-T results."""

from __future__ import annotations

from dataclasses import fields
import logging

from ..relations.types import PairOutcome
from .common import exact_shape, reject
from .preflight import network_resource_policy
from .types import (
    AssociativityJudgment,
    CompositionJudgment,
    EdgeJudgment,
    EvaluationDomainJudgment,
    IdentityLawJudgment,
    IsomorphismJudgment,
    LawStatus,
    NetworkResourcePolicy,
    ObserverNetworkJudgment,
    ObserverPairJudgment,
    PartialMap,
    RefinementStatus,
    RelationReplayRow,
    ResponseStatus,
    TriangleJudgment,
    TriangleStatus,
)

logger = logging.getLogger(__name__)
_OUTPUT_TYPES = {
    ObserverNetworkJudgment,
    PartialMap,
    EvaluationDomainJudgment,
    RelationReplayRow,
    EdgeJudgment,
    CompositionJudgment,
    IdentityLawJudgment,
    IsomorphismJudgment,
    ObserverPairJudgment,
    AssociativityJudgment,
    TriangleJudgment,
}
_OUTPUT_ENUMS = {LawStatus, RefinementStatus, ResponseStatus, TriangleStatus, PairOutcome}


def validate_observer_network_result(
    source, claimed: ObserverNetworkJudgment, policy=None
) -> ObserverNetworkJudgment:
    """Bound shape iteratively, then freshly replay the exact raw source."""
    logger.debug("validate_observer_network_result entry")
    selected = network_resource_policy() if policy is None else policy
    exact_shape(selected, NetworkResourcePolicy, "result-policy")
    limits = tuple(object.__getattribute__(selected, item.name) for item in fields(NetworkResourcePolicy))
    if any(type(item) is not int or item <= 0 for item in limits):
        reject("result-policy-limit-invalid")
    if type(claimed) is not ObserverNetworkJudgment:
        reject("network-judgment-type-invalid")
    _safe_output_shape(claimed, selected)
    from .runtime import observer_network_judgment

    expected = observer_network_judgment(source, selected)
    if claimed != expected:
        reject("observer-network-result-mismatch")
    logger.debug("validate_observer_network_result exit")
    return expected


def _safe_output_shape(value: object, policy: NetworkResourcePolicy) -> None:
    """Iteratively admit exact immutable DTOs/enums/primitives under both caps."""
    logger.debug("safe_output_shape entry type=%s", type(value).__name__)
    stack: list[tuple[bool, object, int]] = [(False, value, 0)]
    active: set[int] = set()
    nodes = 0
    primitive_bytes = 0
    while stack:
        leaving, current, depth = stack.pop()
        if leaving:
            active.discard(id(current))
            continue
        nodes += 1
        if nodes > policy.max_result_nodes:
            reject("result-node-hard-limit")
        if depth > policy.max_result_depth:
            reject("result-depth-hard-limit")
        value_type = type(current)
        if value_type in _OUTPUT_TYPES:
            try:
                instance_dict = object.__getattribute__(current, "__dict__")
            except AttributeError:
                reject("result-instance-shape-invalid")
            if type(instance_dict) is not dict:
                reject("result-instance-shape-invalid")
            if "__dataclass_fields__" in instance_dict:
                reject("result-instance-metadata-invalid")
            names = tuple(item.name for item in fields(value_type))
            if set(dict.keys(instance_dict)) != set(names):
                reject("result-instance-shape-invalid")
            identity = id(current)
            if identity in active:
                reject("result-container-cycle")
            active.add(identity)
            children = tuple(dict.__getitem__(instance_dict, name) for name in names)
            if len(children) > policy.max_result_nodes - nodes:
                reject("result-node-hard-limit")
            stack.append((True, current, depth))
            stack.extend((False, item, depth + 1) for item in reversed(children))
        elif value_type is tuple:
            identity = id(current)
            if identity in active:
                reject("result-container-cycle")
            if len(current) > policy.max_result_nodes - nodes:
                reject("result-node-hard-limit")
            active.add(identity)
            stack.append((True, current, depth))
            stack.extend((False, item, depth + 1) for item in reversed(current))
        elif value_type in _OUTPUT_ENUMS:
            stack.append((False, object.__getattribute__(current, "_value_"), depth + 1))
        elif value_type is str:
            remaining = policy.max_result_bytes - primitive_bytes
            if len(current) > remaining:
                reject("result-byte-hard-limit")
            try:
                encoded = current.encode("utf-8")
            except UnicodeError:
                reject("result-string-encoding-invalid")
            primitive_bytes += len(encoded)
        elif value_type is bool:
            primitive_bytes += 1
        elif value_type is int:
            primitive_bytes += max(8, (abs(current).bit_length() + 7) // 8)
        elif current is not None:
            reject("result-nested-shape-invalid")
        if primitive_bytes > policy.max_result_bytes:
            reject("result-byte-hard-limit")
    logger.debug("safe_output_shape exit nodes=%d bytes=%d", nodes, primitive_bytes)
