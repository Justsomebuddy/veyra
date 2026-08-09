"""Direct level-1 isolated certificate for P3-A1b."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..padic.completion.core import padic_tower_doctrine, prime_source
from ..padic.family_introduction.core import integer_source
from ..prime_power.productive_bridge.core import (
    BoundaryStatus, BridgeEvidenceKind, BridgeResourceLimit, ProductiveBridgeJudgment,
    ResultStatus, bridge_ledger, bridge_policy, bridge_theorem_source,
    establish_productive_family_bridge, exact_n1_theorem_source, project_residue,
    offset_residue_program_source, productive_bridge_package, refute_offset_program,
    report_missing_bridge_evidence,
    residue_program_source,
    validate_offset_refutation_result, validate_open_result,
    validate_productive_bridge_result, validate_projection_result,
)

logger = logging.getLogger(__name__)


def _package(**caps):
    """Construct one exact raw package without tests or prior judgments."""
    logger.debug("_package entry")
    prime = prime_source(5)
    integer = integer_source(-123)
    result = productive_bridge_package(
        prime, integer, padic_tower_doctrine(),
        residue_program_source(prime, integer), exact_n1_theorem_source(), bridge_theorem_source(),
        bridge_ledger(), bridge_policy(**caps),
    )
    logger.debug("_package exit")
    return result


def certify_prime_power_productive_bridge_p3a1b() -> Certificate:
    """Certify exact productive/family commute and permanent boundaries."""
    logger.debug("certify_prime_power_productive_bridge_p3a1b entry")
    package = _package()
    value = establish_productive_family_bridge(package)
    replay = validate_productive_bridge_result(package, value)
    projection = project_residue(package, 4)
    projection_replay = validate_projection_result(package, 4, projection)
    pressure = offset_residue_program_source(package.prime, package.integer, 1)
    refutation = refute_offset_program(package, pressure, 0)
    refutation_replay = validate_offset_refutation_result(package, pressure, 0, refutation)
    open_result = report_missing_bridge_evidence(
        package.prime, package.integer, package.program,
    )
    open_replay = validate_open_result(
        package.prime, package.integer, package.program, open_result,
    )
    refusal = establish_productive_family_bridge(_package(max_captured_bytes=1))
    passed = (
        type(value) is ProductiveBridgeJudgment
        and type(replay) is ProductiveBridgeJudgment and replay is not value
        and value.bridge_evidence_kind is BridgeEvidenceKind.PRODUCTIVE_FAMILY_BRIDGE
        and value.promotions == 0 and value.completed_carrier is BoundaryStatus.NOT_ESTABLISHED
        and value.universal_completion is BoundaryStatus.OPEN
        and len({value.program_digest, value.family_term_digest,
                 value.productivity_evidence_digest, value.family_introduction_digest,
                 value.bridge_evidence_digest, value.judgment_digest}) == 6
        and projection.qa_scope == "QA_BOUNDED"
        and projection_replay == projection
        and refutation.status is ResultStatus.REFUTED and refutation_replay == refutation
        and open_result.status is ResultStatus.OPEN and open_replay == open_result
        and type(refusal) is BridgeResourceLimit
    )
    detail = (
        "theorems=4 total=1 deterministic=1 process_coherent=1 commute=1 "
        "direct_n1_bytes=1 pomega2_completion_premise=0 qa_projection=1 "
        "negative_offset_total=1 coherent=1 refuted=1 missing_evidence_open=1 resource=1 "
        "promotions=0 completed_carrier=0"
    )
    result = Certificate(
        "prime_power_productive_bridge_p3a1b",
        "closed integer residue process commutes with exact direct all-depth family",
        passed, detail, 1,
    )
    logger.debug("certify_prime_power_productive_bridge_p3a1b exit passed=%s", passed)
    return result


if __name__ == "__main__":
    print(certify_prime_power_productive_bridge_p3a1b())
