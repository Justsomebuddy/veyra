"""Adversarial transplant and recomputed-hash tests for R14.5 receipts."""
from __future__ import annotations

from dataclasses import replace
import logging

import pytest

from src.core.intrinsic_mode_transport import encode_recurrence
from src.core.intrinsic_vam_lowering import lower_r11_echo
from src.core.intrinsic_vam_receipts import (
    digest_transport_data,
    intrinsic_transport_envelope_data,
)
from src.core.observer_core_types import Apply, Input, PrimitiveId
from src.core.observer_synthesis_v2_corpus import DEFAULT_CASES
from src.core.observer_synthesis_v2_receipt_codec import (
    RECEIPT_SCHEMA,
    ROW_SCHEMA,
    InvalidObserverSynthesisReceiptV2,
    _bundle_body_data_v2,
    _row_body_data_v2,
    receipt_bundle_data_v2,
)
from src.core.observer_synthesis_v2_receipt_types import (
    ObserverSynthesisReceiptBundleV2,
)
from src.core.observer_synthesis_v2_receipt_validation import (
    validate_observer_synthesis_receipts_v2,
)
import src.core.observer_synthesis_v2_receipt_validation as validation_module
from src.core.observer_synthesis_v2_receipts import (
    build_observer_synthesis_receipts_v2,
)
from src.core.proof_core_codec import digest_data

logger = logging.getLogger(__name__)


def _rehash_row(row):
    """Recompute only public structural hashes, never trusted replay values."""
    logger.debug("_rehash_row entry case_id=%d", row.case_id)
    provisional = replace(row, row_digest="")
    result = replace(
        provisional,
        row_digest=digest_data(_row_body_data_v2(provisional), f"{ROW_SCHEMA}.binding"),
    )
    logger.debug("_rehash_row exit digest=%s", result.row_digest[:12])
    return result


def _rehash_bundle(bundle, rows):
    """Recompute an attacker-controlled outer binding for transplant tests."""
    logger.debug("_rehash_bundle entry rows=%d", len(rows))
    provisional = replace(bundle, rows=rows, bundle_digest="")
    result = replace(
        provisional,
        bundle_digest=digest_data(
            _bundle_body_data_v2(provisional),
            f"{RECEIPT_SCHEMA}.binding",
        ),
    )
    logger.debug("_rehash_bundle exit digest=%s", result.bundle_digest[:12])
    return result


@pytest.mark.parametrize(
    "field,replacement",
    (
        ("schema", "forged"),
        ("catalog_digest", "0" * 64),
        ("winner_ordinal", True),
        ("winner_digest", "0" * 64),
        ("corpus_digest", "0" * 64),
        ("trial_report_digest", "0" * 64),
        ("manifest_digest", "0" * 64),
        ("guarantee_digest", "0" * 64),
        ("winner_retained_digest", "0" * 64),
        ("taxonomy_counts", (2, 4, 24, 6)),
        ("evidence_accepted", True),
        ("promotion_ready", True),
        ("taxonomy_changed", True),
        ("proof_complete", True),
        ("bundle_digest", "0" * 64),
    ),
)
def test_every_global_authority_or_binding_mutation_rejects(
    field: str,
    replacement: object,
) -> None:
    """Reject all global authority escalation and identity drift."""
    logger.info("R14.5 global mutation test entry field=%s", field)
    forged = replace(
        build_observer_synthesis_receipts_v2(),
        **{field: replacement},  # type: ignore[arg-type]
    )
    with pytest.raises(InvalidObserverSynthesisReceiptV2):
        validate_observer_synthesis_receipts_v2(forged)
    logger.info("R14.5 global mutation test exit field=%s", field)


@pytest.mark.parametrize(
    "field,replacement",
    (
        ("ordinal", 1),
        ("case_id", 102),
        ("group_id", 1002),
        ("case_digest", "0" * 64),
        ("case_payload_digest", "0" * 64),
        ("clone_digest", "0" * 64),
        ("required_for_winner", False),
        ("matched", False),
        ("outcome_digest", "0" * 64),
        ("source_digests", ("0" * 64, "1" * 64)),
        ("observer_digest", "0" * 64),
        ("response_kind_digest", "0" * 64),
        ("r12_payload_digest", "0" * 64),
        ("ir_digest", "0" * 64),
        ("r12_binding_digest", "0" * 64),
        ("envelope_digest", "0" * 64),
        ("row_digest", "0" * 64),
    ),
)
def test_every_row_identity_or_semantic_mutation_rejects(
    field: str,
    replacement: object,
) -> None:
    """Reject row metadata, semantics, and digest transplant attempts."""
    logger.info("R14.5 row mutation test entry field=%s", field)
    bundle = build_observer_synthesis_receipts_v2()
    forged_row = replace(
        bundle.rows[0],
        **{field: replacement},  # type: ignore[arg-type]
    )
    forged = replace(bundle, rows=(forged_row,) + bundle.rows[1:])
    with pytest.raises(InvalidObserverSynthesisReceiptV2):
        validate_observer_synthesis_receipts_v2(forged)
    logger.info("R14.5 row mutation test exit field=%s", field)


def test_recomputed_row_and_bundle_hashes_do_not_authorize_case_rename() -> None:
    """Self-consistent attacker hashes remain untrusted against full rebuild."""
    logger.info("R14.5 recomputed case rename test entry")
    bundle = build_observer_synthesis_receipts_v2()
    forged_row = _rehash_row(replace(bundle.rows[0], case_id=999))
    forged = _rehash_bundle(bundle, (forged_row,) + bundle.rows[1:])
    receipt_bundle_data_v2(forged)
    with pytest.raises(
        InvalidObserverSynthesisReceiptV2,
        match="receipt-bundle-replay-mismatch",
    ):
        validate_observer_synthesis_receipts_v2(forged)
    logger.info("R14.5 recomputed case rename test exit")


