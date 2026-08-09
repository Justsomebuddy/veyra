"""Positive formal-generability tests for provisional P1-B finite replay."""

import inspect
import logging

from src.core.finite_builder_runtime import replay_finite_builder, snapshot_replay_artifact
from src.core.finite_builder_types import (
    FormalGenerability, OnticGenesis, PulseStep, ScopedObjectFormation,
    SeedRef, TargetIndependence,
)
from src.core.finite_construction import (
    compose_finite_builder_expressions, construction_source_binding,
    finite_builder_program,
    finite_construction_judgment, finite_recurrence_seed,
    validate_finite_construction_judgment,
)
from src.core.positive_ontology import ontology_stage
from src.core.positive_ontology_doctrine import p0_observer_doctrine
from src.core.proof_core_types import Pulse, Silence

logger = logging.getLogger(__name__)


def _fixture():
    logger.debug("_fixture p1b entry")
    doctrine = p0_observer_doctrine()
    seed = finite_recurrence_seed("silence-seed", Silence())
    program = finite_builder_program(
        "two-pulse", "stage-two", ("crest",),
        PulseStep(PulseStep(SeedRef("silence-seed"))),
    )
    source = construction_source_binding(doctrine, "source-two", program, (seed,))
    logger.debug("_fixture p1b exit")
    return doctrine, source


def test_two_pulse_target_is_formally_generable_but_nothing_more():
    logger.debug("test_two_pulse_generable entry")
    doctrine, source = _fixture()
    target = ontology_stage("stage-two", Pulse(Pulse(Silence())), doctrine, 1)
    row = finite_construction_judgment(doctrine, source, target)
    validated = validate_finite_construction_judgment(
        doctrine, source, target, row
    )
    assert row.formal_generability is FormalGenerability.GENERABLE
    assert row.obstruction == ""
    assert row.replay is not None and row.replay.pulse_depth == 2
    assert row.replay.builder_nodes == 3
    assert row.replay.stage is not target
    assert row.replay.stage.representative is not target.representative
    assert row.ontic_genesis is OnticGenesis.NOT_ESTABLISHED
    assert row.target_independence is TargetIndependence.NOT_ESTABLISHED
    assert row.scoped_object is ScopedObjectFormation.OPEN
    assert validated.formal_generability is FormalGenerability.GENERABLE
    assert validated is not row and validated.replay.stage is not row.replay.stage
    logger.debug("test_two_pulse_generable exit")


def test_valid_replay_mismatch_is_refuted_as_target_mismatch():
    logger.debug("test_target_mismatch entry")
    doctrine, source = _fixture()
    target = ontology_stage(
        "stage-two", Pulse(Pulse(Pulse(Silence()))), doctrine, 1
    )
    row = finite_construction_judgment(doctrine, source, target)
    assert row.formal_generability is FormalGenerability.TARGET_MISMATCH
    assert row.obstruction == "replayed-stage-does-not-match-target"
    assert row.replay is not None and row.replay.pulse_depth == 2
    assert row.ontic_genesis is OnticGenesis.NOT_ESTABLISHED
    assert row.target_independence is TargetIndependence.NOT_ESTABLISHED
    assert row.scoped_object is ScopedObjectFormation.OPEN
    logger.debug("test_target_mismatch exit")


def test_replay_is_deterministic_in_commitment_but_fresh_in_identity():
    logger.debug("test_replay_deterministic_fresh entry")
    doctrine, source = _fixture()
    first = replay_finite_builder(doctrine, source)
    second = replay_finite_builder(doctrine, source)
    assert first.stage_commitment == second.stage_commitment
    assert first.recurrence_commitment == second.recurrence_commitment
    assert first.trace_digest == second.trace_digest
    assert first.stage is not second.stage
    assert first.stage.representative is not second.stage.representative
    logger.debug("test_replay_deterministic_fresh exit")


