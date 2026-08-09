from fractions import Fraction

from src.core.equation import LinearEquation, LinearForm, constant, equation_residual, eval_linear, solution_satisfies, solve_linear
from src.core.ratio import ratio_from_ints, ratio_shadow


def test_linear_equation_unique_integer_solution():
    equation = LinearEquation(
        LinearForm(ratio_from_ints(2), ratio_from_ints(3)),
        constant(7),
    )
    solution = solve_linear(equation)
    assert solution.solved
    assert solution.obstruction == "none"
    assert solution.value is not None
    assert ratio_shadow(solution.value) == 2
    assert solution_satisfies(equation, solution.value)


def test_linear_equation_unique_fraction_solution():
    equation = LinearEquation(
        LinearForm(ratio_from_ints(1, 2), ratio_from_ints(1, 3)),
        constant(5, 6),
    )
    solution = solve_linear(equation)
    assert solution.value is not None
    assert ratio_shadow(solution.value) == 1
    assert ratio_shadow(equation_residual(equation, solution.value)) == 0


def test_linear_equation_none_and_infinite_obstructions():
    no_solution = solve_linear(LinearEquation(
        LinearForm(ratio_from_ints(2), ratio_from_ints(1)),
        LinearForm(ratio_from_ints(2), ratio_from_ints(2)),
    ))
    identity = solve_linear(LinearEquation(
        LinearForm(ratio_from_ints(1), ratio_from_ints(1)),
        LinearForm(ratio_from_ints(1), ratio_from_ints(1)),
    ))
    assert no_solution.status == "none"
    assert no_solution.obstruction == "parallel-obstruction"
    assert identity.status == "infinite"
    assert identity.obstruction == "identity"


def test_eval_linear_shadow():
    form = LinearForm(ratio_from_ints(3, 2), ratio_from_ints(-1, 2))
    assert ratio_shadow(eval_linear(form, ratio_from_ints(2))) == Fraction(5, 2)
