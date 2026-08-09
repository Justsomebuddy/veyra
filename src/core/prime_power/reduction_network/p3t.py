"""Arithmetic-specific raw P3-T source for the exact finite P3-N2 scope."""

from __future__ import annotations

import logging

from ...observer_core_codec import decode_observer
from ...observer_core_semantics import observe
from ...observer_core_types import Apply, Blocked, Input, Pair, PrimitiveId, Ready
from ...observer.morphism import ProjectionStep, observer_source_binding
from ...observer.network.common import reject as reject_p3t
from ...observer.network.source import (
    blocked, grammar_descriptor, input_snapshot, observation_row,
    observer_network_source, observer_source, raw_observer_pair_source, ready,
    translation_row, translation_source, triangle_demand, typed_value,
)
from ...observer.relations.digest import response_payload_digest
from ...observer.relations.replay import observation_bytes
from ...observer.relations.request import relation_evaluation_source
from ...ontology.core import internal_observer
from ...ontology.doctrine import observer_doctrine
from ...proof_core_types import Pulse, Silence
from .common import digest, reject

logger = logging.getLogger(__name__)
P3T_ADAPTER_VERSION = "p3n2-arithmetic-p3t-v1"


def _recurrence(depth: int):
    """Construct one closed recurrence code with visible progress in debug logs."""
    logger.debug("_recurrence entry depth=%d", depth)
    value = Silence()
    for _ in range(depth):
        value = Pulse(value)
    logger.debug("_recurrence exit depth=%d", depth)
    return value


def _observer_programs(depths: tuple[int, ...]):
    """Build the nested rho program chain used by the supported exact slice."""
    logger.debug("_observer_programs entry count=%d", len(depths))
    if not 1 <= len(depths) <= 3:
        reject("arithmetic-p3t-supports-one-to-three-depths")
    programs = [Input()]
    if len(depths) >= 2:
        coarse = Apply(PrimitiveId.CREST, Input())
        programs = [coarse, Pair(coarse, Input())]
    if len(depths) == 3:
        coarse = programs[0]
        middle = Pair(
            coarse,
            Apply(PrimitiveId.CREST, Apply(PrimitiveId.TAIL, Input())),
        )
        programs = [coarse, middle, Pair(middle, Input())]
    result = tuple(programs)
    logger.debug("_observer_programs exit count=%d", len(result))
    return result


def _stage_codes(families, depths: tuple[int, ...]) -> tuple[int, ...]:
    """Synthesize recurrence codes whose P1 equality partitions equal residues."""
    logger.debug("_stage_codes entry families=%d depths=%d", len(families), len(depths))
    coordinates = tuple({x.depth: x.residue for x in family.coordinates} for family in families)
    if len(depths) == 1:
        classes = {row[depths[0]] for row in coordinates}
        if len(classes) > 128:
            reject("single-depth-p3t-class-limit")
        by_value = {value: index for index, value in enumerate(sorted(classes))}
        result = tuple(by_value[row[depths[0]]] for row in coordinates)
    else:
        coarse = {row[depths[0]] for row in coordinates}
        if len(coarse) != 1:
            reject("arithmetic-p3t-coarse-partition-not-representable")
        fine_depth = depths[-1]
        fine_values = tuple(sorted({row[fine_depth] for row in coordinates}))
        if len(depths) == 2:
            by_fine = {value: index + 1 for index, value in enumerate(fine_values)}
        else:
            middle_depth = depths[1]
            middle_groups = {}
            for value in fine_values:
                member = next(row for row in coordinates if row[fine_depth] == value)
                middle_groups.setdefault(member[middle_depth], []).append(value)
            if len(middle_groups) == 1:
                by_fine = {value: index + 2 for index, value in enumerate(fine_values)}
            elif len(middle_groups) == 2:
                singleton = next((values for values in middle_groups.values() if len(values) == 1), None)
                if singleton is None:
                    reject("arithmetic-p3t-middle-partition-not-representable")
                special = singleton[0]
                rest = tuple(value for value in fine_values if value != special)
                by_fine = {special: 1, **{value: index + 2 for index, value in enumerate(rest)}}
            else:
                reject("arithmetic-p3t-middle-partition-not-representable")
        result = tuple(by_fine[row[fine_depth]] for row in coordinates)
    logger.debug("_stage_codes exit distinct=%d", len(set(result)))
    return result


def _family_payload(prime_digest: str, doctrine_digest: str, family) -> bytes:
    """Encode the exact finite compatible-family presentation into input bytes."""
    logger.debug("_family_payload entry family=%s", family.family_id)
    rows = (
        ("prime", prime_digest.encode()), ("doctrine", doctrine_digest.encode()),
        ("family", family.family_digest.encode()), ("integer", str(family.integer).encode()),
        *((f"coordinate-{i}", f"{x.depth}:{x.residue}:{x.coordinate_digest}".encode())
          for i, x in enumerate(family.coordinates)),
    )
    result = bytes.fromhex(digest("veyra.p3n2.p3t-family-input.v1", rows)) + b"\0" + str(family.integer).encode()
    logger.debug("_family_payload exit bytes=%d", len(result))
    return result


