from src.core.proof_core_types import (
    Assume, Bound, CoreType, EqRefl, EqSym, EqTrans, Equal, ForallElim,
    ForallIntro, ImpElim, ImpIntro, NativeLaw, NativeLawId, Pulse,
    ResonanceIntro, Silence, Stitch, Weave,
)
from src.core.proof_dependency_support import (
    DependencyCategory, DependencyId, dependency_category,
    image_composition_support, proof_support, prop_support,
    support_by_category, term_support,
)


def resonance_proof():
    variable = Bound(0)
    equality = NativeLaw(NativeLawId.WEAVE_UNIT_RIGHT, (variable,))
    return ForallIntro(
        CoreType.RECURRENCE,
        ResonanceIntro(variable, variable, Pulse(Silence()), equality),
    )


def test_dependency_ids_are_disjoint_and_exhaustively_categorized():
    rows = {item: dependency_category(item) for item in DependencyId}
    assert len(rows) == len(DependencyId)
    assert set(rows.values()) == set(DependencyCategory)
    assert all(item.value.startswith(rows[item].value + ".") for item in DependencyId)


def test_term_and_proposition_support_is_constructor_derived():
    term = Weave(Pulse(Silence()), Stitch(Bound(0), Silence()))
    assert term_support(term) == {
        DependencyId.RECURRENCE_FORMATION,
        DependencyId.SILENCE_DEFINITION,
        DependencyId.PULSE_DEFINITION,
        DependencyId.STITCH_DEFINITION,
        DependencyId.WEAVE_DEFINITION,
    }
    proposition = Equal(term, Bound(0))
    assert prop_support(proposition) == term_support(term) | {
        DependencyId.PROPOSITION_FORMATION,
        DependencyId.EQUAL_DEFINITION,
    }


def test_r7_resonance_support_is_structural_and_r9_observer_is_explicit():
    support = proof_support(resonance_proof())
    assert support == {
        DependencyId.RECURRENCE_FORMATION,
        DependencyId.PROPOSITION_FORMATION,
        DependencyId.SILENCE_DEFINITION,
        DependencyId.PULSE_DEFINITION,
        DependencyId.WEAVE_DEFINITION,
        DependencyId.EQUAL_DEFINITION,
        DependencyId.FORALL_DEFINITION,
        DependencyId.RESONATES_DEFINITION,
        DependencyId.FORALL_INTRO_RULE,
        DependencyId.RESONANCE_INTRO_RULE,
        DependencyId.WEAVE_UNIT_RIGHT_LAW,
    }
    image_support = image_composition_support(resonance_proof())
    assert image_support == support | {DependencyId.INTRINSIC_MODE_OBSERVER}
    assert DependencyId.FOREIGN_MODE_OBSTRUCTION not in image_support


def test_every_r7_rule_and_native_law_has_computed_support():
    proposition = Equal(Silence(), Silence())
    universal = ForallIntro(CoreType.RECURRENCE, EqRefl(Bound(0)))
    rules = (
        Assume(0),
        ImpIntro(proposition, Assume(0)),
        ImpElim(Assume(0), Assume(1)),
        universal,
        ForallElim(universal, Silence()),
        EqRefl(Silence()),
        EqSym(EqRefl(Silence())),
        EqTrans(EqRefl(Silence()), EqRefl(Silence())),
        ResonanceIntro(Silence(), Silence(), Silence(), EqRefl(Silence())),
    )
    logical = {
        item for proof in rules for item in proof_support(proof)
        if dependency_category(item) is DependencyCategory.LOGICAL
    }
    assert logical == {
        DependencyId.ASSUME_RULE, DependencyId.IMP_INTRO_RULE,
        DependencyId.IMP_ELIM_RULE, DependencyId.FORALL_INTRO_RULE,
        DependencyId.FORALL_ELIM_RULE, DependencyId.EQ_REFL_RULE,
        DependencyId.EQ_SYM_RULE, DependencyId.EQ_TRANS_RULE,
        DependencyId.RESONANCE_INTRO_RULE,
    }
    laws = tuple(NativeLaw(law, (Silence(), Silence()) if law is NativeLawId.WEAVE_PULSE else (Silence(),)) for law in NativeLawId)
    domain = {
        item for proof in laws for item in proof_support(proof)
        if dependency_category(item) is DependencyCategory.DOMAIN
    }
    assert domain == {
        DependencyId.STITCH_SILENCE_LEFT_LAW,
        DependencyId.STITCH_SILENCE_RIGHT_LAW,
        DependencyId.WEAVE_SILENCE_RIGHT_LAW,
        DependencyId.WEAVE_PULSE_LAW,
        DependencyId.WEAVE_UNIT_RIGHT_LAW,
    }


def test_categorized_support_is_deterministic_and_never_calls_itself_minimal():
    rows = support_by_category(image_composition_support(resonance_proof()))
    assert tuple(name for name, _ in rows) == tuple(item.value for item in DependencyCategory)
    assert all(values == tuple(sorted(values)) for _, values in rows)
    assert "no minimality is claimed" in (proof_support.__doc__ or "").lower()
