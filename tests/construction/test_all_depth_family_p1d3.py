"""Positive AFIP, extensional-family, and identity tests for P1-D3."""

from src.core.all_depth_family import (
    ORACLE_CONSTRUCTOR_ID, ORACLE_PURITY_HYPOTHESIS_ID,
    ORACLE_STABILITY_HYPOTHESIS_ID, ORACLE_TOTALITY_HYPOTHESIS_ID,
    SUPPLIED_COMPATIBILITY_LAW_ID, SUPPLIED_CONSTRUCTOR_ID,
    SUPPLIED_COORDINATE_LAW_ID, admit_oracle_family,
    admit_supplied_family, all_depth_family_spec, oracle_family_hypothesis,
    hypothesis_family_ledger, periodic_family_formal_source, periodic_family_ledger,
    project_family_stage,
    replay_all_depth_family, supplied_family_hypothesis, symbolic_family_term,
)
from src.core.all_depth_family_runtime import derive_periodic_family, open_all_depth_family
from src.core.all_depth_family_types import (
    CompletedCarrierStatus, FamilyEvidenceStatus, FamilyProjectionArtifact,
    FamilyProjectionRefusal, FamilyProvenance, HigherStatus, LawStatus,
    LedgerStatus, ProjectionStatus,
)
from src.core.infinity_prefix import prefix_alphabet
from src.core.positive_ontology_doctrine import p0_observer_doctrine
from src.core.productivity import (
    OUTPUT_ENCODING_ID, RESTRICTION_LAW_ID, TOTALITY_BASIS_ID,
    construct_at_depth, execution_policy, periodic_program, productive_process_source,
)
import pytest

pytestmark = pytest.mark.requires_lean


def setup_rows(max_depth=12, max_bytes=20_000):
    doctrine = p0_observer_doctrine()
    alphabet = prefix_alphabet(("a", "b"))
    spec = all_depth_family_spec(doctrine, alphabet)
    ledger = periodic_family_ledger()
    program = periodic_program(alphabet, ("a", "b", "a"))
    policy = execution_policy(max_depth, max_bytes)
    d1 = productive_process_source(
        program, TOTALITY_BASIS_ID, RESTRICTION_LAW_ID, OUTPUT_ENCODING_ID, policy,
    )
    judgment = derive_periodic_family(
        doctrine, spec, d1, periodic_family_formal_source(), ledger,
    )
    return doctrine, spec, ledger, program, policy, d1, judgment


def test_periodic_raw_source_introduces_one_established_relative_family():
    _, spec, ledger, program, _, d1, row = setup_rows()
    assert row.evidence_status is FamilyEvidenceStatus.ESTABLISHED_RELATIVE_TO_LEDGER
    assert row.provenance is FamilyProvenance.FORMALLY_DERIVED
    assert row.spec == spec and row.source is not None
    assert row.source.term.program == program
    assert row.source.generator_digest == d1.generator_digest
    assert row.ledger_status is LedgerStatus.CLOSED
    assert row.ledger_digest == ledger.ledger_digest
    assert row.coordinate_totality is row.restriction_compatibility is LawStatus.ESTABLISHED
    assert all(status is LawStatus.ESTABLISHED for status in vars(row.algebraic_laws).values())


def test_projection_matches_periodic_coordinates_and_compatible_restrictions():
    _, _, _, _, policy, _, row = setup_rows()
    projections = tuple(project_family_stage(row.source, n, policy) for n in range(9))
    assert all(type(item) is FamilyProjectionArtifact for item in projections)
    expected = ("a", "b", "a", "a", "b", "a", "a", "b")
    assert projections[8].stage.symbols == expected
    for m in range(9):
        assert projections[8].stage.symbols[:m] == projections[m].stage.symbols
        assert projections[m].stage.depth == m


def test_family_term_and_evidence_ignore_policy_while_projection_run_binds_it():
    doctrine, spec, ledger, program, p1, _, first = setup_rows()
    p2 = execution_policy(30, 40_000)
    d1_second = productive_process_source(
        program, TOTALITY_BASIS_ID, RESTRICTION_LAW_ID, OUTPUT_ENCODING_ID, p2,
    )
    second = derive_periodic_family(
        doctrine, spec, d1_second, periodic_family_formal_source(), ledger,
    )
    assert first.family_term_digest == second.family_term_digest
    assert first.introduction_evidence_digest == second.introduction_evidence_digest
    assert first.source.source_digest == second.source.source_digest
    a = project_family_stage(first.source, 7, p1)
    b = project_family_stage(second.source, 7, p2)
    assert type(a) is type(b) is FamilyProjectionArtifact
    assert a.stage == b.stage and a.output_digest == b.output_digest
    assert a.policy_digest != b.policy_digest and a.run_digest != b.run_digest


