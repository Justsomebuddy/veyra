"""Positive exploit regressions for the E4 independent-review findings."""

from dataclasses import replace
import logging

import pytest

import src.core.observer_actualization_result_validation as result_validation
import src.core.observer_actualization_runtime as runtime
import src.core.observer_actualization_validation as source_validation
from src.core.observer_actualization import (
    AccessKind, ActualizationResourceBound, ActualizationResourceLimit,
    ActualizationStatus, CounterfactualEvidence, CounterfactualOutcome, EventKind,
    EvidenceAvailability, HistoricalActualizationJudgment,
    ObserverActualizationValidationError, access_edge,
    actualization_resource_policy, historical_actualization_judgment,
    historical_assumption, historical_observer_source, history_event,
    validate_actualization_result,
)
from src.core.observer_genesis_types import (
    GenesisOperation, GenesisResourceBound, GenesisResourceLimit,
)

from observer_actualization_fixture import build_source, d, fixture_inputs

logger = logging.getLogger(__name__)


class ResultSubclass(HistoricalActualizationJudgment):
    pass


class EvilStr(str):
    def __eq__(self, other):
        logger.debug("review EvilStr equality called")
        raise AssertionError("hostile equality reached")


class EvidenceSubclass(CounterfactualEvidence):
    pass


def _forbid_semantics(monkeypatch) -> list[str]:
    logger.debug("install semantic replay trap entry")
    calls: list[str] = []

    def forbidden(*args):
        logger.debug("semantic replay trap called")
        calls.append("semantic")
        raise AssertionError("semantic replay reached")

    monkeypatch.setattr(runtime, "finite_construction_judgment", forbidden)
    monkeypatch.setattr(runtime, "observer_genesis_judgment", forbidden)
    logger.debug("install semantic replay trap exit")
    return calls


def _forbid_result_replay(monkeypatch) -> list[str]:
    logger.debug("install result replay trap entry")
    calls: list[str] = []

    def forbidden(*args):
        logger.debug("result replay trap called")
        calls.append("replay")
        raise AssertionError("fresh result replay reached")

    monkeypatch.setattr(
        result_validation, "historical_actualization_judgment", forbidden,
    )
    logger.debug("install result replay trap exit")
    return calls


@pytest.mark.parametrize("consumer", ("birth", "construction", "oep"))
def test_target_read_into_birth_or_core_dependency_refutes_before_replay(
    monkeypatch, consumer,
):
    logger.debug("test target seal protected consumer entry consumer=%s", consumer)
    source = build_source(access_edges=(
        access_edge("target", consumer, AccessKind.TARGET_READ),
    ))
    calls = _forbid_semantics(monkeypatch)
    result = historical_actualization_judgment(source)
    assert calls == []
    assert result.target_independence is ActualizationStatus.REFUTED
    logger.debug("test target seal protected consumer exit")


def test_future_target_assumption_source_refutes_before_semantic_replay(monkeypatch):
    logger.debug("test future target assumption entry")
    assumptions = (
        historical_assumption("a-construction", "construction", ()),
        historical_assumption("a-oep", "oep", ("a-construction",)),
        historical_assumption("a-target", "target", ("a-oep",)),
    )
    source = build_source(assumptions=assumptions, assumption_roots=("a-target",))
    calls = _forbid_semantics(monkeypatch)
    result = historical_actualization_judgment(source)
    assert calls == []
    assert result.target_independence is ActualizationStatus.REFUTED
    assert result.birth_event is ActualizationStatus.OPEN
    logger.debug("test future target assumption exit")


@pytest.mark.parametrize("event_id", ("intervention", "response"))
def test_foreign_lineage_efficacy_event_cannot_establish_same_token(event_id):
    logger.debug("test foreign efficacy lineage entry event=%s", event_id)
    source = build_source()
    events = tuple(
        replace(item, lineage_id="foreign-lineage")
        if item.event_id == event_id else item for item in source.events
    )
    result = historical_actualization_judgment(build_source(events=events))
    assert result.post_birth_efficacy is ActualizationStatus.REFUTED
    logger.debug("test foreign efficacy lineage exit")


def test_foreign_birth_ancestor_cannot_be_spliced_into_efficacy_trace():
    logger.debug("test foreign birth ancestry entry")
    source = build_source()
    shifted = tuple(
        replace(item, logical_time=item.logical_time + 1)
        if item.event_id in {"target", "intervention", "response"} else item
        for item in source.events
    )
    copied = history_event(
        "foreign-copy", EventKind.COPIED_BIRTH, ("birth",), 3,
        d("foreign-copy"), "foreign-lineage",
    )
    events = tuple(
        replace(item, parent_ids=item.parent_ids + ("foreign-copy",))
        if item.event_id == "response" else item for item in shifted
    ) + (copied,)
    result = historical_actualization_judgment(build_source(events=events))
    assert result.post_birth_efficacy is ActualizationStatus.REFUTED
    logger.debug("test foreign birth ancestry exit")


def test_result_envelope_blocks_object_subclass_and_oversize_before_replay(monkeypatch):
    logger.debug("test result envelope pre-replay entry")
    source = build_source()
    result = historical_actualization_judgment(source)
    calls: list[str] = []

    def forbidden(*args):
        logger.debug("fresh result replay trap called")
        calls.append("replay")
        raise AssertionError("fresh result replay reached")

    monkeypatch.setattr(
        result_validation, "historical_actualization_judgment", forbidden,
    )
    bad_values = (
        object(),
        ResultSubclass(*result.__dict__.values()),
        replace(result, past_event_ids=("x",) * (source.policy.max_events + 1)),
        replace(result, counterfactual_evidence=object()),
        replace(result, source_digest=EvilStr(result.source_digest)),
    )
    for bad in bad_values:
        with pytest.raises(ObserverActualizationValidationError):
            validate_actualization_result(source, bad)  # type: ignore[arg-type]
    assert calls == []
    logger.debug("test result envelope pre-replay exit")


