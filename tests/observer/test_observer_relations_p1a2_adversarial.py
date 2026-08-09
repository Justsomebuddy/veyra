"""Hostile exactness, coverage, preflight, and revalidation pressure for P1-A2."""

from dataclasses import replace

import pytest

import src.core.observer_relation_replay as replay
import src.core.observer_relation_triangles as triangles
from src.core.observer_morphism import (
    observer_source_binding, p1a_observer_morphism_doctrine,
)
from src.core.observer_morphism_types import ProjectionStep
from src.core.observer_relations import (
    ComparisonMode, LawStatus, ObserverRelationJudgment,
    ObserverRelationValidationError, RelationResourceLimit,
    morphism_replay_spec, observer_relation_judgment, observer_relation_scope,
    relation_evaluation_source, relation_resource_policy,
    translation_proposal,
    validate_observer_relation_result,
)
from src.core.observer_relation_digest import stage_commitment
from src.core.observer_relation_types import ObserverRelationScope
from src.core.proof_core_types import Pulse, Silence, Stitch


def recurrence(depth):
    value = Silence()
    for _ in range(depth):
        value = Pulse(value)
    return value


def setup(mode=ComparisonMode.EXTENSIONAL_ONLY, policy=None):
    doctrine = p1a_observer_morphism_doctrine()
    binding = observer_source_binding(
        doctrine, "a2-hostile-source",
        tuple(item.observer_id for item in doctrine.observers),
    )
    source = relation_evaluation_source(
        doctrine, binding, (("d0", recurrence(0)), ("d1", recurrence(1)), ("d2", recurrence(2))),
    )
    keys = tuple((item.stage_id, item.commitment) for item in source.stages)
    scope = observer_relation_scope(
        doctrine, binding, source, "fine-total", "coarse-crest", keys, mode,
    )
    return doctrine, binding, source, scope, policy or relation_resource_policy()


class ScopeSubclass(ObserverRelationScope):
    pass


class PulseSubclass(Pulse):
    pass


class BombTuple(tuple):
    calls = 0

    def __len__(self):
        type(self).calls += 1
        raise AssertionError("hostile tuple length executed")


class AssessmentTrap:
    calls = 0

    @property
    def triangles(self):
        type(self).calls += 1
        raise AssertionError("hostile assessment property executed")


def test_source_binds_canonical_recurrence_bytes_and_rejects_semantic_mutation():
    doctrine, binding, source, _, _ = setup()
    left = stage_commitment("p1a2-source-v1", "same", b"VRR1\x00\x01")
    right = stage_commitment("p1a2-source-v1", "same", b"ALT1\x00\x01")
    assert left != right
    invalid = replace(source.stages[1], recurrence=Stitch(Silence(), Silence()))
    forged = replace(source, stages=(source.stages[0], invalid, source.stages[2]))
    with pytest.raises(ObserverRelationValidationError, match="invalid-relation-recurrence"):
        observer_relation_scope(
            doctrine, binding, forged, "fine-total", "coarse-crest",
            tuple((item.stage_id, item.commitment) for item in forged.stages),
            ComparisonMode.EXTENSIONAL_ONLY,
        )
    subclass = replace(source.stages[1], recurrence=PulseSubclass(Silence()))
    with pytest.raises(ObserverRelationValidationError):
        observer_relation_scope(
            doctrine, binding, replace(source, stages=(source.stages[0], subclass, source.stages[2])),
            "fine-total", "coarse-crest",
            tuple((item.stage_id, item.commitment) for item in source.stages),
            ComparisonMode.EXTENSIONAL_ONLY,
        )


def test_missing_reordered_or_forged_pair_coverage_and_scope_subclass_reject():
    doctrine, binding, source, scope, policy = setup()
    variants = (
        replace(scope, ordered_pairs=scope.ordered_pairs[:-1]),
        replace(scope, ordered_pairs=tuple(reversed(scope.ordered_pairs))),
        replace(scope, stages=tuple(reversed(scope.stages))),
    )
    for variant in variants:
        with pytest.raises(ObserverRelationValidationError):
            observer_relation_judgment(doctrine, binding, source, variant, policy=policy)
    subclass = ScopeSubclass(**scope.__dict__)
    with pytest.raises(ObserverRelationValidationError, match="scope-must-be-exact"):
        observer_relation_judgment(doctrine, binding, source, subclass, policy=policy)


