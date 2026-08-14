"""Frozen resource boundaries and anti-splice limits for RFC 169 P1-A v2."""

from __future__ import annotations

from dataclasses import replace
import logging
import re

import pytest

from src.core.observer_core_semantics import MAX_OBSERVER_DEPTH, MAX_OBSERVER_NODES
from src.core.observer_core_types import (
    Blocked,
    ObserverObstruction,
    ObstructionCode,
    PathStep,
    Ready,
    RecurrenceValue,
)
from src.core.observer_morphism_types import ProjectionStep
from src.core.observer_morphism_validation import translation_digest
from src.core.observer_realization_types import ObservationStatus
from src.core.p1a_realization_transport_v2 import (
    P1AEndpointPartitionLawV2,
    P1AEndpointV2,
    P1AObservationPayloadV2,
    P1ARealizationTransportValidationError,
    p1a_realization_transport_v2,
    verify_p1a_realization_transport_v2,
)
from src.core.p1a_realization_transport_v2 import observation as p1a_observation
from src.core.p1a_realization_transport_v2 import runtime as p1a_runtime
from src.core.p1a_realization_transport_v2 import validation as p1a_validation
from src.core.p1a_realization_transport_v2.digest import (
    payload_digest,
    receipt_digest,
    row_digest,
    transport_digest,
)
from src.core.proof_core_types import Pulse, Silence

from p1a_realization_transport_v2_fixture import (
    P1ATransportCase,
    fixed_p1a_case,
    mixed_projection_case,
)


logger = logging.getLogger(__name__)

TRANSPORT_ID = "limits-v2-transport"
MORPHISM_ID = "limits-v2-morphism"
FINE_ID = "fine-total"
COARSE_ID = "coarse-crest"
PROJECTION = (ProjectionStep.LEFT,)


def _build(case: P1ATransportCase):
    """Build the common exact Ready receipt."""
    logger.debug("limits build helper entry")
    result = p1a_realization_transport_v2(
        case.doctrine,
        case.binding,
        case.source,
        case.target,
        case.source_witness,
        case.target_witness,
        case.context_transport,
        transport_id=TRANSPORT_ID,
        p1a_morphism_id=MORPHISM_ID,
        fine_observer_id=FINE_ID,
        coarse_observer_id=COARSE_ID,
        projection=PROJECTION,
    )
    logger.debug("limits build helper exit rows=%d", len(result.rows))
    return result


def _verify(case: P1ATransportCase, receipt):
    """Verify a supplied receipt against the common authoritative spec."""
    logger.debug("limits verify helper entry")
    result = verify_p1a_realization_transport_v2(
        case.doctrine,
        case.binding,
        case.source,
        case.target,
        case.source_witness,
        case.target_witness,
        case.context_transport,
        receipt,
        transport_id=TRANSPORT_ID,
        p1a_morphism_id=MORPHISM_ID,
        fine_observer_id=FINE_ID,
        coarse_observer_id=COARSE_ID,
        projection=PROJECTION,
    )
    logger.debug("limits verify helper exit rows=%d", len(result.rows))
    return result


def _resign_row(row):
    """Rebind one forged row to all of its current fields."""
    logger.debug("limits resign row helper entry")
    provisional = replace(row, row_digest="0" * 64)
    result = replace(provisional, row_digest=row_digest(provisional))
    logger.debug("limits resign row helper exit")
    return result


def _resign_transport(transport):
    """Rebind one forged transport to all of its current fields."""
    logger.debug("limits resign transport helper entry")
    provisional = replace(transport, transport_digest="0" * 64)
    result = replace(provisional, transport_digest=transport_digest(provisional))
    logger.debug("limits resign transport helper exit")
    return result


def _resign_receipt(receipt, *, transport=None, rows=None):
    """Rebind a forged receipt after an intentional child replacement."""
    logger.debug("limits resign receipt helper entry")
    selected_transport = receipt.transport if transport is None else transport
    selected_rows = receipt.rows if rows is None else rows
    result = replace(
        receipt,
        transport=selected_transport,
        rows=selected_rows,
        receipt_digest=receipt_digest(
            receipt.schema,
            selected_transport,
            selected_rows,
            receipt.source_partition_law,
            receipt.target_partition_law,
            receipt.scope,
        ),
    )
    logger.debug("limits resign receipt helper exit")
    return result


