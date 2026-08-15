"""Deterministic external-composition fixtures for P2 claim admission v2."""

from __future__ import annotations

from hashlib import sha256
import logging

from src.core.claim_composition import (
    AdaptiveCapability,
    ClaimClass,
    ClaimQuantifier,
    CorroborationStatus,
    LocalReceiptValidity,
    PublicWording,
    SourceEffect,
    build_claim_contract,
    build_composition_receipt,
    build_composition_public_export,
    build_composition_replay_package,
    build_exact_conjunction_contract,
    build_exact_conjunction_license,
    build_external_composition_source,
    build_governed_composition_source,
    build_local_claim_receipt,
    canonical_composition_sources,
)
from src.core.observer_discovery_v3.dsl import closed_rows_digest, observer_program_digest
from src.core.observer_discovery_v3.dsl.types import ClosedObserverGrammar, ClosedObserverTerm
from src.core.observer_discovery_v3.ledger import OneShotReservation, reserve_one_shot
from src.core.observer_discovery_v3.schema import (
    RepresentationField,
    RepresentationRow,
    RepresentationSchema,
    canonical_presentation,
)
from src.core.observer_discovery_v3.service import execute_one_shot_closed_evaluation

logger = logging.getLogger(__name__)


def root(label: str) -> str:
    """Return one deterministic lowercase SHA-256 root."""
    logger.debug("root entry label_bytes=%d", len(label))
    result = sha256(label.encode("ascii")).hexdigest()
    logger.debug("root exit")
    return result


def composition_case(count: int = 2):
    """Build a canonical exact conjunction with opaque assumptions and validators."""
    logger.debug("composition_case entry count=%d", count)
    sources = []
    for index in range(count):
        contract = build_claim_contract(
            (root(f"claim-{index:02d}"),),
            (root(f"scope-{index:02d}"),),
            (root(f"assumption-{index:02d}"),),
            ClaimQuantifier.LOCAL,
            (),
            (root(f"doctrine-{index % 2}"),),
            (),
            (),
            (),
            (ClaimClass.EMPIRICAL,),
            CorroborationStatus.SINGLE_LOCAL_RECEIPT,
            AdaptiveCapability.LOCAL_ONLY,
            PublicWording.BOUNDED_LOCAL,
        )
        local = build_local_claim_receipt(
            contract,
            root(f"source-{index:02d}"),
            root(f"validator-{index:02d}"),
            LocalReceiptValidity.ESTABLISHED,
        )
        sources.append(build_external_composition_source(local, SourceEffect.INCLUDE_LOCAL_CLAIM))
    canonical = canonical_composition_sources(tuple(sources))
    target = build_exact_conjunction_contract(canonical)
    license = build_exact_conjunction_license(canonical, target)
    receipt = build_composition_receipt(canonical, target, license)
    logger.debug("composition_case exit count=%d", count)
    return canonical, target, license, receipt


def _governed_result(directory, symbol: str):
    """Execute one deterministic READY governed result for authority-path tests."""
    logger.debug("_governed_result entry symbol=%s", symbol)
    directory.mkdir(mode=0o700)
    schema = RepresentationSchema(
        f"p2-v2-{symbol}",
        (RepresentationField("bit", "binary", (0, 1)),),
        ("no", "yes"),
    )
    presentation = canonical_presentation(
        schema,
        (
            RepresentationRow(f"{symbol}0", "s0", "c0", "g0", (0,), "no"),
            RepresentationRow(f"{symbol}1", "s1", "c1", "g1", (1,), "yes"),
        ),
    )
    grammar = ClosedObserverGrammar(f"grammar-{symbol}", 1, (0,), ("column",), 1, 0, 1)
    terms = (ClosedObserverTerm("column", (0,)),)
    rows = tuple(tuple(row.values) for row in presentation.rows)
    reservation = OneShotReservation(
        f"reservation-{symbol}",
        "p2-v2-authority-control",
        symbol * 64,
        presentation.payload_digest,
        presentation.schema_digest,
        closed_rows_digest(rows),
        observer_program_digest(grammar, terms),
        "f" * 64,
    )
    capability = bytes.fromhex(symbol * 64)
    reserve_one_shot(directory, reservation, capability)
    result = execute_one_shot_closed_evaluation(
        directory,
        reservation.reservation_id,
        capability,
        f"attempt-{symbol}",
        presentation,
        grammar,
        terms,
    )
    logger.debug("_governed_result exit status=%s", result.status)
    return result


def native_and_detached_case(tmp_path):
    """Build equal-v1 native and replay-package-detached authority families."""
    logger.debug("native_and_detached_case entry")
    native = canonical_composition_sources(
        tuple(
            build_governed_composition_source(
                _governed_result(tmp_path / f"native-{symbol}", symbol),
                SourceEffect.INCLUDE_LOCAL_CLAIM,
            )
            for symbol in ("a", "b")
        )
    )
    target = build_exact_conjunction_contract(native)
    license = build_exact_conjunction_license(native, target)
    receipt = build_composition_receipt(native, target, license)
    export = build_composition_public_export(receipt, native, target, license)
    package = build_composition_replay_package(export, native)
    logger.debug("native_and_detached_case exit")
    return native, package.sources, target, license, receipt
