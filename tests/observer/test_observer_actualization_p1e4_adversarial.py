"""Hostile graph, provenance, result, and resource pressure for P1-E4."""

from dataclasses import replace
import logging

import pytest

import src.core.observer_actualization_result_validation as result_validation
import src.core.observer_actualization_validation as source_validation
from src.core.observer_actualization import (
    AccessKind, ActualizationResourceBound, ActualizationResourceLimit,
    ActualizationStatus, EventKind, HistoricalActualizationJudgment,
    ObserverActualizationValidationError, access_edge,
    actualization_resource_policy, historical_actualization_judgment,
    historical_assumption, historical_observer_source, history_event,
    validate_actualization_result,
)
from src.core.observer_actualization_types import HistoricalObserverSource

from observer_actualization_fixture import build_source, d, fixture_inputs

logger = logging.getLogger(__name__)


class SourceSubclass(HistoricalObserverSource):
    pass


class ResultSubclass(HistoricalActualizationJudgment):
    pass


class EvilStr(str):
    def __eq__(self, other):
        logger.debug("EvilStr equality called")
        raise AssertionError("hostile equality reached")


def test_nonmonotone_parent_edge_and_source_digest_mutation_reject():
    logger.debug("test graph/source mutation entry")
    source = build_source()
    bad_events = tuple(
        replace(item, logical_time=0) if item.event_id == "birth" else item
        for item in source.events
    )
    with pytest.raises(ObserverActualizationValidationError, match="nonmonotone"):
        build_source(events=bad_events)
    with pytest.raises(ObserverActualizationValidationError, match="digest-drift"):
        historical_actualization_judgment(replace(source, source_digest="0" * 64))
    with pytest.raises(ObserverActualizationValidationError, match="version-drift"):
        historical_actualization_judgment(replace(source, version="p1-e4-source-v0"))
    subclass = SourceSubclass(*source.__dict__.values())
    with pytest.raises(ObserverActualizationValidationError, match="must-be-exact"):
        historical_actualization_judgment(subclass)
    logger.debug("test graph/source mutation exit")


def test_deleted_exact_raw_binding_field_rejects_as_typed_validation_error():
    logger.debug("test deleted raw binding entry")
    values = fixture_inputs()
    witness = values["e1_witness"]
    object.__delattr__(witness, "witness_digest")
    with pytest.raises(
        ObserverActualizationValidationError,
        match="raw-binding-fields-missing",
    ):
        historical_observer_source(**values)  # type: ignore[arg-type]
    logger.debug("test deleted raw binding exit")


def test_resource_preflight_rejects_event_count_before_event_or_raw_input_walk(monkeypatch):
    logger.debug("test resource preflight entry")
    values = fixture_inputs()
    policy = actualization_resource_policy(max_events=5)
    calls: list[object] = []
    def forbidden(value):
        logger.debug("forbidden event walk called")
        calls.append(value)
        raise AssertionError("deep event validation before count preflight")
    monkeypatch.setattr(source_validation, "snapshot_event", forbidden)
    values["policy"] = policy
    values["events"] = (object(),) * 6
    result = historical_observer_source(**values)  # type: ignore[arg-type]
    assert type(result) is ActualizationResourceLimit
    assert result.failed_bound is ActualizationResourceBound.EVENTS
    assert (result.required_value, result.allowed_value) == (6, 5)
    assert calls == []
    assert not hasattr(result, "history_digest") and not hasattr(result, "events")
    logger.debug("test resource preflight exit")


def test_circular_assumption_closure_is_rejected():
    logger.debug("test circular closure entry")
    base = fixture_inputs()
    events = base["events"]
    assert type(events) is tuple
    circular = history_event(
        "prior-judgment", EventKind.ACTUALIZATION_JUDGMENT, (), 0,
        d("prior-judgment"), "foreign-lineage",
    )
    shifted = tuple(replace(item, logical_time=item.logical_time + 1) for item in events)
    shifted = tuple(
        replace(item, parent_ids=("prior-judgment",))
        if item.event_id == "construction" else item for item in shifted
    )
    assumptions = (
        historical_assumption("a-circular", "prior-judgment", ()),
    )
    source = build_source(
        events=(circular,) + shifted, assumptions=assumptions,
        assumption_roots=("a-circular",),
    )
    with pytest.raises(ObserverActualizationValidationError, match="circular"):
        historical_actualization_judgment(source)
    logger.debug("test circular closure exit")