def _blocked_payload() -> P1AObservationPayloadV2:
    """Return one exact minimal Blocked payload."""
    logger.debug("limits blocked payload helper entry")
    result = p1a_observation.canonical_observation_payload(
        Blocked((ObserverObstruction(ObstructionCode.TAIL_OF_SILENCE, (PathStep.APPLY_TAIL,)),))
    )
    logger.debug("limits blocked payload helper exit")
    return result


def _unique_obstructions(count: int, *, width: int) -> tuple[ObserverObstruction, ...]:
    """Build deterministic unique bounded paths without data-dependent logging."""
    logger.debug("limits obstruction helper entry count=%d width=%d", count, width)
    result = tuple(
        ObserverObstruction(
            ObstructionCode.TAIL_OF_SILENCE,
            tuple(PathStep.PAIR_RIGHT if index & (1 << bit) else PathStep.PAIR_LEFT for bit in range(width))
            + (PathStep.APPLY_TAIL,),
        )
        for index in range(count)
    )
    logger.debug("limits obstruction helper exit count=%d", len(result))
    return result


def test_frozen_resource_constants_and_aggregate_node_crossover() -> None:
    """The combined shallow/decoded ceiling accepts 65,536, not 65,537."""
    logger.debug("aggregate node crossover test entry")
    assert p1a_validation.MAX_P1A_V2_RECEIPT_NODES == 65_536
    assert p1a_validation._charge_expanded_nodes(32_768, 32_768) == 65_536
    with pytest.raises(P1ARealizationTransportValidationError, match="p1a-receipt-node-limit"):
        p1a_validation._charge_expanded_nodes(32_768, 32_769)
    logger.debug("aggregate node crossover test exit")


