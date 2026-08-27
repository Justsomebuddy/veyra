"""Executable certificate for the DI-1 doctrinal-induction candidate lane."""

from __future__ import annotations

import logging

from .certify_types import Certificate
from .doctrinal_induction import (
    InductionDoctrine,
    depth_bomb_contract,
    divides_family_contract,
    doctrinal_induction_checklist,
    license_all_depth,
    name_peeking_contract,
)
from .intrinsic_arithmetic import one, successor
from .native_runtime import nod, rez

logger = logging.getLogger(__name__)

_DOCTRINE = InductionDoctrine("di1.cert.v1", "stitch-one-block")


def _block(width: int):
    logger.debug("certify_di1._block entry width=%d", width)
    value = one()
    for _ in range(width - 1):
        value = successor(value)
    logger.debug("certify_di1._block exit")
    return value


def certify_doctrinal_induction_di1() -> Certificate:
    """Certify the DI-1 license pipeline with both adversarial controls."""
    logger.debug("certify_doctrinal_induction_di1 entry")
    anchor = nod(rez("di1-cert"), "di1-cert")
    probes = tuple(range(1, 13))
    positive = license_all_depth(
        _DOCTRINE, divides_family_contract(_block(3)), anchor, probes
    )
    wide = license_all_depth(
        _DOCTRINE, divides_family_contract(_block(5)), anchor, probes
    )
    positive_ok = (
        positive.status == "licensed"
        and wide.status == "licensed"
        and positive.uniformity is not None
        and positive.uniformity.echoed
        and all(row.valid for row in positive.probes)
        and positive.max_depth == 12
    )
    peek = license_all_depth(_DOCTRINE, name_peeking_contract(), anchor, probes)
    peek_ok = peek.status == "blocked" and peek.obstruction == "nonuniform-step"
    bomb = license_all_depth(
        _DOCTRINE, depth_bomb_contract(_block(3), 5), anchor, probes
    )
    bomb_ok = bomb.status == "blocked" and bomb.obstruction == "step-invalid-at-depth:5"
    checklist_ok = len(doctrinal_induction_checklist()) == 5
    passed = positive_ok and peek_ok and bomb_ok and checklist_ok
    detail = (
        "divides-family licensed to depth 12 for blocks 3 and 5 with anchor-"
        "renaming uniformity; name-peeking step rejected as nonuniform; depth "
        "bomb blocked at exactly 5; ledger-relative license only, no completed "
        "carrier, no promotion"
    )
    result = Certificate(
        "doctrinal_induction_di1",
        "candidate proof-family license: base + uniform step + adopted generator, replayed and adversarially pressured",
        passed,
        detail,
        1,
    )
    if not passed:
        logger.error("certify_doctrinal_induction_di1 failed detail=%s", detail)
    logger.debug("certify_doctrinal_induction_di1 exit passed=%s", passed)
    return result