def test_operational_refusal_does_not_change_positive_family_judgment():
    _, _, _, _, policy, _, row = setup_rows(max_depth=3)
    refusal = project_family_stage(row.source, 4, policy)
    assert type(refusal) is FamilyProjectionRefusal
    assert refusal.status is ProjectionStatus.RESOURCE_LIMIT
    assert not hasattr(refusal, "stage") and not hasattr(refusal, "output_digest")
    assert row.evidence_status is FamilyEvidenceStatus.ESTABLISHED_RELATIVE_TO_LEDGER


def test_supplied_and_oracle_sources_remain_assumed_and_nonexecutable():
    doctrine, spec, ledger, _, policy, _, _ = setup_rows()
    supplied_term = symbolic_family_term(spec, SUPPLIED_CONSTRUCTOR_ID, b"family F : Nat -> Stage")
    supplied_ledger = hypothesis_family_ledger(("H-F", SUPPLIED_COORDINATE_LAW_ID, SUPPLIED_COMPATIBILITY_LAW_ID))
    supplied_h = supplied_family_hypothesis(
        spec, supplied_term, "H-F", SUPPLIED_COORDINATE_LAW_ID,
        SUPPLIED_COMPATIBILITY_LAW_ID, supplied_ledger,
    )
    supplied = admit_supplied_family(doctrine, spec, supplied_h, supplied_ledger)
    oracle_term = symbolic_family_term(spec, ORACLE_CONSTRUCTOR_ID, b"family O : Nat -> Stage")
    oracle_ids = ("H-O", "O-interface", ORACLE_TOTALITY_HYPOTHESIS_ID,
                  ORACLE_PURITY_HYPOTHESIS_ID, ORACLE_STABILITY_HYPOTHESIS_ID, "O-trust")
    oracle_ledger = hypothesis_family_ledger(oracle_ids)
    oracle_h = oracle_family_hypothesis(spec, oracle_term, *oracle_ids, oracle_ledger)
    oracle = admit_oracle_family(doctrine, spec, oracle_h, oracle_ledger)
    assert supplied.evidence_status is oracle.evidence_status is FamilyEvidenceStatus.ASSUMED
    assert supplied.provenance is FamilyProvenance.SUPPLIED_HYPOTHESIS
    assert oracle.provenance is FamilyProvenance.ORACLE_DEPENDENT
    for admitted in (supplied, oracle):
        projection = project_family_stage(admitted.source, 2, policy)
        assert type(projection) is FamilyProjectionRefusal
        assert projection.status is ProjectionStatus.PROJECTION_UNAVAILABLE
        assert projection.failed_bound is projection.required_value is projection.allowed_value is None


def test_valid_missing_source_is_open_with_no_positive_payload():
    doctrine, spec, ledger, *_ = setup_rows()
    row = open_all_depth_family(doctrine, spec, ledger)
    assert row.evidence_status is FamilyEvidenceStatus.OPEN
    assert row.source is row.provenance is None
    assert row.family_term_digest is row.introduction_evidence_digest is None
    assert row.coordinate_totality is row.restriction_compatibility is LawStatus.OPEN


def test_replay_dispatches_raw_sources_not_old_results():
    doctrine, spec, ledger, _, _, d1, derived = setup_rows()
    replayed = replay_all_depth_family(
        doctrine, spec, d1, ledger, periodic_family_formal_source(),
    )
    opened = replay_all_depth_family(doctrine, spec, None, ledger)
    assert replayed == derived and replayed is not derived
    assert opened.evidence_status is FamilyEvidenceStatus.OPEN
    d1_sample = construct_at_depth(d1, 3)
    assert not hasattr(replayed, "prior_judgment") and not hasattr(replayed, "samples")
    assert d1_sample is not replayed.source


def test_all_lanes_keep_completion_and_higher_properties_unclaimed():
    doctrine, spec, ledger, _, _, _, derived = setup_rows()
    opened = open_all_depth_family(doctrine, spec, ledger)
    for row in (derived, opened):
        assert row.completed_carrier is CompletedCarrierStatus.NOT_ESTABLISHED
        assert row.universal_realization is row.observer_separation is HigherStatus.OPEN
