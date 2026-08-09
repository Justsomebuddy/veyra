"""Hostile, resource, TOCTOU, and provenance pressure for provisional P1-B."""

from dataclasses import replace
import logging

import pytest

import src.core.finite_construction as construction
from src.core.finite_builder_codec import _canonical_builder_bytes
from src.core.finite_builder_digest import _program_digest, _source_digest
from src.core.finite_builder_runtime import (
    FiniteBuilderReplayError, replay_finite_builder, snapshot_replay_artifact,
)
from src.core.finite_builder_types import (
    ConstructionSourceBinding, FiniteBuilderProgram, PulseStep, SeedRef,
)
from src.core.finite_builder_validation import FiniteBuilderValidationError
from src.core.finite_construction import (
    compose_finite_builder_expressions, construction_source_binding,
    finite_builder_program,
    finite_construction_judgment, finite_recurrence_seed,
    validate_finite_construction_judgment,
)
from src.core.positive_ontology import ontology_stage, presentation_commitment
from src.core.positive_ontology_doctrine import p0_observer_doctrine
from src.core.proof_core_types import Pulse, Silence

logger = logging.getLogger(__name__)


class NameTrapMeta(type):
    """Forbid hostile type-name inspection before exact gates."""

    def __getattribute__(cls, name):
        if name == "__name__":
            raise AssertionError("hostile class name read")
        return super().__getattribute__(name)


class NameTrap(metaclass=NameTrapMeta):
    """Untrusted input for exact-gate tests."""


def _fixture():
    logger.debug("_fixture p1b adversarial entry")
    doctrine = p0_observer_doctrine()
    seed = finite_recurrence_seed("seed", Silence())
    program = finite_builder_program(
        "builder", "target", ("crest",), PulseStep(SeedRef("seed"))
    )
    source = construction_source_binding(doctrine, "source", program, (seed,))
    logger.debug("_fixture p1b adversarial exit")
    return doctrine, seed, program, source


def test_callables_duck_types_subclasses_and_commitments_are_not_builders():
    logger.debug("test_exact_builder_gates entry")
    doctrine, _, program, source = _fixture()
    with pytest.raises(FiniteBuilderValidationError):
        finite_builder_program("callable", "x", (), lambda: Silence())  # type: ignore[arg-type]
    with pytest.raises(FiniteBuilderValidationError):
        finite_builder_program("hostile", "x", (), NameTrap())  # type: ignore[arg-type]
    class ProgramSubclass(FiniteBuilderProgram):
        pass
    forged = ProgramSubclass(**program.__dict__)
    with pytest.raises(FiniteBuilderValidationError, match="exact"):
        construction_source_binding(doctrine, "subclass", forged, source.seeds)
    target = ontology_stage("target", Pulse(Silence()), doctrine, 1)
    commitment = presentation_commitment("hash-only", target)
    with pytest.raises(FiniteBuilderValidationError):
        construction_source_binding(doctrine, "hash-only", commitment, source.seeds)  # type: ignore[arg-type]
    logger.debug("test_exact_builder_gates exit")


def test_foreign_seed_forged_digest_and_alien_target_prefix_fail_closed():
    logger.debug("test_foreign_forged_alien entry")
    doctrine, _, program, source = _fixture()
    foreign = finite_recurrence_seed("foreign", Silence())
    with pytest.raises(FiniteBuilderValidationError, match="seed-membership"):
        construction_source_binding(doctrine, "foreign", program, (foreign,))
    with pytest.raises(FiniteBuilderValidationError, match="binding-drift"):
        replay_finite_builder(
            doctrine, replace(source, membership_digest="0" * 64)
        )
    target = ontology_stage("target", Pulse(Silence()), doctrine, 1)
    with pytest.raises(FiniteBuilderValidationError, match="target-doctrine"):
        finite_construction_judgment(
            doctrine, source, replace(target, doctrine_id="alien-doctrine")
        )
    logger.debug("test_foreign_forged_alien exit")


def test_builder_and_recurrence_cycles_and_resource_limits_are_rejected():
    logger.debug("test_cycle_resource entry")
    cycle = PulseStep(SeedRef("seed"))
    object.__setattr__(cycle, "child", cycle)
    with pytest.raises(FiniteBuilderValidationError, match="expression"):
        finite_builder_program("cycle", "x", (), cycle)
    with pytest.raises(FiniteBuilderValidationError, match="expression"):
        compose_finite_builder_expressions(cycle, SeedRef("seed"))
    expression = SeedRef("seed")
    for _ in range(128):
        expression = PulseStep(expression)
    with pytest.raises(FiniteBuilderValidationError, match="expression"):
        finite_builder_program("oversize", "x", (), expression)
    recurrence = Pulse(Silence())
    object.__setattr__(recurrence, "tail", recurrence)
    with pytest.raises(FiniteBuilderValidationError, match="seed"):
        finite_recurrence_seed("cycle-seed", recurrence)
    deep = Silence()
    for _ in range(129):
        deep = Pulse(deep)
    with pytest.raises(FiniteBuilderValidationError, match="seed"):
        finite_recurrence_seed("deep-seed", deep)
    logger.debug("test_cycle_resource exit")