def test_policy_and_early_refusal_precede_r11_and_p1a_semantics(monkeypatch):
    doctrine, binding, source, scope, _ = setup()
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("semantic work occurred before preflight")

    monkeypatch.setattr(replay, "observe", forbidden)
    monkeypatch.setattr(triangles, "observer_morphism_judgment", forbidden)
    policy = relation_resource_policy(max_cost=0)
    result = observer_relation_judgment(doctrine, binding, source, scope, policy=policy)
    assert isinstance(result, RelationResourceLimit)
    assert result.policy_digest == policy.policy_digest
    assert result.observer_independent_identity is LawStatus.OPEN
    assert result.universal_refinement is LawStatus.OPEN
    assert calls == []
    with pytest.raises(ObserverRelationValidationError, match="policy-digest-drift"):
        observer_relation_judgment(
            doctrine, binding, source, scope,
            policy=replace(policy, policy_digest="0" * 64),
        )


def test_result_revalidation_rejects_raw_enum_bool_and_outer_container_traps():
    doctrine, binding, source, scope, policy = setup()
    result = observer_relation_judgment(doctrine, binding, source, scope, policy=policy)
    assert isinstance(result, ObserverRelationJudgment)
    with pytest.raises(ObserverRelationValidationError, match="outer-precheck"):
        validate_observer_relation_result(
            doctrine, binding, source, scope, None, None, policy,
            replace(result, preservation="established"),  # type: ignore[arg-type]
        )
    forged_pair = replace(result.pairs[0], pair_index=True)
    with pytest.raises(ObserverRelationValidationError, match="pair-drift"):
        validate_observer_relation_result(
            doctrine, binding, source, scope, None, None, policy,
            replace(result, pairs=(forged_pair,) + result.pairs[1:]),
        )
    BombTuple.calls = 0
    with pytest.raises(ObserverRelationValidationError, match="outer-precheck"):
        validate_observer_relation_result(
            doctrine, binding, source, scope, None, None, policy,
            replace(result, observations=BombTuple(result.observations)),
        )
    assert BombTuple.calls == 0
    AssessmentTrap.calls = 0
    with pytest.raises(ObserverRelationValidationError, match="outer-precheck"):
        validate_observer_relation_result(
            doctrine, binding, source, scope, None, None, policy,
            replace(result, forward=AssessmentTrap()),  # type: ignore[arg-type]
        )
    assert AssessmentTrap.calls == 0
    for forged_nonclaims in (
        tuple(reversed(result.nonclaims)),
        list(result.nonclaims),
        result.nonclaims[:-1] + (1,),
    ):
        with pytest.raises(ObserverRelationValidationError, match="nonclaims-drift"):
            validate_observer_relation_result(
                doctrine, binding, source, scope, None, None, policy,
                replace(result, nonclaims=forged_nonclaims),  # type: ignore[arg-type]
            )


def test_refusal_revalidation_checks_exact_provenance_without_hashing_forged_work():
    doctrine, binding, source, scope, _ = setup()
    policy = relation_resource_policy(max_cost=0)
    result = observer_relation_judgment(doctrine, binding, source, scope, policy=policy)
    assert isinstance(result, RelationResourceLimit)
    for forged in (
        replace(result, required_cost=True),
        replace(result, required_cost=10**100_000),
        replace(result, refusal_digest="0" * 64),
        replace(result, nonclaims=tuple(reversed(result.nonclaims))),
    ):
        with pytest.raises(
            ObserverRelationValidationError,
            match="refusal-(outer-precheck|nonclaims-drift)",
        ):
            validate_observer_relation_result(
                doctrine, binding, source, scope, None, None, policy, forged,
            )


