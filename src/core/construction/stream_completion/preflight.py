"""Hard-first resource accounting for PΩ1."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .common import reject
from .package import (
    HARD_PACKAGE_BYTES, HARD_SOURCE_BYTES, HARD_STATIC_COST, canonical_package_bytes,
)
from .types import CompletionFailedBound, StreamCompletionPackage

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PreflightCharge:
    captured_bytes: int
    package_bytes: int
    ledger_rows: int
    ledger_edges: int
    theorem_count: int
    static_cost: int


def preflight_charge(package: StreamCompletionPackage, generic: bytes) -> PreflightCharge:
    """Validate every hard cap before considering caller policy refusal."""
    logger.debug("preflight_charge entry")
    if type(generic) is not bytes:
        reject("preflight-generic-must-be-bytes")
    captured = len(generic) + len(package.alphabet_presentation.generated_instance_bytes)
    encoded = len(canonical_package_bytes(package))
    rows = len(package.ledger.rows)
    edges = sum(len(row.direct_dependencies) for row in package.ledger.rows)
    theorems = len(package.theorem_source.theorem_ids)
    static = captured + encoded + 256 * rows + 64 * edges + 512 * theorems
    if captured > HARD_SOURCE_BYTES:
        reject("hard-captured-source-limit-exceeded")
    if encoded > HARD_PACKAGE_BYTES:
        reject("hard-package-encoding-limit-exceeded")
    if rows > 128 or edges > 512 or theorems != 15:
        reject("hard-ledger-or-theorem-limit-exceeded")
    if static > HARD_STATIC_COST:
        reject("hard-static-cost-limit-exceeded")
    result = PreflightCharge(captured, encoded, rows, edges, theorems, static)
    logger.debug("preflight_charge exit static=%d", static)
    return result


def first_policy_failure(
    package: StreamCompletionPackage, charge: PreflightCharge,
) -> tuple[CompletionFailedBound, int, int] | None:
    """Apply exact priority CAPTURED_BYTES then STATIC_COST after hard validity."""
    logger.debug("first_policy_failure entry")
    policy = package.policy
    if charge.captured_bytes > policy.max_captured_bytes:
        result = (
            CompletionFailedBound.CAPTURED_BYTES,
            charge.captured_bytes, policy.max_captured_bytes,
        )
    elif charge.static_cost > policy.max_static_cost:
        result = (
            CompletionFailedBound.STATIC_COST,
            charge.static_cost, policy.max_static_cost,
        )
    else:
        result = None
    logger.debug("first_policy_failure exit failed=%s", None if result is None else result[0].value)
    return result
