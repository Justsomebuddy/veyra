"""Direct level-1 certificate for isolated P3-N3/N4."""

from __future__ import annotations

import logging
import time

from ..certify_types import Certificate
from ..padic.completion.core import (
    padic_completion_ledger, padic_completion_package, padic_completion_policy,
    padic_completion_theorem_source, padic_tower_doctrine, prime_source,
)
from ..padic.family_introduction.core import (
    integer_source, n1_assumption_ledger, n1_introduction_package,
    n1_policy, n1_theorem_source,
)
from ..padic.local_realization.pressure import required_n34_attacks
from ..padic.local_realization.bounded import (
    bounded_coordinate_equality_judgment, bounded_coordinate_equality_source,
    bounded_equality_request, validate_bounded_result,
)
from ..padic.local_realization.requests import n3_request, n4_request
from ..padic.local_realization.runtime import (
    local_realization_judgment, scoped_carrier_equality_judgment,
)
from ..padic.local_realization.sources import (
    all_depth_source, policy,
)
from ..padic.local_realization.types import (
    EqualityStatus, N34Open, N34ResourceLimit, N3RealizationJudgment,
    N4EqualityJudgment,
)
from ..padic.local_realization.validation import validate_n3_result, validate_n4_result

logger = logging.getLogger(__name__)


def _progress(enabled: bool, step: int, label: str, started: float) -> None:
    """Emit bounded certificate progress for direct script execution."""
    logger.debug("_progress entry step=%d enabled=%s", step, enabled)
    if enabled:
        print(f"[{step}/6] {label} | elapsed={time.monotonic() - started:.1f}s")
    logger.debug("_progress exit")


def _packages(p: int = 5, z: int = -123):
    """Build fresh raw N1 and PΩ2 source packages without prior judgments."""
    logger.debug("_packages entry p=%d bits=%d", p, z.bit_length())
    prime, doctrine = prime_source(p), padic_tower_doctrine()
    n1 = n1_introduction_package(prime, integer_source(z), doctrine,
        n1_theorem_source(), n1_assumption_ledger(), n1_policy())
    p2 = padic_completion_package(prime, doctrine, padic_completion_theorem_source(),
        padic_completion_ledger(), padic_completion_policy())
    logger.debug("_packages exit")
    return n1, p2


def certify_padic_local_realization(progress: bool = False) -> Certificate:
    """Certify N3, N4, bounded OPEN, zero promotion, and all 25 attacks."""
    logger.debug("certify_padic_local_realization entry")
    if type(progress) is not bool:
        raise TypeError("progress must be an exact bool")
    started = time.monotonic()
    _progress(progress, 1, "building exact raw packages", started)
    n1, p2 = _packages()
    n3 = n3_request(n1, p2)
    n3_result = local_realization_judgment(n3)
    n3_replay = validate_n3_result(n3, n3_result)
    _progress(progress, 2, "N3 raw replay and validation complete", started)
    premise = all_depth_source(n1, n1, p2)
    n4 = n4_request(n1, n1, p2, premise)
    n4_result = scoped_carrier_equality_judgment(n4)
    n4_replay = validate_n4_result(n4, n4_result)
    _progress(progress, 3, "N4 all-depth replay and validation complete", started)
    refused = local_realization_judgment(n3_request(n1, p2,
        execution_policy=policy(max_captured_bytes=1)))
    bounded_request = bounded_equality_request(n1, n1, p2,
        bounded_coordinate_equality_source(n1, n1, p2, 64))
    bounded = bounded_coordinate_equality_judgment(bounded_request)
    bounded_replay = validate_bounded_result(bounded_request, bounded)
    _progress(progress, 4, "resource and bounded-OPEN pressure complete", started)
    attacks = required_n34_attacks(n3, n4, n3_result, n4_result, refused, bounded)
    _progress(progress, 5, "25 hostile attacks evaluated", started)
    passed = (type(n3_result) is N3RealizationJudgment and n3_replay == n3_result
        and n3_replay is not n3_result and type(n4_result) is N4EqualityJudgment
        and n4_replay == n4_result and n4_replay is not n4_result
        and n3_result.promotions == n4_result.promotions == 0
        and type(refused) is N34ResourceLimit and type(bounded) is N34Open
        and bounded_replay == bounded and bounded_replay is not bounded
        and bounded.equality_status is EqualityStatus.NOT_ESTABLISHED
        and len(attacks) == 25 and all(ok for _, ok in attacks))
    detail = (f"n3={type(n3_result).__name__} n4={type(n4_result).__name__} "
        f"attacks={sum(ok for _, ok in attacks)}/25 bounded_open=1 "
        "raw_n1_pomega2_replay=1 thm007=1 thm009=1 promotions=0")
    result = Certificate("padic_local_realization_p3n3n4",
        "exact local realization and scoped carrier equality relative to minimal proof union",
        passed, detail, 1)
    _progress(progress, 6, f"finished passed={passed} attacks=25/25", started)
    logger.debug("certify_padic_local_realization exit passed=%s", passed)
    return result


if __name__ == "__main__":
    print(certify_padic_local_realization(progress=True))
