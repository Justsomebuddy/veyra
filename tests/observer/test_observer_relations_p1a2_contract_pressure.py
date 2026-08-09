"""Mandatory contract-separation pressure for P1-A2.1/A2.2."""

from dataclasses import replace

import pytest

from src.core.observer_morphism import (
    observer_source_binding, p1a_observer_morphism_doctrine,
)
from src.core.observer_morphism_types import ProjectionStep
from src.core.observer_relations import (
    ComparisonMode, LawStatus, ObserverRelationJudgment,
    ObserverRelationValidationError, PairOutcome, RelationClass,
    observer_relation_judgment, observer_relation_scope,
    relation_evaluation_source, relation_resource_policy, translation_proposal,
    validate_observer_relation_result,
)
from src.core.positive_ontology_doctrine import observer_doctrine
from src.core.proof_core_types import Pulse, Silence


def recurrence(depth):
    value = Silence()
    for _ in range(depth):
        value = Pulse(value)
    return value


def setup(
    fine="fine-total", coarse="fine-domain-hole",
    mode=ComparisonMode.EXTENSIONAL_ONLY,
):
    doctrine = p1a_observer_morphism_doctrine()
    binding = observer_source_binding(
        doctrine, "contract-pressure-source",
        tuple(item.observer_id for item in doctrine.observers),
    )
    source = relation_evaluation_source(
        doctrine, binding,
        (("d0", recurrence(0)), ("d1", recurrence(1)), ("d2", recurrence(2))),
    )
    keys = tuple((item.stage_id, item.commitment) for item in source.stages)
    scope = observer_relation_scope(
        doctrine, binding, source, fine, coarse, keys, mode,
    )
    return doctrine, binding, source, scope


def test_ready_intersection_relation_agreement_does_not_promote_unequal_domains():
    doctrine, binding, source, scope = setup()
    result = observer_relation_judgment(doctrine, binding, source, scope)
    assert isinstance(result, ObserverRelationJudgment)
    ready_pairs = tuple(
        row for row in result.pairs
        if row.left != scope.stages[0] and row.right != scope.stages[0]
    )
    assert ready_pairs
    assert all(row.fine_outcome is row.coarse_outcome for row in ready_pairs)
    assert result.domain_equality is LawStatus.REFUTED
    assert result.domain_witness is not None
    assert result.classification is RelationClass.OPEN
    assert result.classification is not RelationClass.EQUIVALENT_ON_SCOPE


def test_foreign_doctrine_binding_stage_source_and_proposal_transplants_reject():
    doctrine, binding, source, scope = setup(
        fine="fine-total", coarse="coarse-crest",
        mode=ComparisonMode.WITH_PROPOSALS,
    )
    foreign_doctrine = observer_doctrine(
        doctrine.doctrine_id, doctrine.admission_rule, doctrine.metadata,
        doctrine.observers, version="p1a2-foreign-doctrine-v1",
    )
    foreign_binding = observer_source_binding(
        foreign_doctrine, "foreign-source",
        tuple(item.observer_id for item in foreign_doctrine.observers),
    )
    foreign_source = relation_evaluation_source(
        foreign_doctrine, foreign_binding,
        (("d0", recurrence(0)), ("d1", recurrence(1)), ("d2", recurrence(2))),
    )
    foreign_proposal = translation_proposal(
        foreign_doctrine, foreign_binding, "foreign-proposal",
        "fine-total", "coarse-crest", (ProjectionStep.LEFT,),
    )
    with pytest.raises(ObserverRelationValidationError):
        observer_relation_judgment(
            doctrine, foreign_binding, source, scope,
        )
    with pytest.raises(ObserverRelationValidationError):
        observer_relation_judgment(
            foreign_doctrine, binding, source, scope,
        )
    with pytest.raises(ObserverRelationValidationError):
        observer_relation_judgment(
            doctrine, binding, foreign_source, scope,
        )
    with pytest.raises(ObserverRelationValidationError, match="proposal-source-transplant"):
        observer_relation_judgment(
            doctrine, binding, source, scope, foreign_proposal,
        )


def test_equal_ids_reject_and_forged_response_rows_never_become_echo():
    doctrine, binding, source, scope = setup(
        fine="fine-total", coarse="coarse-crest",
    )
    keys = tuple((item.stage_id, item.commitment) for item in source.stages)
    with pytest.raises(ObserverRelationValidationError, match="observer-pair"):
        observer_relation_scope(
            doctrine, binding, source, "fine-total", "fine-total", keys,
            ComparisonMode.EXTENSIONAL_ONLY,
        )
    policy = relation_resource_policy()
    result = observer_relation_judgment(
        doctrine, binding, source, scope, policy=policy,
    )
    assert isinstance(result, ObserverRelationJudgment)
    row = result.pairs[0]
    variants = (
        replace(row, fine_left_payload="0" * 64),
        replace(row, fine_outcome=PairOutcome.MISMATCH),
        replace(row, row_digest="0" * 64),
    )
    for forged_row in variants:
        forged = replace(result, pairs=(forged_row,) + result.pairs[1:])
        with pytest.raises(ObserverRelationValidationError, match="pair-drift"):
            validate_observer_relation_result(
                doctrine, binding, source, scope, None, None, policy, forged,
            )


def test_duplicate_stage_ids_commitments_and_scope_keys_reject():
    doctrine = p1a_observer_morphism_doctrine()
    binding = observer_source_binding(
        doctrine, "duplicate-pressure-source",
        tuple(item.observer_id for item in doctrine.observers),
    )
    with pytest.raises(ObserverRelationValidationError, match="duplicate-relation-stage-id"):
        relation_evaluation_source(
            doctrine, binding, (("same", recurrence(0)), ("same", recurrence(1))),
        )
    source = relation_evaluation_source(
        doctrine, binding, (("d0", recurrence(0)), ("d1", recurrence(1))),
    )
    forged_commitments = replace(
        source,
        ordered_commitments=(source.ordered_commitments[0],) * 2,
    )
    keys = tuple((item.stage_id, item.commitment) for item in source.stages)
    with pytest.raises(ObserverRelationValidationError, match="commitment-drift"):
        observer_relation_scope(
            doctrine, binding, forged_commitments, "fine-total", "coarse-crest",
            keys, ComparisonMode.EXTENSIONAL_ONLY,
        )
    with pytest.raises(ObserverRelationValidationError, match="stage-order-or-mode-drift"):
        observer_relation_scope(
            doctrine, binding, source, "fine-total", "coarse-crest",
            (keys[0], keys[0]), ComparisonMode.EXTENSIONAL_ONLY,
        )