def test_snapshot_uses_one_inclusive_shallow_plus_decoded_node_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Receipt snapshotting applies one ceiling to its DTO and decoded JSON nodes."""
    logger.debug("snapshot aggregate node budget test entry")
    case = fixed_p1a_case(name="limits-snapshot-node-budget")
    receipt = _build(case)
    shallow = p1a_validation._preflight_receipt(receipt)
    decoded = sum(
        p1a_validation._canonical_payload(payload)[1]
        for row in receipt.rows
        for payload in (
            row.source_fine,
            row.source_transported,
            row.source_coarse,
            row.target_fine,
            row.target_transported,
            row.target_coarse,
        )
    )
    assert decoded > 0
    monkeypatch.setattr(p1a_validation, "MAX_P1A_V2_RECEIPT_NODES", shallow + decoded)
    assert (
        p1a_validation.snapshot_receipt(
            receipt,
            case.doctrine,
            case.binding,
            source_count=len(case.source.inputs),
            target_count=len(case.target.inputs),
        )
        == receipt
    )
    monkeypatch.setattr(p1a_validation, "MAX_P1A_V2_RECEIPT_NODES", shallow + decoded - 1)
    with pytest.raises(P1ARealizationTransportValidationError, match="p1a-receipt-node-limit"):
        p1a_validation.snapshot_receipt(
            receipt,
            case.doctrine,
            case.binding,
            source_count=len(case.source.inputs),
            target_count=len(case.target.inputs),
        )
    logger.debug("snapshot aggregate node budget test exit")


def test_utf8_nonpayload_text_crossover_excludes_canonical_payload_bytes() -> None:
    """UTF-8 text accepts 1,048,576 bytes and payload bodies are separately charged."""
    logger.debug("aggregate text crossover test entry")
    assert p1a_validation.MAX_P1A_V2_RECEIPT_TEXT_BYTES == 1_048_576
    exact = "é" * 524_288
    assert p1a_validation._charge_text(0, exact, "test-text") == 1_048_576
    with pytest.raises(P1ARealizationTransportValidationError, match="p1a-receipt-text-limit"):
        p1a_validation._charge_text(0, exact + "x", "test-text")

    empty = P1AObservationPayloadV2(ObservationStatus.READY, b"", payload_digest(b""))
    full_raw = b"x" * p1a_validation.MAX_P1A_V2_PAYLOAD_BYTES
    full = P1AObservationPayloadV2(ObservationStatus.READY, full_raw, payload_digest(full_raw))
    assert p1a_validation._preflight_payload(empty) == p1a_validation._preflight_payload(full)
    logger.debug("aggregate text crossover test exit")


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        (
            b'{"tag":"ready","tag":"ready","value":{"mark":"silent","tag":"mark"}}',
            "invalid-p1a-payload",
        ),
        (
            b'{"tag":"ready","value":{"mark":"silent","tag":"mark"}}x',
            "invalid-p1a-payload",
        ),
        (
            b'{ "tag":"ready","value":{"mark":"silent","tag":"mark"}}',
            "p1a-payload-noncanonical",
        ),
    ],
    ids=["duplicate-key", "trailing-json", "noncanonical-json"],
)
def test_hostile_json_payloads_reject_before_replay(raw: bytes, reason: str) -> None:
    """Duplicate, trailing, and noncanonical JSON never enter semantic replay."""
    logger.debug("hostile JSON payload test entry case=%s", reason)
    payload = P1AObservationPayloadV2(ObservationStatus.READY, raw, payload_digest(raw))
    with pytest.raises(P1ARealizationTransportValidationError, match=reason):
        p1a_validation._canonical_payload(payload)
    logger.debug("hostile JSON payload test exit case=%s", reason)


def test_six_stream_precharge_exact_boundary_and_one_byte_over() -> None:
    """The preconstructor accepts 33,554,432 retained bytes and rejects one more."""
    logger.debug("six stream exact crossover test entry")
    assert p1a_validation.MAX_P1A_V2_SIX_STREAM_BYTES == 33_554_432
    assert p1a_runtime.MAX_P1A_V2_SIX_STREAM_BYTES == 33_554_432
    assert p1a_validation.MAX_P1A_V2_ROWS == 256

    base = P1AObservationPayloadV2(ObservationStatus.READY, b"x" * 21_845, "0" * 64)
    larger = P1AObservationPayloadV2(ObservationStatus.READY, b"x" * 21_847, "0" * 64)
    one_over = P1AObservationPayloadV2(ObservationStatus.READY, b"x" * 21_848, "0" * 64)
    base_stream = (base,) * 256
    larger_stream = (larger,) * 256
    graph = tuple(range(256))
    assert (
        p1a_runtime._precharge_retained_streams(
            graph,
            base_stream,
            base_stream,
            base_stream,
            base_stream,
            base_stream,
            larger_stream,
        )
        == 33_554_432
    )
    over_stream = (one_over,) + larger_stream[1:]
    with pytest.raises(P1ARealizationTransportValidationError, match="p1a-six-stream-byte-limit"):
        p1a_runtime._precharge_retained_streams(
            graph,
            base_stream,
            base_stream,
            base_stream,
            base_stream,
            base_stream,
            over_stream,
        )
    logger.debug("six stream exact crossover test exit")


@pytest.mark.parametrize("endpoint_field", ["source_transported", "target_transported"])
def test_transported_endpoint_accepts_8388608_and_rejects_8388609(
    endpoint_field: str,
) -> None:
    """Each transported endpoint has its own inclusive 8 MiB receipt ceiling."""
    logger.debug("transported endpoint crossover test entry endpoint=%s", endpoint_field)
    case = fixed_p1a_case(name=f"limits-endpoint-bytes-{endpoint_field}")
    receipt = _build(case)
    assert p1a_validation.MAX_P1A_V2_TRANSPORTED_ENDPOINT_BYTES == 8_388_608

    empty = P1AObservationPayloadV2(ObservationStatus.READY, b"", "0" * 64)
    exact = P1AObservationPayloadV2(ObservationStatus.READY, b"x" * 32_768, "0" * 64)
    one_over = P1AObservationPayloadV2(ObservationStatus.READY, b"x" * 32_769, "0" * 64)
    exact_row = replace(
        receipt.rows[0],
        source_fine=empty,
        source_transported=exact,
        source_coarse=empty,
        target_fine=empty,
        target_transported=exact,
        target_coarse=empty,
    )
    exact_receipt = replace(receipt, rows=(exact_row,) * 256)
    assert p1a_validation._preflight_receipt(exact_receipt) > 0

    over_row = replace(exact_row, **{endpoint_field: one_over})
    over_receipt = replace(exact_receipt, rows=(over_row, *exact_receipt.rows[1:]))
    with pytest.raises(
        P1ARealizationTransportValidationError,
        match="p1a-transported-endpoint-byte-limit",
    ):
        p1a_validation._preflight_receipt(over_receipt)
    logger.debug("transported endpoint crossover test exit endpoint=%s", endpoint_field)


def test_runtime_precharge_rejects_before_row_digest_or_receipt_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Public construction fails at precharge before retaining any row or receipt."""
    logger.debug("six stream ordering test entry")
    case = fixed_p1a_case(name="limits-precharge-order")
    receipt = _build(case)
    total = sum(
        len(payload.canonical_payload)
        for row in receipt.rows
        for payload in (
            row.source_fine,
            row.source_transported,
            row.source_coarse,
            row.target_fine,
            row.target_transported,
            row.target_coarse,
        )
    )
    calls = {"row_digest": 0, "receipt": 0}

    def forbidden_row_digest(_value):
        logger.error("forbidden row digest trap called")
        calls["row_digest"] += 1
        raise AssertionError("row digest constructed before precharge")

    def forbidden_receipt(*_args, **_kwargs):
        logger.error("forbidden receipt trap called")
        calls["receipt"] += 1
        raise AssertionError("receipt constructed before precharge")

    monkeypatch.setattr(p1a_runtime, "MAX_P1A_V2_SIX_STREAM_BYTES", total)
    assert _build(case) == receipt
    monkeypatch.setattr(p1a_runtime, "MAX_P1A_V2_SIX_STREAM_BYTES", total - 1)
    monkeypatch.setattr(p1a_runtime, "row_digest", forbidden_row_digest)
    monkeypatch.setattr(p1a_runtime, "P1ARealizationTransportReceiptV2", forbidden_receipt)
    with pytest.raises(P1ARealizationTransportValidationError, match="p1a-six-stream-byte-limit"):
        _build(case)
    assert calls == {"row_digest": 0, "receipt": 0}
    logger.debug("six stream ordering test exit")


