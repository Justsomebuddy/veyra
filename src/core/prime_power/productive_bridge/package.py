"""Deep raw package replay and hard-first charging for P3-A1b."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from ...padic.completion.common import PadicCompletionValidationError
from ...padic.completion.doctrine import snapshot_doctrine
from ...padic.completion.prime import snapshot_prime
from ...padic.family_introduction.sources import snapshot_integer, snapshot_theorem as snapshot_n1
from .common import digest, exact_digest, exact_int, exact_shape, reject
from .sources import (
    HARD_SOURCE_BYTES, HARD_STATIC_COST, bridge_ledger, bridge_policy,
    snapshot_ledger, snapshot_policy, snapshot_program, snapshot_theorem,
)
from .types import (
    BridgeLedger, BridgePolicy, BridgeTheoremSource, FailedBound,
    ProductiveBridgePackage, ResidueProgramSource,
)

logger = logging.getLogger(__name__)
HARD_PACKAGE_BYTES = 4 * 1024 * 1024


@dataclass(frozen=True)
class PreflightCharge:
    captured_bytes: int
    package_bytes: int
    requested_depth: int
    output_bound: int
    static_cost: int


def _package_digest(prime, integer, doctrine, program, n1, theorem, ledger, policy) -> str:
    """Bind p/z, exact program, direct family source, bridge, doctrine, and caps."""
    logger.debug("_package_digest entry")
    result = digest("veyra.p3a1b.package.v1", (
        ("prime", prime.source_digest.encode()), ("integer", integer.source_digest.encode()),
        ("doctrine", doctrine.doctrine_digest.encode()), ("stage", doctrine.stage_id.encode()),
        ("reduction", doctrine.reduction_id.encode()), ("family", doctrine.family_class_id.encode()),
        ("program", program.program_digest.encode()), ("n1", n1.source_digest.encode()),
        ("bridge", theorem.source_digest.encode()), ("ledger", ledger.ledger_digest.encode()),
        ("policy", policy.policy_digest.encode()),
    ))
    logger.debug("_package_digest exit")
    return result


def productive_bridge_package(prime, integer, doctrine, program: ResidueProgramSource,
                              n1_theorem, theorem: BridgeTheoremSource,
                              ledger: BridgeLedger, policy: BridgePolicy) -> ProductiveBridgePackage:
    """Build one raw-only package; no N1/PΩ judgment or certificate is accepted."""
    logger.debug("productive_bridge_package entry")
    try:
        p = snapshot_prime(prime)
        d = snapshot_doctrine(doctrine)
    except PadicCompletionValidationError:
        reject("prime-or-doctrine-invalid")
    z = snapshot_integer(integer)
    g = snapshot_program(program)
    if g.prime_digest != p.source_digest or g.integer_digest != z.source_digest:
        reject("closed-program-p-or-z-binding-mismatch")
    family = snapshot_n1(n1_theorem)
    theorem_value = snapshot_theorem(theorem)
    if family.artifact_sha256 != theorem_value.n1_artifact_sha256:
        reject("n1-continuity-identity-mismatch")
    ledger_value = snapshot_ledger(ledger)
    policy_value = snapshot_policy(policy)
    result = ProductiveBridgePackage(
        p, z, d, g, family, theorem_value, ledger_value, policy_value,
        _package_digest(p, z, d, g, family, theorem_value, ledger_value, policy_value),
    )
    logger.debug("productive_bridge_package exit")
    return result


def snapshot_package(value: ProductiveBridgePackage) -> ProductiveBridgePackage:
    """Deeply replay all raw commitments before file IO or semantics."""
    logger.debug("snapshot_package entry")
    raw = exact_shape(value, ProductiveBridgePackage, "bridge-package")
    try:
        exact_digest(raw["package_digest"], "package-digest")
        expected = productive_bridge_package(
            raw["prime"], raw["integer"], raw["doctrine"], raw["program"], raw["n1_theorem"],
            raw["theorem"], raw["ledger"], raw["policy"],
        )
    except AttributeError:
        reject("bridge-package-fields-missing")
    if value != expected:
        reject("bridge-package-drift")
    logger.debug("snapshot_package exit")
    return expected


def canonical_package_bytes(value: ProductiveBridgePackage) -> bytes:
    """Encode every raw source identity without hostile object serialization."""
    logger.debug("canonical_package_bytes entry")
    value = snapshot_package(value)
    rows = (
        ("prime", value.prime.source_digest.encode()),
        ("integer", value.integer.source_digest.encode()),
        ("doctrine", value.doctrine.doctrine_digest.encode()),
        ("program", value.program.program_digest.encode()),
        ("n1", value.n1_theorem.source_digest.encode()),
        ("theorem", value.theorem.source_digest.encode()),
        ("ledger", value.ledger.ledger_digest.encode()),
        ("policy", value.policy.policy_digest.encode()),
    )
    result = b"".join(
        len(a.encode()).to_bytes(8, "big") + a.encode() + len(b).to_bytes(8, "big") + b
        for a, b in rows
    )
    logger.debug("canonical_package_bytes exit bytes=%d", len(result))
    return result


def preflight_charge(package: ProductiveBridgePackage, captured: tuple[bytes, ...], depth: int = 1,
                     bound_source: bytes = b"", expected_sources: int = 4) -> PreflightCharge:
    """Charge nested exact bytes, structures, request, and output before semantics."""
    logger.debug("preflight_charge entry depth_type=%s", type(depth).__name__)
    expected = exact_int(expected_sources, "expected-source-count")
    if (type(captured) is not tuple or len(captured) != expected
            or any(type(x) is not bytes for x in captured) or type(bound_source) is not bytes):
        reject("captured-source-shape-invalid")
    requested = exact_int(depth, "projection-depth")
    if requested < 0:
        reject("projection-depth-invalid")
    source_bytes = sum(len(x) for x in captured)
    package_bytes = len(canonical_package_bytes(package)) + len(bound_source)
    static = source_bytes + package_bytes + 256 * len(package.ledger.ordered_rows) + 64 * len(package.ledger.direct_edges)
    if source_bytes > HARD_SOURCE_BYTES or package_bytes > HARD_PACKAGE_BYTES or static > HARD_STATIC_COST:
        reject("hard-resource-limit")
    result = PreflightCharge(source_bytes, package_bytes, requested, package.policy.max_output_bytes, static)
    logger.debug("preflight_charge exit static=%d", static)
    return result


def first_policy_failure(package: ProductiveBridgePackage, charge: PreflightCharge):
    """Return the first typed refusal under a fixed priority."""
    logger.debug("first_policy_failure entry")
    checks = (
        (FailedBound.CAPTURED_BYTES, charge.captured_bytes, package.policy.max_captured_bytes),
        (FailedBound.STATIC_COST, charge.static_cost, package.policy.max_static_cost),
        (FailedBound.REQUESTED_DEPTH, charge.requested_depth, package.policy.max_depth),
    )
    result = next((row for row in checks if row[1] > row[2]), None)
    logger.debug("first_policy_failure exit failed=%s", None if result is None else result[0].value)
    return result


__all__ = [
    "PreflightCharge", "bridge_ledger", "bridge_policy", "canonical_package_bytes",
    "first_policy_failure", "preflight_charge", "productive_bridge_package", "snapshot_package",
]
