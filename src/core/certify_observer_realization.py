"""Bounded executable certificate for the relative P1-to-R16 contract."""

from __future__ import annotations

import logging

from .certify_types import Certificate
from .observer_realization import (
    observer_realization_context,
    realize_observer_doctrine_r16,
    verify_observer_realization_r16,
)
from .observer_realization_types import ObservationStatus
from .observer_realization_validation import ObserverRealizationValidationError
from .positive_ontology_doctrine import p0_observer_doctrine
from .proof_core_types import Pulse, Silence

logger = logging.getLogger(__name__)

P1_R16_CERTIFICATE_NAME = "observer_realization_p1_r16"
P1_R16_CERTIFICATE_METHOD = (
    "context-relative structured Ready/Blocked replay with deterministic finite "
    "join completion; not a canonical functor, theorem, or promotion"
)


def _recurrence(depth: int):
    """Build one small closed recurrence for the bounded certificate scope."""
    logger.debug("realization certificate recurrence entry depth=%d", depth)
    result = Silence()
    for _ in range(depth):
        result = Pulse(result)
    logger.debug("realization certificate recurrence exit depth=%d", depth)
    return result


def certify_observer_realization_p1_r16() -> Certificate:
    """Certify one blocked scope, one ready-only scope, and exact replay."""
    logger.debug("certify_observer_realization_p1_r16 entry")
    try:
        doctrine = p0_observer_doctrine()
        blocked_context = observer_realization_context(
            doctrine,
            "certificate-blocked-scope",
            (("z", _recurrence(0)), ("one", _recurrence(1)), ("two", _recurrence(2))),
            (("crest", 2), ("tail", 3)),
        )
        ready_context = observer_realization_context(
            doctrine,
            "certificate-ready-scope",
            (("one", _recurrence(1)), ("two", _recurrence(2))),
            (("crest", 2), ("tail", 3)),
        )
        blocked = realize_observer_doctrine_r16(doctrine, blocked_context)
        replayed = verify_observer_realization_r16(
            doctrine, blocked_context, blocked
        )
        ready = realize_observer_doctrine_r16(doctrine, ready_context)
        blocked_rows = tuple(
            row
            for row in replayed.evaluations
            if row.status is ObservationStatus.BLOCKED
        )
        passed = (
            replayed == blocked
            and len(blocked.evaluations) == 6
            and len(blocked_rows) == 1
            and len(blocked.closure) == 3
            and blocked.closure[0].observer_name == "bottom"
            and blocked.closure[0].generator_ids == ()
            and len(blocked.source_mapping) == 2
            and blocked.context_digest != ready.context_digest
            and blocked.doctrine_digest != ready.doctrine_digest
            and blocked.witness_digest != ready.witness_digest
        )
        detail = (
            "sources=2 states=3 replay=6 structured-blocked=1 closure=3 "
            "bottom=derived exact-verification=pass alternate-scope=distinct "
            "nonclaims=canonical-map,echo-embedding,functoriality,quotient-"
            "transport,ready-only-chain-theorem,authentication,promotion"
        )
    except ObserverRealizationValidationError as error:
        logger.exception("certify_observer_realization_p1_r16 blocked")
        passed = False
        detail = f"blocked={type(error).__name__}:{error}"
    result = Certificate(
        P1_R16_CERTIFICATE_NAME,
        P1_R16_CERTIFICATE_METHOD,
        passed,
        detail,
        1,
    )
    if not passed:
        logger.error(
            "certify_observer_realization_p1_r16 failed detail=%s", detail
        )
    logger.debug("certify_observer_realization_p1_r16 exit result=%r", result)
    return result
