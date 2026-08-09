"""Hostile boundaries for AFIP source, result, identity, and projection lanes."""

from dataclasses import replace
import inspect

import pytest

import src.core.all_depth_family_projection as projection_runtime
from src.core.all_depth_family import (
    SUPPLIED_COMPATIBILITY_LAW_ID, SUPPLIED_CONSTRUCTOR_ID,
    SUPPLIED_COORDINATE_LAW_ID, AllDepthFamilyValidationError,
    all_depth_family_spec, assumption_ledger, assumption_row, hypothesis_family_ledger,
    periodic_family_formal_source, periodic_family_ledger, project_family_stage,
    replay_all_depth_family, supplied_family_hypothesis, symbolic_family_term,
    validate_derived_family_judgment, validate_family_projection,
)
from src.core.all_depth_family_runtime import derive_periodic_family
from src.core.all_depth_family_sources import snapshot_family_source
from src.core.all_depth_family_types import (
    AssumptionKind, FamilyEvidenceStatus, FamilyProjectionArtifact,
    FamilyProjectionRefusal, ProjectionCapability, ProjectionStatus,
)
from src.core.infinity_prefix import prefix_alphabet
from src.core.positive_ontology_doctrine import observer_doctrine, p0_observer_doctrine
from src.core.productivity import (
    OUTPUT_ENCODING_ID, RESTRICTION_LAW_ID, TOTALITY_BASIS_ID,
    construct_at_depth, execution_policy, periodic_program, productive_process_source,
)

pytestmark = pytest.mark.requires_lean


def setup_rows(max_depth=10, max_bytes=20_000, period=("a", "b", "a")):
    doctrine = p0_observer_doctrine()
    alphabet = prefix_alphabet(("a", "b"))
    spec = all_depth_family_spec(doctrine, alphabet)
    ledger = periodic_family_ledger()
    program = periodic_program(alphabet, period)
    policy = execution_policy(max_depth, max_bytes)
    d1 = productive_process_source(
        program, TOTALITY_BASIS_ID, RESTRICTION_LAW_ID, OUTPUT_ENCODING_ID, policy,
    )
    formal = periodic_family_formal_source()
    row = derive_periodic_family(doctrine, spec, d1, formal, ledger)
    return doctrine, spec, ledger, program, policy, d1, formal, row


def test_finite_artifact_old_judgment_and_callable_are_not_family_sources():
    doctrine, spec, ledger, _, _, d1, formal, row = setup_rows()
    sample = construct_at_depth(d1, 4)
    for invalid in (sample, row, lambda n: n):
        with pytest.raises(AllDepthFamilyValidationError, match="unsupported-all-depth-family-source"):
            replay_all_depth_family(doctrine, spec, invalid, ledger, formal_source=None)


def test_formal_name_digest_and_tcb_lookalikes_reject_before_positive_status():
    doctrine, spec, ledger, _, _, d1, formal, _ = setup_rows()
    for forged in (
        replace(formal, theorem_ids=(formal.theorem_ids[0] + "_lookalike", *formal.theorem_ids[1:])),
        replace(formal, artifact_sha256="0" * 64),
        replace(formal, tcb_digest="0" * 64),
        replace(formal, axiom_closure=("Classical.choice",)),
    ):
        with pytest.raises(AllDepthFamilyValidationError):
            derive_periodic_family(doctrine, spec, d1, forged, ledger)


def test_doctrine_spec_and_ledger_transplants_reject():
    doctrine, spec, ledger, _, _, d1, formal, _ = setup_rows()
    foreign = observer_doctrine(
        "foreign", doctrine.admission_rule, doctrine.metadata, doctrine.observers,
        version=doctrine.version,
    )
    with pytest.raises(AllDepthFamilyValidationError, match="family-spec-doctrine-transplant"):
        derive_periodic_family(foreign, spec, d1, formal, ledger)
    altered_rows = ledger.rows + (
        assumption_row("extra-proof-trust", AssumptionKind.TRUSTED_IMPORT),
    )
    with pytest.raises(AllDepthFamilyValidationError, match="periodic-family-ledger-required"):
        derive_periodic_family(doctrine, spec, d1, formal, assumption_ledger(altered_rows))


