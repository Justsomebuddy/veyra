"""Frozen-contract pressure for C3 hostile boundaries and complete byte charge."""

from dataclasses import replace

import pytest

from src.core.observer_morphism import observer_morphism_judgment
from src.core.observer_morphism_types import ProjectionStep
from src.core.observer_relation_request import observer_relation_scope, translation_proposal
from src.core.observer_relation_runtime import observer_relation_judgment
from src.core.observer_relation_types import ComparisonMode
from src.core.translated_confluence import (
    C3TransportMode, TranslatedConfluenceResourceLimit,
    TranslatedConfluenceValidationError,
    TranslatedResourceBound, TranslatedResourceSource,
    translated_confluence_judgment, translated_echo_transport_spec,
    validate_translated_confluence_result,
)
from src.core.translated_confluence_preflight import snapshot_translated_request

from translated_confluence_fixture import translated_fixture


def _forbidden(calls):
    def fail(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("semantic call crossed a pre-semantic rejection")
    return fail


def test_complete_canonical_charge_grows_for_unbridged_doctrine_and_stage_entries():
    baseline = translated_fixture()
    padded = translated_fixture(padding_observers=1, padding_stages=1)
    first = snapshot_translated_request(*baseline[:9])
    second = snapshot_translated_request(*padded[:9])
    assert second.required_bytes > first.required_bytes
    assert len(padded[0].observers) > len(baseline[0].observers)
    assert len(padded[1].stages) > len(baseline[1].stages)


def test_complete_encoding_over_two_mib_is_hard_rejected_before_semantics(monkeypatch):
    fixture = translated_fixture(padding_observers=10, padding_stages=60)
    calls = []
    forbidden = _forbidden(calls)
    monkeypatch.setattr("src.core.translated_confluence_runtime.observer_relation_judgment", forbidden)
    monkeypatch.setattr("src.core.translated_confluence_runtime.observer_morphism_judgment", forbidden)
    monkeypatch.setattr("src.core.translated_confluence_runtime._check_persistence", forbidden)
    monkeypatch.setattr("src.core.translated_confluence_cell.observe", forbidden)
    with pytest.raises(TranslatedConfluenceValidationError, match="hard-cap"):
        translated_confluence_judgment(*fixture[:9])
    assert calls == []


def test_nested_a2_check_refusal_is_reachable_exact_and_presemantic(monkeypatch):
    fixture = translated_fixture()
    from src.core.observer_relations import relation_resource_policy
    spec = translated_echo_transport_spec(
        fixture[0], fixture[1], fixture[2], fixture[3], fixture[4], fixture[5],
        fixture[6], "nested-small", fixture[7].direction,
        fixture[7].diagram_fine_observer_id, fixture[7].diagram_coarse_observer_id,
        fixture[7].morphism, fixture[7].relation_scope,
        relation_resource_policy(max_cost=1, max_encoded_bytes=1_000_000),
        fixture[7].required_class, fixture[7].required_loss,
    )
    calls = []
    forbidden = _forbidden(calls)
    monkeypatch.setattr("src.core.translated_confluence_runtime.observer_relation_judgment", forbidden)
    monkeypatch.setattr("src.core.translated_confluence_runtime.observer_morphism_judgment", forbidden)
    result = translated_confluence_judgment(*fixture[:7], spec, fixture[8])
    assert type(result) is TranslatedConfluenceResourceLimit
    assert result.failed_bound is TranslatedResourceBound.CHECKS
    assert result.limit_source is TranslatedResourceSource.NESTED_A2
    assert result.failed_required > result.failed_allowed == 1
    assert calls == []
    monkeypatch.undo()
    fresh = validate_translated_confluence_result(
        *fixture[:7], spec, fixture[8], result,
    )
    assert type(fresh) is TranslatedConfluenceResourceLimit
    assert fresh is not result and fresh.refusal_digest == result.refusal_digest


def test_bridge_and_spec_protocol_version_mode_scope_are_digest_bound():
    fixture = translated_fixture()
    for forged in (
        replace(fixture[6], version="p1-c3-bridge-v2"),
        replace(fixture[6], scope="broader"),
    ):
        with pytest.raises(TranslatedConfluenceValidationError):
            translated_confluence_judgment(*fixture[:6], forged, fixture[7], fixture[8])
    for forged in (
        replace(fixture[7], version="p1-c3-spec-v2"),
        replace(fixture[7], scope="broader"),
        replace(fixture[7], mode=C3TransportMode.DIRECT_ECHO),
    ):
        with pytest.raises(TranslatedConfluenceValidationError):
            translated_confluence_judgment(*fixture[:7], forged, fixture[8])


def test_prior_artifacts_and_proposal_cannot_be_reused_as_raw_c3_evidence():
    fixture = translated_fixture()
    prior_morphism = observer_morphism_judgment(
        fixture[3], fixture[4], fixture[7].morphism.morphism_id,
        fixture[7].morphism.fine_observer_id, fixture[7].morphism.coarse_observer_id,
        fixture[7].morphism.projection,
    )
    prior_a2 = observer_relation_judgment(
        fixture[3], fixture[4], fixture[5], fixture[7].relation_scope,
        fixture[7].morphism,
    )
    proposal = translation_proposal(
        fixture[3], fixture[4], "proposal", fixture[7].p1a_fine_observer_id,
        fixture[7].p1a_coarse_observer_id, (ProjectionStep.LEFT,),
    )
    common = (
        fixture[0], fixture[1], fixture[2], fixture[3], fixture[4], fixture[5],
        fixture[6], "prior-rejected", fixture[7].direction,
        fixture[7].diagram_fine_observer_id, fixture[7].diagram_coarse_observer_id,
    )
    for morphism, scope in (
        (prior_morphism, fixture[7].relation_scope),
        (proposal, fixture[7].relation_scope),
        (fixture[7].morphism, prior_a2),
    ):
        with pytest.raises(TranslatedConfluenceValidationError):
            translated_echo_transport_spec(
                *common, morphism, scope, fixture[7].relation_policy,
                fixture[7].required_class, fixture[7].required_loss,
            )


def test_deleting_blocked_stage_cannot_relabel_partial_a2_as_complete():
    fixture = translated_fixture(variant="blocked")
    source = fixture[5]
    keys = tuple((row.stage_id, row.commitment) for row in source.stages[1:])
    partial = observer_relation_scope(
        fixture[3], fixture[4], source, fixture[7].p1a_fine_observer_id,
        fixture[7].p1a_coarse_observer_id, keys, ComparisonMode.WITH_P1A_REPLAY,
    )
    with pytest.raises(TranslatedConfluenceValidationError):
        translated_echo_transport_spec(
            fixture[0], fixture[1], fixture[2], fixture[3], fixture[4], source,
            fixture[6], "deleted-block", fixture[7].direction,
            fixture[7].diagram_fine_observer_id,
            fixture[7].diagram_coarse_observer_id, fixture[7].morphism,
            partial, fixture[7].relation_policy, fixture[7].required_class,
            fixture[7].required_loss,
        )


def test_unexpected_post_preflight_fault_propagates(monkeypatch):
    fixture = translated_fixture()

    def fault(*args, **kwargs):
        raise RuntimeError("unexpected-c3-fault")

    monkeypatch.setattr("src.core.translated_confluence_runtime.observer_relation_judgment", fault)
    with pytest.raises(RuntimeError, match="unexpected-c3-fault"):
        translated_confluence_judgment(*fixture[:9])