def test_obstruction_path_depth_accepts_128_and_rejects_129() -> None:
    """Construction accepts the exact obstruction depth cap and rejects cap+1."""
    logger.debug("obstruction depth test entry")
    assert MAX_OBSERVER_DEPTH == 128
    exact_path = (PathStep.PAIR_LEFT,) * 127 + (PathStep.APPLY_TAIL,)
    assert (
        len(
            p1a_observation._safe_obstructions_data(
                (ObserverObstruction(ObstructionCode.TAIL_OF_SILENCE, exact_path),)
            )[0]["path"]
        )
        == 128
    )
    over_path = (PathStep.PAIR_LEFT,) * 128 + (PathStep.APPLY_TAIL,)
    with pytest.raises(ValueError, match="p1a-obstruction-invalid"):
        p1a_observation._safe_obstructions_data((ObserverObstruction(ObstructionCode.TAIL_OF_SILENCE, over_path),))
    logger.debug("obstruction depth test exit")


def test_obstruction_count_accepts_2048_and_rejects_2049() -> None:
    """Construction accepts the exact obstruction count cap and rejects cap+1."""
    logger.debug("obstruction count test entry")
    assert MAX_OBSERVER_NODES == 2_048
    exact = _unique_obstructions(2_048, width=11)
    assert len(p1a_observation._safe_obstructions_data(exact)) == 2_048
    with pytest.raises(ValueError, match="p1a-obstruction-invalid"):
        p1a_observation._safe_obstructions_data(_unique_obstructions(2_049, width=12))
    logger.debug("obstruction count test exit")


@pytest.mark.parametrize("location", ["source", "target", "partition"])
@pytest.mark.parametrize("value", [True, -1, 256])
def test_indices_and_partition_classes_reject_bool_negative_and_over_255(
    location: str,
    value: object,
) -> None:
    """Every bounded integer surface rejects Boolean coercion and out-of-range values."""
    logger.debug("bounded integer test entry location=%s kind=%s", location, type(value).__name__)
    case = fixed_p1a_case(name=f"limits-int-{location}-{type(value).__name__}-{value}")
    receipt = _build(case)
    if location in {"source", "target"}:
        field = "source_index" if location == "source" else "target_index"
        forged_row = replace(receipt.rows[0], **{field: value})
        forged = replace(receipt, rows=(forged_row, *receipt.rows[1:]))
    else:
        law = replace(
            receipt.source_partition_law,
            fine_partition=(value, *receipt.source_partition_law.fine_partition[1:]),
        )
        assert type(law) is P1AEndpointPartitionLawV2
        forged = replace(receipt, source_partition_law=law)
    with pytest.raises(P1ARealizationTransportValidationError):
        _verify(case, forged)
    logger.debug("bounded integer test exit location=%s", location)