def test_ordered_source_and_transport_transplants_fail_even_with_rehash() -> None:
    """A valid R12 transport from another case cannot be relabelled."""
    logger.info("R14.5 transport transplant test entry")
    bundle = build_observer_synthesis_receipts_v2()
    donor = bundle.rows[2]
    target = bundle.rows[0]
    forged_row = _rehash_row(
        replace(
            target,
            source_digests=donor.source_digests,
            r12_payload_digest=donor.r12_payload_digest,
            ir_digest=donor.ir_digest,
            r12_binding_digest=donor.r12_binding_digest,
            envelope_digest=donor.envelope_digest,
            transport=donor.transport,
        )
    )
    forged = _rehash_bundle(bundle, (forged_row,) + bundle.rows[1:])
    receipt_bundle_data_v2(forged)
    with pytest.raises(InvalidObserverSynthesisReceiptV2):
        validate_observer_synthesis_receipts_v2(forged)
    logger.info("R14.5 transport transplant test exit")


def test_r9_provenance_cannot_replace_the_pinned_r7_receipt() -> None:
    """Equivalent recurrence images do not erase the exact source lane."""
    logger.info("R14.5 R9 provenance test entry")
    bundle = build_observer_synthesis_receipts_v2()
    case = DEFAULT_CASES[0]
    observer = Apply(PrimitiveId.CREST, Input())
    transport = lower_r11_echo(
        observer,
        encode_recurrence(case.left),
        encode_recurrence(case.right),
    )
    envelope = intrinsic_transport_envelope_data(transport)
    row = bundle.rows[0]
    forged_row = replace(
        row,
        source_digests=transport.receipt.source_digests,
        r12_payload_digest=transport.receipt.payload_digest,
        ir_digest=transport.receipt.ir_digest,
        r12_binding_digest=transport.receipt.binding_digest,
        envelope_digest=digest_transport_data(envelope),
        transport=transport,
    )
    forged = replace(bundle, rows=(forged_row,) + bundle.rows[1:])
    with pytest.raises(InvalidObserverSynthesisReceiptV2):
        validate_observer_synthesis_receipts_v2(forged)
    logger.info("R14.5 R9 provenance test exit")


def test_exact_bundle_type_rejects_subclass_and_unrelated_object() -> None:
    """Close extension DTOs before any equality hooks can run."""
    logger.info("R14.5 exact bundle type test entry")

    class BundleSubclass(ObserverSynthesisReceiptBundleV2):
        """Hostile extension marker."""

    bundle = build_observer_synthesis_receipts_v2()
    subclass = BundleSubclass(
        *(
            getattr(bundle, field)
            for field in bundle.__dataclass_fields__
        )
    )
    for hostile in (object(), subclass):
        with pytest.raises(InvalidObserverSynthesisReceiptV2):
            validate_observer_synthesis_receipts_v2(hostile)
    logger.info("R14.5 exact bundle type test exit")


@pytest.mark.parametrize(
    "depth,field",
    (
        (0, "catalog_digest"),
        (1, "case_digest"),
        (2, "receipt"),
        (3, "lane"),
    ),
)
def test_deleted_slots_map_to_typed_invalid(depth: int, field: str) -> None:
    """Malformed bundle, row, transport, and receipt DTOs fail closed."""
    logger.info("R14.5 deleted-slot test entry depth=%d field=%s", depth, field)
    bundle = build_observer_synthesis_receipts_v2()
    targets = (bundle, bundle.rows[0], bundle.rows[0].transport,
               bundle.rows[0].transport.receipt)
    object.__delattr__(targets[depth], field)
    with pytest.raises(InvalidObserverSynthesisReceiptV2):
        validate_observer_synthesis_receipts_v2(bundle)
    logger.info("R14.5 deleted-slot test exit depth=%d", depth)


def test_oversized_winner_canonical_rejects_before_codec(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exact literal winner binding rejects before decoding hostile bytes."""
    logger.info("R14.5 oversized winner canonical test entry")
    bundle = build_observer_synthesis_receipts_v2()
    forged = replace(bundle, winner_canonical=b"A" * (1024 * 1024))

    def forbidden_codec(_bundle: object) -> bytes:
        raise AssertionError("codec reached before exact winner preflight")

    monkeypatch.setattr(validation_module, "receipt_bundle_bytes_v2", forbidden_codec)
    with pytest.raises(
        InvalidObserverSynthesisReceiptV2,
        match="invalid-receipt-winner-binding",
    ):
        validate_observer_synthesis_receipts_v2(forged)
    logger.info("R14.5 oversized winner canonical test exit")


def test_winner_preflight_rejects_hostile_equality_without_calling_it() -> None:
    """Winner preflight exact-types fields before any comparison hook."""
    logger.info("R14.5 hostile winner equality test entry")
    calls = 0

    class Hostile:
        def __eq__(self, _other: object) -> bool:
            nonlocal calls
            calls += 1
            raise AssertionError("hostile equality executed")

    bundle = build_observer_synthesis_receipts_v2()
    for field in ("winner_ordinal", "winner_cost", "winner_depth",
                  "winner_canonical", "winner_digest"):
        with pytest.raises(
            InvalidObserverSynthesisReceiptV2,
            match="invalid-receipt-winner-fields",
        ):
            forged = replace(bundle, **{field: Hostile()})  # type: ignore[arg-type]
            validate_observer_synthesis_receipts_v2(forged)
    assert calls == 0
    logger.info("R14.5 hostile winner equality test exit calls=%d", calls)
