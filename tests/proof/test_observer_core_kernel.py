"""Conservative observer proof-kernel acceptance and rejection tests."""

from __future__ import annotations

from dataclasses import replace
import pytest

import src.core.observer_core_proof_types as proof_types
from src.core.observer_core_kernel import (
    MAX_EMBEDDED_R7_PROOF_DEPTH,
    MAX_EMBEDDED_R7_PROOF_NODES,
    MAX_OBSERVER_PROOF_DEPTH,
    ObserverProofError,
    crest_observer,
    infer_observer_proof,
    is_structurally_total,
    tail_observer,
)
from src.core.observer_core_proof_types import (
    CrestPulseEcho,
    Echoes,
    EmbedR7,
    EqualityReadyEcho,
    Obstructed,
    ObserverLawId,
    ObserverRuleId,
    ObserverSupportId,
    TailSilenceObstruction,
)
from src.core.observer_core_types import (
    Apply,
    Blocked,
    Echo,
    Input,
    Mark,
    MarkValue,
    Mismatch,
    ObstructionCode,
    Pair,
    PathStep,
    PrimitiveId,
)
from src.core.observer_core_semantics import MAX_OBSERVER_NODES
from src.core.observer_core_support import outcome_data, support_closure
from src.core.proof_core_kernel import ProofKernelError
from src.core.proof_core_types import (
    Assume,
    Bound,
    CheckedJudgment,
    CoreType,
    EqRefl,
    EqSym,
    EqTrans,
    Equal,
    ForallElim,
    ForallIntro,
    ImpElim,
    ImpIntro,
    NativeLaw,
    NativeLawId,
    ProofContext,
    Pulse,
    ResonanceIntro,
    RuleId,
    Silence,
    Weave,
)


def test_exact_crest_pulse_echo_is_replayed() -> None:
    proof = CrestPulseEcho(Silence(), Pulse(Silence()))
    judgment = infer_observer_proof(ProofContext(), proof)
    assert type(judgment.conclusion) is Echoes
    assert judgment.conclusion.observer == crest_observer()
    assert type(judgment.outcome) is Echo
    assert type(judgment.outcome.value) is MarkValue
    assert judgment.outcome.value.mark is Mark.PULSE
    assert judgment.rule_closure == (ObserverRuleId.CREST_PULSE_ECHO,)
    assert judgment.observer_law_closure == (ObserverLawId.CREST_PULSE_ECHO,)
    assert ObserverSupportId.CREST_PULSE_LAW in judgment.support


def test_exact_tail_silence_obstruction_is_replayed() -> None:
    judgment = infer_observer_proof(ProofContext(), TailSilenceObstruction())
    assert type(judgment.conclusion) is Obstructed
    assert judgment.conclusion.observer == tail_observer()
    assert type(judgment.outcome) is Blocked
    assert judgment.outcome.obstructions[0].code is ObstructionCode.TAIL_OF_SILENCE
    assert judgment.obstruction_paths == ((PathStep.APPLY_TAIL,),)
    assert judgment.observer_law_closure == (ObserverLawId.TAIL_SILENCE_OBSTRUCTION,)
    assert ObserverSupportId.TAIL_SILENCE_LAW in judgment.support


def test_equality_echo_rechecks_r7_and_derives_closures() -> None:
    term = Pulse(Pulse(Silence()))
    proof = EqualityReadyEcho(crest_observer(), EmbedR7(EqRefl(term)))
    judgment = infer_observer_proof(ProofContext(), proof)
    assert type(judgment.conclusion) is Echoes
    assert type(judgment.outcome) is Echo
    assert judgment.rule_trace == (ObserverRuleId.EMBED_R7, ObserverRuleId.EQUALITY_READY_ECHO)
    assert judgment.r7_rule_closure == ("eq-refl",)
    assert judgment.r7_native_law_closure == ()
    assert ObserverSupportId.R7_KERNEL in judgment.support
    assert ObserverSupportId.STRUCTURAL_TOTALITY in judgment.support


def test_substitution_safe_r7_instantiation_can_feed_closed_echo() -> None:
    term = Pulse(Silence())
    evidence = ForallElim(
        ForallIntro(CoreType.RECURRENCE, EqRefl(Bound(0))),
        term,
    )
    judgment = infer_observer_proof(
        ProofContext(),
        EqualityReadyEcho(Input(), EmbedR7(evidence)),
    )
    assert type(judgment.outcome) is Echo
    assert judgment.r7_rule_closure == ("forall-intro", "forall-elim", "eq-refl")


