"""Positive and boundary tests for finite P1-E4 historical actualization."""

from dataclasses import replace
import logging

import src.core.observer_actualization_runtime as runtime
from src.core.observer_actualization import (
    ActualizationStatus, ConsciousnessStatus, CounterfactualOutcome,
    EvidenceAvailability, EventKind, HistoricalActualization,
    PhysicalInstantiation, historical_actualization_judgment,
    history_event, validate_actualization_result,
)
from src.core.positive_ontology import ontology_stage
from src.core.proof_core_types import Pulse, Silence

from observer_actualization_fixture import build_source, d, fixture_inputs, leak_edge

logger = logging.getLogger(__name__)


def test_exact_history_establishes_only_history_relative_actualization():
    logger.debug("test exact history entry")
    source = build_source()
    result = historical_actualization_judgment(source)
    assert result.past_event_ids == ("construction", "oep")
    assert result.future_event_ids == ("target", "intervention", "response")
    assert tuple(item.outcome for item in result.counterfactual_evidence) == (
        CounterfactualOutcome.PASSED,
        CounterfactualOutcome.PASSED,
        CounterfactualOutcome.PASSED,
    )
    assert (
        result.oep_role, result.prior_construction, result.birth_event,
        result.target_independence, result.post_birth_efficacy,
    ) == (ActualizationStatus.ESTABLISHED,) * 5
    assert result.historical_actualization is HistoricalActualization.ESTABLISHED_RELATIVE_TO_HISTORY
    assert result.physical_instantiation is PhysicalInstantiation.NOT_ESTABLISHED
    assert result.consciousness is ConsciousnessStatus.NOT_CLAIMED
    logger.debug("test exact history exit")


def test_later_target_variation_preserves_birth_and_token_but_changes_history():
    logger.debug("test target variation entry")
    first = build_source()
    events = tuple(
        replace(item, payload_digest=d("target-c"))
        if item.event_id == "target" else item
        for item in first.events
    )
    second = build_source(events=events)
    a = historical_actualization_judgment(first)
    b = historical_actualization_judgment(second)
    assert first.birth_core_digest == second.birth_core_digest
    assert first.historical_token_id == second.historical_token_id
    assert first.history_digest != second.history_digest
    assert a.actualization_judgment_digest != b.actualization_judgment_digest
    logger.debug("test target variation exit")


def test_target_access_leak_refutes_before_p1b_or_e1_semantic_replay(monkeypatch):
    logger.debug("test leak precedence entry")
    source = build_source(access_edges=leak_edge())
    calls: list[str] = []
    def forbidden(*args):
        logger.debug("forbidden semantic replay called")
        calls.append("semantic")
        raise AssertionError("semantic replay after target leak")
    monkeypatch.setattr(runtime, "finite_construction_judgment", forbidden)
    monkeypatch.setattr(runtime, "observer_genesis_judgment", forbidden)
    result = historical_actualization_judgment(source)
    assert calls == []
    assert result.target_independence is ActualizationStatus.REFUTED
    assert result.oep_role is ActualizationStatus.OPEN
    assert result.prior_construction is ActualizationStatus.OPEN
    assert result.historical_actualization is HistoricalActualization.OPEN
    logger.debug("test leak precedence exit")


def test_earlier_same_lineage_copy_refutes_first_birth_only():
    logger.debug("test first birth entry")
    base = fixture_inputs()
    events = base["events"]
    assert type(events) is tuple
    copied = history_event(
        "earlier-copy", EventKind.COPIED_BIRTH, (), 0, d("copy"),
        "observer-lineage",
    )
    shifted = tuple(replace(item, logical_time=item.logical_time + 1) for item in events)
    shifted = tuple(
        replace(item, parent_ids=("earlier-copy",))
        if item.event_id == "construction" else item for item in shifted
    )
    source = build_source(events=(copied,) + shifted)
    result = historical_actualization_judgment(source)
    assert "earlier-copy" in result.past_event_ids
    assert result.birth_event is ActualizationStatus.REFUTED
    assert result.historical_actualization is HistoricalActualization.OPEN
    logger.debug("test first birth exit")


def test_timestamp_without_parent_reachability_does_not_create_causal_past():
    logger.debug("test timestamp not causality entry")
    source = build_source()
    events = tuple(
        replace(item, parent_ids=()) if item.event_id == "oep"
        else replace(item, parent_ids=("oep",)) if item.event_id == "birth"
        else item
        for item in source.events
    )
    result = historical_actualization_judgment(build_source(events=events))
    assert "construction" not in result.past_event_ids
    assert result.birth_event is ActualizationStatus.REFUTED
    assert result.historical_actualization is HistoricalActualization.OPEN
    logger.debug("test timestamp not causality exit")


def test_unavailable_post_birth_evidence_is_open_not_refuted():
    logger.debug("test unavailable efficacy entry")
    source = build_source()
    events = tuple(
        replace(item, availability=EvidenceAvailability.UNAVAILABLE)
        if item.event_id == "response" else item for item in source.events
    )
    result = historical_actualization_judgment(build_source(events=events))
    assert result.post_birth_efficacy is ActualizationStatus.OPEN
    assert result.historical_actualization is HistoricalActualization.OPEN
    logger.debug("test unavailable efficacy exit")


def test_wrong_available_response_refutes_post_birth_efficacy():
    logger.debug("test wrong efficacy entry")
    source = build_source()
    events = tuple(
        replace(item, payload_digest=d("wrong-response"))
        if item.event_id == "response" else item for item in source.events
    )
    result = historical_actualization_judgment(build_source(events=events))
    assert result.post_birth_efficacy is ActualizationStatus.REFUTED
    assert result.historical_actualization is HistoricalActualization.OPEN
    logger.debug("test wrong efficacy exit")


def test_raw_p1b_target_mismatch_refutes_prior_construction_without_nonexistence():
    logger.debug("test p1b mismatch entry")
    values = fixture_inputs()
    p0 = values["p0_doctrine"]
    assert p0 is not None
    target = ontology_stage("e4-stage", Pulse(Pulse(Silence())), p0, 1)  # type: ignore[arg-type]
    source = build_source(construction_target=target)
    result = historical_actualization_judgment(source)
    assert result.prior_construction is ActualizationStatus.REFUTED
    assert result.historical_actualization is HistoricalActualization.OPEN
    assert result.physical_instantiation is PhysicalInstantiation.NOT_ESTABLISHED
    logger.debug("test p1b mismatch exit")


def test_result_validation_replays_raw_inputs_and_returns_fresh_evidence():
    logger.debug("test result validation entry")
    source = build_source()
    result = historical_actualization_judgment(source)
    fresh = validate_actualization_result(source, result)
    assert fresh == result and fresh is not result
    assert fresh.counterfactual_evidence is not result.counterfactual_evidence
    assert fresh.counterfactual_evidence[0] is not result.counterfactual_evidence[0]
    logger.debug("test result validation exit")
