"""Exact raw-P1-backed positive and pressure fixture for P3-T."""

from __future__ import annotations

import logging

from ...observer_core_codec import decode_observer
from ...observer_core_semantics import observe
from ...observer_core_types import Blocked as P1Blocked, Ready as P1Ready
from ..morphism import (
    ProjectionStep, observer_source_binding, p1a_observer_morphism_doctrine,
)
from ..relations.request import relation_evaluation_source
from ..relations.digest import response_payload_digest
from ..relations.replay import observation_bytes
from ...proof_core_types import Pulse, Silence
from .common import reject
from .source import (
    blocked,
    grammar_descriptor,
    input_snapshot,
    observation_row,
    observer_network_source,
    observer_source,
    raw_observer_pair_source,
    ready,
    translation_row,
    translation_source,
    triangle_demand,
    typed_value,
)

logger = logging.getLogger(__name__)


def _recurrence(depth: int):
    """Build one closed recurrence term for an exact finite depth."""
    logger.debug("example recurrence entry depth=%d", depth)
    value = Silence()
    for _ in range(depth):
        value = Pulse(value)
    logger.debug("example recurrence exit depth=%d", depth)
    return value


def _observer_table(member, stages, inputs):
    """Replay one admitted P1 observer and bind exact response bytes."""
    logger.debug("example observer_table entry observer=%s", member.observer_id)
    descriptor = grammar_descriptor(f"p1:{member.observer_id}", "observation", member.canonical)
    program = decode_observer(member.canonical)
    rows = []
    values = []
    for stage, input_value in zip(stages.stages, inputs):
        actual = observe(program, stage.recurrence)
        payload = observation_bytes(actual)
        if type(actual) is P1Ready:
            value = typed_value(descriptor.grammar_id, descriptor.kind_id, payload)
            response = ready(value)
            values.append(value)
        elif type(actual) is P1Blocked:
            response = blocked(response_payload_digest(payload))
            values.append(None)
        else:
            reject("example-p1-response-unknown")
        rows.append(observation_row(input_value, response))
    source = observer_source(member.observer_id, "p1-stage", descriptor, tuple(rows))
    logger.debug("example observer_table exit observer=%s", member.observer_id)
    return source, tuple(values)


def _edge(edge_id, source_id, target_id, values, observers, *, limit=None):
    """Derive one deterministic table from corresponding actual P1 occurrences."""
    logger.debug("example edge entry edge=%s", edge_id)
    seen = set()
    rows = []
    for source_value, target_value in zip(values[source_id], values[target_id]):
        if source_value is None or target_value is None or source_value.value_digest in seen:
            continue
        seen.add(source_value.value_digest)
        rows.append(translation_row(source_value, target_value))
    if limit is not None:
        rows = rows[:limit]
    by_id = {item.observer_id: item for item in observers}
    dependencies = (
        by_id[source_id].grammar_descriptor.commitment,
        by_id[target_id].grammar_descriptor.commitment,
    )
    domain = tuple(item.source_value.value_digest for item in rows)
    result = translation_source(edge_id, source_id, target_id, domain, tuple(rows), dependencies)
    logger.debug("example edge exit edge=%s rows=%d", edge_id, len(rows))
    return result


def example_observer_network():
    """Build one exact P1-backed three-edge chain with direct path pressure."""
    logger.debug("example_observer_network entry")
    doctrine = p1a_observer_morphism_doctrine()
    observer_ids = tuple(item.observer_id for item in doctrine.observers)
    binding = observer_source_binding(doctrine, "p3t-example-binding", observer_ids)
    stages = relation_evaluation_source(
        doctrine,
        binding,
        tuple((f"depth-{depth}", _recurrence(depth)) for depth in range(4)),
    )
    inputs = tuple(
        input_snapshot(stage.stage_id, "p1-stage", stage.stage_id.encode(), stage.commitment)
        for stage in stages.stages
    )
    observers = []
    values = {}
    for member in doctrine.observers:
        source, table = _observer_table(member, stages, inputs)
        observers.append(source)
        values[member.observer_id] = table
    frozen_observers = tuple(observers)
    projections = {
        ("fine-triply-nested", "fine-nested"): (ProjectionStep.LEFT,),
        ("fine-nested", "fine-total"): (ProjectionStep.LEFT,),
        ("fine-total", "coarse-crest"): (ProjectionStep.LEFT,),
        ("fine-triply-nested", "fine-total"): (ProjectionStep.LEFT, ProjectionStep.LEFT),
        ("fine-domain-hole", "coarse-crest"): (ProjectionStep.LEFT,),
    }
    edges = (
        _edge("triply-nested", "fine-triply-nested", "fine-nested", values, frozen_observers),
        _edge("nested-total", "fine-nested", "fine-total", values, frozen_observers),
        _edge("total-nested", "fine-total", "fine-nested", values, frozen_observers),
        _edge("total-crest", "fine-total", "coarse-crest", values, frozen_observers),
        _edge("triply-total", "fine-triply-nested", "fine-total", values, frozen_observers),
        _edge("triply-total-partial", "fine-triply-nested", "fine-total", values, frozen_observers, limit=2),
        _edge("hole-crest", "fine-domain-hole", "coarse-crest", values, frozen_observers),
    )
    raw_pairs = tuple(
        raw_observer_pair_source(
            f"pair:{source_id}:{target_id}",
            source_id,
            target_id,
            f"morphism:{source_id}:{target_id}" if (source_id, target_id) in projections else "",
            projections.get((source_id, target_id)),
        )
        for source_id in observer_ids
        for target_id in observer_ids
        if source_id != target_id
    )
    triangles = (
        triangle_demand("triangle-exact", "triply-total", ("triply-nested", "nested-total")),
        triangle_demand(
            "triangle-partial", "triply-total-partial", ("triply-nested", "nested-total")
        ),
    )
    result = observer_network_source(
        doctrine.doctrine_id,
        "p3t-example",
        "1",
        inputs,
        frozen_observers,
        edges,
        triangles,
        doctrine,
        binding,
        stages,
        raw_pairs,
    )
    logger.debug("example_observer_network exit")
    return result