def test_missing_reordered_or_duplicate_counterfactual_class_rejects():
    logger.debug("test counterfactual catalog entry")
    source = build_source()
    variants = (
        source.counterfactuals[:-1],
        tuple(reversed(source.counterfactuals)),
        source.counterfactuals[:2] + (source.counterfactuals[1],),
    )
    for cases in variants:
        with pytest.raises(ObserverActualizationValidationError, match="counterfactual"):
            build_source(counterfactuals=cases)
    logger.debug("test counterfactual catalog exit")


def test_failed_prefix_and_foreign_copy_pressure_refute_independence():
    logger.debug("test failed pressure entry")
    source = build_source()
    prefix = replace(
        source.counterfactuals[0],
        alternate_target_digest=next(
            item.payload_digest for item in source.events if item.event_id == "target"
        ),
    )
    copy = replace(
        source.counterfactuals[2], copied_lineage_id=source.lineage_id,
        copied_parent_ids=next(
            item.parent_ids for item in source.events if item.event_id == "birth"
        ),
    )
    for cases in (
        (prefix,) + source.counterfactuals[1:],
        source.counterfactuals[:2] + (copy,),
    ):
        result = historical_actualization_judgment(build_source(counterfactuals=cases))
        assert result.target_independence is ActualizationStatus.REFUTED
    logger.debug("test failed pressure exit")


def test_unknown_access_endpoint_rejects_before_semantic_replay():
    logger.debug("test unknown access entry")
    source = build_source(access_edges=(
        access_edge("target", "unknown-event", AccessKind.TARGET_READ),
    ))
    with pytest.raises(ObserverActualizationValidationError, match="unknown-event"):
        historical_actualization_judgment(source)
    logger.debug("test unknown access exit")


def test_result_subclass_digest_and_huge_nested_tuple_reject_fail_closed(monkeypatch):
    logger.debug("test result hostile entry")
    source = build_source()
    result = historical_actualization_judgment(source)
    subclass = ResultSubclass(*result.__dict__.values())
    with pytest.raises(ObserverActualizationValidationError, match="must-be-exact"):
        validate_actualization_result(source, subclass)
    with pytest.raises(ObserverActualizationValidationError, match="outer-drift"):
        validate_actualization_result(
            source, replace(result, actualization_judgment_digest="0" * 64),
        )
    with pytest.raises(ObserverActualizationValidationError, match="envelope"):
        validate_actualization_result(
            source, replace(result, source_digest=EvilStr(result.source_digest)),
        )
    calls: list[object] = []
    def forbidden(*args):
        logger.debug("forbidden nested result walk called")
        calls.append(args)
        raise AssertionError("nested walk before outer length gate")
    monkeypatch.setattr(result_validation, "_counterfactual", forbidden)
    huge = replace(result, counterfactual_evidence=result.counterfactual_evidence * 10_000)
    with pytest.raises(ObserverActualizationValidationError, match="envelope"):
        validate_actualization_result(source, huge)
    assert calls == []
    logger.debug("test result hostile exit")


def test_assumption_cycle_and_same_token_birth_are_not_silently_accepted():
    logger.debug("test assumption cycle entry")
    assumptions = (
        historical_assumption("a", "construction", ("b",)),
        historical_assumption("b", "oep", ("a",)),
    )
    source = build_source(assumptions=assumptions, assumption_roots=("a",))
    with pytest.raises(ObserverActualizationValidationError, match="cyclic"):
        historical_actualization_judgment(source)
    incomplete = build_source(
        assumptions=(historical_assumption("only-construction", "construction", ()),),
        assumption_roots=("only-construction",),
    )
    result = historical_actualization_judgment(incomplete)
    assert result.birth_event is ActualizationStatus.OPEN
    logger.debug("test assumption cycle exit")
