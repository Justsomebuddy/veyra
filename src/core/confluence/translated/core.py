"""Public P1-C3 typed translated-confluence surface."""

import logging

from ..runtime import fork_confluence_judgment
from ..types import DirectEchoTransport

from .bridge import p0_p1a_response_bridge
from .result_validation import validate_translated_confluence_result
from .runtime import translated_confluence_judgment
from .transport import (
    translated_confluence_policy, translated_echo_transport_spec,
)
from .types import (
    C3TransportMode, C3TransportSpec, ObserverProgramBridgeRow,
    P0P1AResponseBridgeSource, StageInputBridgeRow,
    TRANSLATED_CONFLUENCE_NONCLAIMS, TranslatedConfluenceJudgment,
    TranslatedConfluencePolicy, TranslatedConfluenceResourceLimit,
    TranslatedConfluenceResult, TranslatedEchoTransportSpec,
    TranslatedResourceBound, TranslatedResourceSource,
    TranslatedResponseRow, TranslatedTransport2CellArtifact,
    TranslationDirection,
)
from .validation import TranslatedConfluenceValidationError

logger = logging.getLogger(__name__)


def c3_confluence_judgment(
    p0_doctrine, diagram, plan, transport: C3TransportSpec, *,
    p1a_doctrine=None, p1a_source=None, a2_stage_source=None,
    bridge=None, policy=None,
):
    """Dispatch an exact disjoint direct C1 or translated C3 request."""
    logger.debug("c3_confluence_judgment entry type=%s", type(transport).__name__)
    translated_inputs = (p1a_doctrine, p1a_source, a2_stage_source, bridge, policy)
    if type(transport) is DirectEchoTransport:
        if any(item is not None for item in translated_inputs):
            logger.error("c3 direct lane received translated fields")
            raise TranslatedConfluenceValidationError("direct-lane-translated-fields")
        result = fork_confluence_judgment(p0_doctrine, diagram, plan, transport)
    elif type(transport) is TranslatedEchoTransportSpec:
        if any(item is None for item in translated_inputs[:4]):
            logger.error("c3 translated lane missing raw fields")
            raise TranslatedConfluenceValidationError("translated-lane-missing-raw-fields")
        result = translated_confluence_judgment(
            p0_doctrine, diagram, plan, p1a_doctrine, p1a_source,
            a2_stage_source, bridge, transport, policy,
        )
    else:
        logger.error("c3 unknown transport variant")
        raise TranslatedConfluenceValidationError("unknown-c3-transport-variant")
    logger.debug("c3_confluence_judgment exit type=%s", type(result).__name__)
    return result

__all__ = [
    "C3TransportMode", "C3TransportSpec", "ObserverProgramBridgeRow",
    "P0P1AResponseBridgeSource", "StageInputBridgeRow",
    "TRANSLATED_CONFLUENCE_NONCLAIMS", "TranslatedConfluenceJudgment",
    "TranslatedConfluencePolicy", "TranslatedConfluenceResourceLimit",
    "TranslatedConfluenceResult", "TranslatedConfluenceValidationError",
    "TranslatedEchoTransportSpec", "TranslatedResponseRow",
    "TranslatedResourceBound", "TranslatedResourceSource",
    "TranslatedTransport2CellArtifact", "TranslationDirection",
    "p0_p1a_response_bridge", "translated_confluence_judgment",
    "c3_confluence_judgment",
    "translated_confluence_policy", "translated_echo_transport_spec",
    "validate_translated_confluence_result",
]