def test_prior_judgment_is_not_raw_translation_and_unexpected_exception_propagates(monkeypatch):
    doctrine, binding, source, scope, policy = setup()
    prior = observer_relation_judgment(doctrine, binding, source, scope, policy=policy)
    with pytest.raises(ObserverRelationValidationError, match="translation-input-must-be-exact"):
        observer_relation_judgment(
            doctrine, binding, source, scope, prior, policy=policy,  # type: ignore[arg-type]
        )

    def explode(*args):
        raise RuntimeError("unexpected-observe")

    monkeypatch.setattr(replay, "observe", explode)
    with pytest.raises(RuntimeError, match="unexpected-observe"):
        observer_relation_judgment(doctrine, binding, source, scope, policy=policy)


def test_mode_discipline_rejects_raw_p1a_spec_in_extensional_or_proposal_mode():
    doctrine, binding, source, scope, policy = setup()
    raw = morphism_replay_spec(
        "raw", "fine-total", "coarse-crest", (ProjectionStep.LEFT,),
    )
    with pytest.raises(ObserverRelationValidationError, match="extensional-mode"):
        observer_relation_judgment(doctrine, binding, source, scope, raw, policy=policy)
    _, _, _, proposal_scope, _ = setup(ComparisonMode.WITH_PROPOSALS)
    with pytest.raises(ObserverRelationValidationError, match="proposal-mode"):
        observer_relation_judgment(
            doctrine, binding, source, proposal_scope, raw, policy=policy,
        )


def test_raw_p1a_wrong_endpoint_kind_rejects_before_morphism_semantics(monkeypatch):
    doctrine, binding, source, scope, policy = setup(
        ComparisonMode.WITH_P1A_REPLAY,
    )
    calls = []

    def forbidden(*args):
        calls.append(args)
        raise AssertionError("P1-A semantics reached for kind-invalid syntax")

    monkeypatch.setattr(triangles, "observer_morphism_judgment", forbidden)
    wrong = morphism_replay_spec("wrong-kind", "fine-total", "coarse-crest", ())
    with pytest.raises(
        ObserverRelationValidationError, match="morphism-replay-endpoint-kind-mismatch",
    ):
        observer_relation_judgment(
            doctrine, binding, source, scope, wrong, policy=policy,
        )
    assert calls == []


def test_assessment_binds_exact_proposal_and_p1a_input_identity():
    doctrine, binding, source, proposal_scope, policy = setup(
        ComparisonMode.WITH_PROPOSALS,
    )
    proposal_one = translation_proposal(
        doctrine, binding, "proposal-one", "fine-total", "coarse-crest",
        (ProjectionStep.LEFT,),
    )
    proposal_two = translation_proposal(
        doctrine, binding, "proposal-two", "fine-total", "coarse-crest",
        (ProjectionStep.LEFT,),
    )
    first = observer_relation_judgment(
        doctrine, binding, source, proposal_scope, proposal_one, policy=policy,
    )
    second = observer_relation_judgment(
        doctrine, binding, source, proposal_scope, proposal_two, policy=policy,
    )
    assert isinstance(first, ObserverRelationJudgment)
    assert isinstance(second, ObserverRelationJudgment)
    assert first.forward.input_commitment != second.forward.input_commitment
    assert first.judgment_digest != second.judgment_digest
    with pytest.raises(ObserverRelationValidationError, match="outer-precheck"):
        validate_observer_relation_result(
            doctrine, binding, source, proposal_scope, proposal_two, None,
            policy, first,
        )

    doctrine, binding, source, replay_scope, policy = setup(
        ComparisonMode.WITH_P1A_REPLAY,
    )
    replay_one = morphism_replay_spec(
        "replay-one", "fine-total", "coarse-crest", (ProjectionStep.LEFT,),
    )
    replay_two = morphism_replay_spec(
        "replay-two", "fine-total", "coarse-crest", (ProjectionStep.LEFT,),
    )
    first = observer_relation_judgment(
        doctrine, binding, source, replay_scope, replay_one, policy=policy,
    )
    second = observer_relation_judgment(
        doctrine, binding, source, replay_scope, replay_two, policy=policy,
    )
    assert isinstance(first, ObserverRelationJudgment)
    assert isinstance(second, ObserverRelationJudgment)
    assert first.forward.input_commitment != second.forward.input_commitment
    with pytest.raises(ObserverRelationValidationError, match="outer-precheck"):
        validate_observer_relation_result(
            doctrine, binding, source, replay_scope, replay_two, None,
            policy, first,
        )