@pytest.mark.parametrize(
    "blocked_fields",
    [
        ("source_transported", "source_coarse", "target_transported", "target_coarse"),
        ("source_fine", "source_transported", "target_fine", "target_transported"),
    ],
    ids=["fine-ready-coarse-blocked", "projected-blocked-coarse-ready"],
)
def test_both_mixed_ready_blocked_status_directions_reject(
    blocked_fields: tuple[str, ...],
) -> None:
    """Neither direction of a mixed Ready/Blocked six-square can be resigned."""
    logger.debug("mixed status direction test entry fields=%d", len(blocked_fields))
    case = fixed_p1a_case(name="limits-mixed-status")
    receipt = _build(case)
    changes = {field: _blocked_payload() for field in blocked_fields}
    row = _resign_row(replace(receipt.rows[0], **changes))
    forged = _resign_receipt(receipt, rows=(row, *receipt.rows[1:]))
    with pytest.raises(P1ARealizationTransportValidationError, match="p1a-row-status-law-drift"):
        _verify(case, forged)
    logger.debug("mixed status direction test exit")


@pytest.mark.parametrize(
    "surface",
    ["doctrine", "source-binding", "response-kind", "response-policy", "cost-policy", "closure-policy"],
)
def test_exact_authority_and_each_policy_surface_are_anti_splice(surface: str) -> None:
    """Every doctrine/binding/kind/policy authority surface rejects a splice."""
    logger.debug("authority anti-splice test entry surface=%s", surface)
    case = fixed_p1a_case(name=f"limits-splice-{surface}")
    receipt = _build(case)
    transport = receipt.transport
    if surface == "doctrine":
        transport = replace(transport, doctrine_fingerprint="0" * 64)
    elif surface == "source-binding":
        transport = replace(transport, source_binding_digest="0" * 64)
    elif surface == "response-kind":
        translation = transport.translation
        forged_translation = replace(translation, fine_kind=translation.coarse_kind)
        forged_translation = replace(
            forged_translation,
            translation_digest=translation_digest(
                forged_translation.translation_id,
                forged_translation.doctrine_fingerprint,
                forged_translation.source_binding_digest,
                forged_translation.fine_observer_id,
                forged_translation.coarse_observer_id,
                forged_translation.projection,
                forged_translation.fine_kind,
                forged_translation.coarse_kind,
            ),
        )
        transport = replace(transport, translation=forged_translation)
    else:
        field = surface.replace("-", "_")
        transport = replace(transport, **{field: getattr(transport, field).value})

    # Exact policy-type splices reject before digesting; all other structurally
    # digestible splices are fully resigned so stale outer hashes cannot mask them.
    if surface not in {"response-policy", "cost-policy", "closure-policy"}:
        transport = _resign_transport(transport)
        forged = _resign_receipt(receipt, transport=transport)
    else:
        forged = replace(receipt, transport=transport)
    with pytest.raises(P1ARealizationTransportValidationError):
        _verify(case, forged)
    logger.debug("authority anti-splice test exit surface=%s", surface)


@pytest.mark.parametrize(
    ("law_field", "wrong_endpoint"),
    [
        ("source_partition_law", P1AEndpointV2.TARGET),
        ("target_partition_law", P1AEndpointV2.SOURCE),
    ],
)
def test_partition_law_rejects_the_wrong_authoritative_endpoint(
    law_field: str,
    wrong_endpoint: P1AEndpointV2,
) -> None:
    """A structurally exact partition law cannot be moved across endpoints."""
    logger.debug("wrong partition endpoint test entry law=%s", law_field)
    case = fixed_p1a_case(name=f"limits-wrong-partition-{law_field}")
    receipt = _build(case)
    law = replace(getattr(receipt, law_field), endpoint=wrong_endpoint)
    forged = replace(receipt, **{law_field: law})
    with pytest.raises(
        P1ARealizationTransportValidationError,
        match="p1a-partition-law-must-be-exact",
    ):
        _verify(case, forged)
    logger.debug("wrong partition endpoint test exit law=%s", law_field)


