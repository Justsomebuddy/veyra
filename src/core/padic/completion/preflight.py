"""Atomic hard-first source accounting for PΩ2."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .common import reject
from .package import (
    HARD_PACKAGE_BYTES, HARD_SOURCE_BYTES, HARD_STATIC_COST, canonical_package_bytes,
)
from .types import PadicCompletionPackage, PadicFailedBound

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PadicPreflightCharge:
    captured_bytes: int
    package_bytes: int
    ledger_rows: int
    ledger_edges: int
    theorem_count: int
    static_cost: int


def preflight_charge(package: PadicCompletionPackage, generic: bytes) -> PadicPreflightCharge:
    """Validate every hard cap before caller policy refusal."""
    logger.debug("preflight_charge entry")
    if type(generic) is not bytes:
        reject("padic-preflight-generic-must-be-bytes")
    captured = len(generic) + len(package.prime.generated_witness_bytes)
    encoded = len(canonical_package_bytes(package))
    rows = len(package.ledger.rows)
    edges = sum(len(row.direct_dependencies) for row in package.ledger.rows)
    theorems = len(package.theorem_source.theorem_ids)
    static = captured + encoded + 256 * rows + 64 * edges + 512 * theorems
    if captured > HARD_SOURCE_BYTES or encoded > HARD_PACKAGE_BYTES:
        reject("padic-hard-source-or-package-limit")
    if rows > 128 or edges > 512 or theorems != 17 or static > HARD_STATIC_COST:
        reject("padic-hard-static-ledger-or-theorem-limit")
    result = PadicPreflightCharge(captured, encoded, rows, edges, theorems, static)
    logger.debug("preflight_charge exit static=%d", static)
    return result


def first_policy_failure(
    package: PadicCompletionPackage, charge: PadicPreflightCharge,
) -> tuple[PadicFailedBound, int, int] | None:
    """Apply CAPTURED_BYTES then STATIC_COST exact refusal priority."""
    logger.debug("first_policy_failure entry")
    if charge.captured_bytes > package.policy.max_captured_bytes:
        result = (PadicFailedBound.CAPTURED_BYTES, charge.captured_bytes, package.policy.max_captured_bytes)
    elif charge.static_cost > package.policy.max_static_cost:
        result = (PadicFailedBound.STATIC_COST, charge.static_cost, package.policy.max_static_cost)
    else:
        result = None
    logger.debug("first_policy_failure exit failed=%r", None if result is None else result[0])
    return result
