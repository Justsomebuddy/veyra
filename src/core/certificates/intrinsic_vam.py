"""One integration certificate for the bounded intrinsic-VAM R12 stack."""

from __future__ import annotations

import logging

from vam.intrinsic import (
    INTRINSIC_PROFILE,
    decode_intrinsic_frame,
    encode_intrinsic_frame,
    inspect_intrinsic_frame,
)

from ..certify_types import Certificate
from ..intrinsic_mode_transport import encode_recurrence, recurrence_equal
from ..intrinsic_vam_formal_bridge import (
    intrinsic_vam_formal_bridge_data,
    intrinsic_vam_formal_bridge_report,
)
from ..intrinsic_vam_formal_effects import intrinsic_vam_formal_effect_digest
from ..intrinsic_vam_formal_lean_render import THEOREM_IDS
from ..intrinsic_vam_formal_manifest import (
    EXPECTED_BINDING_DIGEST,
    EXPECTED_R12_5_TCB_DIGESTS,
)
from ..intrinsic_vam_formal_objects import EXPECTED_R12_5_OBJECTS
from ..intrinsic_vam_formal_report import valid_intrinsic_vam_formal_report_shape
from ..intrinsic_vam_lowering import (
    lower_r11_echo,
    lower_r11_observation,
    lower_r7_recurrence,
    lower_r9_intrinsic_mode,
    raise_r11_echo,
    raise_r11_observation,
    raise_r7_recurrence,
    raise_r9_intrinsic_mode,
)
from ..intrinsic_vam_lowering_types import IntrinsicLoweringLane
from ..intrinsic_vam_receipts import intrinsic_transport_envelope_data
from ..observer_core_semantics import echo, observe
from ..observer_core_support import outcome_data
from ..observer_core_types import Apply, Input, PrimitiveId
from ..proof_core_types import Pulse, Silence
from ..shadow_effect_types import BridgeCapability, EvidenceClass, EvidenceScope
from ..shadow_effects import shadow_effect_registry_digest, shadow_effect_summary

logger = logging.getLogger(__name__)
_METHOD = (
    "four-lane intrinsic IR/VAMI replay plus R11-continuous valid-image "
    "Lean preservation"
)


def _transport_replay() -> tuple[bool, tuple[object, ...], tuple[bytes, ...]]:
    """Replay the four exact R12.3 lanes through R12.4 VAMI."""
    logger.debug("certify_intrinsic_vam._transport_replay entry")
    source = Pulse(Pulse(Silence()))
    mode = encode_recurrence(source)
    observer = Apply(PrimitiveId.CREST, Input())
    transports = (
        lower_r7_recurrence(source),
        lower_r9_intrinsic_mode(mode),
        lower_r11_observation(observer, source),
        lower_r11_echo(observer, source, source),
    )
    raised = (
        recurrence_equal(raise_r7_recurrence(source, transports[0]), source),
        raise_r9_intrinsic_mode(mode, transports[1]) == mode,
        outcome_data(
            raise_r11_observation(observer, source, transports[2]).observation
        )
        == outcome_data(observe(observer, source)),
        outcome_data(raise_r11_echo(observer, source, source, transports[3]))
        == outcome_data(echo(observer, source, source)),
    )
    expected_lanes = tuple(item.value for item in IntrinsicLoweringLane)
    envelopes = tuple(intrinsic_transport_envelope_data(item) for item in transports)
    receipt_ok = all(
        row["verification"] == "unverified-envelope"
        and row["evidence_accepted"] is False
        and row["taxonomy_changed"] is False
        and row["receipt"]["evidence"]["class"] == "executable-witness"
        and row["receipt"]["evidence"]["scope"] == "finite"
        and row["receipt"]["evidence"]["may_enter_promotion_contract"] is False
        and row["receipt"]["promotion_ready"] is False
        for row in envelopes
    )
    frames = tuple(encode_intrinsic_frame(item.value) for item in transports)
    reports = tuple(inspect_intrinsic_frame(frame) for frame in frames)
    codec_ok = all(
        decode_intrinsic_frame(frame) == item.value
        and report["ok"] is True
        and report["profile"] == INTRINSIC_PROFILE
        and report["execution"]["evidence_accepted"] is False
        and report["execution"]["promotion_ready"] is False
        and report["execution"]["taxonomy_changed"] is False
        for item, frame, report in zip(transports, frames, reports, strict=True)
    )
    lanes = tuple(row["receipt"]["lane"] for row in envelopes)
    passed = all(raised) and lanes == expected_lanes and receipt_ok and codec_ok
    logger.debug(
        "certify_intrinsic_vam._transport_replay exit passed=%s lanes=%d frames=%d",
        passed,
        len(lanes),
        len(frames),
    )
    return passed, transports, frames


