"""Focused positive and separating models for P1-A2.1/A2.2."""

from src.core.observer_core_kernel import tail_observer
from src.core.observer_core_types import Input, Pair
from src.core.observer_morphism import (
    observer_source_binding, p1a_observer_morphism_doctrine,
)
from src.core.observer_morphism_types import ProjectionStep
from src.core.observer_relation_laws import relation_classification
from src.core.observer_relations import (
    ComparisonMode, CoverageStatus, InvertibilityStatus, LawStatus, LossStatus,
    MorphismEvidenceStatus, ObserverRelationJudgment, PairOutcome,
    OBSERVER_RELATION_NONCLAIMS,
    ProposalStatus, RelationClass, morphism_replay_spec,
    TranslationInputKind,
    observer_relation_judgment, observer_relation_scope,
    observer_relations_scope_boundary,
    relation_evaluation_source, relation_resource_policy, translation_proposal,
    validate_observer_relation_result,
)
from src.core.positive_ontology import internal_observer
from src.core.positive_ontology_doctrine import observer_doctrine
from src.core.proof_core_types import Pulse, Silence


def recurrence(depth):
    value = Silence()
    for _ in range(depth):
        value = Pulse(value)
    return value


def setup(fine="fine-total", coarse="coarse-crest", mode=ComparisonMode.EXTENSIONAL_ONLY):
    doctrine = p1a_observer_morphism_doctrine()
    binding = observer_source_binding(
        doctrine, "p1a2-source", tuple(item.observer_id for item in doctrine.observers),
    )
    source = relation_evaluation_source(
        doctrine, binding,
        (("depth-0", recurrence(0)), ("depth-1", recurrence(1)), ("depth-2", recurrence(2))),
    )
    keys = tuple((item.stage_id, item.commitment) for item in source.stages)
    scope = observer_relation_scope(doctrine, binding, source, fine, coarse, keys, mode)
    return doctrine, binding, source, scope


def test_strict_refinement_replays_all_ordered_pairs_and_p1a_triangles():
    doctrine, binding, source, scope = setup(mode=ComparisonMode.WITH_P1A_REPLAY)
    forward = morphism_replay_spec(
        "fine-total-to-crest", "fine-total", "coarse-crest", (ProjectionStep.LEFT,),
    )
    result = observer_relation_judgment(doctrine, binding, source, scope, forward)
    assert isinstance(result, ObserverRelationJudgment)
    assert len(result.observations) == 3
    assert len(result.pairs) == 9
    assert tuple((row.left, row.right) for row in result.pairs) == scope.ordered_pairs
    assert tuple(row.pair_index for row in result.pairs) == tuple(range(9))
    assert result.preservation is LawStatus.ESTABLISHED
    assert result.reflection is LawStatus.REFUTED
    assert result.domain_equality is LawStatus.ESTABLISHED
    assert result.classification is RelationClass.STRICT_REFINEMENT_ON_SCOPE
    assert result.reflection_witness is not None
    witness = result.pairs[result.reflection_witness.pair_index]
    assert witness.coarse_outcome is PairOutcome.ECHO
    assert witness.fine_outcome is PairOutcome.MISMATCH
    assert result.forward.morphism_status is MorphismEvidenceStatus.P1A_ESTABLISHED
    assert result.forward.input_kind is TranslationInputKind.P1A_REPLAY
    assert result.reverse.input_kind is TranslationInputKind.ABSENT
    assert result.forward.proposal_status is ProposalStatus.COMMUTES_ON_SCOPE
    assert len(result.forward.triangles) == 3
    assert result.information_loss is LossStatus.LOSSY_ON_SCOPE
    assert result.structural_invertibility is InvertibilityStatus.NOT_ESTABLISHED
    assert result.coverage is CoverageStatus.COMPLETE
    assert result.nonclaims == OBSERVER_RELATION_NONCLAIMS
    assert observer_relations_scope_boundary() == result.nonclaims
    assert "off-scope-equivalence" in result.nonclaims
    assert "physical-instantiation" in result.nonclaims


def test_reverse_orientation_is_strict_coarsening_not_incomparability():
    doctrine, binding, source, scope = setup(
        fine="coarse-crest", coarse="fine-total",
    )
    result = observer_relation_judgment(doctrine, binding, source, scope)
    assert isinstance(result, ObserverRelationJudgment)
    assert result.preservation is LawStatus.REFUTED
    assert result.reflection is LawStatus.ESTABLISHED
    assert result.classification is RelationClass.STRICT_COARSENING_ON_SCOPE
    assert result.preservation_witness is not None
    assert result.information_loss is LossStatus.NOT_ESTABLISHED