def test_actual_cross_doctrine_authoritative_inputs_reject() -> None:
    """Foreign contexts, witnesses, and v1 evidence cannot cross doctrine authority."""
    logger.debug("cross-doctrine authoritative input test entry")
    authority = fixed_p1a_case(name="limits-cross-doctrine-authority")
    foreign = mixed_projection_case(name="limits-cross-doctrine-foreign")
    assert authority.doctrine.fingerprint != foreign.doctrine.fingerprint
    with pytest.raises(P1ARealizationTransportValidationError):
        p1a_realization_transport_v2(
            authority.doctrine,
            authority.binding,
            foreign.source,
            foreign.target,
            foreign.source_witness,
            foreign.target_witness,
            foreign.context_transport,
            transport_id=TRANSPORT_ID,
            p1a_morphism_id=MORPHISM_ID,
            fine_observer_id=FINE_ID,
            coarse_observer_id=COARSE_ID,
            projection=PROJECTION,
        )
    logger.debug("cross-doctrine authoritative input test exit")


class _CapturingFilter(logging.Filter):
    """Capture the record text visible to a pre-existing logger filter."""

    def __init__(self) -> None:
        """Initialize an empty record capture."""
        super().__init__()
        self.messages: list[str] = []

    def filter(self, record: logging.LogRecord) -> bool:
        """Capture without logging recursively from inside a logging filter."""
        self.messages.append(record.getMessage())
        return True


def test_root_and_all_logger_capture_never_discloses_nested_payloads(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Debug/error logs omit Pulse reprs, canonical bodies, and obstruction paths."""
    logger.debug("log non-disclosure test entry")
    pulse = Pulse(Pulse(Silence()))
    obstruction = ObserverObstruction(
        ObstructionCode.TAIL_OF_SILENCE,
        (PathStep.PAIR_RIGHT, PathStep.PAIR_LEFT, PathStep.APPLY_TAIL),
    )
    payload = _blocked_payload()
    case = fixed_p1a_case(name="limits-root-log-boundary")
    recurrence_repr = repr(case.source.inputs[0].recurrence)
    lower_loggers = tuple(
        logging.getLogger(name)
        for name in (
            "src.core.proof_core_codec",
            "src.core.observer_descent",
            "src.core.observer_descent_validation",
        )
    )
    preexisting_filter = _CapturingFilter()
    lower_loggers[0].addFilter(preexisting_filter)
    try:
        filters_before = tuple(tuple(item.filters) for item in lower_loggers)
        factory_before = logging.getLogRecordFactory()
        for name, candidate in logging.root.manager.loggerDict.items():
            if isinstance(candidate, logging.Logger):
                caplog.set_level(logging.DEBUG, logger=name)
        logging.setLogRecordFactory(logging.LogRecord)
        try:
            with caplog.at_level(logging.DEBUG):
                ready_payload = p1a_observation.canonical_observation_payload(Ready(RecurrenceValue(pulse)))
                blocked_payload = p1a_observation.canonical_observation_payload(Blocked((obstruction,)))
                with pytest.raises(P1ARealizationTransportValidationError, match="p1a-payload-digest-drift"):
                    p1a_validation._canonical_payload(replace(payload, payload_digest="0" * 64))
                receipt = _build(case)
                assert _verify(case, receipt) == receipt
        finally:
            logging.setLogRecordFactory(factory_before)
        assert logging.getLogRecordFactory() is factory_before
        assert tuple(tuple(item.filters) for item in lower_loggers) == filters_before
        preexisting_capture = "\n".join(preexisting_filter.messages)
    finally:
        lower_loggers[0].removeFilter(preexisting_filter)
    captured = caplog.text + preexisting_capture
    assert re.search(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", captured) is None
    assert repr(pulse) not in captured
    assert recurrence_repr not in captured
    assert repr(payload.canonical_payload) not in captured
    assert payload.canonical_payload.decode("ascii") not in captured
    assert ready_payload.canonical_payload.decode("ascii") not in captured
    assert blocked_payload.canonical_payload.decode("ascii") not in captured
    assert repr(obstruction.path) not in captured
    for row in receipt.rows:
        assert row.source_fine.canonical_payload.decode("ascii") not in captured
        assert row.source_coarse.canonical_payload.decode("ascii") not in captured
    logger.debug("log non-disclosure test exit")
