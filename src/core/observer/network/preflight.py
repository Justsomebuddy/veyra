"""Atomic hard-first aggregate charging for P3-T."""

from __future__ import annotations

from dataclasses import fields
import logging

from ..morphism import ObserverSourceBinding
from .common import exact_shape, reject
from .source_bytes import charge_source_bytes
from .types import (
    InputSnapshot,
    NetworkResourcePolicy,
    ObserverNetworkSource,
    ObserverSource,
    RawObserverPairSource,
    TranslationSource,
    TriangleDemand,
)
from .work import evaluation_charge
from ..relations.types import RelationEvaluationSource, RelationStage
from ...ontology.types import InternalObserver, ObserverDoctrine
from ...proof_core_types import Pulse, Silence

logger = logging.getLogger(__name__)


def network_resource_policy() -> NetworkResourcePolicy:
    """Return conservative finite execution caps."""
    logger.debug("network_resource_policy entry")
    result = NetworkResourcePolicy(64, 64, 256, 4096, 32768, 4096, 1_048_576, 50_000, 128, 4_194_304)
    logger.debug("network_resource_policy exit")
    return result


def hard_preflight(raw: ObserverNetworkSource, policy: NetworkResourcePolicy) -> None:
    """Validate all container counts before traversing or byte-charging members."""
    logger.debug("network hard_preflight entry")
    exact_shape(policy, NetworkResourcePolicy, "preflight-policy")
    exact_shape(raw, ObserverNetworkSource, "preflight-root")
    policy_dict = object.__getattribute__(policy, "__dict__")
    values = tuple(dict.__getitem__(policy_dict, item.name) for item in fields(NetworkResourcePolicy))
    if any(type(value) is not int or value <= 0 for value in values):
        reject("resource-policy-invalid")
    raw_dict = object.__getattribute__(raw, "__dict__")
    containers = tuple(
        dict.__getitem__(raw_dict, name)
        for name in ("inputs", "observers", "translations", "triangles", "raw_pairs")
    )
    if any(type(container) is not tuple for container in containers):
        reject("network-container-invalid")
    inputs, observers, edges, triangles, raw_pairs = containers
    if len(inputs) > policy.max_inputs or len(observers) > policy.max_observers or len(edges) > policy.max_edges:
        reject("network-hard-count-limit")
    if len(triangles) + len(raw_pairs) > policy.max_paths:
        reject("path-hard-limit")

    doctrine = dict.__getitem__(raw_dict, "p1a_doctrine")
    binding = dict.__getitem__(raw_dict, "p1a_binding")
    stages = dict.__getitem__(raw_dict, "p1a_stage_source")
    exact_shape(doctrine, ObserverDoctrine, "p1-doctrine")
    exact_shape(binding, ObserverSourceBinding, "p1-binding")
    exact_shape(stages, RelationEvaluationSource, "p1-stage-source")
    doctrine_dict = object.__getattribute__(doctrine, "__dict__")
    binding_dict = object.__getattribute__(binding, "__dict__")
    stage_dict = object.__getattribute__(stages, "__dict__")
    p1_containers = (
        dict.__getitem__(doctrine_dict, "metadata"),
        dict.__getitem__(doctrine_dict, "observers"),
        dict.__getitem__(binding_dict, "observer_ids"),
        dict.__getitem__(binding_dict, "observer_digests"),
        dict.__getitem__(stage_dict, "stages"),
        dict.__getitem__(stage_dict, "ordered_commitments"),
    )
    if any(type(container) is not tuple for container in p1_containers):
        reject("p1-raw-container-invalid")
    metadata, p1_observers, binding_ids, binding_digests, p1_stages, ordered = p1_containers
    p1_member_count = sum(len(container) for container in p1_containers)
    if (
        len(p1_observers) > policy.max_observers
        or len(binding_ids) > policy.max_observers
        or len(binding_digests) > policy.max_observers
        or len(p1_stages) > policy.max_inputs
        or len(ordered) > policy.max_inputs
        or len(p1_stages) != len(inputs)
        or p1_member_count > policy.max_rows
    ):
        reject("p1-raw-count-limit")

    row_count = 0
    nested_count = 0
    for observer in observers:
        exact_shape(observer, ObserverSource, "observer-member")
        observer_dict = object.__getattribute__(observer, "__dict__")
        rows = dict.__getitem__(observer_dict, "rows")
        if type(rows) is not tuple:
            reject("observer-rows-container-invalid")
        row_count += len(rows)
    for edge in edges:
        exact_shape(edge, TranslationSource, "translation-member")
        edge_dict = object.__getattribute__(edge, "__dict__")
        edge_containers = tuple(
            dict.__getitem__(edge_dict, name) for name in ("rows", "dependency_ids", "declared_domain")
        )
        if any(type(container) is not tuple for container in edge_containers):
            reject("translation-container-invalid")
        rows, dependencies, domain = edge_containers
        row_count += len(rows)
        nested_count += len(dependencies) + len(domain)
    if row_count > policy.max_rows or row_count + nested_count > policy.max_rows:
        reject("network-hard-work-limit")

    for item in inputs:
        exact_shape(item, InputSnapshot, "input-member")
    for item in triangles:
        exact_shape(item, TriangleDemand, "triangle-demand-member")
    for item in raw_pairs:
        exact_shape(item, RawObserverPairSource, "raw-pair-member")
    for item in p1_observers:
        exact_shape(item, InternalObserver, "p1-observer-member")
    for item in p1_stages:
        exact_shape(item, RelationStage, "p1-stage-member")

    byte_count = 0
    root_text = tuple(dict.__getitem__(raw_dict, name) for name in (
        "version", "doctrine_id", "source_id", "source_version", "network_digest"
    ))
    byte_count = _charge_many(byte_count, root_text, policy.max_canonical_bytes)
    p1_text = (
        dict.__getitem__(doctrine_dict, "doctrine_id"),
        dict.__getitem__(doctrine_dict, "admission_rule"),
        *metadata,
        dict.__getitem__(doctrine_dict, "version"),
        dict.__getitem__(doctrine_dict, "fingerprint"),
        dict.__getitem__(binding_dict, "binding_id"),
        dict.__getitem__(binding_dict, "doctrine_fingerprint"),
        *binding_ids,
        *binding_digests,
        dict.__getitem__(binding_dict, "membership_digest"),
        dict.__getitem__(binding_dict, "scope"),
        dict.__getitem__(stage_dict, "doctrine_fingerprint"),
        *ordered,
        dict.__getitem__(stage_dict, "observer_source_digest"),
        dict.__getitem__(stage_dict, "version"),
        dict.__getitem__(stage_dict, "source_digest"),
    )
    if any(type(item) is not str for item in p1_text):
        reject("p1-raw-text-invalid")
    byte_count = _charge_many(byte_count, p1_text, policy.max_canonical_bytes)
    for item in p1_observers:
        item_dict = object.__getattribute__(item, "__dict__")
        observer_id = dict.__getitem__(item_dict, "observer_id")
        canonical = dict.__getitem__(item_dict, "canonical")
        if type(observer_id) is not str or type(canonical) is not bytes:
            reject("p1-observer-member-invalid")
        byte_count = _charge_many(byte_count, (observer_id, canonical), policy.max_canonical_bytes)
    for item in p1_stages:
        item_dict = object.__getattribute__(item, "__dict__")
        stage_id = dict.__getitem__(item_dict, "stage_id")
        commitment = dict.__getitem__(item_dict, "commitment")
        if type(stage_id) is not str or type(commitment) is not str:
            reject("p1-stage-member-invalid")
        byte_count = _charge_many(byte_count, (stage_id, commitment), policy.max_canonical_bytes)
        byte_count += _recurrence_bytes(dict.__getitem__(item_dict, "recurrence"))
        if byte_count > policy.max_canonical_bytes:
            reject("canonical-byte-hard-limit")
    byte_count = _charge_many(
        byte_count, (*triangles, *raw_pairs, *inputs, *observers, *edges), policy.max_canonical_bytes
    )

    evaluations, ordered_a2_rows = evaluation_charge(
        inputs, observers, edges, triangles, raw_pairs, row_count, policy.max_paths
    )
    if evaluations > policy.max_evaluations:
        reject("network-hard-work-limit")
    logger.debug(
        "network hard_preflight exit rows=%d a2_rows=%d work=%d bytes=%d",
        row_count,
        ordered_a2_rows,
        evaluations,
        byte_count,
    )


def _charge_many(total: int, values: tuple[object, ...], cap: int) -> int:
    """Charge sequentially so every text sees the true remaining byte budget."""
    logger.debug("network charge_many entry count=%d total=%d", len(values), total)
    for value in values:
        total += charge_source_bytes(value, cap - total)
    logger.debug("network charge_many exit total=%d", total)
    return total


def _recurrence_bytes(value: object) -> int:
    """Charge one exact bounded recurrence iteratively before upstream replay."""
    logger.debug("charge recurrence entry")
    depth = 0
    cursor = value
    visited: set[int] = set()
    while type(cursor) is Pulse:
        exact_shape(cursor, Pulse, "p1-stage-pulse")
        if id(cursor) in visited:
            reject("p1-stage-recurrence-cycle")
        visited.add(id(cursor))
        depth += 1
        if depth > 128:
            reject("p1-stage-recurrence-hard-limit")
        pulse_dict = object.__getattribute__(cursor, "__dict__")
        cursor = dict.__getitem__(pulse_dict, "tail")
    exact_shape(cursor, Silence, "p1-stage-silence")
    result = 6 + depth
    logger.debug("charge recurrence exit bytes=%d", result)
    return result
