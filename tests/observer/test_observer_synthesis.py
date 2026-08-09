from functools import partial
from operator import itemgetter
import sys

from src.core.observer_synthesis import (
    canonical_term, enumerate_observer_terms, evaluate_observer, fit_observer,
    observer_fingerprint, observer_term_cost, score_observer, validate_observer,
)
from src.core.observer_synthesis_types import (
    ObserverCase, ObserverGrammar, ObserverPrimitive, ObserverTerm, SynthesisConfig,
)
from src.core.observer_synthesis_protocol import callable_identity, digest_value, evaluation_digest


def _grammar(*primitives, outputs=("scalar",), depth=2, cost=3):
    return ObserverGrammar("test", "input", outputs, tuple(primitives), depth, cost)


def _apply(name, kind="scalar"):
    return ObserverTerm("apply", kind, name, (ObserverTerm("input", "input"),))


def test_typed_enumeration_and_fingerprints_are_deterministic():
    grammar = _grammar(
        ObserverPrimitive("head", "input", "scalar", 1, lambda value: value[0], "head-v1"),
        ObserverPrimitive("mark", "scalar", "tag", 1, lambda value: ("mark", value), "mark-v1"),
        outputs=("scalar", "tag"),
    )
    first = enumerate_observer_terms(grammar)
    second = enumerate_observer_terms(grammar)
    assert first == second
    assert len({observer_fingerprint(term) for term in first}) == len(first)
    assert all(observer_term_cost(term, {p.name: p for p in grammar.primitives}) <= 3 for term in first)
    assert canonical_term(first[0]) == canonical_term(second[0])


def test_invalid_composition_is_rejected():
    primitive = ObserverPrimitive("head", "input", "scalar", 1, lambda value: value[0], "head-v1")
    invalid = ObserverTerm("apply", "scalar", "head", (ObserverTerm("input", "wrong"),))
    try:
        observer_term_cost(invalid, {"head": primitive})
    except ValueError as exc:
        assert str(exc) == "invalid-composition"
    else:
        raise AssertionError("invalid composition accepted")


def test_exception_and_noncanonical_results_become_obstructions():
    broken = ObserverPrimitive("broken", "input", "scalar", 1, lambda _value: 1 / 0, "broken-v1")
    listed = ObserverPrimitive("listed", "input", "scalar", 1, lambda _value: [1], "listed-v1")
    for primitive in (broken, listed):
        response = evaluate_observer(_apply(primitive.name), object(), {primitive.name: primitive})
        assert response.status == "blocked"
        assert response.obstruction.startswith("evaluation-error:")


def test_unexpected_obstruction_never_counts_as_separation():
    broken = ObserverPrimitive("broken", "input", "scalar", 1, lambda _value: 1 / 0, "broken-v1")
    grammar = _grammar(broken)
    separate = score_observer(_apply("broken"), (ObserverCase("s", "g", 1, 2, "separate"),), grammar, SynthesisConfig())
    blocked = score_observer(_apply("broken"), (ObserverCase("b", "h", 1, 2, "blocked-left", "ZeroDivisionError"),), grammar, SynthesisConfig())
    assert separate.fit == 0.0
    assert separate.evidence[0].reason == "unexpected-obstruction"
    assert blocked.fit == 1.0


def test_minimum_cost_wins_over_redundant_pair():
    parity = ObserverPrimitive("parity", "input", "scalar", 1, lambda value: value & 1, "parity-v1")
    grammar = _grammar(parity, outputs=("scalar", "pair"), depth=2, cost=3)
    fit = fit_observer(grammar, (ObserverCase("s", "g", 0, 1, "separate"),))
    assert fit.status == "ready"
    assert fit.winner is not None
    assert fit.winner.term == _apply("parity")
    assert all(row.complexity >= fit.winner.complexity for row in fit.alternatives)


def test_holdout_cannot_rerank_the_locked_train_winner():
    first = ObserverPrimitive("first", "input", "scalar", 1, lambda value: value[0], "first-v1")
    second = ObserverPrimitive("second", "input", "scalar", 1, lambda value: value[1], "second-v1")
    grammar = _grammar(first, second)
    fit = fit_observer(grammar, (ObserverCase("train", "train-group", (0, 0), (1, 1), "separate"),))
    assert fit.winner is not None
    chosen = fit.winner.term.primitive
    left, right = ((0, 0), (0, 1)) if chosen == "first" else ((0, 0), (1, 0))
    report = validate_observer(fit, grammar, (ObserverCase("hold", "hold-group", left, right, "separate"),))
    assert report.status == "blocked"
    assert report.winner_evaluation is not None
    assert report.winner_evaluation.term.primitive == chosen


