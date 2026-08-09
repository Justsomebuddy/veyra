"""Certificate gate for the R9 proof-recurrence/native-mode transport."""
from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..intrinsic_mode_bridge import (
    THEOREM_IDS, intrinsic_mode_bridge_report, verify_intrinsic_mode_bridge_report,
)
from ..intrinsic_mode_laws import transport_law_rows
from ..intrinsic_mode_refutations import erasure_boundary_rows
from ..intrinsic_mode_transport import (
    IntrinsicMode, decode_mode, encode_recurrence, recurrence_equal,
)
from ..proof_core_types import Pulse, Silence

logger = logging.getLogger(__name__)


def _samples() -> tuple[object, ...]:
    logger.debug("certify_intrinsic_mode._samples entry")
    silence = Silence()
    result = (silence, Pulse(silence), Pulse(Pulse(silence)))
    logger.debug("certify_intrinsic_mode._samples exit")
    return result


def certify_intrinsic_mode_transport_r9() -> Certificate:
    """Gate exact round trips, laws, refutations, Lean binding, and no promotion."""
    logger.debug("certify_intrinsic_mode_transport_r9 entry")
    roundtrips = []
    for recurrence in _samples():
        encoded = encode_recurrence(recurrence)
        decoded = decode_mode(encoded.native)
        roundtrips.append(
            type(decoded) is IntrinsicMode
            and recurrence_equal(decoded.recurrence, recurrence)
            and encode_recurrence(decoded.recurrence).native == encoded.native
        )
    laws = transport_law_rows()
    refutations = erasure_boundary_rows()
    bridge = intrinsic_mode_bridge_report()
    law_ids = tuple(row.law_id for row in laws)
    refutation_facts = tuple(
        (row.row_id, row.intrinsic_echo, row.cyclic_resonance, row.phase_offsets, row.separated)
        for row in refutations
    )
    passed = (
        len(roundtrips) == 3 and all(roundtrips)
        and law_ids == (
            "R9-LAW-ZERO", "R9-LAW-SUCCESSOR", "R9-LAW-SUCCESSOR",
            "THM-R9-005", "THM-R9-005", "THM-R9-006", "THM-R9-006",
            "THM-R9-006", "THM-R9-008",
        )
        and all(row.holds and row.expected_digest == row.native_digest for row in laws)
        and refutation_facts == (
            ("R9-REFUTE-LABEL", True, False, (), True),
            ("R9-REFUTE-PHASE", True, True, (1, 3), True),
            ("R9-REFUTE-SILENT", True, False, (), True),
        )
        and bridge.status == "checked" and bridge.theorem_ids == THEOREM_IDS
        and bridge.r7_artifact_checked and bridge.manifest_checked
        and bridge.source_bound and bridge.lean_checked
        and verify_intrinsic_mode_bridge_report(bridge)
        and "no generic Mode" in bridge.boundary
    )
    detail = (
        f"roundtrips={sum(roundtrips)}/3 laws={sum(row.holds for row in laws)}/{len(laws)} "
        f"refutations={sum(row.separated for row in refutations)}/3 "
        f"theorems={len(bridge.theorem_ids)} binding={bridge.binding_digest[:16]}"
    )
    result = Certificate(
        "intrinsic_mode_transport_r9",
        "fixed-anchor structural codec plus reviewed Python/native/Lean transport binding",
        passed, detail, 2,
    )
    if not passed:
        logger.error("certify_intrinsic_mode_transport_r9 blocked detail=%s", detail)
    logger.debug("certify_intrinsic_mode_transport_r9 exit result=%r", result)
    return result
