"""Concrete LA19/LA20/LA22 bindings for replay-derived P3-N0 outcomes."""

from __future__ import annotations

import logging

from .common import digest, indexed, reject
from .types import N0BoundPostbirthLedger
from .nested_validation import validate_bound_ledger_shape
from .types import N0History, SuffixSelector

logger = logging.getLogger(__name__)


def bound_postbirth_ledger(strict, open_history) -> N0BoundPostbirthLedger:
    """Bind LA19/20 to concrete outcome+efficacy and LA22 to their exact join."""
    logger.debug("bound_postbirth_ledger entry")
    if (type(strict) is not N0History or type(open_history) is not N0History
            or strict.selector is not SuffixSelector.STRICT_SUFFIX
            or open_history.selector is not SuffixSelector.OPEN_SUFFIX):
        reject("n0-bound-postbirth-history-types-invalid")
    la19 = digest("veyra.p3n0.LA19.v2", (
        ("outcome", strict.outcome_digest.encode()),
        ("efficacy", strict.efficacy_digest.encode()),
    ))
    la20 = digest("veyra.p3n0.LA20.v2", (
        ("outcome", open_history.outcome_digest.encode()),
        ("efficacy", open_history.efficacy_digest.encode()),
    ))
    la22 = digest("veyra.p3n0.LA22.v2", (
        ("LA19", la19.encode()), ("LA20", la20.encode()),
    ))
    rows = (("LA19", la19), ("LA20", la20), ("LA22", la22))
    value = digest("veyra.p3n0.bound-postbirth-ledger.v2", (
        *indexed("row", (f"{name}:{payload}" for name, payload in rows)),
        ("strict-outcome", strict.outcome_digest.encode()),
        ("open-outcome", open_history.outcome_digest.encode()),
        ("strict-efficacy", strict.efficacy_digest.encode()),
        ("open-efficacy", open_history.efficacy_digest.encode()),
    ))
    result = N0BoundPostbirthLedger(
        rows, strict.outcome_digest, open_history.outcome_digest,
        strict.efficacy_digest, open_history.efficacy_digest, value,
    )
    logger.debug("bound_postbirth_ledger exit")
    return result


def validate_bound_postbirth_ledger(value) -> N0BoundPostbirthLedger:
    """Recompute all three concrete row payloads and the terminal ledger digest."""
    logger.debug("validate_bound_postbirth_ledger entry")
    validate_bound_ledger_shape(value)
    la19 = digest("veyra.p3n0.LA19.v2", (
        ("outcome", value.strict_outcome_digest.encode()),
        ("efficacy", value.strict_efficacy_digest.encode()),
    ))
    la20 = digest("veyra.p3n0.LA20.v2", (
        ("outcome", value.open_outcome_digest.encode()),
        ("efficacy", value.open_efficacy_digest.encode()),
    ))
    la22 = digest("veyra.p3n0.LA22.v2", (("LA19", la19.encode()), ("LA20", la20.encode())))
    rows = (("LA19", la19), ("LA20", la20), ("LA22", la22))
    expected = digest("veyra.p3n0.bound-postbirth-ledger.v2", (
        *indexed("row", (f"{name}:{payload}" for name, payload in rows)),
        ("strict-outcome", value.strict_outcome_digest.encode()),
        ("open-outcome", value.open_outcome_digest.encode()),
        ("strict-efficacy", value.strict_efficacy_digest.encode()),
        ("open-efficacy", value.open_efficacy_digest.encode()),
    ))
    if value.row_payloads != rows or value.ledger_digest != expected:
        reject("n0-bound-postbirth-ledger-drift")
    logger.debug("validate_bound_postbirth_ledger exit")
    return value
