"""Linear resonance constraints over Veyra ratio shadows."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .ratio import RatioMode, add_ratios, multiply_ratios, ratio_from_fraction, ratio_from_ints, ratio_shadow, subtract_ratios

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LinearForm:
    """A one-variable form: coefficient·x plus offset."""

    coefficient: RatioMode
    offset: RatioMode


@dataclass(frozen=True)
class LinearEquation:
    """Equation between two linear forms."""

    left: LinearForm
    right: LinearForm


@dataclass(frozen=True)
class LinearSolution:
    """Result of solving a linear equation."""

    status: str
    value: RatioMode | None
    obstruction: str

    @property
    def solved(self) -> bool:
        """Return True iff there is a unique solution."""
        logger.debug("LinearSolution.solved entry status=%s", self.status)
        result = self.status == "unique"
        logger.debug("LinearSolution.solved exit result=%s", result)
        return result


def constant(value: int, denominator: int = 1) -> LinearForm:
    """Build constant linear form."""
    logger.debug("constant entry value=%d denominator=%d", value, denominator)
    zero = ratio_from_ints(0)
    result = LinearForm(zero, ratio_from_ints(value, denominator))
    logger.debug("constant exit result=%r", result)
    return result


def variable(coefficient: int = 1, offset: int = 0) -> LinearForm:
    """Build integer-coefficient variable form."""
    logger.debug("variable entry coefficient=%d offset=%d", coefficient, offset)
    result = LinearForm(ratio_from_ints(coefficient), ratio_from_ints(offset))
    logger.debug("variable exit result=%r", result)
    return result


def eval_linear(form: LinearForm, value: RatioMode) -> RatioMode:
    """Evaluate a linear form at a ratio value."""
    logger.debug("eval_linear entry form=%r value=%s", form, value.word)
    result = add_ratios(multiply_ratios(form.coefficient, value), form.offset)
    logger.debug("eval_linear exit result=%s", result.word)
    return result


def solve_linear(equation: LinearEquation) -> LinearSolution:
    """Solve a linear equation in the rational length-shadow layer."""
    logger.debug("solve_linear entry equation=%r", equation)
    coeff_gap = subtract_ratios(equation.left.coefficient, equation.right.coefficient)
    offset_gap = subtract_ratios(equation.right.offset, equation.left.offset)
    coeff_shadow = ratio_shadow(coeff_gap)
    offset_shadow = ratio_shadow(offset_gap)
    if coeff_shadow == 0 and offset_shadow == 0:
        result = LinearSolution("infinite", None, "identity")
    elif coeff_shadow == 0:
        result = LinearSolution("none", None, "parallel-obstruction")
    else:
        result = LinearSolution("unique", ratio_from_fraction(offset_shadow / coeff_shadow), "none")
    logger.debug("solve_linear exit result=%r", result)
    return result


def equation_residual(equation: LinearEquation, value: RatioMode) -> RatioMode:
    """Return left(value)-right(value) residual."""
    logger.debug("equation_residual entry equation=%r value=%s", equation, value.word)
    result = subtract_ratios(eval_linear(equation.left, value), eval_linear(equation.right, value))
    logger.debug("equation_residual exit result=%s", result.word)
    return result


def solution_satisfies(equation: LinearEquation, value: RatioMode) -> bool:
    """Return True iff value makes residual zero."""
    logger.debug("solution_satisfies entry equation=%r value=%s", equation, value.word)
    result = ratio_shadow(equation_residual(equation, value)) == 0
    logger.debug("solution_satisfies exit result=%s", result)
    return result
