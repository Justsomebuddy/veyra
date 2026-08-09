"""Fresh target-free runtime for closed provisional P1-B builders."""

from __future__ import annotations

from hashlib import sha256
import logging

from .construction.finite_builder.codec import _decode_builder, _decode_recurrence
from .construction.finite_builder.digest import _trace_digest
from .finite_builder_types import (
    ConstructionSourceBinding, ReplayArtifact, ReplayStatus,
)
from .finite_builder_validation import (
    FiniteBuilderValidationError, _builder_shape, _hex_digest,
    _snapshot_doctrine, _snapshot_source, _snapshot_target_stage,
)
from .positive_ontology import ontology_stage
from .positive_ontology_doctrine import stage_commitment
from .positive_ontology_types import ObserverDoctrine
from .proof_core_types import CoreTerm, Pulse

logger = logging.getLogger(__name__)


class FiniteBuilderReplayError(RuntimeError):
    """A validated closed builder violated a replay invariant."""


def _recurrence_depth(value: CoreTerm) -> int:
    """Count a trusted fresh Silence/Pulse recurrence."""
    logger.debug("_recurrence_depth entry")
    depth, cursor = 0, value
    while type(cursor) is Pulse:
        depth += 1
        cursor = cursor.tail
    logger.debug("_recurrence_depth exit depth=%d", depth)
    return depth


def _output_recurrence_commitment(value: CoreTerm) -> str:
    """Commit one trusted replay output independently of object identity."""
    logger.debug("_output_recurrence_commitment entry")
    depth = _recurrence_depth(value)
    digest = sha256()
    for token in (b"kind", b"p1b-output-recurrence", b"depth", str(depth).encode("ascii")):
        digest.update(len(token).to_bytes(4, "big"))
        digest.update(token)
    result = digest.hexdigest()
    logger.debug("_output_recurrence_commitment exit")
    return result


def replay_finite_builder(
    doctrine: ObserverDoctrine, source: ConstructionSourceBinding
) -> ReplayArtifact:
    """Replay one fixed source without accepting or reading any target."""
    logger.debug("replay_finite_builder entry")
    doctrine = _snapshot_doctrine(doctrine)
    source = _snapshot_source(source, doctrine)
    expression = _decode_builder(source.program.canonical)
    seed_id, added_pulses, nodes = _builder_shape(expression)
    seeds = {item.seed_id: item for item in source.seeds}
    if seed_id not in seeds:
        logger.error("replay_finite_builder seed unbound")
        raise FiniteBuilderReplayError("replay-seed-unbound")
    recurrence = _decode_recurrence(seeds[seed_id].canonical)
    seed_depth = _recurrence_depth(recurrence)
    output_depth = seed_depth + added_pulses
    if output_depth > 128:
        logger.error("replay_finite_builder total depth limit")
        raise FiniteBuilderValidationError("replay-total-depth-limit")
    for _ in range(added_pulses):
        recurrence = Pulse(recurrence)
    stage = ontology_stage(
        source.program.output_stage_id, recurrence, doctrine,
        len(source.program.observer_ids),
    )
    stage_digest = stage_commitment(stage)
    recurrence_digest = _output_recurrence_commitment(stage.representative)
    trace = _trace_digest(
        source.membership_digest, stage_digest, recurrence_digest, nodes, output_depth
    )
    result = ReplayArtifact(
        source.membership_digest, stage, stage_digest, recurrence_digest,
        trace, nodes, output_depth,
    )
    logger.debug("replay_finite_builder exit depth=%d", output_depth)
    return result


def snapshot_replay_artifact(
    doctrine: ObserverDoctrine,
    source: ConstructionSourceBinding,
    value: ReplayArtifact,
) -> ReplayArtifact:
    """Revalidate nested output and return a fresh artifact for downstream use."""
    logger.debug("snapshot_replay_artifact entry")
    doctrine = _snapshot_doctrine(doctrine)
    source = _snapshot_source(source, doctrine)
    if type(value) is not ReplayArtifact:
        logger.error("snapshot_replay_artifact exact gate rejected")
        raise FiniteBuilderValidationError("replay-artifact-must-be-exact")
    try:
        source_digest, stage = value.source_binding_digest, value.stage
        stage_digest = value.stage_commitment
        recurrence_digest, trace = value.recurrence_commitment, value.trace_digest
        nodes, depth = value.builder_nodes, value.pulse_depth
        status, scope = value.status, value.scope
    except AttributeError as exc:
        logger.error("snapshot_replay_artifact missing fields")
        raise FiniteBuilderValidationError("replay-artifact-missing-fields") from exc
    source_digest = _hex_digest(source_digest, "replay-source-digest")
    stage_digest = _hex_digest(stage_digest, "replay-stage-commitment")
    recurrence_digest = _hex_digest(
        recurrence_digest, "replay-recurrence-commitment"
    )
    trace = _hex_digest(trace, "replay-trace-digest")
    if (
        type(nodes) is not int or type(depth) is not int
        or type(status) is not ReplayStatus or type(scope) is not str
    ):
        logger.error("snapshot_replay_artifact scalar fields rejected")
        raise FiniteBuilderValidationError("invalid-replay-artifact-fields")
    stage = _snapshot_target_stage(stage, doctrine)
    expected = replay_finite_builder(doctrine, source)
    if (
        source_digest != source.membership_digest
        or stage != expected.stage
        or stage_commitment(stage) != expected.stage_commitment
        or stage_digest != expected.stage_commitment
        or recurrence_digest != expected.recurrence_commitment
        or trace != expected.trace_digest
        or nodes != expected.builder_nodes
        or depth != expected.pulse_depth
        or status is not ReplayStatus.REPLAYED
        or scope != "fresh-finite-replay"
    ):
        logger.error("snapshot_replay_artifact semantic drift")
        raise FiniteBuilderValidationError("replay-artifact-semantic-drift")
    result = ReplayArtifact(
        source.membership_digest, stage, expected.stage_commitment,
        expected.recurrence_commitment, expected.trace_digest,
        expected.builder_nodes, expected.pulse_depth,
    )
    logger.debug("snapshot_replay_artifact exit")
    return result
