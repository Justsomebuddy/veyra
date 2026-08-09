"""Exact fifteen-case PΩ2 counterpressure and hostile shell tests."""

from dataclasses import replace

import pytest

from src.core.padic_completion import (
    PadicCompletionValidationError, PadicObligationStatus,
    padic_completion_judgment, prime_source, validate_padic_completion_result,
)

from padic_completion_fixture import exact_padic_package


ATTACKS = (
    "finite-residue-list-as-family",
    "incompatible-independent-residues",
    "productive-algorithm-as-extensional-family",
    "one-family-as-universal-completion",
    "representative-equality-as-zmod-equality",
    "bounded-equality-as-joint-separation",
    "composite-base-under-prime-doctrine",
    "different-prime-transplant",
    "circular-existence-uniqueness",
    "zero-family-nonvacuity-omitted",
    "ring-closure-silently-assumed",
    "topological-completion-relabel",
    "categorical-limit-relabel",
    "stale-formal-artifact",
    "physical-infinity-promotion",
)


class ForeignPackage:
    """A package-shaped semantic payload that must fail exact type admission."""

    def __init__(self, payload):
        self.family = payload


def _package_attack(name, package):
    """Build one bounded attack without invoking target semantics."""
    if name in {
        "finite-residue-list-as-family", "incompatible-independent-residues",
        "productive-algorithm-as-extensional-family", "one-family-as-universal-completion",
    }:
        return ForeignPackage((0, 1, 2))
    if name == "representative-equality-as-zmod-equality":
        doctrine = replace(package.doctrine, equality_id="integer-representative-equality")
        return replace(package, doctrine=doctrine)
    if name == "bounded-equality-as-joint-separation":
        theorem = replace(package.theorem_source, theorem_ids=package.theorem_source.theorem_ids[:-1])
        return replace(package, theorem_source=theorem)
    if name == "different-prime-transplant":
        return replace(package, prime=prime_source(7))
    if name == "circular-existence-uniqueness":
        rows = list(package.ledger.rows)
        rows[26] = replace(rows[26], direct_dependencies=(rows[26].row_id,))
        return replace(package, ledger=replace(package.ledger, rows=tuple(rows)))
    if name == "zero-family-nonvacuity-omitted":
        ids = package.theorem_source.theorem_ids
        return replace(package, theorem_source=replace(package.theorem_source, theorem_ids=ids[:10] + ids[11:]))
    if name == "ring-closure-silently-assumed":
        ids = package.theorem_source.theorem_ids
        return replace(package, theorem_source=replace(package.theorem_source, theorem_ids=ids[:15] + ids[16:]))
    if name == "stale-formal-artifact":
        return replace(package, theorem_source=replace(package.theorem_source, artifact_sha256="0" * 64))
    raise AssertionError(name)


@pytest.mark.parametrize("name", ATTACKS, ids=ATTACKS)
def test_exact_fifteen_counterpressure_cases_fail_closed(name, lean_available):
    package = exact_padic_package()
    if name == "composite-base-under-prime-doctrine":
        with pytest.raises(PadicCompletionValidationError):
            prime_source(6)
        return
    if name in {
        "topological-completion-relabel", "categorical-limit-relabel",
        "physical-infinity-promotion",
    }:
        if not lean_available:
            pytest.skip("forging a judgment needs the pinned Lean toolchain")
        result = padic_completion_judgment(package)
        field = {
            "topological-completion-relabel": "topological_completion",
            "categorical-limit-relabel": "categorical_inverse_limit_universal_property",
            "physical-infinity-promotion": "physical_instantiation",
        }[name]
        forged = replace(result, **{field: PadicObligationStatus.ESTABLISHED})
        with pytest.raises(PadicCompletionValidationError):
            validate_padic_completion_result(package, forged)
        return
    hostile = _package_attack(name, package)
    with pytest.raises(PadicCompletionValidationError):
        padic_completion_judgment(hostile)


def test_hostile_outer_variants_and_huge_bound_fail_before_replay():
    package = exact_padic_package()
    with pytest.raises(PadicCompletionValidationError):
        validate_padic_completion_result(package, object())
    refusal = padic_completion_judgment(exact_padic_package(max_captured_bytes=1))
    hostile = replace(refusal, required_value=10 ** 10_000)
    with pytest.raises(PadicCompletionValidationError):
        validate_padic_completion_result(package, hostile)


@pytest.mark.parametrize("field,value", (
    ("representation_id", "custom-VeyraCompatibleFamily-structure-v1"),
    ("canonical_ops_id", "uninstantiated-ops-parameter"),
    ("concrete_instance_id", "conditional-THM017-without-prime-application"),
))
def test_old_custom_or_conditional_formal_presentations_fail_closed(field, value):
    package = exact_padic_package()
    theorem = replace(package.theorem_source, **{field: value})
    with pytest.raises(PadicCompletionValidationError):
        padic_completion_judgment(replace(package, theorem_source=theorem))