def _actual_rows(member, descriptor, inputs, stage_source):
    """Replay literal P1 observations and retain their ready value tokens."""
    logger.debug("_actual_rows entry observer=%s", member.observer_id)
    program = decode_observer(member.canonical)
    rows, values = [], []
    for input_value, stage in zip(inputs, stage_source.stages, strict=True):
        actual = observe(program, stage.recurrence)
        payload = observation_bytes(actual)
        if type(actual) is Ready:
            value = typed_value(descriptor.grammar_id, descriptor.kind_id, payload)
            rows.append(observation_row(input_value, ready(value)))
            values.append(value)
        elif type(actual) is Blocked:
            rows.append(observation_row(input_value, blocked(response_payload_digest(payload))))
            values.append(None)
        else:
            reject_p3t("arithmetic-p3t-unknown-observation")
    result = (observer_source(member.observer_id, "p3n2-family", descriptor, tuple(rows)), tuple(values))
    logger.debug("_actual_rows exit ready=%d", sum(x is not None for x in values))
    return result


def arithmetic_p3t_source(prime, doctrine, nodes, families, binding_digest: str):
    """Build one genuine raw P3-T network whose equality partitions are residues."""
    logger.debug("arithmetic_p3t_source entry")
    depths = tuple(x.depth for x in nodes)
    programs = _observer_programs(depths)
    ids = tuple(f"rho-depth-{depth}" for depth in depths)
    members = tuple(internal_observer(name, program) for name, program in zip(ids, programs, strict=True))
    p1_doctrine = observer_doctrine(
        f"P3N2-arithmetic-{binding_digest[:16]}", "closed-r11-nested-rho-projections",
        (P3T_ADAPTER_VERSION, prime.source_digest, doctrine.doctrine_digest, binding_digest),
        members, version=P3T_ADAPTER_VERSION,
    )
    binding = observer_source_binding(p1_doctrine, f"p3n2-binding-{binding_digest[:16]}", ids)
    codes = _stage_codes(families, depths)
    stage_source = relation_evaluation_source(p1_doctrine, binding, tuple(
        (f"family-{index}", _recurrence(code)) for index, code in enumerate(codes)
    ))
    inputs = tuple(input_snapshot(
        stage.stage_id, "p3n2-family", _family_payload(prime.source_digest, doctrine.doctrine_digest, family),
        stage.commitment,
    ) for stage, family in zip(stage_source.stages, families, strict=True))
    observers, values = [], {}
    for member, depth in zip(members, depths, strict=True):
        descriptor = grammar_descriptor(f"p3n2-rho-{depth}", "p1-residue-code", member.canonical)
        source, actual = _actual_rows(member, descriptor, inputs, stage_source)
        if any(item is None for item in actual):
            reject("arithmetic-p3t-observer-not-total-on-scope")
        observers.append(source)
        values[depth] = actual
    edges = []
    for fine_index, fine in enumerate(depths):
        for coarse_index, coarse in enumerate(depths):
            if coarse >= fine:
                continue
            seen, rows = set(), []
            for source_value, target_value in zip(values[fine], values[coarse], strict=True):
                if source_value.value_digest in seen:
                    continue
                seen.add(source_value.value_digest)
                rows.append(translation_row(source_value, target_value))
            dependencies = (
                observers[fine_index].grammar_descriptor.commitment,
                observers[coarse_index].grammar_descriptor.commitment,
            )
            edges.append(translation_source(
                f"reduce-{fine}-to-{coarse}", ids[fine_index], ids[coarse_index],
                tuple(x.source_value.value_digest for x in rows), tuple(rows), dependencies,
            ))
    pairs = tuple(raw_observer_pair_source(
        f"pair-{fine}-{coarse}", ids[i], ids[j],
        f"rho-projection-{fine}-to-{coarse}" if fine > coarse else "",
        tuple(ProjectionStep.LEFT for _ in range(i - j)) if fine > coarse else None,
    ) for i, fine in enumerate(depths) for j, coarse in enumerate(depths) if i != j)
    edge_ids = {(x.source_observer_id, x.target_observer_id): x.edge_id for x in edges}
    triangles = tuple(triangle_demand(
        f"triangle-{fine}-{middle}-{coarse}", edge_ids[(ids[i], ids[k])],
        (edge_ids[(ids[i], ids[j])], edge_ids[(ids[j], ids[k])]),
    ) for i, fine in enumerate(depths) for j, middle in enumerate(depths)
      for k, coarse in enumerate(depths) if k < j < i)
    result = observer_network_source(
        p1_doctrine.doctrine_id, f"p3n2-network-{binding_digest[:16]}", P3T_ADAPTER_VERSION,
        inputs, tuple(observers), tuple(edges), triangles, p1_doctrine, binding,
        stage_source, pairs,
    )
    logger.debug("arithmetic_p3t_source exit digest=%s", result.network_digest)
    return result
