"""Exact PΩ1 policy/package construction and raw snapshotting."""

from __future__ import annotations

import logging

from .alphabet import (
    formal_alphabet_presentation, snapshot_alphabet, snapshot_presentation,
)
from .common import exact_digest, exact_shape, reject
from .digest import digest, frame
from .doctrine import snapshot_doctrine
from .formal import snapshot_theorem_source
from .ledger import snapshot_ledger
from .types import (
    StreamAlphabetSource, StreamCompletionDoctrine, StreamCompletionLedger,
    StreamCompletionPackage, StreamCompletionPolicy, StreamCompletionTheoremSource,
)

logger = logging.getLogger(__name__)
POLICY_VERSION = "pomega1-policy-v1"
PACKAGE_VERSION = "pomega1-package-v1"
HARD_SOURCE_BYTES = 2 * 1024 * 1024
HARD_PACKAGE_BYTES = 4 * 1024 * 1024
HARD_STATIC_COST = 8 * 1024 * 1024


def stream_completion_policy(
    max_captured_bytes: int = HARD_SOURCE_BYTES,
    max_static_cost: int = HARD_STATIC_COST,
    compile_timeout_seconds: int = 120,
    max_output_bytes: int = 1024 * 1024,
) -> StreamCompletionPolicy:
    """Construct one exact bounded executable policy."""
    logger.debug("stream_completion_policy entry")
    values = (max_captured_bytes, max_static_cost, compile_timeout_seconds, max_output_bytes)
    if any(type(value) is not int for value in values):
        reject("stream-policy-integers-must-be-exact")
    if not 1 <= max_captured_bytes <= HARD_SOURCE_BYTES:
        reject("stream-policy-captured-bytes-invalid")
    if not 1 <= max_static_cost <= HARD_STATIC_COST:
        reject("stream-policy-static-cost-invalid")
    if not 1 <= compile_timeout_seconds <= 300:
        reject("stream-policy-timeout-invalid")
    if not 1 <= max_output_bytes <= 4 * 1024 * 1024:
        reject("stream-policy-output-invalid")
    value = digest("veyra.pomega1.policy.v1", (
        ("version", POLICY_VERSION.encode()),
        ("captured", max_captured_bytes.to_bytes(8, "big")),
        ("static", max_static_cost.to_bytes(8, "big")),
        ("timeout", compile_timeout_seconds.to_bytes(4, "big")),
        ("output", max_output_bytes.to_bytes(8, "big")),
    ))
    result = StreamCompletionPolicy(POLICY_VERSION, *values, value)
    logger.debug("stream_completion_policy exit")
    return result


def snapshot_policy(value: StreamCompletionPolicy) -> StreamCompletionPolicy:
    """Reject subclasses, Boolean caps, extra fields, and stale policy digests."""
    logger.debug("snapshot_policy entry")
    exact_shape(value, StreamCompletionPolicy, "stream-policy")
    try:
        if type(value.version) is not str:
            reject("stream-policy-version-type-invalid")
        expected = stream_completion_policy(
            value.max_captured_bytes, value.max_static_cost,
            value.compile_timeout_seconds, value.max_output_bytes,
        )
        exact_digest(value.policy_digest, "stream-policy-digest")
    except AttributeError:
        reject("stream-policy-missing-fields")
    if value != expected:
        reject("stream-policy-drift")
    logger.debug("snapshot_policy exit")
    return expected


def _package_digest(
    doctrine: StreamCompletionDoctrine, alphabet: StreamAlphabetSource,
    presentation_digest: str, theorem: StreamCompletionTheoremSource,
    ledger: StreamCompletionLedger, policy: StreamCompletionPolicy,
) -> str:
    """Commit every exact source and repeated doctrine identifier."""
    logger.debug("_package_digest entry")
    result = digest("veyra.pomega1.package.v1", (
        ("version", PACKAGE_VERSION.encode()), ("doctrine", doctrine.doctrine_digest.encode()),
        ("alphabet", alphabet.alphabet_digest.encode()),
        ("presentation", presentation_digest.encode()),
        ("family", doctrine.family_class_id.encode()), ("carrier", doctrine.carrier_id.encode()),
        ("restriction", doctrine.restriction_id.encode()),
        ("theorem", theorem.source_digest.encode()), ("ledger", ledger.ledger_digest.encode()),
        ("policy", policy.policy_digest.encode()),
    ))
    logger.debug("_package_digest exit")
    return result