def test_seed_and_pulse_steps_have_exact_finite_depth_semantics():
    logger.debug("test_seed_pulse_semantics entry")
    doctrine = p0_observer_doctrine()
    seed = finite_recurrence_seed("one-pulse-seed", Pulse(Silence()))
    base = finite_builder_program(
        "base", "base-stage", (), SeedRef("one-pulse-seed")
    )
    step = finite_builder_program(
        "step", "step-stage", (), PulseStep(SeedRef("one-pulse-seed"))
    )
    base_source = construction_source_binding(doctrine, "base-source", base, (seed,))
    step_source = construction_source_binding(doctrine, "step-source", step, (seed,))
    assert replay_finite_builder(doctrine, base_source).pulse_depth == 1
    assert replay_finite_builder(doctrine, step_source).pulse_depth == 2
    logger.debug("test_seed_pulse_semantics exit")


def test_closed_builder_composition_is_associative_and_replayable():
    logger.debug("test_builder_composition entry")
    doctrine = p0_observer_doctrine()
    seed = finite_recurrence_seed("composition-seed", Silence())
    outer = PulseStep(SeedRef("outer-port"))
    middle = PulseStep(PulseStep(SeedRef("middle-port")))
    inner = PulseStep(SeedRef("composition-seed"))
    left = compose_finite_builder_expressions(
        outer, compose_finite_builder_expressions(middle, inner)
    )
    right = compose_finite_builder_expressions(
        compose_finite_builder_expressions(outer, middle), inner
    )
    left_program = finite_builder_program("assoc", "assoc-stage", (), left)
    right_program = finite_builder_program("assoc", "assoc-stage", (), right)
    assert left_program.canonical == right_program.canonical
    assert left_program.program_digest == right_program.program_digest
    assert compose_finite_builder_expressions(SeedRef("unit-port"), inner) == inner
    assert compose_finite_builder_expressions(
        inner, SeedRef("composition-seed")
    ) == inner
    source = construction_source_binding(
        doctrine, "assoc-source", left_program, (seed,)
    )
    assert replay_finite_builder(doctrine, source).pulse_depth == 4
    logger.debug("test_builder_composition exit")


def test_exact_replay_snapshot_returns_fresh_revalidated_evidence():
    logger.debug("test_replay_snapshot entry")
    doctrine, source = _fixture()
    replay = replay_finite_builder(doctrine, source)
    captured = snapshot_replay_artifact(doctrine, source, replay)
    assert captured.stage_commitment == replay.stage_commitment
    assert captured.trace_digest == replay.trace_digest
    assert captured.stage is not replay.stage
    assert captured.stage.representative is not replay.stage.representative
    logger.debug("test_replay_snapshot exit")


def test_target_free_replay_signature_and_hard_boundary_enums_are_closed():
    logger.debug("test_target_free_signature entry")
    assert tuple(inspect.signature(replay_finite_builder).parameters) == (
        "doctrine", "source",
    )
    assert tuple(OnticGenesis) == (OnticGenesis.NOT_ESTABLISHED,)
    assert tuple(TargetIndependence) == (TargetIndependence.NOT_ESTABLISHED,)
    assert tuple(ScopedObjectFormation) == (ScopedObjectFormation.OPEN,)
    assert tuple(FormalGenerability) == (
        FormalGenerability.GENERABLE, FormalGenerability.TARGET_MISMATCH,
    )
    logger.debug("test_target_free_signature exit")


def test_ex_post_exact_builder_still_does_not_establish_independence_or_genesis():
    logger.debug("test_ex_post_nonpromotion entry")
    doctrine = p0_observer_doctrine()
    target = ontology_stage("ex-post", Pulse(Silence()), doctrine, 0)
    seed = finite_recurrence_seed("copied-target-seed", target.representative)
    program = finite_builder_program(
        "selected-after-target", "ex-post", (), SeedRef("copied-target-seed")
    )
    source = construction_source_binding(doctrine, "ex-post-source", program, (seed,))
    row = finite_construction_judgment(doctrine, source, target)
    assert row.formal_generability is FormalGenerability.GENERABLE
    assert row.target_independence is TargetIndependence.NOT_ESTABLISHED
    assert row.ontic_genesis is OnticGenesis.NOT_ESTABLISHED
    assert row.scoped_object is ScopedObjectFormation.OPEN
    assert source.scope == "immutability-membership-not-chronology-or-target-independence"
    logger.debug("test_ex_post_nonpromotion exit")
