"""Adversarial source, gate, direction, and resource pressure for P1-C3."""

from dataclasses import replace

import pytest

from src.core.confluence import fork_join_plan
from src.core.confluence_types import ConfluenceStatus
from src.core.observer_relation_types import (
    LossStatus, RelationClass, RelationEvaluationSource,
)
from src.core.translated_confluence import (
    TranslatedConfluenceJudgment, TranslatedConfluenceResourceLimit,
    TranslatedConfluenceValidationError, TranslationDirection,
    TranslatedResourceBound, TranslatedResourceSource,
    p0_p1a_response_bridge, translated_confluence_judgment,
    translated_confluence_policy, translated_echo_transport_spec,
)

from translated_confluence_fixture import translated_fixture


def test_same_kind_different_program_and_equal_names_do_not_bridge():
    fixture = translated_fixture()
    p0, diagram, _, p1a, binding, source = fixture[:6]
    alien = replace(p0, fingerprint="0" * 64)
    with pytest.raises(Exception):
        p0_p1a_response_bridge(alien, diagram, p1a, binding, source)
    forged = replace(fixture[6].observer_rows[0], p1a_observer_id="diagram-fine")
    with pytest.raises(TranslatedConfluenceValidationError):
        translated_confluence_judgment(
            *fixture[:6], replace(fixture[6], observer_rows=(forged, *fixture[6].observer_rows[1:])),
            fixture[7], fixture[8],
        )


def test_foreign_stage_recurrence_and_partial_coverage_are_invalid():
    fixture = translated_fixture()
    source = fixture[5]
    foreign_stage = replace(source.stages[0], recurrence=source.stages[2].recurrence)
    foreign = RelationEvaluationSource(
        source.doctrine_fingerprint, (foreign_stage, *source.stages[1:]),
        source.ordered_commitments, source.observer_source_digest,
        source.version, source.source_digest,
    )
    with pytest.raises(Exception):
        p0_p1a_response_bridge(fixture[0], fixture[1], fixture[3], fixture[4], foreign)
    partial = replace(fixture[6], stage_rows=fixture[6].stage_rows[:-1])
    with pytest.raises(TranslatedConfluenceValidationError):
        translated_confluence_judgment(
            *fixture[:6], partial, fixture[7], fixture[8],
        )


def test_direction_cannot_be_reused_after_plan_swap():
    fixture = translated_fixture()
    p0, diagram, plan, p1a, binding, source, bridge, spec, policy, placeholder = fixture
    from src.core.confluence import swap_fork_join_plan
    swapped = swap_fork_join_plan(p0, diagram, plan, placeholder, "hostile-swap")
    with pytest.raises(TranslatedConfluenceValidationError):
        translated_confluence_judgment(
            p0, diagram, swapped, p1a, binding, source, bridge, spec, policy,
        )


def test_wrong_class_and_loss_requirements_yield_open_not_promotion():
    fixture = translated_fixture()
    spec = translated_echo_transport_spec(
        fixture[0], fixture[1], fixture[2], fixture[3], fixture[4], fixture[5], fixture[6],
        "wrong-gates", TranslationDirection.LEFT_FINE_TO_RIGHT_COARSE,
        "diagram-fine", "diagram-coarse", fixture[7].morphism,
        fixture[7].relation_scope, fixture[7].relation_policy,
        RelationClass.EQUIVALENT_ON_SCOPE, LossStatus.LOSSLESS_ON_SCOPE,
    )
    result = translated_confluence_judgment(
        *fixture[:7], spec, fixture[8],
    )
    assert type(result) is TranslatedConfluenceJudgment
    assert result.status is ConfluenceStatus.OPEN
    assert result.transport_cell is None


def test_blocked_a2_triangle_and_information_only_morphism_are_open():
    blocked_fixture = translated_fixture(variant="blocked")
    blocked = translated_confluence_judgment(*blocked_fixture[:9])
    assert type(blocked) is TranslatedConfluenceJudgment
    assert blocked.status is ConfluenceStatus.OPEN
    assert blocked.transport_cell is None
    information_fixture = translated_fixture(variant="information-only")
    information = translated_confluence_judgment(*information_fixture[:9])
    assert type(information) is TranslatedConfluenceJudgment
    assert information.status is ConfluenceStatus.OPEN
    assert information.transport_cell is None
    assert information.first_obstruction.outcome == "p1a-morphism-not-strong"


def test_outer_refusal_is_payload_free_and_bytes_precede_checks():
    fixture = translated_fixture()
    policy = translated_confluence_policy(max_checks=1, max_bytes=1)
    result = translated_confluence_judgment(*fixture[:8], policy)
    assert type(result) is TranslatedConfluenceResourceLimit
    assert not hasattr(result, "transport_cell")
    assert not hasattr(result, "response_rows")
    assert result.required_bytes > result.allowed_bytes
    assert result.required_checks > result.allowed_checks
    assert result.failed_bound is TranslatedResourceBound.BYTES
    assert result.limit_source is TranslatedResourceSource.OUTER
    assert result.failed_required == result.required_bytes
    assert result.failed_allowed == result.allowed_bytes


def test_outer_refusal_happens_before_observe_translate_or_a2_replay(monkeypatch):
    fixture = translated_fixture()
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("semantic work ran before outer refusal")

    monkeypatch.setattr("src.core.translated_confluence_cell.observe", forbidden)
    monkeypatch.setattr("src.core.translated_confluence_cell.translate_response", forbidden)
    monkeypatch.setattr("src.core.translated_confluence_runtime.observer_relation_judgment", forbidden)
    monkeypatch.setattr("src.core.translated_confluence_runtime.observer_morphism_judgment", forbidden)
    monkeypatch.setattr("src.core.translated_confluence_runtime._check_persistence", forbidden)
    result = translated_confluence_judgment(
        *fixture[:8], translated_confluence_policy(max_checks=1, max_bytes=1),
    )
    assert type(result) is TranslatedConfluenceResourceLimit
    assert calls == []


def test_plan_transport_digest_is_bound_to_exact_ordered_pair():
    fixture = translated_fixture()
    p0, diagram, plan, *_, placeholder = fixture
    reversed_placeholder = replace(placeholder, observer_ids=tuple(reversed(placeholder.observer_ids)))
    with pytest.raises(Exception):
        fork_join_plan(
            p0, diagram, "bad-order", "lb", "rb", "ljp", "rjp",
            plan.alignment, reversed_placeholder,
        )