@pytest.mark.parametrize("bad", (object(), EvilStr("construction")))
def test_past_element_type_bomb_rejects_before_semantic_replay(monkeypatch, bad):
    logger.debug("test past element type gate entry")
    source = build_source()
    result = historical_actualization_judgment(source)
    calls = _forbid_result_replay(monkeypatch)
    with pytest.raises(ObserverActualizationValidationError, match="element-type"):
        validate_actualization_result(
            source, replace(result, past_event_ids=(bad, "oep")),
        )
    assert calls == []
    logger.debug("test past element type gate exit")


def test_future_element_object_rejects_before_semantic_replay(monkeypatch):
    logger.debug("test future element type gate entry")
    source = build_source()
    result = historical_actualization_judgment(source)
    calls = _forbid_result_replay(monkeypatch)
    with pytest.raises(ObserverActualizationValidationError, match="element-type"):
        validate_actualization_result(
            source, replace(result, future_event_ids=(object(),)),
        )
    assert calls == []
    logger.debug("test future element type gate exit")


def test_counterfactual_row_subclass_rejects_before_semantic_replay(monkeypatch):
    logger.debug("test counterfactual row type gate entry")
    source = build_source()
    result = historical_actualization_judgment(source)
    row = EvidenceSubclass(*result.counterfactual_evidence[0].__dict__.values())
    calls = _forbid_result_replay(monkeypatch)
    with pytest.raises(ObserverActualizationValidationError, match="element-type"):
        validate_actualization_result(
            source, replace(
                result, counterfactual_evidence=(
                    row, *result.counterfactual_evidence[1:],
                ),
            ),
        )
    assert calls == []
    logger.debug("test counterfactual row type gate exit")


def test_e1_resource_limit_keeps_wrong_response_efficacy_open(monkeypatch):
    logger.debug("test efficacy resource refusal precedence entry")
    source = build_source()
    events = tuple(
        replace(item, payload_digest=d("wrong-response"))
        if item.event_id == "response" else item for item in source.events
    )
    limited = build_source(events=events)
    resource = GenesisResourceLimit(
        GenesisOperation.JUDGMENT, GenesisResourceBound.TRANSITION_ROWS,
        24, 23, *(d(f"genesis-resource-{index}") for index in range(8)),
    )

    def resource_refusal(*args):
        logger.debug("raw e1 resource refusal returned")
        return resource

    monkeypatch.setattr(runtime, "observer_genesis_judgment", resource_refusal)
    result = historical_actualization_judgment(limited)
    assert result.post_birth_efficacy is ActualizationStatus.OPEN
    logger.debug("test efficacy resource refusal precedence exit")


def test_available_genuine_wrong_response_remains_refuted():
    logger.debug("test genuine wrong response remains refuted entry")
    source = build_source()
    events = tuple(
        replace(item, payload_digest=d("wrong-response-genuine"))
        if item.event_id == "response" else item for item in source.events
    )
    result = historical_actualization_judgment(build_source(events=events))
    assert result.post_birth_efficacy is ActualizationStatus.REFUTED
    logger.debug("test genuine wrong response remains refuted exit")


def test_missing_or_unavailable_copy_parent_keeps_counterfactual_open():
    logger.debug("test copy parent availability entry")
    source = build_source()
    unavailable_parent = history_event(
        "copy-parent", EventKind.OTHER, (), 0, d("copy-parent"),
        "foreign-lineage", EvidenceAvailability.UNAVAILABLE,
    )
    cases = source.counterfactuals[:2] + (
        replace(source.counterfactuals[2], copied_parent_ids=("copy-parent",)),
    )
    result = historical_actualization_judgment(
        build_source(events=source.events + (unavailable_parent,), counterfactuals=cases),
    )
    assert result.counterfactual_evidence[2].outcome is CounterfactualOutcome.OPEN
    assert result.target_independence is ActualizationStatus.OPEN
    logger.debug("test copy parent availability exit")


def test_concrete_copy_contradiction_precedes_missing_parent_open_state():
    logger.debug("test copy refutation precedence entry")
    source = build_source()
    cases = source.counterfactuals[:2] + (
        replace(
            source.counterfactuals[2], copied_lineage_id=source.lineage_id,
            copied_parent_ids=("missing-parent",),
        ),
    )
    result = historical_actualization_judgment(build_source(counterfactuals=cases))
    assert result.counterfactual_evidence[2].outcome is CounterfactualOutcome.FAILED
    assert result.target_independence is ActualizationStatus.REFUTED
    logger.debug("test copy refutation precedence exit")


def test_aggregate_parent_bound_refuses_before_any_event_snapshot(monkeypatch):
    logger.debug("test raw aggregate parent preflight entry")
    values = fixture_inputs()
    values["policy"] = actualization_resource_policy(max_parent_edges=6)
    calls: list[object] = []

    def forbidden(value):
        logger.debug("event snapshot trap called")
        calls.append(value)
        raise AssertionError("event snapshot reached")

    monkeypatch.setattr(source_validation, "snapshot_event", forbidden)
    result = historical_observer_source(**values)  # type: ignore[arg-type]
    assert type(result) is ActualizationResourceLimit
    assert result.failed_bound is ActualizationResourceBound.PARENT_EDGES
    assert (result.required_value, result.allowed_value) == (7, 6)
    assert calls == []
    logger.debug("test raw aggregate parent preflight exit")
