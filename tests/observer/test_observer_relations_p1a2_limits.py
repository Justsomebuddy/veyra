"""Aggregate projection-limit pressure for P1-A2."""

import pytest

import src.core.observer_relation_replay as replay
import src.core.observer_relation_triangles as triangles
from src.core.observer_morphism import (
    observer_source_binding, p1a_observer_morphism_doctrine,
)
from src.core.observer_morphism_types import ProjectionStep
from src.core.observer_relations import (
    ComparisonMode, ObserverRelationValidationError, morphism_replay_spec,
    observer_relation_judgment, observer_relation_scope,
    relation_evaluation_source,
)
from src.core.proof_core_types import Pulse, Silence


def test_total_projection_step_limit_rejects_64_plus_65_before_semantics(monkeypatch):
    doctrine = p1a_observer_morphism_doctrine()
    binding = observer_source_binding(
        doctrine, "projection-limit-source",
        tuple(item.observer_id for item in doctrine.observers),
    )
    source = relation_evaluation_source(
        doctrine, binding, (("d0", Silence()), ("d1", Pulse(Silence()))),
    )
    keys = tuple((item.stage_id, item.commitment) for item in source.stages)
    scope = observer_relation_scope(
        doctrine, binding, source, "fine-total", "coarse-crest", keys,
        ComparisonMode.WITH_P1A_REPLAY,
    )
    forward = morphism_replay_spec(
        "forward-64", "fine-total", "coarse-crest",
        (ProjectionStep.LEFT,) * 64,
    )
    reverse = morphism_replay_spec(
        "reverse-65", "coarse-crest", "fine-total",
        (ProjectionStep.LEFT,) * 65,
    )
    calls = []

    def forbidden(*args):
        calls.append(args)
        raise AssertionError("semantic work occurred before total projection gate")

    monkeypatch.setattr(replay, "observe", forbidden)
    monkeypatch.setattr(triangles, "observer_morphism_judgment", forbidden)
    with pytest.raises(
        ObserverRelationValidationError, match="relation-total-projection-step-limit",
    ):
        observer_relation_judgment(
            doctrine, binding, source, scope, forward, reverse,
        )
    assert calls == []
