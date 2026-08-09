"""Direct level-1 certificate for isolated PΩ2 prime-power completion."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..padic.completion.core import (
    PadicCompletedCarrierStatus, PadicCompletionJudgment,
    PadicCompletionResourceLimit, bounded_padic_shadow,
    padic_completion_judgment, padic_completion_ledger, padic_completion_package,
    padic_completion_policy, padic_completion_theorem_source, padic_tower_doctrine,
    prime_source, validate_padic_completion_result,
)

logger = logging.getLogger(__name__)


def _package(p: int = 5, **policy_caps):
    """Build one exact source-only package without test imports."""
    logger.debug("_package entry p=%d", p)
    result = padic_completion_package(
        prime_source(p), padic_tower_doctrine(), padic_completion_theorem_source(),
        padic_completion_ledger(), padic_completion_policy(**policy_caps),
    )
    logger.debug("_package exit")
    return result


def certify_padic_completion_pomega2() -> Certificate:
    """Certify one ledger-relative PPCP and bounded shadows/nonclaims."""
    logger.debug("certify_padic_completion_pomega2 entry")
    package = _package()
    value = padic_completion_judgment(package)
    validated = validate_padic_completion_result(package, value)
    refusal = padic_completion_judgment(_package(max_captured_bytes=1))
    shadows = tuple(bounded_padic_shadow(p, 8) for p in (2, 3, 5))
    passed = (
        type(value) is PadicCompletionJudgment
        and type(validated) is PadicCompletionJudgment
        and validated is not value and validated.judgment_digest == value.judgment_digest
        and value.completed_carrier is PadicCompletedCarrierStatus.ESTABLISHED_RELATIVE_TO_LEDGER
        and value.canonical_ops_id == package.theorem_source.canonical_ops_id
        and value.concrete_instance_id == package.theorem_source.concrete_instance_id
        and type(refusal) is PadicCompletionResourceLimit
        and all(row.incompatible_first_failure == (0, 1) for row in shadows)
        and all(row.scope == "bounded-arithmetic-pressure-not-family-or-completion-evidence" for row in shadows)
        and not hasattr(package, "family") and not hasattr(package, "adapter")
    )
    detail = (
        "theorems=17 obligations=17 positive=1 resource=1 shadows=3 "
        "canonical_ops=1 concrete_instance=1 categorical=0 topology=0 physical=0 adapter=0"
    )
    result = Certificate(
        "padic_completion_pomega2",
        "pinned Lean PPCP, exact source/ledger closure, hostile replay, bounded residue QA",
        passed, detail, 1,
    )
    logger.debug("certify_padic_completion_pomega2 exit passed=%s", passed)
    return result


if __name__ == "__main__":
    print(certify_padic_completion_pomega2())
