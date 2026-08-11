"""Provisional P1-B constructors and formal finite-generability judgment."""

from __future__ import annotations

import logging

from .construction.finite_builder.codec import (
    FiniteBuilderCodecError, _canonical_builder_bytes, _canonical_recurrence_bytes,
)
from .construction.finite_builder.digest import (
    _program_digest, _seed_digest, _source_digest,
)
from .construction.finite_builder.runtime import replay_finite_builder, snapshot_replay_artifact
from .construction.finite_builder.types import (
    ConstructionSourceBinding, FiniteBuilderExpr, FiniteBuilderProgram,
    FiniteConstructionJudgment, FiniteRecurrenceSeed, FormalGenerability,
    OnticGenesis, PulseStep, ScopedObjectFormation, TargetIndependence,
)
from .construction.finite_builder.validation import (
    FiniteBuilderValidationError, _builder_shape, _hex_digest, _identifier,
    _snapshot_builder_expr, _snapshot_doctrine, _snapshot_program,
    _snapshot_seed, _snapshot_source, _snapshot_target_stage,
)
from .positive_ontology_doctrine import stage_commitment
from .positive_ontology_types import ObserverDoctrine, OntologyStage
from .proof_core_types import CoreTerm

logger = logging.getLogger(__name__)


def compose_finite_builder_expressions(
    outer: FiniteBuilderExpr, inner: FiniteBuilderExpr
) -> FiniteBuilderExpr:
    """Substitute the inner result for the outer expression's sole SeedRef."""
    logger.debug("compose_finite_builder_expressions entry")
    outer = _snapshot_builder_expr(outer)
    inner = _snapshot_builder_expr(inner)
    _, outer_pulses, _ = _builder_shape(outer)
    result = inner
    for _ in range(outer_pulses):
        result = PulseStep(result)
    result = _snapshot_builder_expr(result)
    logger.debug("compose_finite_builder_expressions exit pulses=%d", outer_pulses)
    return result


def finite_recurrence_seed(seed_id: str, recurrence: CoreTerm) -> FiniteRecurrenceSeed:
    """Capture one exact admitted seed before any construction target is read."""
    logger.debug("finite_recurrence_seed entry")
    seed_id = _identifier(seed_id, "seed-id")
    try:
        canonical = _canonical_recurrence_bytes(recurrence)
    except FiniteBuilderCodecError as exc:
        logger.error("finite_recurrence_seed recurrence rejected")
        raise FiniteBuilderValidationError("invalid-construction-seed") from exc
    result = _snapshot_seed(
        FiniteRecurrenceSeed(seed_id, canonical, _seed_digest(seed_id, canonical))
    )
    logger.debug("finite_recurrence_seed exit")
    return result


def finite_builder_program(
    builder_id: str,
    output_stage_id: str,
    observer_ids: tuple[str, ...],
    expression: FiniteBuilderExpr,
) -> FiniteBuilderProgram:
    """Capture closed SeedRef/PulseStep syntax with no target input channel."""
    logger.debug("finite_builder_program entry")
    builder_id = _identifier(builder_id, "builder-id")
    output_stage_id = _identifier(output_stage_id, "output-stage-id")
    if type(observer_ids) is not tuple or len(observer_ids) > 64:
        logger.error("finite_builder_program observer tuple rejected")
        raise FiniteBuilderValidationError("invalid-builder-observer-prefix")
    observers = tuple(_identifier(item, "observer-id") for item in observer_ids)
    captured = _snapshot_builder_expr(expression)
    seed_id, _, _ = _builder_shape(captured)
    canonical = _canonical_builder_bytes(captured)
    seed_ids = (seed_id,)
    digest = _program_digest(
        builder_id, output_stage_id, observers, canonical, seed_ids
    )
    result = _snapshot_program(FiniteBuilderProgram(
        builder_id, output_stage_id, observers, canonical, seed_ids, digest
    ))
    logger.debug("finite_builder_program exit")
    return result