def test_cyclic_forward_missing_duplicate_and_string_enum_ledger_rows_reject():
    with pytest.raises(AllDepthFamilyValidationError, match="cyclic-or-forward"):
        assumption_ledger((
            assumption_row("a", AssumptionKind.DEFINITION, ("b",)),
            assumption_row("b", AssumptionKind.DEFINITION),
        ))
    with pytest.raises(AllDepthFamilyValidationError, match="missing-assumption"):
        assumption_ledger((assumption_row("a", AssumptionKind.DEFINITION, ("missing",)),))
    row = assumption_row("a", AssumptionKind.DEFINITION)
    with pytest.raises(AllDepthFamilyValidationError, match="duplicate-assumption"):
        assumption_ledger((row, row))
    with pytest.raises(AllDepthFamilyValidationError, match="assumption-kind-must-be-exact"):
        assumption_row("a", "definition")  # type: ignore[arg-type]


def test_string_enum_promotion_and_nested_result_mutation_fail_fast():
    doctrine, spec, ledger, _, _, d1, formal, row = setup_rows()
    forged = replace(row, evidence_status=row.evidence_status.value)
    with pytest.raises(AllDepthFamilyValidationError, match="enum-lookalike"):
        validate_derived_family_judgment(doctrine, spec, d1, formal, ledger, forged)
    object.__setattr__(row.algebraic_laws, "relation_reflexive", "established")
    with pytest.raises(AllDepthFamilyValidationError, match="lookalike"):
        validate_derived_family_judgment(doctrine, spec, d1, formal, ledger, row)


def test_capability_and_generator_transplants_reject_at_projection_boundary():
    *_, policy, _, _, row = setup_rows()
    forged_capability = replace(row.source, capability=ProjectionCapability.SYMBOLIC_ONLY)
    with pytest.raises(AllDepthFamilyValidationError, match="invalid-derived-source-shape"):
        project_family_stage(forged_capability, 2, policy)
    forged_generator = replace(row.source, generator_digest="0" * 64)
    with pytest.raises(AllDepthFamilyValidationError, match="derived-generator"):
        snapshot_family_source(forged_generator)


def test_boolean_negative_and_above_static_depth_reject_without_semantic_status():
    *_, policy, _, _, row = setup_rows()
    for depth in (True, -1, 1_000_001):
        with pytest.raises(AllDepthFamilyValidationError, match="invalid-projection-depth"):
            project_family_stage(row.source, depth, policy)


def test_resource_preflight_is_atomic_and_never_relabels_family(monkeypatch):
    doctrine, spec, ledger, program, _, _, formal, row = setup_rows(max_depth=2)
    calls = []
    import src.core.productivity_runtime as d1_runtime
    original = d1_runtime._build_stage

    def counted(source, depth):
        calls.append(depth)
        return original(source, depth)

    monkeypatch.setattr(d1_runtime, "_build_stage", counted)
    refusal = project_family_stage(row.source, 3, execution_policy(2, 20_000))
    assert type(refusal) is FamilyProjectionRefusal and calls == []
    assert refusal.status is ProjectionStatus.RESOURCE_LIMIT
    assert row.evidence_status is FamilyEvidenceStatus.ESTABLISHED_RELATIVE_TO_LEDGER
    assert derive_periodic_family(
        doctrine, spec, productive_process_source(
            program, TOTALITY_BASIS_ID, RESTRICTION_LAW_ID, OUTPUT_ENCODING_ID,
            execution_policy(1, 100),
        ), formal, ledger,
    ).family_term_digest == row.family_term_digest


def test_projection_result_mutation_and_union_swap_reject():
    *_, policy, _, _, row = setup_rows()
    artifact = project_family_stage(row.source, 3, policy)
    assert type(artifact) is FamilyProjectionArtifact
    object.__setattr__(artifact.stage, "symbols", ("b", "b", "b"))
    with pytest.raises(AllDepthFamilyValidationError, match="semantic-drift"):
        validate_family_projection(row.source, 3, policy, artifact)
    refusal = project_family_stage(row.source, 11, policy)
    with pytest.raises(AllDepthFamilyValidationError, match="union-variant"):
        validate_family_projection(row.source, 3, policy, refusal)