def test_structural_totality_is_closed_and_conservative() -> None:
    assert is_structurally_total(Input())
    assert is_structurally_total(crest_observer())
    assert is_structurally_total(Pair(Input(), crest_observer()))
    assert not is_structurally_total(tail_observer())
    assert not is_structurally_total(Pair(crest_observer(), tail_observer()))


def test_partial_observer_cannot_receive_equality_transport() -> None:
    proof = EqualityReadyEcho(tail_observer(), EmbedR7(EqRefl(Pulse(Silence()))))
    with pytest.raises(ObserverProofError, match="needs-total-observer"):
        infer_observer_proof(ProofContext(), proof)


def test_native_law_nonvalue_equality_is_not_smuggled_into_semantics() -> None:
    evidence = NativeLaw(NativeLawId.STITCH_SILENCE_LEFT, (Pulse(Silence()),))
    proof = EqualityReadyEcho(Input(), EmbedR7(evidence))
    with pytest.raises(ObserverProofError, match="must-be-closed-recurrence-value"):
        infer_observer_proof(ProofContext(), proof)


def test_open_bound_equality_is_rejected_even_when_r7_context_types_it() -> None:
    proof = EqualityReadyEcho(Input(), EmbedR7(EqRefl(Bound(0))))
    with pytest.raises(ObserverProofError, match="must-be-closed-recurrence-value"):
        infer_observer_proof(ProofContext((CoreType.RECURRENCE,), ()), proof)


@pytest.mark.parametrize("tail", [Bound(0), NativeLawId.WEAVE_PULSE])
def test_crest_law_rejects_nonclosed_or_nonterm_tails(tail: object) -> None:
    context = ProofContext((CoreType.RECURRENCE,), ())
    with pytest.raises((ObserverProofError, ProofKernelError)):
        infer_observer_proof(context, CrestPulseEcho(tail, Silence()))


def test_non_equality_r7_evidence_cannot_feed_equality_rule() -> None:
    evidence = ForallIntro(CoreType.RECURRENCE, EqRefl(Bound(0)))
    with pytest.raises(ObserverProofError, match="needs-r7-equality"):
        infer_observer_proof(
            ProofContext(),
            EqualityReadyEcho(Input(), EmbedR7(evidence)),
        )


def test_type_subclass_and_cyclic_proof_are_rejected() -> None:
    class ForgedEmbed(EmbedR7):
        pass

    with pytest.raises(ObserverProofError, match="unknown-observer-proof"):
        infer_observer_proof(ProofContext(), ForgedEmbed(EqRefl(Silence())))
    cyclic = EqualityReadyEcho(Input(), EmbedR7(EqRefl(Silence())))
    object.__setattr__(cyclic, "equality", cyclic)
    with pytest.raises(ObserverProofError, match="circular-observer-proof"):
        infer_observer_proof(ProofContext(), cyclic)


def test_no_echo_to_equality_constructor_exists() -> None:
    assert not hasattr(proof_types, "EchoToEquality")
    assert not hasattr(proof_types, "EchoImpliesEqual")
    assert Apply(PrimitiveId.CREST, Input()) == crest_observer()


def test_every_rule_rejects_forged_context_shape() -> None:
    context = ProofContext()
    object.__setattr__(context, "term_types", [CoreType.RECURRENCE])
    with pytest.raises(ObserverProofError, match="invalid-context-containers"):
        infer_observer_proof(context, TailSilenceObstruction())


def test_proof_depth_is_bounded_before_python_recursion() -> None:
    proof = EmbedR7(EqRefl(Silence()))
    for _ in range(MAX_OBSERVER_PROOF_DEPTH + 2):
        proof = EqualityReadyEcho(Input(), proof)
    with pytest.raises(ObserverProofError, match="observer-proof-resource-limit"):
        infer_observer_proof(ProofContext(), proof)


def test_embedded_r7_preflight_preserves_every_exact_constructor() -> None:
    equality = Equal(Silence(), Silence())
    universal = ForallIntro(CoreType.RECURRENCE, EqRefl(Bound(0)))
    carrier = Weave(Silence(), Silence())
    cases = (
        (ProofContext((), (equality,)), Assume(0)),
        (ProofContext(), ImpIntro(equality, Assume(0))),
        (ProofContext(), ImpElim(ImpIntro(equality, Assume(0)), EqRefl(Silence()))),
        (ProofContext(), universal),
        (ProofContext(), ForallElim(universal, Silence())),
        (ProofContext(), EqRefl(Silence())),
        (ProofContext(), EqSym(EqRefl(Silence()))),
        (ProofContext(), EqTrans(EqRefl(Silence()), EqRefl(Silence()))),
        (ProofContext(), NativeLaw(NativeLawId.STITCH_SILENCE_LEFT, (Silence(),))),
        (ProofContext(), ResonanceIntro(Silence(), carrier, Silence(), EqRefl(carrier))),
    )
    for context, evidence in cases:
        judgment = infer_observer_proof(context, EmbedR7(evidence))
        assert judgment.rule_closure == (ObserverRuleId.EMBED_R7,)
        assert outcome_data(judgment.outcome)["tag"] == "r7"


