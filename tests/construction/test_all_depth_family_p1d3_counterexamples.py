"""Exact finite candidate-law countermodels and review hardening for P1-D3."""

from dataclasses import replace

import pytest

from src.core.all_depth_family import (
    SUPPLIED_COMPATIBILITY_LAW_ID, SUPPLIED_CONSTRUCTOR_ID,
    SUPPLIED_COORDINATE_LAW_ID, AllDepthFamilyValidationError,
    all_depth_family_spec, assess_family_law_counterexample,
    finite_family_law_witness, hypothesis_family_ledger,
    periodic_family_formal_source, periodic_family_ledger, relation_edge,
    restriction_row, supplied_family_hypothesis, symbolic_family_term,
    validate_derived_family_judgment, validate_family_law_counterexample_assessment,
)
from src.core.all_depth_family_counterexample_types import (
    FamilyLaw, FamilyNonexistence,
)
from src.core.all_depth_family_runtime import admit_supplied_family, derive_periodic_family
from src.core.all_depth_family_sources import snapshot_family_source
from src.core.all_depth_family_spec import snapshot_family_spec, snapshot_family_term
from src.core.all_depth_family_types import (
    CompletedCarrierStatus, FamilyEvidenceStatus, LawStatus,
)
from src.core.infinity_prefix import prefix_alphabet
from src.core.positive_ontology_doctrine import p0_observer_doctrine
from src.core.productivity import (
    OUTPUT_ENCODING_ID, RESTRICTION_LAW_ID, TOTALITY_BASIS_ID,
    execution_policy, periodic_program, productive_process_source,
)

pytestmark = pytest.mark.requires_lean


class EqualString(str):
    def __eq__(self, other):
        return True

    __hash__ = str.__hash__


class EqualTuple(tuple):
    def __eq__(self, other):
        return True


class EqualBytes(bytes):
    def __eq__(self, other):
        return True


def setup_rows():
    doctrine = p0_observer_doctrine()
    alphabet = prefix_alphabet(("a", "b"))
    spec = all_depth_family_spec(doctrine, alphabet)
    ledger = periodic_family_ledger()
    program = periodic_program(alphabet, ("a", "b"))
    policy = execution_policy(8, 10_000)
    d1 = productive_process_source(
        program, TOTALITY_BASIS_ID, RESTRICTION_LAW_ID, OUTPUT_ENCODING_ID, policy,
    )
    formal = periodic_family_formal_source()
    judgment = derive_periodic_family(doctrine, spec, d1, formal, ledger)
    return doctrine, spec, ledger, d1, formal, judgment


def witnesses():
    return (
        finite_family_law_witness(
            FamilyLaw.RELATION_REFLEXIVE, ("a",), (), (), ("a",),
        ),
        finite_family_law_witness(
            FamilyLaw.RELATION_TRANSITIVE, ("a", "b", "c"),
            (relation_edge("a", "b"), relation_edge("b", "c")), (),
            ("a", "b", "c"),
        ),
        finite_family_law_witness(
            FamilyLaw.RESTRICTION_CONGRUENCE, ("a", "b", "c", "d"),
            (relation_edge("a", "b"),),
            (restriction_row("r", "a", "c"), restriction_row("r", "b", "d")),
            ("r", "a", "b"),
        ),
        finite_family_law_witness(
            FamilyLaw.RESTRICTION_IDENTITY, ("a", "b"),
            (relation_edge("a", "b"),), (restriction_row("id", "a", "b"),),
            ("id", "a"),
        ),
        finite_family_law_witness(
            FamilyLaw.RESTRICTION_COMPOSITION, ("a", "b", "c", "d"),
            (relation_edge("d", "c"),),
            (restriction_row("upper", "a", "b"), restriction_row("lower", "b", "c"),
             restriction_row("direct", "a", "d")),
            ("upper", "lower", "direct", "a"),
        ),
    )


def test_five_closed_countermodels_refute_only_the_affected_candidate_law():
    _, spec, _, _, _, judgment = setup_rows()
    before = judgment
    for witness in witnesses():
        assessment = assess_family_law_counterexample(spec, judgment.source, witness)
        statuses = vars(assessment.law_statuses)
        affected = witness.law.value.replace("-", "_")
        assert assessment.affected_status is LawStatus.REFUTED
        assert statuses[affected] is LawStatus.REFUTED
        assert all(value is LawStatus.OPEN for name, value in statuses.items() if name != affected)
        assert assessment.family_evidence is FamilyEvidenceStatus.OPEN
        assert assessment.family_nonexistence is FamilyNonexistence.NOT_PROVED
        assert assessment.afip_introduction is False
        assert assessment.completed_carrier is CompletedCarrierStatus.NOT_ESTABLISHED
    assert judgment == before
    assert judgment.evidence_status is FamilyEvidenceStatus.ESTABLISHED_RELATIVE_TO_LEDGER


def test_reversed_identity_and_composition_edges_do_not_fake_forward_laws():
    _, spec, _, _, _, judgment = setup_rows()
    identity, composition = witnesses()[3:]
    assert (identity.restriction_rows[0].target, identity.arguments[1]) not in {
        (edge.left, edge.right) for edge in identity.relation_edges
    }
    assert (identity.arguments[1], identity.restriction_rows[0].target) in {
        (edge.left, edge.right) for edge in identity.relation_edges
    }
    for witness in (identity, composition):
        assert assess_family_law_counterexample(spec, judgment.source, witness).affected_status \
            is LawStatus.REFUTED


