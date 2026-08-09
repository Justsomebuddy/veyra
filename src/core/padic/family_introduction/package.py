"""Exact N1 ledger, policy, package construction, and hard preflight."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from ..completion.common import PadicCompletionValidationError
from ..completion.doctrine import snapshot_doctrine
from ..completion.prime import snapshot_prime
from .common import digest, exact_digest, exact_shape, frame, reject
from .sources import (
    AXIOM_CLOSURE, HARD_SOURCE_BYTES, HARD_STATIC_COST, LEDGER_EDGES, LEDGER_ROWS,
    LEDGER_DIGEST_ORACLE, LEDGER_VERSION, PACKAGE_VERSION, POLICY_VERSION,
    snapshot_integer, snapshot_theorem,
)
from .types import (
    IntegerSource, N1AssumptionLedger, N1FailedBound, N1IntroductionPackage,
    N1Policy, N1TheoremSource,
)
from ..completion.types import PadicTowerDoctrine, PrimeSource

logger = logging.getLogger(__name__)
HARD_PACKAGE_BYTES = 4 * 1024 * 1024


@dataclass(frozen=True)
class N1PreflightCharge:
    captured_bytes: int
    package_bytes: int
    ledger_rows: int
    ledger_edges: int
    theorem_count: int
    static_cost: int


def n1_assumption_ledger() -> N1AssumptionLedger:
    """Construct the exact acyclic used-source ledger; completion is absent."""
    logger.debug("n1_assumption_ledger entry")
    encoded_edges = tuple((f"edge-{i}", f"{a}\0{b}".encode()) for i, (a, b) in enumerate(LEDGER_EDGES))
    value = digest("veyra.p3n1.ledger.v1", (
        ("version", LEDGER_VERSION.encode()),
        *((f"row-{i}", row.encode()) for i, row in enumerate(LEDGER_ROWS)),
        *encoded_edges, *(("axiom", row.encode()) for row in AXIOM_CLOSURE),
    ))
    if value != LEDGER_DIGEST_ORACLE:
        logger.error("n1_assumption_ledger oracle drift")
        raise RuntimeError("internal P3-N1 ledger oracle drift")
    result = N1AssumptionLedger(LEDGER_VERSION, LEDGER_ROWS, LEDGER_EDGES, AXIOM_CLOSURE, value)
    logger.debug("n1_assumption_ledger exit rows=%d edges=%d", len(LEDGER_ROWS), len(LEDGER_EDGES))
    return result


def snapshot_ledger(value: N1AssumptionLedger) -> N1AssumptionLedger:
    """Reject alternate/circular ledgers and hidden completion dependencies."""
    logger.debug("snapshot_ledger entry")
    exact_shape(value, N1AssumptionLedger, "n1-ledger")
    try:
        if type(value.ordered_rows) is not tuple or type(value.direct_edges) is not tuple:
            reject("n1-ledger-container-invalid")
        if any(type(x) is not str for x in (*value.ordered_rows, *value.theorem_axiom_closure)):
            reject("n1-ledger-row-type-invalid")
        if any(type(e) is not tuple or len(e) != 2 or any(type(x) is not str for x in e) for e in value.direct_edges):
            reject("n1-ledger-edge-type-invalid")
        exact_digest(value.ledger_digest, "n1-ledger-digest")
    except AttributeError:
        reject("n1-ledger-missing-fields")
    expected = n1_assumption_ledger()
    if value != expected:
        reject("n1-ledger-drift")
    positions = {name: i for i, name in enumerate(value.ordered_rows)}
    if len(positions) != len(value.ordered_rows):
        reject("n1-ledger-duplicate-row")
    if any(a not in positions or b not in positions or positions[b] >= positions[a] for a, b in value.direct_edges):
        reject("n1-ledger-forward-missing-or-cycle")
    logger.debug("snapshot_ledger exit")
    return expected


def n1_policy(
    max_captured_bytes: int = HARD_SOURCE_BYTES, max_static_cost: int = HARD_STATIC_COST,
    compile_timeout_seconds: int = 120, max_output_bytes: int = 1024 * 1024,
) -> N1Policy:
    """Construct exact hard-bounded compilation policy."""
    logger.debug("n1_policy entry")
    values = (max_captured_bytes, max_static_cost, compile_timeout_seconds, max_output_bytes)
    if any(type(x) is not int for x in values):
        reject("n1-policy-exact-integers-required")
    if not 1 <= max_captured_bytes <= HARD_SOURCE_BYTES or not 1 <= max_static_cost <= HARD_STATIC_COST:
        reject("n1-policy-source-or-static-invalid")
    if not 1 <= compile_timeout_seconds <= 300 or not 1 <= max_output_bytes <= 4 * 1024 * 1024:
        reject("n1-policy-time-or-output-invalid")
    value = digest("veyra.p3n1.policy.v1", (
        ("version", POLICY_VERSION.encode()),
        *((f"value-{i}", x.to_bytes(8, "big")) for i, x in enumerate(values)),
    ))
    result = N1Policy(POLICY_VERSION, *values, value)
    logger.debug("n1_policy exit")
    return result


def snapshot_policy(value: N1Policy) -> N1Policy:
    """Reject policy subclasses, Boolean caps, and digest drift."""
    logger.debug("snapshot_policy entry")
    exact_shape(value, N1Policy, "n1-policy")
    try:
        expected = n1_policy(value.max_captured_bytes, value.max_static_cost,
                             value.compile_timeout_seconds, value.max_output_bytes)
        exact_digest(value.policy_digest, "n1-policy-digest")
    except AttributeError:
        reject("n1-policy-missing-fields")
    if value != expected:
        reject("n1-policy-drift")
    logger.debug("snapshot_policy exit")
    return expected


def _package_digest(prime, integer, doctrine, theorem, ledger, policy) -> str:
    """Bind exact p, z, tower/doctrine IDs, theorem, ledger, and policy."""
    logger.debug("_package_digest entry")
    result = digest("veyra.p3n1.package.v1", (
        ("version", PACKAGE_VERSION.encode()), ("prime", prime.source_digest.encode()),
        ("integer", integer.source_digest.encode()), ("doctrine", doctrine.doctrine_digest.encode()),
        ("stage", doctrine.stage_id.encode()), ("reduction", doctrine.reduction_id.encode()),
        ("family-class", doctrine.family_class_id.encode()), ("carrier", doctrine.carrier_id.encode()),
        ("theorem", theorem.source_digest.encode()), ("ledger", ledger.ledger_digest.encode()),
        ("policy", policy.policy_digest.encode()),
    ))
    logger.debug("_package_digest exit")
    return result


def n1_introduction_package(
    prime: PrimeSource, integer: IntegerSource, doctrine: PadicTowerDoctrine,
    theorem: N1TheoremSource, ledger: N1AssumptionLedger, policy: N1Policy,
) -> N1IntroductionPackage:
    """Build one raw N1 package; prior judgments/certificates have no lane."""
    logger.debug("n1_introduction_package entry")
    try:
        p = snapshot_prime(prime)
        d = snapshot_doctrine(doctrine)
    except PadicCompletionValidationError:
        reject("n1-prime-or-doctrine-invalid")
    z = snapshot_integer(integer)
    theorem_value = snapshot_theorem(theorem)
    ledger_value = snapshot_ledger(ledger)
    policy_value = snapshot_policy(policy)
    result = N1IntroductionPackage(
        p, z, d, theorem_value, ledger_value, policy_value,
        _package_digest(p, z, d, theorem_value, ledger_value, policy_value),
    )
    logger.debug("n1_introduction_package exit")
    return result


def snapshot_package(value: N1IntroductionPackage) -> N1IntroductionPackage:
    """Deeply capture exact raw inputs before file IO or semantic work."""
    logger.debug("snapshot_package entry")
    exact_shape(value, N1IntroductionPackage, "n1-package")
    try:
        expected = n1_introduction_package(
            value.prime, value.integer, value.doctrine, value.theorem_source,
            value.ledger, value.policy,
        )
        exact_digest(value.package_digest, "n1-package-digest")
    except AttributeError:
        reject("n1-package-missing-fields")
    if value != expected:
        reject("n1-package-drift")
    logger.debug("snapshot_package exit")
    return expected


def canonical_package_bytes(value: N1IntroductionPackage) -> bytes:
    """Encode all exact raw commitments, excluding no source identity."""
    logger.debug("canonical_package_bytes entry")
    value = snapshot_package(value)
    result = frame("veyra.p3n1.package-encoding.v1", tuple(
        (name, getattr(value, name).source_digest.encode())
        for name in ("prime", "integer", "theorem_source")
    ) + (("doctrine", value.doctrine.doctrine_digest.encode()),
         ("ledger", value.ledger.ledger_digest.encode()),
         ("policy", value.policy.policy_digest.encode())))
    logger.debug("canonical_package_bytes exit bytes=%d", len(result))
    return result


def preflight_charge(package: N1IntroductionPackage, captured: tuple[bytes, ...]) -> N1PreflightCharge:
    """Charge all raw bytes and structures under immutable hard limits first."""
    logger.debug("preflight_charge entry")
    if type(captured) is not tuple or len(captured) != 3 or any(type(x) is not bytes for x in captured):
        reject("n1-captured-source-shape-invalid")
    source_bytes = sum(len(x) for x in captured)
    package_bytes = len(canonical_package_bytes(package))
    static = source_bytes + package_bytes + 256 * len(package.ledger.ordered_rows) + 64 * len(package.ledger.direct_edges)
    if source_bytes > HARD_SOURCE_BYTES or package_bytes > HARD_PACKAGE_BYTES or static > HARD_STATIC_COST:
        reject("n1-hard-resource-limit")
    result = N1PreflightCharge(source_bytes, package_bytes, len(package.ledger.ordered_rows),
                               len(package.ledger.direct_edges), len(package.theorem_source.theorem_ids), static)
    logger.debug("preflight_charge exit static=%d", static)
    return result


def first_policy_failure(package: N1IntroductionPackage, charge: N1PreflightCharge):
    """Apply captured-byte then static-cost refusal priority."""
    logger.debug("first_policy_failure entry")
    if charge.captured_bytes > package.policy.max_captured_bytes:
        result = (N1FailedBound.CAPTURED_BYTES, charge.captured_bytes, package.policy.max_captured_bytes)
    elif charge.static_cost > package.policy.max_static_cost:
        result = (N1FailedBound.STATIC_COST, charge.static_cost, package.policy.max_static_cost)
    else:
        result = None
    logger.debug("first_policy_failure exit failed=%s", None if result is None else result[0].value)
    return result