def test_embedded_r7_depth_nodes_and_cycles_are_bounded_iteratively() -> None:
    deep = EqRefl(Silence())
    for _ in range(MAX_EMBEDDED_R7_PROOF_DEPTH + 1):
        deep = EqSym(deep)
    with pytest.raises(ObserverProofError, match="embedded-r7-proof-resource-limit"):
        infer_observer_proof(ProofContext(), EmbedR7(deep))
    wide = EqRefl(Silence())
    for _ in range(MAX_EMBEDDED_R7_PROOF_NODES.bit_length()):
        wide = EqTrans(wide, wide)
    with pytest.raises(ObserverProofError, match="embedded-r7-proof-resource-limit"):
        infer_observer_proof(ProofContext(), EmbedR7(wide))
    cyclic = EqSym(EqRefl(Silence()))
    object.__setattr__(cyclic, "evidence", cyclic)
    with pytest.raises(ObserverProofError, match="circular-embedded-r7-proof"):
        infer_observer_proof(ProofContext(), EmbedR7(cyclic))


def test_embedded_r7_outcome_closures_reject_custom_iterables_before_access() -> None:
    class ProtocolTrap:
        def __len__(self):
            raise AssertionError("len trap")

        def __iter__(self):
            raise AssertionError("iter trap")

        def __repr__(self):
            raise AssertionError("repr trap")

    outcome = infer_observer_proof(ProofContext(), EmbedR7(EqRefl(Silence()))).outcome
    object.__setattr__(outcome, "rule_closure", ProtocolTrap())
    with pytest.raises(ValueError, match="invalid-r7-outcome-closures"):
        outcome_data(outcome)


def test_r7_outcome_preflight_rejects_hostile_context_and_forged_closures() -> None:
    class AttributeTrap:
        def __getattribute__(self, _name):
            raise AssertionError("attribute trap")

    class ProtocolTrap:
        def __len__(self):
            raise AssertionError("len trap")

        def __iter__(self):
            raise AssertionError("iter trap")

    outcome = infer_observer_proof(ProofContext(), EmbedR7(EqRefl(Silence()))).outcome
    assert type(outcome) is CheckedJudgment and outcome_data(outcome)["tag"] == "r7"
    context = ProofContext()
    object.__setattr__(context, "term_types", ProtocolTrap())
    for hostile in (AttributeTrap(), context):
        with pytest.raises(ValueError, match="invalid-r7-outcome-context"):
            outcome_data(replace(outcome, context=hostile))
    forged = (
        {"rule_trace": ()},
        {"rule_trace": (RuleId.EQ_REFL,) * (MAX_OBSERVER_NODES + 1)},
        {"rule_closure": (RuleId.EQ_REFL, RuleId.EQ_REFL)},
        {"rule_trace": (RuleId.EQ_SYM,), "rule_closure": (RuleId.EQ_REFL,)},
        {"native_law_closure": (NativeLawId.STITCH_SILENCE_RIGHT, NativeLawId.STITCH_SILENCE_LEFT)},
        {"native_law_closure": (NativeLawId.STITCH_SILENCE_LEFT,) * 2},
    )
    for fields in forged:
        with pytest.raises(ValueError, match="invalid-r7-outcome-closures"):
            outcome_data(replace(outcome, **fields))
    with pytest.raises(ValueError, match="unbound-term-variable"):
        outcome_data(replace(outcome, conclusion=Equal(Bound(99), Bound(99))))


def test_mismatch_and_support_closures_require_canonical_separation_and_order() -> None:
    pulse, silent = MarkValue(Mark.PULSE), MarkValue(Mark.SILENT)
    with pytest.raises(ValueError, match="invalid-mismatch"):
        outcome_data(Mismatch(pulse, pulse))
    assert outcome_data(Mismatch(pulse, silent))["tag"] == "mismatch"
    bad = (
        ((ObserverRuleId.EMBED_R7,) * 2, ()),
        ((ObserverRuleId.CREST_PULSE_ECHO, ObserverRuleId.EMBED_R7), ()),
        ((), (ObserverLawId.TAIL_SILENCE_OBSTRUCTION, ObserverLawId.CREST_PULSE_ECHO)),
    )
    for rules, laws in bad:
        with pytest.raises(ValueError, match="invalid-support-input"):
            support_closure(rules, laws)