def test_non_counterexample_and_missing_restriction_rows_are_not_refutations():
    _, spec, _, _, _, judgment = setup_rows()
    reflexive = finite_family_law_witness(
        FamilyLaw.RELATION_REFLEXIVE, ("a",), (relation_edge("a", "a"),), (), ("a",),
    )
    missing = finite_family_law_witness(
        FamilyLaw.RESTRICTION_IDENTITY, ("a",), (), (), ("id", "a"),
    )
    with pytest.raises(AllDepthFamilyValidationError, match="does-not-refute"):
        assess_family_law_counterexample(spec, judgment.source, reflexive)
    with pytest.raises(AllDepthFamilyValidationError, match="missing-restriction"):
        assess_family_law_counterexample(spec, judgment.source, missing)


def test_assessment_transplant_relabel_extra_field_and_nested_status_reject():
    _, spec, _, _, _, judgment = setup_rows()
    witness = witnesses()[0]
    assessment = assess_family_law_counterexample(spec, judgment.source, witness)
    relabeled = replace(assessment, law=assessment.law.value)
    with pytest.raises(AllDepthFamilyValidationError, match="enum-lookalike"):
        validate_family_law_counterexample_assessment(
            spec, judgment.source, witness, relabeled,
        )
    nested = replace(assessment.law_statuses, relation_reflexive="refuted")
    with pytest.raises(AllDepthFamilyValidationError, match="status-lookalike"):
        validate_family_law_counterexample_assessment(
            spec, judgment.source, witness, replace(assessment, law_statuses=nested),
        )
    object.__setattr__(assessment, "injected", True)
    with pytest.raises(AllDepthFamilyValidationError, match="shape-drift"):
        validate_family_law_counterexample_assessment(spec, judgment.source, witness, assessment)
    other_program = periodic_program(spec.alphabet, ("a",))
    other_d1 = productive_process_source(
        other_program, TOTALITY_BASIS_ID, RESTRICTION_LAW_ID, OUTPUT_ENCODING_ID,
        execution_policy(8, 10_000),
    )
    other = derive_periodic_family(
        p0_observer_doctrine(), spec, other_d1, periodic_family_formal_source(),
        periodic_family_ledger(),
    )
    clean = assess_family_law_counterexample(spec, judgment.source, witness)
    with pytest.raises(AllDepthFamilyValidationError, match="semantic-drift"):
        validate_family_law_counterexample_assessment(spec, other.source, witness, clean)


def test_formal_spec_and_periodic_term_equality_traps_reject_before_equality():
    doctrine, spec, ledger, d1, formal, judgment = setup_rows()
    with pytest.raises(AllDepthFamilyValidationError, match="scalar-must-be-exact"):
        derive_periodic_family(
            doctrine, spec, d1, replace(formal, version=EqualString(formal.version)), ledger,
        )
    forged_spec = replace(spec, relation_law_ids=EqualTuple(spec.relation_law_ids))
    with pytest.raises(AllDepthFamilyValidationError, match="family-spec-law-drift"):
        snapshot_family_spec(forged_spec)
    member_trap = replace(
        spec, relation_law_ids=(EqualString(spec.relation_law_ids[0]), *spec.relation_law_ids[1:]),
    )
    with pytest.raises(AllDepthFamilyValidationError, match="family-spec-law-drift"):
        snapshot_family_spec(member_trap)
    formal_subclass = type("FormalSubclass", (type(formal),), {})
    subclass_value = formal_subclass(**vars(formal))
    with pytest.raises(AllDepthFamilyValidationError, match="formal-family-source-must-be-exact"):
        derive_periodic_family(doctrine, spec, d1, subclass_value, ledger)
    forged_term = replace(
        judgment.source.term, symbolic_term=EqualBytes(judgment.source.term.symbolic_term),
    )
    with pytest.raises(AllDepthFamilyValidationError, match="symbolic-bytes"):
        snapshot_family_term(forged_term, spec)


def test_supplied_forbidden_optional_payloads_and_digest_subclass_reject():
    doctrine, spec, _, _, formal, _ = setup_rows()
    ids = ("H", SUPPLIED_COORDINATE_LAW_ID, SUPPLIED_COMPATIBILITY_LAW_ID)
    ledger = hypothesis_family_ledger(ids)
    term = symbolic_family_term(spec, SUPPLIED_CONSTRUCTOR_ID, b"F")
    hypothesis = supplied_family_hypothesis(spec, term, *ids, ledger)
    judgment = admit_supplied_family(doctrine, spec, hypothesis, ledger)
    for forged in (
        replace(judgment.source, generator_digest="0" * 64),
        replace(judgment.source, formal_source=formal),
        replace(judgment.source, hypothesis_digest=EqualString(hypothesis.hypothesis_digest)),
    ):
        with pytest.raises(AllDepthFamilyValidationError):
            snapshot_family_source(forged)


def test_nested_judgment_source_trap_rejects_during_result_validation():
    doctrine, spec, ledger, d1, formal, judgment = setup_rows()
    trapped_source = replace(
        judgment.source, introduction_evidence_digest=EqualString(
            judgment.source.introduction_evidence_digest
        ),
    )
    forged = replace(judgment, source=trapped_source)
    with pytest.raises(AllDepthFamilyValidationError, match="introduction-evidence-digest"):
        validate_derived_family_judgment(doctrine, spec, d1, formal, ledger, forged)
