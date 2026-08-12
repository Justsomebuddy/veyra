"""Self-contained local-receipt replay package for independent composition verification."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from typing import NoReturn

from ..proof_core_codec import canonical_json, digest_data, exact_keys, load_canonical
from .export import (
    _contract_data,
    _contract_from_data,
    _export_data,
    _export_from_data,
    validate_composition_public_export,
)
from .protocol import (
    ClaimCompositionError,
    build_external_composition_source,
    build_local_claim_receipt,
    canonical_composition_sources,
    validate_local_claim_receipt,
)
from .types import (
    ClaimCompositionSource,
    CompositionPublicExport,
    LocalReceiptValidity,
    SourceEffect,
)

logger = logging.getLogger(__name__)

COMPOSITION_REPLAY_SCHEMA = "veyra.claim-composition.replay-package.v1"
COMPOSITION_REPLAY_BOUNDARY = (
    "self-contained replay of local-receipt bindings and composition semantics; external "
    "validator trust, source truth, P2 promotion, theoremhood, and signer trust remain external"
)
MAX_COMPOSITION_REPLAY_BYTES = 1_500_000
_REPLAY_DOMAIN = "veyra.claim-composition.replay-package-payload.v1"


@dataclass(frozen=True, slots=True)
class CompositionReplayPackage:
    """Canonical export plus detached local receipts sufficient for composition replay."""

    schema_version: str
    export: CompositionPublicExport
    sources: tuple[ClaimCompositionSource, ...]
    payload_digest: str
    boundary: str = COMPOSITION_REPLAY_BOUNDARY


def build_composition_replay_package(
    export: CompositionPublicExport,
    sources: tuple[ClaimCompositionSource, ...],
) -> CompositionReplayPackage:
    """Detach source receipts and bind one independently replayable composition package."""
    logger.debug("build_composition_replay_package entry")
    if not validate_composition_public_export(export, sources):
        _reject("replay-package-export")
    detached = canonical_composition_sources(
        tuple(
            build_external_composition_source(source.receipt, source.effect)
            for source in sources
        )
    )
    if tuple(source.receipt.receipt_digest for source in detached) != (
        export.receipt.source_receipt_digests
    ):
        _reject("replay-package-source-family")
    if not validate_composition_public_export(export, detached):
        _reject("replay-package-detached-replay")
    draft = CompositionReplayPackage(
        COMPOSITION_REPLAY_SCHEMA,
        export,
        detached,
        "",
        COMPOSITION_REPLAY_BOUNDARY,
    )
    result = CompositionReplayPackage(
        draft.schema_version,
        draft.export,
        draft.sources,
        digest_data(_replay_payload_data(draft), _REPLAY_DOMAIN),
        draft.boundary,
    )
    logger.info("build_composition_replay_package state=REPLAYABLE source_truth=False")
    logger.debug("build_composition_replay_package exit digest=%s", result.payload_digest[:12])
    return result


def validate_composition_replay_package(value: object) -> bool:
    """Freshly replay a complete package without trusting its derived fields."""
    logger.debug("validate_composition_replay_package entry type=%s", type(value).__name__)
    try:
        valid = (
            type(value) is CompositionReplayPackage
            and value.schema_version == COMPOSITION_REPLAY_SCHEMA
            and value.boundary == COMPOSITION_REPLAY_BOUNDARY
            and value.payload_digest == digest_data(_replay_payload_data(value), _REPLAY_DOMAIN)
            and build_composition_replay_package(value.export, value.sources) == value
        )
    except (AttributeError, ClaimCompositionError, TypeError, UnicodeError, ValueError):
        logger.error("validate_composition_replay_package rejected")
        valid = False
    logger.debug("validate_composition_replay_package exit valid=%s", valid)
    return valid


def composition_replay_package_json(value: CompositionReplayPackage) -> str:
    """Render canonical replay-package JSON only after fresh independent replay."""
    logger.debug("composition_replay_package_json entry")
    if not validate_composition_replay_package(value):
        _reject("replay-package-invalid")
    result = canonical_json(_replay_data(value))
    if len(result.encode("utf-8")) > MAX_COMPOSITION_REPLAY_BYTES:
        _reject("replay-package-size")
    logger.debug("composition_replay_package_json exit bytes=%d", len(result.encode("utf-8")))
    return result


def composition_replay_package_from_json(text: str) -> CompositionReplayPackage:
    """Strictly decode canonical JSON and freshly replay every source binding."""
    logger.debug("composition_replay_package_from_json entry type=%s", type(text).__name__)
    if type(text) is not str or len(text) > MAX_COMPOSITION_REPLAY_BYTES:
        _reject("replay-package-size")
    try:
        encoded = text.encode("utf-8")
    except UnicodeError as exc:
        raise ClaimCompositionError("replay-package-format") from exc
    if len(encoded) > MAX_COMPOSITION_REPLAY_BYTES:
        _reject("replay-package-size")
    try:
        data = load_canonical(text)
        result = _replay_from_data(data)
    except (json.JSONDecodeError, KeyError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        logger.error("composition_replay_package_from_json rejected type=%s", type(exc).__name__)
        raise ClaimCompositionError("replay-package-format") from exc
    if not validate_composition_replay_package(result):
        _reject("replay-package-replay")
    logger.debug("composition_replay_package_from_json exit")
    return result


def _replay_from_data(data: object) -> CompositionReplayPackage:
    """Decode exact package fields without accepting them yet."""
    logger.debug("_replay_from_data entry")
    row = exact_keys(data, {"schema_version", "export", "sources", "payload_digest", "boundary"})
    if row["schema_version"] != COMPOSITION_REPLAY_SCHEMA or type(row["sources"]) is not list:
        _reject("replay-package-schema")
    decoded_sources = tuple(_source_from_data(item) for item in row["sources"])
    sources = canonical_composition_sources(decoded_sources)
    if decoded_sources != sources:
        _reject("replay-package-source-order")
    result = CompositionReplayPackage(
        _text(row["schema_version"], "replay-package-schema"),
        _export_from_data(row["export"]),
        sources,
        _text(row["payload_digest"], "replay-package-digest"),
        _text(row["boundary"], "replay-package-boundary"),
    )
    logger.debug("_replay_from_data exit")
    return result


def _source_from_data(data: object) -> ClaimCompositionSource:
    """Reconstruct one detached local receipt and effect from exact fields."""
    logger.debug("_source_from_data entry")
    row = exact_keys(data, {"contract", "source_receipt_root", "source_validator_root", "validity", "receipt_digest", "effect"})
    receipt = build_local_claim_receipt(
        _contract_from_data(row["contract"]),
        _text(row["source_receipt_root"], "replay-package-source-root"),
        _text(row["source_validator_root"], "replay-package-validator-root"),
        LocalReceiptValidity(_text(row["validity"], "replay-package-validity")),
    )
    if receipt.receipt_digest != _text(
        row["receipt_digest"], "replay-package-receipt-digest"
    ) or not validate_local_claim_receipt(receipt):
        _reject("replay-package-local-receipt")
    result = build_external_composition_source(
        receipt,
        SourceEffect(_text(row["effect"], "replay-package-effect")),
    )
    logger.debug("_source_from_data exit")
    return result


def _replay_data(value: CompositionReplayPackage) -> dict[str, object]:
    """Return complete canonical data including the package digest."""
    logger.debug("_replay_data entry")
    result = {**_replay_payload_data(value), "payload_digest": value.payload_digest}
    logger.debug("_replay_data exit")
    return result


def _replay_payload_data(value: CompositionReplayPackage) -> dict[str, object]:
    """Return the non-self-referential package payload."""
    logger.debug("_replay_payload_data entry")
    result: dict[str, object] = {
        "schema_version": value.schema_version,
        "export": _export_data(value.export),
        "sources": [_source_data(source) for source in value.sources],
        "boundary": value.boundary,
    }
    logger.debug("_replay_payload_data exit")
    return result


def _source_data(source: ClaimCompositionSource) -> dict[str, object]:
    """Serialize only the local receipt contract and its external validator binding."""
    logger.debug("_source_data entry")
    result: dict[str, object] = {
        "contract": _contract_data(source.receipt.contract),
        "source_receipt_root": source.receipt.source_receipt_root,
        "source_validator_root": source.receipt.source_validator_root,
        "validity": source.receipt.validity.value,
        "receipt_digest": source.receipt.receipt_digest,
        "effect": source.effect.value,
    }
    logger.debug("_source_data exit")
    return result


def _text(value: object, reason: str) -> str:
    """Narrow one strict decoded JSON value to non-empty text."""
    logger.debug("_text entry reason=%s type=%s", reason, type(value).__name__)
    if type(value) is not str or not value:
        _reject(reason)
    logger.debug("_text exit reason=%s", reason)
    return value


def _reject(reason: str) -> NoReturn:
    """Raise one stable logged composition-replay error."""
    logger.error("composition replay package rejected reason=%s", reason)
    raise ClaimCompositionError(reason)
