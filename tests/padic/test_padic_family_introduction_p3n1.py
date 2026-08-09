"""Positive and boundary tests for P3-N1 integer family introduction."""

from dataclasses import replace

import pytest

from src.core.padic_completion import padic_tower_doctrine, prime_source
from src.core.padic_family_introduction import (
    N1EvidenceProvenance, N1EvidenceStatus, N1FamilyJudgment, N1JudgmentKind,
    N1ResourceLimit, PadicFamilyIntroductionValidationError, integer_source,
    introduce_integer_residue_family, n1_assumption_ledger, n1_introduction_package,
    n1_policy, n1_theorem_source, validate_n1_result,
)
from padic_family_introduction_fixture import exact_n1_package

pytestmark = pytest.mark.requires_lean


def test_public_introduction_has_no_depth_callback_or_prior_evidence_parameter():
    import inspect

    assert tuple(inspect.signature(introduce_integer_residue_family).parameters) == ("raw_package",)


def test_exact_integer_family_is_formally_derived_at_all_depths():
    package = exact_n1_package()
    value = introduce_integer_residue_family(package)
    assert type(value) is N1FamilyJudgment
    assert value.kind is N1JudgmentKind.ALL_DEPTH_FAMILY
    assert value.status is N1EvidenceStatus.ESTABLISHED
    assert value.provenance is N1EvidenceProvenance.FORMALLY_DERIVED
    assert value.coordinate_totality is N1EvidenceStatus.ESTABLISHED
    assert value.all_reductions_compatible is N1EvidenceStatus.ESTABLISHED
    assert value.theorem_axiom_closure == ("propext",)
    assert len({value.theorem_source_digest, value.family_term_digest,
                value.introduction_evidence_digest, value.judgment_digest}) == 4


def test_result_is_freshly_replayed_and_nonpromoting():
    package = exact_n1_package(z=987654321)
    value = introduce_integer_residue_family(package)
    replay = validate_n1_result(package, value)
    assert replay == value and replay is not value
    assert "universal-pomega2-completion" in value.nonclaims
    assert "local-carrier-realization" in value.nonclaims
    assert not hasattr(value, "completed_carrier")
    assert not hasattr(value, "realization")


def test_negative_zero_and_positive_integers_have_distinct_families():
    rows = [introduce_integer_residue_family(exact_n1_package(z=z)) for z in (-1, 0, 1)]
    assert all(type(row) is N1FamilyJudgment for row in rows)
    assert len({row.family_term_digest for row in rows}) == 3
    assert len({row.integer_digest for row in rows}) == 3


def test_policy_refuses_before_formal_execution():
    value = introduce_integer_residue_family(exact_n1_package(max_captured_bytes=1))
    assert type(value) is N1ResourceLimit
    assert value.required_value > value.allowed_value
    assert not hasattr(value, "family_term_digest")


@pytest.mark.parametrize("bad", [True, False, lambda depth: depth, (1, 2, 3), {0: 1}])
def test_booleans_callbacks_or_finite_tables_are_not_integer_sources(bad):
    with pytest.raises(PadicFamilyIntroductionValidationError):
        integer_source(bad)


@pytest.mark.parametrize("p", [0, 1, -3, 4, 9, True])
def test_nonprime_or_boolean_prime_sources_are_rejected(p):
    with pytest.raises(Exception):
        prime_source(p)


def test_prior_judgment_cannot_reenter_any_raw_package_lane():
    result = introduce_integer_residue_family(exact_n1_package())
    with pytest.raises(PadicFamilyIntroductionValidationError):
        n1_introduction_package(
            result, integer_source(1), padic_tower_doctrine(), n1_theorem_source(),
            n1_assumption_ledger(), n1_policy(),
        )


def test_cross_prime_and_cross_integer_transplants_fail_closed():
    package = exact_n1_package()
    for mutant in (replace(package, prime=prime_source(7)),
                   replace(package, integer=integer_source(124))):
        with pytest.raises(PadicFamilyIntroductionValidationError):
            introduce_integer_residue_family(mutant)


def test_source_and_doctrine_mutation_cannot_reuse_package_digest():
    package = exact_n1_package()
    bad_theorem = replace(package.theorem_source, family_definition_id="alien-family")
    bad_doctrine = replace(package.doctrine, reduction_id="reverse-or-alien-reduction")
    for mutant in (replace(package, theorem_source=bad_theorem),
                   replace(package, doctrine=bad_doctrine)):
        with pytest.raises(PadicFamilyIntroductionValidationError):
            introduce_integer_residue_family(mutant)


def test_family_result_mutation_and_cross_integer_validation_fail():
    package = exact_n1_package()
    value = introduce_integer_residue_family(package)
    with pytest.raises(PadicFamilyIntroductionValidationError):
        validate_n1_result(package, replace(value, family_term_digest="0" * 64))
    with pytest.raises(PadicFamilyIntroductionValidationError):
        validate_n1_result(exact_n1_package(z=-124), value)
