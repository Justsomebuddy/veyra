"""Public exact surface for provisional P1-D1 productivity."""

from __future__ import annotations

import logging

from ..infinity_prefix import PrefixAlphabet
from .result_validation import (
    validate_construction_result, validate_restriction_result,
)
from .runtime import construct_at_depth, restriction_judgment
from .types import (
    ExecutionPolicy, PeriodicProgram, ProductiveProcessSource,
)
from .validation import (
    OUTPUT_ENCODING_ID, POLICY_VERSION, PROGRAM_VERSION, RESTRICTION_LAW_ID,
    TOTALITY_BASIS_ID, build_execution_policy, build_periodic_program,
    build_productive_source,
)

logger = logging.getLogger(__name__)


def periodic_program(
    alphabet: PrefixAlphabet, period: tuple[str, ...],
    version: str = PROGRAM_VERSION,
) -> PeriodicProgram:
    """Construct the sole closed nonempty periodic program grammar."""
    logger.debug("periodic_program entry")
    result = build_periodic_program(alphabet, period, version)
    logger.debug("periodic_program exit")
    return result


def execution_policy(
    max_depth: int, max_output_bytes: int, version: str = POLICY_VERSION,
) -> ExecutionPolicy:
    """Construct operational caps separate from generator identity."""
    logger.debug("execution_policy entry")
    result = build_execution_policy(max_depth, max_output_bytes, version)
    logger.debug("execution_policy exit")
    return result


def productive_process_source(
    program: PeriodicProgram, totality_basis_id: str,
    restriction_law_id: str, output_encoding_id: str,
    policy: ExecutionPolicy,
) -> ProductiveProcessSource:
    """Bind one structurally admitted generator to one execution policy."""
    logger.debug("productive_process_source entry")
    result = build_productive_source(
        program, totality_basis_id, restriction_law_id, output_encoding_id, policy
    )
    logger.debug("productive_process_source exit")
    return result


__all__ = [
    "OUTPUT_ENCODING_ID", "POLICY_VERSION", "PROGRAM_VERSION",
    "RESTRICTION_LAW_ID", "TOTALITY_BASIS_ID", "construct_at_depth",
    "execution_policy", "periodic_program", "productive_process_source",
    "restriction_judgment", "validate_construction_result",
    "validate_restriction_result",
]
