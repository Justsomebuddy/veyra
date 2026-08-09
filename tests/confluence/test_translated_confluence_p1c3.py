"""Positive and boundary pressure for P1-C3."""

from src.core.confluence import swap_fork_join_plan
from src.core.confluence_types import ConfluenceStatus
from src.core.observer_relation_types import LawStatus, LossStatus, RelationClass
from src.core.translated_confluence import (
    TRANSLATED_CONFLUENCE_NONCLAIMS, TranslatedConfluenceJudgment,
    TranslationDirection, c3_confluence_judgment, translated_confluence_judgment,
    translated_echo_transport_spec, validate_translated_confluence_result,
)

from translated_confluence_fixture import translated_fixture


def judge(fixture):
    return translated_confluence_judgment(*fixture[:9])


def test_left_fine_to_right_coarse_replays_every_occurrence_and_a2_gate():
    fixture = translated_fixture()
    result = judge(fixture)
    assert type(result) is TranslatedConfluenceJudgment
    assert result.status is ConfluenceStatus.ESTABLISHED
    assert result.transport_cell is not None
    assert len(result.transport_cell.response_rows) == len(fixture[2].alignment) == 3
    assert tuple(row.point_index for row in result.transport_cell.response_rows) == (0, 1, 2)
    assert {row.outcome for row in result.transport_cell.response_rows} == {"translated-echo"}
    assert result.preservation is LawStatus.ESTABLISHED
    assert result.domain_equality is LawStatus.ESTABLISHED
    assert result.relation_class is RelationClass.STRICT_REFINEMENT_ON_SCOPE
    assert result.information_loss is LossStatus.LOSSY_ON_SCOPE
    assert result.direction is TranslationDirection.LEFT_FINE_TO_RIGHT_COARSE
    assert result.nonclaims == TRANSLATED_CONFLUENCE_NONCLAIMS


def test_fresh_revalidation_returns_distinct_exact_artifact():
    fixture = translated_fixture()
    result = judge(fixture)
    validated = validate_translated_confluence_result(*fixture[:8], fixture[8], result)
    assert validated == result and validated is not result
    assert validated.transport_cell is not result.transport_cell
    assert validated.transport_cell.response_rows is not result.transport_cell.response_rows


def test_explicit_reverse_direction_requires_new_spec_and_cell():
    fixture = translated_fixture()
    p0, diagram, plan, p1a, binding, source, bridge, spec, policy, placeholder = fixture
    swapped = swap_fork_join_plan(p0, diagram, plan, placeholder, "c3-swapped")
    reverse = translated_echo_transport_spec(
        p0, diagram, swapped, p1a, binding, source, bridge, "c3-reverse",
        TranslationDirection.RIGHT_FINE_TO_LEFT_COARSE,
        spec.diagram_fine_observer_id, spec.diagram_coarse_observer_id,
        spec.morphism, spec.relation_scope, spec.relation_policy,
        spec.required_class, spec.required_loss,
    )
    result = translated_confluence_judgment(
        p0, diagram, swapped, p1a, binding, source, bridge, reverse, policy,
    )
    assert type(result) is TranslatedConfluenceJudgment
    assert result.status is ConfluenceStatus.ESTABLISHED
    assert result.spec_digest != judge(fixture).spec_digest
    assert result.transport_cell.trace_digest != judge(fixture).transport_cell.trace_digest


def test_direct_c1_lane_is_unchanged_and_contains_no_translation_payload():
    fixture = translated_fixture(left_depth=1, right_depth=1)
    p0, diagram, plan, _, _, _, _, _, _, placeholder = fixture
    direct = c3_confluence_judgment(p0, diagram, plan, placeholder)
    assert direct.status is ConfluenceStatus.ESTABLISHED
    assert not hasattr(direct.transport_cell, "bridge_digest")
    assert not hasattr(direct.transport_cell, "a2_result_digest")


def test_direct_dispatch_rejects_any_translated_field():
    fixture = translated_fixture(left_depth=1, right_depth=1)
    with __import__("pytest").raises(Exception):
        c3_confluence_judgment(
            fixture[0], fixture[1], fixture[2], fixture[9], bridge=fixture[6],
        )


def test_distinct_programs_can_be_equivalent_on_scope_under_exact_translation():
    result = judge(translated_fixture(variant="equivalent"))
    assert type(result) is TranslatedConfluenceJudgment
    assert result.status is ConfluenceStatus.ESTABLISHED
    assert result.relation_class is RelationClass.EQUIVALENT_ON_SCOPE
    assert result.transport_cell is not None
    assert {row.outcome for row in result.transport_cell.response_rows} == {"translated-echo"}


def test_ready_cross_history_triangle_mismatch_is_refuted_not_open():
    result = judge(translated_fixture(left_depth=0, right_depth=2))
    assert type(result) is TranslatedConfluenceJudgment
    assert result.status is ConfluenceStatus.REFUTED
    assert result.transport_cell is not None
    assert any(row.outcome == "translated-mismatch" for row in result.transport_cell.response_rows)


def test_output_mutation_cannot_change_fresh_replay():
    fixture = translated_fixture()
    first = judge(fixture)
    assert first.transport_cell is not None
    object.__setattr__(first.transport_cell.response_rows[0], "outcome", "forged")
    second = judge(fixture)
    assert second.transport_cell.response_rows[0].outcome == "translated-echo"
    assert second.judgment_digest != "forged"
