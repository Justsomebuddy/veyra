"""Atomic hard-first scalar/count estimator for P3-N0."""

from __future__ import annotations

import logging

from .common import exact_hex, exact_shape, reject
from .types import (
    FailedBound, N0Policy, N0Source, PrimePowerObserverDoctrine,
)

logger = logging.getLogger(__name__)


def hard_first(source):
    """Charge scalar/count estimates before pow, capture, traversal, or formal work."""
    logger.debug("hard_first entry")
    raw = exact_shape(source, N0Source, "n0-source")
    policy = raw["policy"]
    if type(policy) is not N0Policy:
        reject("n0-policy-exact-type-required")
    exact_hex(raw["source_digest"], "n0-source-digest")
    cap_names = (
        "max_depth", "max_integer_bits", "max_exponent", "max_modulus_bits",
        "max_events", "max_parent_edges", "max_access_edges", "max_evaluations",
        "max_families", "max_finite_rows", "max_reductions", "max_assumptions",
        "max_ledger_bytes", "max_captured_bytes", "max_output_bytes", "timeout_seconds",
    )
    hard_caps = (64, 4096, 65, 4096, 64, 256, 128, 8192, 1024, 100_000,
                 1024, 64, 2 * 1024 * 1024, 8 * 1024 * 1024,
                 4 * 1024 * 1024, 300)
    values = tuple(getattr(policy, name, None) for name in cap_names)
    if any(type(value) is not int or not 1 <= value <= cap
           for value, cap in zip(values, hard_caps, strict=True)):
        reject("n0-policy-cap-type-or-sign-invalid")
    if type(raw["prime"]) is not int or type(raw["depth"]) is not int:
        reject("n0-prime-depth-exact-int-required")
    p, n = raw["prime"], raw["depth"]
    if p < 2 or p > 65521 or n < 0:
        reject("n0-prime-depth-negative-or-outside-hard-envelope")
    early_checks = (
        (FailedBound.DEPTH, n, policy.max_depth),
        (FailedBound.EXPONENT, n + 2, policy.max_exponent),
        (FailedBound.MODULUS_BITS, (n + 2) * p.bit_length(), policy.max_modulus_bits),
        (FailedBound.INTEGER_BITS, (n + 1) * p.bit_length(), policy.max_integer_bits),
    )
    for bound, required, allowed in early_checks:
        if required > allowed:
            logger.debug("hard_first exit early-refusal=%s", bound.value)
            return bound, required, allowed
    if (type(raw["doctrine"]) is not PrimePowerObserverDoctrine
            or type(raw["doctrine"].premises) is not tuple
            or len(raw["doctrine"].premises) > 64):
        reject("n0-doctrine-hard-envelope-invalid")
    fine = 1
    for _ in range(n + 2):
        fine = min(policy.max_finite_rows + 1, fine * p)
    coarse = 1
    for _ in range(n + 1):
        coarse = min(policy.max_finite_rows + 1, coarse * p)
    finite_rows = min(policy.max_finite_rows + 1, 2 * (coarse + 2 * fine))
    checks = (
        (FailedBound.EVENTS, 26, policy.max_events),
        (FailedBound.EDGES, 2 * 13, policy.max_parent_edges),
        (FailedBound.ACCESS_EDGES, 2 * 9, policy.max_access_edges),
        (FailedBound.EVALUATIONS, 16, policy.max_evaluations),
        (FailedBound.FAMILIES, 3, policy.max_families),
        (FailedBound.FINITE_ROWS, finite_rows, policy.max_finite_rows),
        (FailedBound.REDUCTIONS, 6, policy.max_reductions),
        (FailedBound.ASSUMPTIONS, len(raw["doctrine"].premises), policy.max_assumptions),
        (FailedBound.LEDGER_BYTES, 16 * 1024, policy.max_ledger_bytes),
    )
    for bound, required, allowed in checks:
        if required > allowed:
            logger.debug("hard_first exit refusal=%s", bound.value)
            return bound, required, allowed
    logger.debug("hard_first exit refusal=none")
    return None
