"""Exact PΩ2 policy/package construction and raw snapshotting."""

from __future__ import annotations

import logging

from .common import exact_digest, exact_shape, reject
from .digest import digest, frame
from .doctrine import snapshot_doctrine
from .formal import snapshot_theorem_source
from .ledger import snapshot_ledger
from .prime import snapshot_prime
from .types import (
    PadicCompletionLedger, PadicCompletionPackage, PadicCompletionPolicy,
    PadicCompletionTheoremSource, PadicTowerDoctrine, PrimeSource,
)

logger = logging.getLogger(__name__)
POLICY_VERSION = "pomega2-policy-v1"
PACKAGE_VERSION = "pomega2-package-v1"
HARD_SOURCE_BYTES = 2 * 1024 * 1024
HARD_PACKAGE_BYTES = 4 * 1024 * 1024
HARD_STATIC_COST = 8 * 1024 * 1024


def padic_completion_policy(
    max_captured_bytes: int = HARD_SOURCE_BYTES,
    max_static_cost: int = HARD_STATIC_COST,
    compile_timeout_seconds: int = 120,
    max_output_bytes: int = 1024 * 1024,
) -> PadicCompletionPolicy:
    """Construct an exact bounded executable policy."""
    logger.debug("padic_completion_policy entry")
    values = (max_captured_bytes, max_static_cost, compile_timeout_seconds, max_output_bytes)
    if any(type(value) is not int for value in values):
        reject("padic-policy-integers-must-be-exact")
    if not 1 <= max_captured_bytes <= HARD_SOURCE_BYTES:
        reject("padic-policy-captured-bytes-invalid")
    if not 1 <= max_static_cost <= HARD_STATIC_COST:
        reject("padic-policy-static-cost-invalid")
    if not 1 <= compile_timeout_seconds <= 300:
        reject("padic-policy-timeout-invalid")
    if not 1 <= max_output_bytes <= 4 * 1024 * 1024:
        reject("padic-policy-output-invalid")
    value = digest("veyra.pomega2.policy.v1", (
        ("version", POLICY_VERSION.encode()),
        ("captured", max_captured_bytes.to_bytes(8, "big")),
        ("static", max_static_cost.to_bytes(8, "big")),
        ("timeout", compile_timeout_seconds.to_bytes(4, "big")),
        ("output", max_output_bytes.to_bytes(8, "big")),
    ))
    result = PadicCompletionPolicy(POLICY_VERSION, *values, value)
    logger.debug("padic_completion_policy exit")
    return result


def snapshot_policy(value: PadicCompletionPolicy) -> PadicCompletionPolicy:
    """Reject subclasses, Booleans, extra fields, and digest drift."""
    logger.debug("snapshot_policy entry")
    exact_shape(value, PadicCompletionPolicy, "padic-policy")
    try:
        if type(value.version) is not str:
            reject("padic-policy-version-type-invalid")
        expected = padic_completion_policy(
            value.max_captured_bytes, value.max_static_cost,
            value.compile_timeout_seconds, value.max_output_bytes,
        )
        exact_digest(value.policy_digest, "padic-policy-digest")
    except AttributeError:
        reject("padic-policy-missing-fields")
    if value != expected:
        reject("padic-policy-drift")
    logger.debug("snapshot_policy exit")
    return expected


def _package_digest(
    prime: PrimeSource, doctrine: PadicTowerDoctrine,
    theorem: PadicCompletionTheoremSource, ledger: PadicCompletionLedger,
    policy: PadicCompletionPolicy,
) -> str:
    """Commit every source and exact doctrine identity."""
    logger.debug("_package_digest entry")
    result = digest("veyra.pomega2.package.v1", (
        ("version", PACKAGE_VERSION.encode()), ("prime", prime.source_digest.encode()),
        ("doctrine", doctrine.doctrine_digest.encode()),
        ("family", doctrine.family_class_id.encode()),
        ("carrier", doctrine.carrier_id.encode()),
        ("reduction", doctrine.reduction_id.encode()),
        ("ring", doctrine.ring_id.encode()), ("theorem", theorem.source_digest.encode()),
        ("canonical-ops", theorem.canonical_ops_id.encode()),
        ("concrete-instance", theorem.concrete_instance_id.encode()),
        ("ledger", ledger.ledger_digest.encode()), ("policy", policy.policy_digest.encode()),
    ))
    logger.debug("_package_digest exit")
    return result


def padic_completion_package(
    prime: PrimeSource, doctrine: PadicTowerDoctrine,
    theorem_source: PadicCompletionTheoremSource,
    ledger: PadicCompletionLedger, policy: PadicCompletionPolicy,
) -> PadicCompletionPackage:
    """Build a source-only package with no family adapter or prior result."""
    logger.debug("padic_completion_package entry")
    prime = snapshot_prime(prime)
    doctrine = snapshot_doctrine(doctrine)
    theorem_source = snapshot_theorem_source(theorem_source)
    ledger = snapshot_ledger(ledger)
    policy = snapshot_policy(policy)
    result = PadicCompletionPackage(
        prime, doctrine, theorem_source, ledger, policy,
        _package_digest(prime, doctrine, theorem_source, ledger, policy),
    )
    logger.debug("padic_completion_package exit")
    return result


def snapshot_package(value: PadicCompletionPackage) -> PadicCompletionPackage:
    """Deeply capture every exact source before source IO or compilation."""
    logger.debug("snapshot_package entry")
    exact_shape(value, PadicCompletionPackage, "padic-completion-package")
    try:
        prime = snapshot_prime(value.prime)
        doctrine = snapshot_doctrine(value.doctrine)
        theorem = snapshot_theorem_source(value.theorem_source)
        ledger = snapshot_ledger(value.ledger)
        policy = snapshot_policy(value.policy)
        exact_digest(value.package_digest, "padic-package-digest")
    except AttributeError:
        reject("padic-package-missing-fields")
    expected = PadicCompletionPackage(
        prime, doctrine, theorem, ledger, policy,
        _package_digest(prime, doctrine, theorem, ledger, policy),
    )
    if value != expected:
        reject("padic-package-drift")
    logger.debug("snapshot_package exit")
    return expected


def canonical_package_bytes(value: PadicCompletionPackage) -> bytes:
    """Encode all bounded source commitments and captured witness bytes."""
    logger.debug("canonical_package_bytes entry")
    value = snapshot_package(value)
    result = frame("veyra.pomega2.package-encoding.v1", (
        ("package", value.package_digest.encode()),
        ("prime", value.prime.source_digest.encode()),
        ("prime-witness", value.prime.generated_witness_bytes),
        ("doctrine", value.doctrine.doctrine_digest.encode()),
        ("theorem", value.theorem_source.source_digest.encode()),
        ("canonical-ops", value.theorem_source.canonical_ops_id.encode()),
        ("concrete-instance", value.theorem_source.concrete_instance_id.encode()),
        ("ledger", value.ledger.ledger_digest.encode()),
        ("policy", value.policy.policy_digest.encode()),
    ))
    logger.debug("canonical_package_bytes exit bytes=%d", len(result))
    return result