def test_unexpected_projection_fault_propagates_not_semantically_normalized(monkeypatch):
    *_, policy, _, _, row = setup_rows()

    def boom(*_args, **_kwargs):
        raise RuntimeError("unexpected-engine-fault")

    monkeypatch.setattr(projection_runtime, "construct_at_depth", boom)
    with pytest.raises(RuntimeError, match="unexpected-engine-fault"):
        projection_runtime.project_family_stage(row.source, 2, policy)


def test_same_finite_outputs_do_not_collapse_family_term_identity():
    doctrine, spec, ledger, _, policy, _, formal, first = setup_rows(period=("a",))
    second_program = periodic_program(spec.alphabet, ("a", "a"))
    second_d1 = productive_process_source(
        second_program, TOTALITY_BASIS_ID, RESTRICTION_LAW_ID, OUTPUT_ENCODING_ID, policy,
    )
    second = derive_periodic_family(doctrine, spec, second_d1, formal, ledger)
    assert project_family_stage(first.source, 5, policy).stage.symbols == project_family_stage(
        second.source, 5, policy,
    ).stage.symbols
    assert first.family_term_digest != second.family_term_digest
    assert not hasattr(first, "family_extensional_equality")


def test_same_symbolic_term_different_ledger_changes_evidence_not_term():
    doctrine, spec, ledger, *_ = setup_rows()
    term = symbolic_family_term(spec, SUPPLIED_CONSTRUCTOR_ID, b"F")
    ledger1 = hypothesis_family_ledger((
        "H", SUPPLIED_COORDINATE_LAW_ID, SUPPLIED_COMPATIBILITY_LAW_ID,
    ))
    h1 = supplied_family_hypothesis(
        spec, term, "H", SUPPLIED_COORDINATE_LAW_ID,
        SUPPLIED_COMPATIBILITY_LAW_ID, ledger1,
    )
    ledger2 = assumption_ledger(ledger1.rows + (
        assumption_row("additional-trust", AssumptionKind.TRUSTED_IMPORT),
    ))
    h2 = supplied_family_hypothesis(
        spec, term, "H", SUPPLIED_COORDINATE_LAW_ID,
        SUPPLIED_COMPATIBILITY_LAW_ID, ledger2,
    )
    first = replay_all_depth_family(doctrine, spec, h1, ledger1)
    second = replay_all_depth_family(doctrine, spec, h2, ledger2)
    assert first.family_term_digest == second.family_term_digest
    assert first.introduction_evidence_digest != second.introduction_evidence_digest


def test_reversed_or_foreign_supplied_law_statement_is_not_admitted():
    _, spec, _, *_ = setup_rows()
    term = symbolic_family_term(spec, SUPPLIED_CONSTRUCTOR_ID, b"F")
    ledger = hypothesis_family_ledger(("H", "reversed-law", SUPPLIED_COMPATIBILITY_LAW_ID))
    with pytest.raises(AllDepthFamilyValidationError, match="law-statement-drift"):
        supplied_family_hypothesis(
            spec, term, "H", "reversed-law", SUPPLIED_COMPATIBILITY_LAW_ID, ledger,
        )


def test_hypothesis_identity_and_laws_must_be_explicit_in_ledger_closure():
    _, spec, ledger, *_ = setup_rows()
    term = symbolic_family_term(spec, SUPPLIED_CONSTRUCTOR_ID, b"F")
    with pytest.raises(AllDepthFamilyValidationError, match="not-closed-in-ledger"):
        supplied_family_hypothesis(
            spec, term, "H", SUPPLIED_COORDINATE_LAW_ID,
            SUPPLIED_COMPATIBILITY_LAW_ID, ledger,
        )


def test_symbolic_constructor_cannot_cross_supplied_or_oracle_lane():
    doctrine, spec, ledger, *_ = setup_rows()
    from src.core.all_depth_family import ORACLE_CONSTRUCTOR_ID
    wrong = symbolic_family_term(spec, ORACLE_CONSTRUCTOR_ID, b"O")
    with pytest.raises(AllDepthFamilyValidationError, match="requires-supplied"):
        supplied_family_hypothesis(spec, wrong, "H", "coord", "compat", ledger)


def test_public_projection_has_no_expected_stage_or_target_parameter():
    assert set(inspect.signature(project_family_stage).parameters) == {
        "family_source", "n", "policy",
    }