def test_split_leakage_blocks_fit_and_validation():
    primitive = ObserverPrimitive("identity", "input", "scalar", 1, lambda value: value, "identity-v1")
    grammar = _grammar(primitive)
    duplicate = (ObserverCase("same", "g1", 0, 1, "separate"), ObserverCase("same", "g2", 2, 3, "separate"))
    assert fit_observer(grammar, duplicate).obstructions[0].reason == "split-leakage"
    fitted = fit_observer(grammar, (ObserverCase("train", "shared", 0, 1, "separate"),))
    report = validate_observer(fitted, grammar, (ObserverCase("hold", "shared", 2, 3, "separate"),))
    assert report.obstructions[0].reason == "split-leakage"
    payload_clone = validate_observer(fitted, grammar, (ObserverCase("renamed", "new-group", 1, 0, "separate"),))
    assert payload_clone.obstructions[0].reason == "split-leakage"
    relabelled_payload = validate_observer(fitted, grammar, (ObserverCase("renamed-2", "new-group-2", 0, 1, "echo"),))
    assert relabelled_payload.obstructions[0].reason == "split-leakage"


def test_holdout_cannot_change_protocol_config_or_primitive_semantics():
    primitive = ObserverPrimitive("identity", "input", "scalar", 1, lambda value: value, "identity-v1")
    grammar = _grammar(primitive)
    fitted = fit_observer(grammar, (ObserverCase("train", "g1", 0, 1, "separate"),))
    holdout = (ObserverCase("hold", "g2", 2, 3, "separate"),)
    changed_config = validate_observer(fitted, grammar, holdout, config=SynthesisConfig(complexity_penalty=0.2))
    changed_primitive = ObserverPrimitive("identity", "input", "scalar", 1, lambda _value: 0, "identity-v1")
    changed_grammar = _grammar(changed_primitive)
    changed_semantics = validate_observer(fitted, changed_grammar, holdout)
    assert changed_config.obstructions[0].reason == "protocol-mismatch"
    assert changed_semantics.obstructions[0].reason == "protocol-mismatch"



def _protocol_helper(value):
    return value


def _protocol_global_primitive(value):
    return _protocol_helper(value)


def test_protocol_digest_tracks_same_module_helper_semantics(monkeypatch):
    primitive = ObserverPrimitive("global", "input", "scalar", 1, _protocol_global_primitive, "global-v1")
    grammar = _grammar(primitive)
    before = evaluation_digest(grammar, (), SynthesisConfig())
    monkeypatch.setattr(sys.modules[__name__], "_protocol_helper", lambda _value: 0)
    after = evaluation_digest(grammar, (), SynthesisConfig())
    assert before != after


def test_callable_identity_structurally_binds_reducible_and_partial_callables():
    assert callable_identity(itemgetter(0), "getter-v1") != callable_identity(itemgetter(1), "getter-v1")
    assert callable_identity(partial(pow, 2), "power-v1") != callable_identity(partial(pow, 3), "power-v1")
    assert digest_value(b"a") != digest_value("61")


def test_posthoc_evaluator_replacement_is_protocol_mismatch():
    original = ObserverPrimitive("get", "input", "scalar", 1, itemgetter(0), "getter-v1")
    fitted = fit_observer(
        _grammar(original),
        (ObserverCase("train", "g1", (0, 9), (1, 9), "separate"),),
    )
    replacement = ObserverPrimitive("get", "input", "scalar", 1, itemgetter(1), "getter-v1")
    report = validate_observer(
        fitted,
        _grammar(replacement),
        (ObserverCase("hold", "g2", (4, 2), (4, 3), "separate"),),
    )
    assert report.obstructions[0].reason == "protocol-mismatch"


def test_missing_semantic_id_is_unbound_semantics():
    primitive = ObserverPrimitive("identity", "input", "scalar", 1, lambda value: value)
    fitted = fit_observer(_grammar(primitive), (ObserverCase("train", "g1", 0, 1, "separate"),))
    assert fitted.status == "blocked"
    assert fitted.obstructions[0].reason == "unbound-semantics"


def test_opaque_payload_requires_key_and_keyed_clone_is_split_leakage():
    Box = type("Box", (), {})
    left, right = Box(), Box()
    primitive = ObserverPrimitive("constant", "input", "scalar", 1, lambda _value: 0, "constant-v1")
    grammar = _grammar(primitive)
    unbound = fit_observer(grammar, (ObserverCase("opaque", "g0", left, right, "echo"),))
    assert unbound.obstructions[0].reason == "unbound-semantics"

    fitted = fit_observer(
        grammar,
        (ObserverCase("train", "g1", left, right, "echo", payload_key="box-pair-v1"),),
    )
    clone = validate_observer(
        fitted,
        grammar,
        (ObserverCase("hold", "g2", Box(), Box(), "echo", payload_key="box-pair-v1"),),
    )
    assert clone.obstructions[0].reason == "split-leakage"

def test_nondeterministic_evaluator_is_blocked():
    state = {"value": 0}
    def changing(_value):
        state["value"] += 1
        return state["value"]
    primitive = ObserverPrimitive("changing", "input", "scalar", 1, changing, "changing-v1")
    row = score_observer(_apply("changing"), (ObserverCase("n", "g", 1, 2, "separate"),), _grammar(primitive), SynthesisConfig(determinism_checks=3))
    assert row.fit == 0.0
    assert row.evidence[0].reason == "nondeterministic-evaluator"