def test_distinct_observers_can_be_extensionally_equivalent_without_invertibility():
    doctrine, binding, source, scope = setup(
        fine="fine-total", coarse="fine-nested",
    )
    result = observer_relation_judgment(doctrine, binding, source, scope)
    assert isinstance(result, ObserverRelationJudgment)
    assert scope.fine_observer_id != scope.coarse_observer_id
    assert result.preservation is LawStatus.ESTABLISHED
    assert result.reflection is LawStatus.ESTABLISHED
    assert result.domain_equality is LawStatus.ESTABLISHED
    assert result.classification is RelationClass.EQUIVALENT_ON_SCOPE
    assert result.forward.morphism_status is MorphismEvidenceStatus.ABSENT
    assert result.forward.input_kind is TranslationInputKind.ABSENT
    assert result.information_loss is LossStatus.NOT_ESTABLISHED
    assert result.structural_invertibility is InvertibilityStatus.NOT_ESTABLISHED


def test_blocked_stage_is_not_deleted_and_keeps_positive_laws_open():
    doctrine, binding, source, scope = setup(
        fine="fine-domain-hole", coarse="coarse-crest",
    )
    result = observer_relation_judgment(doctrine, binding, source, scope)
    assert isinstance(result, ObserverRelationJudgment)
    assert result.coverage is CoverageStatus.PARTIAL_BLOCKED
    assert result.domain_equality is LawStatus.REFUTED
    assert result.domain_witness is not None
    assert result.domain_witness.stage == scope.stages[0]
    assert result.preservation is LawStatus.OPEN
    assert result.reflection is LawStatus.REFUTED
    assert result.reflection_witness is not None
    assert result.classification is RelationClass.OPEN
    assert len(result.pairs) == 9


def test_typed_nonfactorizing_proposal_conflict_does_not_change_relation_class():
    doctrine = observer_doctrine(
        "P1A2-conflict", "closed-r11-proposal-separation",
        ("source-fixed", "finite-relation-only"),
        (
            internal_observer("fine-pair", Pair(Input(), Input())),
            internal_observer("coarse-tail", tail_observer()),
        ),
        version="p1a2-conflict-v1",
    )
    binding = observer_source_binding(doctrine, "conflict-source", ("fine-pair", "coarse-tail"))
    source = relation_evaluation_source(
        doctrine, binding, (("depth-1", recurrence(1)), ("depth-2", recurrence(2))),
    )
    keys = tuple((item.stage_id, item.commitment) for item in source.stages)
    scope = observer_relation_scope(
        doctrine, binding, source, "fine-pair", "coarse-tail", keys,
        ComparisonMode.WITH_PROPOSALS,
    )
    proposal = translation_proposal(
        doctrine, binding, "wrong-left", "fine-pair", "coarse-tail",
        (ProjectionStep.LEFT,),
    )
    result = observer_relation_judgment(doctrine, binding, source, scope, proposal)
    assert isinstance(result, ObserverRelationJudgment)
    assert result.classification is RelationClass.EQUIVALENT_ON_SCOPE
    assert result.forward.morphism_status is MorphismEvidenceStatus.ABSENT
    assert result.forward.input_kind is TranslationInputKind.PROPOSAL
    assert result.forward.proposal_status is ProposalStatus.CONFLICT_ON_SCOPE
    assert result.forward.conflict is not None
    assert result.information_loss is LossStatus.NOT_ESTABLISHED


def test_result_revalidation_returns_fresh_artifact_from_raw_inputs():
    doctrine, binding, source, scope = setup()
    policy = relation_resource_policy()
    result = observer_relation_judgment(doctrine, binding, source, scope, policy=policy)
    validated = validate_observer_relation_result(
        doctrine, binding, source, scope, None, None, policy, result,
    )
    assert validated == result
    assert validated is not result


def test_scope_can_select_an_order_preserving_source_subset_only():
    doctrine, binding, source, _ = setup()
    keys = tuple((item.stage_id, item.commitment) for item in source.stages[1:])
    scope = observer_relation_scope(
        doctrine, binding, source, "fine-total", "coarse-crest", keys,
        ComparisonMode.EXTENSIONAL_ONLY,
    )
    result = observer_relation_judgment(doctrine, binding, source, scope)
    assert isinstance(result, ObserverRelationJudgment)
    assert tuple(item.stage for item in result.observations) == keys
    assert len(result.pairs) == 4
    assert tuple((item.left, item.right) for item in result.pairs) == scope.ordered_pairs


def test_classifier_has_exact_incomparable_branch_without_claiming_runtime_model():
    assert relation_classification(
        LawStatus.REFUTED, LawStatus.REFUTED, LawStatus.ESTABLISHED,
    ) is RelationClass.INCOMPARABLE_ON_SCOPE