def stream_completion_package(
    doctrine: StreamCompletionDoctrine, alphabet: StreamAlphabetSource,
    theorem_source: StreamCompletionTheoremSource, ledger: StreamCompletionLedger,
    policy: StreamCompletionPolicy,
) -> StreamCompletionPackage:
    """Build a source-only package; no family, generator, callback, or old result."""
    logger.debug("stream_completion_package entry")
    doctrine = snapshot_doctrine(doctrine)
    alphabet = snapshot_alphabet(alphabet)
    theorem_source = snapshot_theorem_source(theorem_source)
    ledger = snapshot_ledger(ledger)
    policy = snapshot_policy(policy)
    presentation = formal_alphabet_presentation(alphabet, theorem_source.source_digest)
    value = _package_digest(
        doctrine, alphabet, presentation.presentation_digest,
        theorem_source, ledger, policy,
    )
    result = StreamCompletionPackage(
        doctrine, alphabet, presentation, doctrine.family_class_id,
        doctrine.carrier_id, doctrine.restriction_id, theorem_source, ledger,
        policy, value,
    )
    logger.debug("stream_completion_package exit")
    return result


def snapshot_package(value: StreamCompletionPackage) -> StreamCompletionPackage:
    """Deeply capture the exact package before source IO or compilation."""
    logger.debug("snapshot_package entry")
    exact_shape(value, StreamCompletionPackage, "stream-completion-package")
    try:
        doctrine = snapshot_doctrine(value.doctrine)
        alphabet = snapshot_alphabet(value.alphabet)
        theorem = snapshot_theorem_source(value.theorem_source)
        presentation = snapshot_presentation(
            value.alphabet_presentation, alphabet, theorem.source_digest,
        )
        ledger = snapshot_ledger(value.ledger)
        policy = snapshot_policy(value.policy)
        exact_digest(value.package_digest, "stream-package-digest")
        repeated = (value.family_class_id, value.carrier_id, value.restriction_id)
        if any(type(item) is not str for item in repeated):
            reject("stream-package-id-type-invalid")
    except AttributeError:
        reject("stream-package-missing-fields")
    expected = StreamCompletionPackage(
        doctrine, alphabet, presentation, doctrine.family_class_id,
        doctrine.carrier_id, doctrine.restriction_id, theorem, ledger, policy,
        _package_digest(doctrine, alphabet, presentation.presentation_digest, theorem, ledger, policy),
    )
    if value != expected:
        reject("stream-package-drift")
    logger.debug("snapshot_package exit")
    return expected


def canonical_package_bytes(value: StreamCompletionPackage) -> bytes:
    """Encode bounded source commitments and captured instance deterministically."""
    logger.debug("canonical_package_bytes entry")
    value = snapshot_package(value)
    result = frame("veyra.pomega1.package-encoding.v1", (
        ("package", value.package_digest.encode()),
        ("doctrine", value.doctrine.doctrine_digest.encode()),
        ("alphabet", value.alphabet.alphabet_digest.encode()),
        ("presentation", value.alphabet_presentation.presentation_digest.encode()),
        ("instance", value.alphabet_presentation.generated_instance_bytes),
        ("theorem", value.theorem_source.source_digest.encode()),
        ("ledger", value.ledger.ledger_digest.encode()),
        ("policy", value.policy.policy_digest.encode()),
    ))
    logger.debug("canonical_package_bytes exit bytes=%d", len(result))
    return result
