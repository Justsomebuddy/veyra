import pytest
import random

from src.core.proof_core_substitution import (
    free_prop_indices, free_term_indices, instantiate_prop, shift_prop,
    shift_term, subst_prop,
)
from src.core.proof_core_types import (
    Bound, CoreType, Equal, Forall, Implies, Pulse, Resonates, Silence, Stitch,
    Weave,
)


def test_shift_walks_terms_and_respects_proposition_binders():
    assert shift_term(Stitch(Bound(0), Bound(1)), 2, 1) == Stitch(Bound(0), Bound(3))
    proposition = Forall(CoreType.RECURRENCE, Equal(Bound(0), Bound(1)))
    assert shift_prop(proposition, 1) == Forall(CoreType.RECURRENCE, Equal(Bound(0), Bound(2)))


def test_top_instantiation_is_capture_safe_beneath_a_nested_forall():
    body = Forall(CoreType.RECURRENCE, Equal(Bound(1), Bound(0)))
    instantiated = instantiate_prop(body, Bound(0))
    assert instantiated == Forall(CoreType.RECURRENCE, Equal(Bound(1), Bound(0)))
    assert free_prop_indices(instantiated) == frozenset({0})


def test_substitution_traverses_every_proposition_constructor():
    source = Implies(
        Resonates(Bound(0), Pulse(Bound(0))),
        Equal(Bound(0), Silence()),
    )
    expected = Implies(
        Resonates(Pulse(Silence()), Pulse(Pulse(Silence()))),
        Equal(Pulse(Silence()), Silence()),
    )
    assert subst_prop(source, 0, Pulse(Silence())) == expected


def test_free_indices_distinguish_bound_and_outer_variables():
    assert free_term_indices(Stitch(Bound(0), Bound(2)), depth=1) == frozenset({1})
    proposition = Forall(CoreType.RECURRENCE, Equal(Bound(0), Bound(2)))
    assert free_prop_indices(proposition) == frozenset({1})


@pytest.mark.parametrize("bad", [-1, True, 1.5])
def test_invalid_indices_are_rejected(bad):
    with pytest.raises((TypeError, ValueError)):
        shift_term(Bound(bad), 1)


@pytest.mark.parametrize("bad", [True, 1.5])
def test_non_integer_shift_deltas_are_rejected(bad):
    with pytest.raises((TypeError, ValueError)):
        shift_term(Silence(), bad)


def test_removing_a_binder_cannot_produce_a_negative_free_index():
    with pytest.raises(ValueError, match="negative"):
        shift_term(Bound(0), -1)


def _term(rng, arity, depth):
    choices = [Silence()]
    if arity:
        choices.append(Bound(rng.randrange(arity)))
    if depth:
        left, right = _term(rng, arity, depth - 1), _term(rng, arity, depth - 1)
        choices += [Pulse(left), Stitch(left, right), Weave(left, right)]
    return rng.choice(choices)


def _prop(rng, arity, depth):
    left, right = _term(rng, arity, 2), _term(rng, arity, 2)
    choices = [Equal(left, right), Resonates(left, right)]
    if depth:
        choices += [
            Implies(_prop(rng, arity, depth - 1), _prop(rng, arity, depth - 1)),
            Forall(CoreType.RECURRENCE, _prop(rng, arity + 1, depth - 1)),
        ]
    return rng.choice(choices)


def _eval_term(term, env):
    if type(term) is Bound:
        return env[term.index]
    if type(term) is Silence:
        return 0
    if type(term) is Pulse:
        return 1 + _eval_term(term.tail, env)
    if type(term) is Stitch:
        return _eval_term(term.left, env) + _eval_term(term.right, env)
    return _eval_term(term.left, env) * _eval_term(term.right, env)


def _eval_prop(prop, env):
    if type(prop) is Equal:
        return _eval_term(prop.left, env) == _eval_term(prop.right, env)
    if type(prop) is Resonates:
        return _eval_term(prop.factor, env) <= _eval_term(prop.carrier, env)
    if type(prop) is Implies:
        return not _eval_prop(prop.premise, env) or _eval_prop(prop.conclusion, env)
    return all(_eval_prop(prop.body, (value,) + env) for value in range(3))


def test_seeded_nested_binder_instantiation_semantics_property():
    rng = random.Random(7004)
    for _ in range(2000):
        arity = rng.randrange(4)
        environment = tuple(rng.randrange(4) for _ in range(arity))
        argument = _term(rng, arity, 3)
        body = _prop(rng, arity + 1, 3)
        instantiated = instantiate_prop(body, argument)
        expected_env = (_eval_term(argument, environment),) + environment
        assert _eval_prop(instantiated, environment) == _eval_prop(body, expected_env)
