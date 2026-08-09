import pytest

from src.core.proof_core_kernel import (
    ProofKernelError, check_prop, check_term, infer_proof, native_law_conclusion,
)
from src.core.proof_core_types import (
    Assume, Bound, CoreType, EqRefl, EqSym, EqTrans, Equal, Forall, ForallElim,
    ForallIntro, ImpElim, ImpIntro, Implies, NativeLaw, NativeLawId,
    ProofContext, Pulse, ResonanceIntro, Resonates, RuleId, Silence, Stitch,
    Weave,
)


def resonance_reflexive_proof():
    unit = Pulse(Silence())
    equality = NativeLaw(NativeLawId.WEAVE_UNIT_RIGHT, (Bound(0),))
    return ForallIntro(
        CoreType.RECURRENCE,
        ResonanceIntro(Bound(0), Bound(0), unit, equality),
    )


def test_general_resonance_proof_has_checker_derived_statement_and_closures():
    judgment = infer_proof(ProofContext(), resonance_reflexive_proof())
    assert judgment.conclusion == Forall(CoreType.RECURRENCE, Resonates(Bound(0), Bound(0)))
    assert judgment.rule_trace == (RuleId.NATIVE_LAW, RuleId.RESONANCE_INTRO, RuleId.FORALL_INTRO)
    assert judgment.rule_closure == (RuleId.FORALL_INTRO, RuleId.NATIVE_LAW, RuleId.RESONANCE_INTRO)
    assert judgment.native_law_closure == (NativeLawId.WEAVE_UNIT_RIGHT,)


def test_implication_and_universal_rules_infer_without_expected_claim_input():
    proposition = Equal(Silence(), Silence())
    identity = ImpIntro(proposition, Assume(0))
    assert infer_proof(ProofContext(), identity).conclusion == Implies(proposition, proposition)
    application_context = ProofContext((), (Implies(proposition, proposition), proposition))
    assert infer_proof(application_context, ImpElim(Assume(0), Assume(1))).conclusion == proposition
    universal = ForallIntro(CoreType.RECURRENCE, EqRefl(Bound(0)))
    assert infer_proof(ProofContext(), ForallElim(universal, Silence())).conclusion == proposition


def test_forall_intro_weakens_existing_assumptions_without_capture():
    context = ProofContext((CoreType.RECURRENCE,), (Equal(Bound(0), Bound(0)),))
    judgment = infer_proof(context, ForallIntro(CoreType.RECURRENCE, Assume(0)))
    assert judgment.conclusion == Forall(CoreType.RECURRENCE, Equal(Bound(1), Bound(1)))


def test_equality_symmetry_and_ordered_transitivity():
    context = ProofContext((CoreType.RECURRENCE,), ())
    law = NativeLaw(NativeLawId.STITCH_SILENCE_LEFT, (Bound(0),))
    judgment = infer_proof(context, EqTrans(law, EqSym(law)))
    term = Stitch(Silence(), Bound(0))
    assert judgment.conclusion == Equal(term, term)
    with pytest.raises(ProofKernelError, match="middle"):
        infer_proof(context, EqTrans(EqSym(law), EqSym(law)))


def test_every_native_law_has_fixed_arity_and_exact_template():
    context = ProofContext((CoreType.RECURRENCE, CoreType.RECURRENCE), ())
    x, y = Bound(0), Bound(1)
    assert native_law_conclusion(context, NativeLawId.STITCH_SILENCE_LEFT, (x,)) == Equal(Stitch(Silence(), x), x)
    assert native_law_conclusion(context, NativeLawId.STITCH_SILENCE_RIGHT, (x,)) == Equal(Stitch(x, Silence()), x)
    assert native_law_conclusion(context, NativeLawId.WEAVE_SILENCE_RIGHT, (x,)) == Equal(Weave(x, Silence()), Silence())
    assert native_law_conclusion(context, NativeLawId.WEAVE_PULSE, (x, y)) == Equal(Weave(x, Pulse(y)), Stitch(x, Weave(x, y)))
    assert native_law_conclusion(context, NativeLawId.WEAVE_UNIT_RIGHT, (x,)) == Equal(Weave(x, Pulse(Silence())), x)
    with pytest.raises(ProofKernelError, match="arity"):
        native_law_conclusion(context, NativeLawId.WEAVE_PULSE, (x,))


def test_ill_typed_unbound_and_mismatched_proofs_are_rejected():
    with pytest.raises(ProofKernelError, match="unbound-term"):
        check_term(ProofContext(), Bound(0))
    with pytest.raises(ProofKernelError, match="nonnegative"):
        check_term(ProofContext((CoreType.RECURRENCE,), ()), Bound(True))
    proposition = Equal(Silence(), Silence())
    with pytest.raises(ProofKernelError, match="premise-mismatch"):
        infer_proof(ProofContext((), (Implies(proposition, proposition),)), ImpElim(Assume(0), Assume(0)))
    bad = ResonanceIntro(Silence(), Silence(), Pulse(Silence()), EqRefl(Silence()))
    with pytest.raises(ProofKernelError, match="resonance-witness"):
        infer_proof(ProofContext(), bad)


def test_unknown_runtime_values_and_circular_proof_terms_are_rejected():
    with pytest.raises(ProofKernelError, match="unknown-native-law"):
        infer_proof(ProofContext(), NativeLaw("forged", (Silence(),)))
    cycle = EqSym(EqRefl(Silence()))
    object.__setattr__(cycle, "evidence", cycle)
    with pytest.raises(ProofKernelError, match="circular"):
        infer_proof(ProofContext(), cycle)

    with pytest.raises(ProofKernelError, match="containers"):
        infer_proof(ProofContext([], []), EqRefl(Silence()))
    with pytest.raises(ProofKernelError, match="args-must-be-tuple"):
        infer_proof(ProofContext(), NativeLaw(NativeLawId.WEAVE_UNIT_RIGHT, [Silence()]))


def test_proposition_checker_rejects_unknown_or_unbound_nodes():
    with pytest.raises(ProofKernelError, match="unbound"):
        check_prop(ProofContext(), Equal(Bound(0), Silence()))
    with pytest.raises(ProofKernelError, match="unknown-proposition"):
        check_prop(ProofContext(), object())
