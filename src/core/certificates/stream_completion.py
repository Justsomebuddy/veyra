"""Level-1 certificate for PΩ1.1–PΩ1.3 stream completion."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..construction.stream_completion.core import (
    AXIOM_CLOSURE, THEOREM_IDS, bounded_stream_shadow, stream_alphabet_source,
    stream_completion_doctrine, stream_completion_judgment,
    stream_completion_ledger, stream_completion_package, stream_completion_policy,
    stream_completion_theorem_source, validate_stream_completion_result,
)
from ..construction.stream_completion.formal import capture_generic_source
from ..construction.stream_completion.types import (
    CompletedCarrierStatus, CompletionFailedBound, ObligationStatus,
    StreamCompletionJudgment, StreamCompletionResourceLimit,
)

logger = logging.getLogger(__name__)


def certify_stream_completion_pomega1() -> Certificate:
    """Certify one positive carrier, one first-bound refusal, and finite shadows."""
    logger.debug("certify_stream_completion_pomega1 entry")
    doctrine = stream_completion_doctrine()
    alphabet = stream_alphabet_source(("0", "1", "λ"))
    theorem = stream_completion_theorem_source()
    ledger = stream_completion_ledger()
    policy = stream_completion_policy()
    package = stream_completion_package(doctrine, alphabet, theorem, ledger, policy)
    positive = stream_completion_judgment(package)
    validated = validate_stream_completion_result(package, positive)
    generic = capture_generic_source(theorem)
    required = len(generic) + len(package.alphabet_presentation.generated_instance_bytes)
    refusal_policy = stream_completion_policy(max_captured_bytes=required - 1)
    refusal_package = stream_completion_package(
        doctrine, alphabet, theorem, ledger, refusal_policy,
    )
    refusal = stream_completion_judgment(refusal_package)
    shadow0 = bounded_stream_shadow(alphabet, 0)
    shadow8 = bounded_stream_shadow(alphabet, 8)
    passed = (
        type(positive) is StreamCompletionJudgment and validated == positive
        and positive.completed_carrier is CompletedCarrierStatus.ESTABLISHED_RELATIVE_TO_LEDGER
        and positive.universal_realization is ObligationStatus.ESTABLISHED
        and positive.joint_separation is ObligationStatus.ESTABLISHED
        and positive.theorem_ids == THEOREM_IDS
        and positive.theorem_axiom_closure == AXIOM_CLOSURE
        and type(refusal) is StreamCompletionResourceLimit
        and refusal.failed_bound is CompletionFailedBound.CAPTURED_BYTES
        and refusal.required_value == required and refusal.allowed_value == required - 1
        and shadow0.finite_stream == shadow0.diagonal == ()
        and shadow8.finite_stream == shadow8.diagonal
        and len(shadow8.restrictions) == 9
    )
    result = Certificate(
        "stream_completion_pomega1",
        "completed Stream(Fin N) relative to exact SCP doctrine and ledger",
        passed,
        "theorems=15 obligations=11 positive=1 resource=1 shadows=2 physical=0 metaphysical=0",
        1,
    )
    logger.debug("certify_stream_completion_pomega1 exit passed=%s", passed)
    return result


if __name__ == "__main__":
    certificate = certify_stream_completion_pomega1()
    print(f"{certificate.name}: {'PASS' if certificate.passed else 'FAIL'} {certificate.detail}")
