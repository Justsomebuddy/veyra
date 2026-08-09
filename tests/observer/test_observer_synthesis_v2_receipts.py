"""Functional exact-vector tests for finite in-process R14.5 receipts."""
from __future__ import annotations

import logging
from typing import cast

from src.core.intrinsic_vam_lowering import raise_r11_echo
from src.core.intrinsic_vam_receipts import intrinsic_transport_envelope_data
from src.core.observer_core_support import outcome_data
from src.core.observer_synthesis_v2_corpus import DEFAULT_CASES
from src.core.observer_synthesis_v2_receipt_codec import (
    receipt_bundle_bytes_v2,
    receipt_bundle_data_v2,
)
from src.core.observer_synthesis_v2_receipt_pins import (
    EXPECTED_BINDING_DIGESTS,
    EXPECTED_CASE_IDS,
    EXPECTED_ENVELOPE_DIGESTS,
    EXPECTED_IR_DIGESTS,
    EXPECTED_OUTCOME_DIGESTS,
    EXPECTED_PAYLOAD_DIGESTS,
    EXPECTED_RECEIPT_BUNDLE_DIGEST,
    EXPECTED_SOURCE_DIGESTS,
)
from src.core.observer_synthesis_v2_receipt_validation import (
    validate_observer_synthesis_receipts_v2,
)
from src.core.observer_synthesis_v2_receipts import (
    build_observer_synthesis_receipts_v2,
)
from src.core.observer_synthesis_v2_trial import (
    EXPECTED_GUARANTEE_DIGEST,
    EXPECTED_TRIAL_REPORT_DIGEST,
)
from src.core.observer_synthesis_v2_trial_validation import (
    EXPECTED_WINNER_CANONICAL,
    EXPECTED_WINNER_DIGEST,
)
from src.core.observer_core_types import Apply, Input, PrimitiveId

logger = logging.getLogger(__name__)


def test_exact_six_digest_vectors_and_final_bundle_pin() -> None:
    """Pin every reviewed case-to-R12/R14 digest vector."""
    logger.info("R14.5 exact receipt vector test entry")
    bundle = build_observer_synthesis_receipts_v2()
    rows = bundle.rows
    assert tuple(row.case_id for row in rows) == EXPECTED_CASE_IDS
    assert tuple(row.source_digests for row in rows) == EXPECTED_SOURCE_DIGESTS
    assert tuple(row.r12_binding_digest for row in rows) == EXPECTED_BINDING_DIGESTS
    assert tuple(row.r12_payload_digest for row in rows) == EXPECTED_PAYLOAD_DIGESTS
    assert tuple(row.ir_digest for row in rows) == EXPECTED_IR_DIGESTS
    assert tuple(row.envelope_digest for row in rows) == EXPECTED_ENVELOPE_DIGESTS
    assert tuple(row.outcome_digest for row in rows) == EXPECTED_OUTCOME_DIGESTS
    assert bundle.bundle_digest == EXPECTED_RECEIPT_BUNDLE_DIGEST
    logger.info("R14.5 exact receipt vector test exit")


def test_bundle_binds_exact_winner_corpus_trial_and_taxonomy() -> None:
    """Bind global R14 state without adding evidence or taxonomy authority."""
    logger.info("R14.5 global binding test entry")
    bundle = build_observer_synthesis_receipts_v2()
    assert bundle.winner_canonical == EXPECTED_WINNER_CANONICAL
    assert bundle.winner_digest == EXPECTED_WINNER_DIGEST
    assert bundle.trial_report_digest == EXPECTED_TRIAL_REPORT_DIGEST
    assert bundle.guarantee_digest == EXPECTED_GUARANTEE_DIGEST
    assert bundle.taxonomy_counts == (2, 4, 25, 5)
    assert bundle.corpus_digest == (
        "050352b6964eada5f3bb36d68a7989b11d781ab89e20a92aeaaa9bfe5ce146b1"
    )
    assert bundle.manifest_digest == (
        "4de40e8fdc41475c7e2f39d4370aecb0447e1b73b0254d723d17b1dc49221317"
    )
    assert bundle.winner_retained_digest == (
        "101b805ca0920511c9e2b14710157cc8170b09e59e99bea01bf08d82660ccb27"
    )
    logger.info("R14.5 global binding test exit")


def test_all_claim_and_promotion_flags_remain_false() -> None:
    """A finite preservation receipt never becomes evidence or proof."""
    logger.info("R14.5 false-claim test entry")
    bundle = build_observer_synthesis_receipts_v2()
    false_flags = (
        bundle.general_completeness,
        bundle.general_minimality,
        bundle.novelty,
        bundle.superiority,
        bundle.evidence_accepted,
        bundle.promotion_ready,
        bundle.taxonomy_changed,
        bundle.proof_complete,
    )
    data = receipt_bundle_data_v2(bundle)
    assert false_flags == (False,) * 8
    assert data["capabilities"] == ["preserves"]
    assert data["evidence"] == {
        "accepted": False,
        "class": "executable-witness",
        "may_enter_promotion_contract": False,
        "scope": "finite",
    }
    assert set(cast(dict[str, bool], data["false_claims"]).values()) == {False}
    logger.info("R14.5 false-claim test exit")


def test_each_transport_is_unverified_until_exact_raise_replay() -> None:
    """Exercise lower-envelope-raise with every exact ordered corpus pair."""
    logger.info("R14.5 R12 replay test entry")
    bundle = build_observer_synthesis_receipts_v2()
    observer = Apply(PrimitiveId.CREST, Input())
    tags = []
    for case, row in zip(DEFAULT_CASES, bundle.rows, strict=True):
        envelope = intrinsic_transport_envelope_data(row.transport)
        assert envelope["verification"] == "unverified-envelope"
        assert envelope["evidence_accepted"] is False
        assert envelope["taxonomy_changed"] is False
        raised = raise_r11_echo(observer, case.left, case.right, row.transport)
        tags.append(outcome_data(raised)["tag"])
    assert tuple(tags) == (
        "mismatch", "echo", "mismatch", "echo", "echo",
        "mismatch", "mismatch", "echo", "mismatch", "mismatch",
    )
    logger.info("R14.5 R12 replay test exit")


def test_diagnostic_misses_are_retained_as_actual_not_expected_success() -> None:
    """Cases 403/404 preserve SEPARATE and remain unmatched diagnostics."""
    logger.info("R14.5 diagnostic receipt test entry")
    rows = build_observer_synthesis_receipts_v2().rows
    assert tuple(row.actual.value for row in rows[-2:]) == ("SEPARATE", "SEPARATE")
    assert tuple(row.expected.value for row in rows[-2:]) == (
        "DOMAIN_BLOCKED",
        "DOMAIN_BLOCKED",
    )
    assert tuple(row.matched for row in rows[-2:]) == (False, False)
    logger.info("R14.5 diagnostic receipt test exit")


def test_repeated_builds_are_byte_exact_and_validation_returns_fresh() -> None:
    """Validation rebuilds all values and never returns caller identities."""
    logger.info("R14.5 fresh validation test entry")
    first = build_observer_synthesis_receipts_v2()
    second = build_observer_synthesis_receipts_v2()
    trusted = validate_observer_synthesis_receipts_v2(first)
    assert receipt_bundle_bytes_v2(first) == receipt_bundle_bytes_v2(second)
    assert trusted is not first
    assert trusted.rows is not first.rows
    assert all(
        accepted is not supplied
        and accepted.transport is not supplied.transport
        for accepted, supplied in zip(trusted.rows, first.rows, strict=True)
    )
    logger.info("R14.5 fresh validation test exit")