def construction_source_binding(
    doctrine: ObserverDoctrine,
    binding_id: str,
    program: FiniteBuilderProgram,
    seeds: tuple[FiniteRecurrenceSeed, ...],
) -> ConstructionSourceBinding:
    """Bind exact doctrine/program/seed membership, never selection chronology."""
    logger.debug("construction_source_binding entry")
    doctrine = _snapshot_doctrine(doctrine)
    binding_id = _identifier(binding_id, "construction-binding-id")
    program = _snapshot_program(program)
    if type(seeds) is not tuple or not seeds or len(seeds) > 128:
        logger.error("construction_source_binding seed tuple rejected")
        raise FiniteBuilderValidationError("invalid-construction-seeds")
    captured = tuple(_snapshot_seed(item) for item in seeds)
    ids = tuple(item.seed_id for item in captured)
    digest = _source_digest(
        binding_id, doctrine.fingerprint, program.program_digest,
        ids, tuple(item.seed_digest for item in captured),
    )
    result = _snapshot_source(ConstructionSourceBinding(
        binding_id, doctrine.fingerprint, program, captured, digest
    ), doctrine)
    logger.debug("construction_source_binding exit")
    return result


def finite_construction_judgment(
    doctrine: ObserverDoctrine,
    source: ConstructionSourceBinding,
    target: OntologyStage,
) -> FiniteConstructionJudgment:
    """Replay first, then read the target, and compare exact stage commitments."""
    logger.debug("finite_construction_judgment entry")
    doctrine = _snapshot_doctrine(doctrine)
    source = _snapshot_source(source, doctrine)
    replay = replay_finite_builder(doctrine, source)
    target = _snapshot_target_stage(target, doctrine)
    target_digest = stage_commitment(target)
    if replay.stage_commitment == target_digest:
        status, obstruction = FormalGenerability.GENERABLE, ""
    else:
        status = FormalGenerability.TARGET_MISMATCH
        obstruction = "replayed-stage-does-not-match-target"
    result = FiniteConstructionJudgment(
        doctrine.fingerprint, source.membership_digest, target.stage_id,
        target_digest, replay, status, obstruction,
    )
    logger.debug("finite_construction_judgment exit status=%s", status.value)
    return result


def validate_finite_construction_judgment(
    doctrine: ObserverDoctrine,
    source: ConstructionSourceBinding,
    target: OntologyStage,
    value: FiniteConstructionJudgment,
) -> FiniteConstructionJudgment:
    """Recompute and freshly validate a judgment before downstream reliance."""
    logger.debug("validate_finite_construction_judgment entry")
    doctrine = _snapshot_doctrine(doctrine)
    source = _snapshot_source(source, doctrine)
    if type(value) is not FiniteConstructionJudgment:
        logger.error("validate_finite_construction_judgment exact gate rejected")
        raise FiniteBuilderValidationError("construction-judgment-must-be-exact")
    expected = finite_construction_judgment(doctrine, source, target)
    try:
        fingerprint = value.doctrine_fingerprint
        source_digest, target_id = value.source_binding_digest, value.target_stage_id
        target_digest, replay = value.target_commitment, value.replay
        formal, obstruction = value.formal_generability, value.obstruction
        genesis, independence = value.ontic_genesis, value.target_independence
        scoped, scope = value.scoped_object, value.scope
    except AttributeError as exc:
        logger.error("validate_finite_construction_judgment missing fields")
        raise FiniteBuilderValidationError("construction-judgment-missing-fields") from exc
    fingerprint = _hex_digest(fingerprint, "judgment-doctrine-fingerprint")
    source_digest = _hex_digest(source_digest, "judgment-source-digest")
    target_digest = _hex_digest(target_digest, "judgment-target-commitment")
    target_id = _identifier(target_id, "judgment-target-id")
    replay = snapshot_replay_artifact(doctrine, source, replay)
    if (
        type(formal) is not FormalGenerability
        or type(obstruction) is not str
        or genesis is not OnticGenesis.NOT_ESTABLISHED
        or independence is not TargetIndependence.NOT_ESTABLISHED
        or scoped is not ScopedObjectFormation.OPEN
        or type(scope) is not str
    ):
        logger.error("validate_finite_construction_judgment scalar fields rejected")
        raise FiniteBuilderValidationError("invalid-construction-judgment-fields")
    if (
        fingerprint != expected.doctrine_fingerprint
        or source_digest != expected.source_binding_digest
        or target_id != expected.target_stage_id
        or target_digest != expected.target_commitment
        or replay.stage_commitment != expected.replay.stage_commitment
        or formal is not expected.formal_generability
        or obstruction != expected.obstruction
        or scope != "provisional-p1b-formal-finite-generability"
    ):
        logger.error("validate_finite_construction_judgment semantic drift")
        raise FiniteBuilderValidationError("construction-judgment-semantic-drift")
    logger.debug("validate_finite_construction_judgment exit")
    return expected
