"""Focused classical residue-window tests for bounded I1."""

import logging

import pytest

import src.core as core
from src.core.padic_residue_tower import (
    add_padic_windows,
    first_padic_obstruction,
    integer_padic_window,
    multiply_padic_windows,
    padic_coherence_report,
    padic_residue_window,
    padic_residue_stage,
    prime_base,
    project_padic_stage,
)
from src.core.padic_residue_validation import PadicResidueValidationError

logger = logging.getLogger(__name__)


def test_p5_classical_residue_shadow_and_first_obstruction():
    logger.debug("test_p5_classical_residue_shadow_and_first_obstruction entry")
    base = prime_base(5)
    coherent = padic_residue_window(base, (2, 7, 57, 307))
    broken = padic_residue_window(base, (2, 8, 57))
    assert padic_coherence_report(coherent) == core.PadicCoherenceReport(5, 4, 3, True, None)
    obstruction = first_padic_obstruction(broken)
    assert obstruction == core.PadicCompatibilityObstruction(0, 1, 2, 3)
    assert padic_coherence_report(broken) == core.PadicCoherenceReport(5, 3, 1, False, obstruction)
    assert project_padic_stage(base, padic_residue_stage(base, 3, 307), 1).residue == 7
    logger.debug("test_p5_classical_residue_shadow_and_first_obstruction exit")


def test_componentwise_addition_and_multiplication_preserve_finite_coherence():
    logger.debug("test_componentwise_addition_and_multiplication_preserve_finite_coherence entry")
    base = prime_base(5)
    left = integer_padic_window(base, 307, 4)
    right = integer_padic_window(base, 18, 4)
    added = add_padic_windows(left, right)
    multiplied = multiply_padic_windows(left, right)
    assert tuple(stage.residue for stage in added.stages) == (0, 0, 75, 325)
    assert tuple(stage.residue for stage in multiplied.stages) == (1, 1, 26, 526)
    assert padic_coherence_report(added).coherent
    assert padic_coherence_report(multiplied).coherent
    logger.debug("test_componentwise_addition_and_multiplication_preserve_finite_coherence exit")


def test_incompatible_or_incoherent_residue_operations_are_rejected():
    logger.debug("test_incompatible_or_incoherent_residue_operations_are_rejected entry")
    coherent = padic_residue_window(prime_base(5), (2, 7, 57))
    broken = padic_residue_window(prime_base(5), (2, 8, 57))
    other_prime = integer_padic_window(prime_base(7), 2, 3)
    other_depth = integer_padic_window(prime_base(5), 2, 2)
    with pytest.raises(PadicResidueValidationError, match="coherent"):
        add_padic_windows(coherent, broken)
    with pytest.raises(PadicResidueValidationError, match="equal prime and depth"):
        add_padic_windows(coherent, other_prime)
    with pytest.raises(PadicResidueValidationError, match="equal prime and depth"):
        multiply_padic_windows(coherent, other_depth)
    logger.debug("test_incompatible_or_incoherent_residue_operations_are_rejected exit")


def test_i1_padic_public_api_is_exported_without_ready_layer_claim():
    logger.debug("test_i1_padic_public_api_is_exported_without_ready_layer_claim entry")
    expected = {
        "PrimeBase", "PadicResidueStage", "PadicResidueWindow",
        "PadicCompatibilityObstruction", "PadicCoherenceReport", "prime_base",
        "padic_residue_window", "integer_padic_window", "padic_residue_stage",
        "first_padic_obstruction", "padic_coherence_report", "project_padic_stage",
        "add_padic_windows", "multiply_padic_windows",
    }
    assert expected <= set(core.__all__)
    logger.debug("test_i1_padic_public_api_is_exported_without_ready_layer_claim exit")
