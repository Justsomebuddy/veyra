# ruff: noqa: F401,F403
"""Isolated public API for finite and symbolic prime-power reductions."""

import logging

from ...padic.completion.core import padic_tower_doctrine, prime_source
from .common import PrimePowerReductionValidationError
from .pressure import (
    path_pressure_candidate, refute_pressure_candidate,
    refute_wrong_path_candidate, refute_wrong_square_candidate,
    report_missing_symbolic_evidence, square_pressure_candidate,
)
from .runtime import prime_power_reduction_judgment
from .sources import (
    AXIOM_ROWS, THEOREM_IDS, exact_n1_theorem_source, finite_reduction_source,
    n2_ledger, n2_policy, reduction_network_package, theorem_source,
)
from .types import *
from .validation import (
    validate_n2_open, validate_n2_refutation, validate_prime_power_reduction_result,
)

logger = logging.getLogger(__name__)


def exact_reduction_network_package(p=2, depths=(0, 1, 2), **caps):
    """Build one canonical raw-only fixture; no prior judgment is accepted."""
    logger.debug("exact_reduction_network_package entry")
    prime = prime_source(p)
    doctrine = padic_tower_doctrine()
    finite = finite_reduction_source(prime, doctrine, depths)
    result = reduction_network_package(prime, doctrine, finite, exact_n1_theorem_source(),
        theorem_source(), n2_ledger(), n2_policy(**caps))
    logger.debug("exact_reduction_network_package exit")
    return result


__all__ = tuple(name for name in globals() if not name.startswith("_"))