def test_seed_depth_plus_builder_pulses_is_bounded_before_output_build():
    logger.debug("test_total_depth_bound entry")
    doctrine = p0_observer_doctrine()
    recurrence = Silence()
    for _ in range(128):
        recurrence = Pulse(recurrence)
    seed = finite_recurrence_seed("max-seed", recurrence)
    program = finite_builder_program(
        "overflow", "overflow-stage", (), PulseStep(SeedRef("max-seed"))
    )
    source = construction_source_binding(doctrine, "overflow-source", program, (seed,))
    with pytest.raises(FiniteBuilderValidationError, match="total-depth"):
        replay_finite_builder(doctrine, source)
    logger.debug("test_total_depth_bound exit")


def test_source_snapshots_survive_ast_seed_and_replay_artifact_mutation():
    logger.debug("test_toctou_alias entry")
    doctrine = p0_observer_doctrine()
    recurrence = Pulse(Silence())
    seed = finite_recurrence_seed("mutable-seed", recurrence)
    expression = PulseStep(SeedRef("mutable-seed"))
    program = finite_builder_program("stable", "stable-stage", (), expression)
    object.__setattr__(recurrence, "tail", Pulse(Pulse(Silence())))
    object.__setattr__(expression, "child", SeedRef("foreign"))
    source = construction_source_binding(doctrine, "stable-source", program, (seed,))
    first = replay_finite_builder(doctrine, source)
    object.__setattr__(first.stage.representative, "tail", Silence())
    with pytest.raises(FiniteBuilderValidationError, match="artifact-semantic-drift"):
        snapshot_replay_artifact(doctrine, source, first)
    second = replay_finite_builder(doctrine, source)
    assert first.pulse_depth == second.pulse_depth == 2
    assert second.stage_commitment == replay_finite_builder(doctrine, source).stage_commitment
    logger.debug("test_toctou_alias exit")


def test_mutated_nested_judgment_is_rejected_by_downstream_revalidation():
    logger.debug("test_judgment_revalidation entry")
    doctrine, _, _, source = _fixture()
    target = ontology_stage("target", Pulse(Silence()), doctrine, 1)
    row = finite_construction_judgment(doctrine, source, target)
    object.__setattr__(row.replay.stage.representative, "tail", Pulse(Silence()))
    with pytest.raises(FiniteBuilderValidationError, match="artifact-semantic-drift"):
        validate_finite_construction_judgment(doctrine, source, target, row)
    fresh = finite_construction_judgment(doctrine, source, target)
    assert fresh.formal_generability.value == "generable"
    logger.debug("test_judgment_revalidation exit")


def test_target_is_touched_only_after_target_free_replay(monkeypatch):
    logger.debug("test_target_read_order entry")
    doctrine, _, _, source = _fixture()
    target = ontology_stage("target", Pulse(Silence()), doctrine, 1)
    real_replay = construction.replay_finite_builder
    real_target = construction._snapshot_target_stage
    state = {"replayed": False}
    def ordered_replay(*args):
        logger.debug("ordered_replay entry")
        result = real_replay(*args)
        state["replayed"] = True
        logger.debug("ordered_replay exit")
        return result
    def ordered_target(*args):
        logger.debug("ordered_target entry")
        assert state["replayed"]
        result = real_target(*args)
        logger.debug("ordered_target exit")
        return result
    monkeypatch.setattr(construction, "replay_finite_builder", ordered_replay)
    monkeypatch.setattr(construction, "_snapshot_target_stage", ordered_target)
    assert finite_construction_judgment(doctrine, source, target).replay is not None
    logger.debug("test_target_read_order exit")


def test_runtime_failure_propagates_without_reading_target(monkeypatch):
    logger.debug("test_runtime_failure_propagates entry")
    doctrine, _, _, source = _fixture()
    target = ontology_stage("target", Pulse(Silence()), doctrine, 1)
    def failed_replay(*args):
        logger.debug("failed_replay entry")
        raise FiniteBuilderReplayError("named-runtime-failure")
    def forbidden_target(*args):
        logger.error("forbidden_target called")
        raise AssertionError("target read after failed replay")
    monkeypatch.setattr(construction, "replay_finite_builder", failed_replay)
    monkeypatch.setattr(construction, "_snapshot_target_stage", forbidden_target)
    with pytest.raises(FiniteBuilderReplayError, match="named-runtime-failure"):
        finite_construction_judgment(doctrine, source, target)
    logger.debug("test_runtime_failure_propagates exit")


def test_tagged_counted_digests_resist_old_separator_like_identifiers():
    logger.debug("test_separator_collision entry")
    canonical = _canonical_builder_bytes(SeedRef("seed-digest-separator"))
    first = _program_digest(
        "b", "s", ("program-separator",), canonical,
        ("seed-digest-separator",),
    )
    second = _program_digest(
        "b", "s", ("seed-digest-separator",), canonical,
        ("program-separator",),
    )
    assert first != second
    source_a = _source_digest(
        "x", "a" * 64, first, ("seed-digest-separator",), ("b" * 64,)
    )
    source_b = _source_digest(
        "x", "a" * 64, first, ("program-separator",), ("b" * 64,)
    )
    assert source_a != source_b
    logger.debug("test_separator_collision exit")


def test_source_binding_subclass_and_bool_like_payloads_fail_exactly():
    logger.debug("test_source_subclass entry")
    doctrine, _, _, source = _fixture()
    class SourceSubclass(ConstructionSourceBinding):
        pass
    forged = SourceSubclass(**source.__dict__)
    with pytest.raises(FiniteBuilderValidationError, match="exact"):
        replay_finite_builder(doctrine, forged)
    with pytest.raises(FiniteBuilderValidationError):
        finite_builder_program(True, "x", (), SeedRef("seed"))  # type: ignore[arg-type]
    logger.debug("test_source_subclass exit")