def _formal_replay() -> tuple[bool, dict[str, object]]:
    """Consume the self-verifying R12.5 public report exactly once."""
    logger.debug("certify_intrinsic_vam._formal_replay entry")
    report = intrinsic_vam_formal_bridge_report()
    if not valid_intrinsic_vam_formal_report_shape(report):
        logger.error("certify_intrinsic_vam._formal_replay invalid report shape")
        return False, {}
    data = intrinsic_vam_formal_bridge_data(report)
    checks = data["checks"]
    passed = (
        report.status == "checked"
        and report.theorem_ids == THEOREM_IDS
        and len(report.theorem_ids) == 9
        and report.source_digests == tuple(EXPECTED_R12_5_TCB_DIGESTS.items())
        and len(report.source_digests) == 28
        and report.object_records == tuple(EXPECTED_R12_5_OBJECTS.items())
        and len(report.object_records) == 9
        and report.capability is BridgeCapability.PRESERVES
        and report.evidence_class is EvidenceClass.FORMAL_BRIDGE
        and report.evidence_scope is EvidenceScope.GENERAL
        and report.effect_registry_digest == shadow_effect_registry_digest()
        and report.effect_digest == intrinsic_vam_formal_effect_digest()
        and report.binding_digest == EXPECTED_BINDING_DIGEST
        and type(checks) is dict
        and tuple(checks.values()) == (True, True, True, True, True, True)
        and report.promotion_ready is False
        and report.taxonomy_changed is False
    )
    logger.debug("certify_intrinsic_vam._formal_replay exit passed=%s", passed)
    return passed, data


def certify_intrinsic_vam_r12() -> Certificate:
    """Certify integration readiness without accepting or promoting new evidence."""
    logger.debug("certify_intrinsic_vam_r12 entry")
    try:
        shadow = shadow_effect_summary()
        transport_ok, transports, frames = _transport_replay()
        formal_ok, formal = _formal_replay()
        passed = (
            shadow["rows"] == 4
            and shadow["promotion_ready"] == 0
            and shadow["r12_complete"] is False
            and shadow["taxonomy_changed"] is False
            and shadow["digest"] == formal.get("effect_registry_digest")
            and transport_ok
            and formal_ok
        )
        theorem_rows = formal.get("theorem_ids")
        source_rows = formal.get("source_digests")
        object_rows = formal.get("object_records")
        detail = (
            f"registry={str(shadow['digest'])[:16]} lanes={len(transports)}/4 "
            f"vami={len(frames)}/4 "
            f"theorems={len(theorem_rows) if type(theorem_rows) is list else 0}/9 "
            f"sources={len(source_rows) if type(source_rows) is list else 0}/28 "
            f"objects={len(object_rows) if type(object_rows) is list else 0}/9 "
            f"binding={str(formal.get('binding_digest', ''))[:16]}"
        )
    except (KeyError, OSError, TypeError, UnicodeDecodeError, ValueError) as error:
        logger.exception("certify_intrinsic_vam_r12 blocked")
        passed, detail = False, f"blocked={type(error).__name__}:{error}"
    result = Certificate("intrinsic_vam_r12", _METHOD, passed, detail, 2)
    if not passed:
        logger.error("certify_intrinsic_vam_r12 failed detail=%s", detail)
    logger.debug("certify_intrinsic_vam_r12 exit result=%r", result)
    return result
