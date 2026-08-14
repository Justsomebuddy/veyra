"""Injective domain-separated digests for P1-A transport v2."""

from __future__ import annotations
from hashlib import sha256
import logging
from ..observer_morphism_types import ObserverMorphismJudgment
from ..observer_morphism_validation import response_kind_signature
from .types import P1AEndpointPartitionLawV2, P1AObservationCommutingRowV2, P1AObservationTransportV2

logger = logging.getLogger(__name__)


def _f(tag: str, payload: bytes) -> bytes:
    logger.debug("p1a v2 digest frame entry tag=%s bytes=%d", tag, len(payload))
    name = tag.encode("ascii")
    result = len(name).to_bytes(2, "big") + name + len(payload).to_bytes(8, "big") + payload
    logger.debug("p1a v2 digest frame exit tag=%s bytes=%d", tag, len(result))
    return result


def _s(tag: str, items: tuple[bytes, ...]) -> bytes:
    logger.debug("p1a v2 digest sequence entry tag=%s items=%d", tag, len(items))
    result = _f(tag, len(items).to_bytes(4, "big") + b"".join(_f("item", item) for item in items))
    logger.debug("p1a v2 digest sequence exit tag=%s bytes=%d", tag, len(result))
    return result


def _d(domain: str, *fields: bytes) -> str:
    logger.debug("p1a v2 digest root entry domain=%s fields=%d", domain, len(fields))
    result = sha256(_f("domain", domain.encode("ascii")) + b"".join(fields)).hexdigest()
    logger.debug("p1a v2 digest root exit domain=%s digest=%s", domain, result[:12])
    return result


def _text(tag: str, value: str) -> bytes:
    """Frame one exact textual field without delimiter ambiguity."""
    logger.debug("p1a v2 digest text entry tag=%s", tag)
    result = _f(tag, value.encode("utf-8"))
    logger.debug("p1a v2 digest text exit tag=%s", tag)
    return result


def _domain_profile(tag: str, profile) -> bytes:
    """Frame every field of one freshly reconstructed domain profile."""
    logger.debug("p1a v2 domain profile root entry tag=%s", tag)
    result = _s(
        tag,
        (
            _text("observer-id", profile.observer_id),
            _text("minimum-pulse-depth", str(profile.minimum_pulse_depth)),
            _text("nonempty-witness-depth", str(profile.nonempty_witness_depth)),
            _text("structurally-confirmed", str(profile.structurally_confirmed)),
            _text("scope", profile.scope),
        ),
    )
    logger.debug("p1a v2 domain profile root exit tag=%s", tag)
    return result


def judgment_root(j: ObserverMorphismJudgment) -> str:
    logger.debug("p1a v2 judgment_root entry")
    t = j.translation
    comparison = j.comparison_domain
    translation = (
        _s(
            "translation",
            (
                _text("translation-id", t.translation_id),
                _text("doctrine", t.doctrine_fingerprint),
                _text("binding", t.source_binding_digest),
                _text("fine-observer", t.fine_observer_id),
                _text("coarse-observer", t.coarse_observer_id),
                _s("projection", tuple(_text("step", step.value) for step in t.projection)),
                _s("fine-kind", tuple(_text("kind", item) for item in response_kind_signature(t.fine_kind))),
                _s("coarse-kind", tuple(_text("kind", item) for item in response_kind_signature(t.coarse_kind))),
                _text("digest", t.translation_digest),
                _text("scope", t.scope),
            ),
        )
        if t is not None
        else _s("translation", ())
    )
    result = _d(
        "veyra.p1-r16.p1a-strong-judgment.v2",
        _text("morphism-id", j.morphism_id),
        _text("doctrine", j.doctrine_fingerprint),
        _text("binding", j.source_binding_digest),
        _text("fine-observer", j.fine_observer_id),
        _text("coarse-observer", j.coarse_observer_id),
        _domain_profile("fine-domain", j.fine_domain),
        _domain_profile("coarse-domain", j.coarse_domain),
        _s(
            "comparison-domain",
            (
                _text("fine-minimum-depth", str(comparison.fine_minimum_depth)),
                _text("coarse-minimum-depth", str(comparison.coarse_minimum_depth)),
                _text("witness-depth", str(comparison.witness_depth)),
                _text("confirmed-nonempty", str(comparison.confirmed_nonempty)),
                _text("scope", comparison.scope),
            ),
        ),
        translation,
        _text("information-factorizes", str(j.information_factorizes_on_comparison)),
        _text("coarse-domain-in-fine", str(j.coarse_domain_in_fine_domain)),
        _text("witness-checked", str(j.witness_checked)),
        _text("information-loss", j.information_loss.value),
        _text("status", j.status.value),
        _text("obstruction", j.obstruction),
        _text("scope", j.scope),
    )
    logger.debug("p1a v2 judgment_root exit digest=%s", result[:12])
    return result


def payload_digest(payload: bytes) -> str:
    logger.debug("p1a v2 payload digest entry bytes=%d", len(payload))
    result = sha256(payload).hexdigest()
    logger.debug("p1a v2 payload digest exit digest=%s", result[:12])
    return result


def row_digest(row: P1AObservationCommutingRowV2) -> str:
    logger.debug("p1a v2 row digest entry source=%d target=%d", row.source_index, row.target_index)
    payloads = (
        row.source_fine,
        row.source_transported,
        row.source_coarse,
        row.target_fine,
        row.target_transported,
        row.target_coarse,
    )
    result = _d(
        "veyra.p1-r16.p1a-observation-row.v2",
        _f("source", row.source_index.to_bytes(4, "big")),
        _f("target", row.target_index.to_bytes(4, "big")),
        _f("source-input", row.source_input_commitment.encode("ascii")),
        _f("target-input", row.target_input_commitment.encode("ascii")),
        _s(
            "payloads",
            tuple(
                _f("status", p.status.value.encode("ascii"))
                + _f("bytes", p.canonical_payload)
                + _f("digest", p.payload_digest.encode("ascii"))
                for p in payloads
            ),
        ),
        _f("law", row.law.value.encode("ascii")),
    )
    logger.debug("p1a v2 row digest exit digest=%s", result[:12])
    return result


def _partition_classes(items: tuple[int, ...]) -> bytes:
    """Frame one finite partition class sequence."""
    logger.debug("p1a v2 partition classes entry items=%d", len(items))
    result = _s("classes", tuple(item.to_bytes(4, "big") for item in items))
    logger.debug("p1a v2 partition classes exit bytes=%d", len(result))
    return result


def partition_digest(law: P1AEndpointPartitionLawV2) -> str:
    logger.debug("p1a v2 partition digest entry endpoint=%s", law.endpoint.value)
    result = _d(
        "veyra.p1-r16.p1a-partition-law.v2",
        _f("endpoint", law.endpoint.value.encode("ascii")),
        _partition_classes(law.fine_partition),
        _partition_classes(law.transported_partition),
        _partition_classes(law.coarse_partition),
        _s("class-map", tuple(i.to_bytes(4, "big") for i in law.fine_to_coarse_class_map)),
    )
    logger.debug("p1a v2 partition digest exit endpoint=%s digest=%s", law.endpoint.value, result[:12])
    return result


def transport_digest(t: P1AObservationTransportV2) -> str:
    logger.debug("p1a v2 transport digest entry")
    result = _d(
        "veyra.p1-r16.p1a-observation-transport.v2",
        *(
            _f(k, v)
            for k, v in (
                ("id", t.transport_id.encode()),
                ("doctrine", t.doctrine_fingerprint.encode("ascii")),
                ("binding", t.source_binding_digest.encode("ascii")),
                ("judgment", t.strong_judgment_root.encode("ascii")),
                ("translation", t.translation.translation_digest.encode("ascii")),
                ("source-context", t.source_context_digest.encode("ascii")),
                ("target-context", t.target_context_digest.encode("ascii")),
                ("source-witness", t.source_witness_digest.encode("ascii")),
                ("target-witness", t.target_witness_digest.encode("ascii")),
                ("morphism", t.context_morphism_digest.encode("ascii")),
                ("v1-receipt", t.v1_receipt_digest.encode("ascii")),
                ("response-policy", t.response_policy.value.encode("ascii")),
                ("cost-policy", t.cost_policy.value.encode("ascii")),
                ("closure-policy", t.closure_policy.value.encode("ascii")),
                ("version", t.version.encode("ascii")),
                ("scope", t.scope.encode("ascii")),
            )
        ),
    )
    logger.debug("p1a v2 transport digest exit digest=%s", result[:12])
    return result


def receipt_digest(
    schema: str,
    t: P1AObservationTransportV2,
    rows: tuple[P1AObservationCommutingRowV2, ...],
    source: P1AEndpointPartitionLawV2,
    target: P1AEndpointPartitionLawV2,
    scope: str,
) -> str:
    logger.debug("p1a v2 receipt digest entry rows=%d", len(rows))
    result = _d(
        "veyra.p1-r16.p1a-realization-transport-receipt.v2",
        _f("schema", schema.encode("ascii")),
        _f("transport", t.transport_digest.encode("ascii")),
        _s("rows", tuple(r.row_digest.encode("ascii") for r in rows)),
        _f("source-partition", source.partition_digest.encode("ascii")),
        _f("target-partition", target.partition_digest.encode("ascii")),
        _f("scope", scope.encode("ascii")),
    )
    logger.debug("p1a v2 receipt digest exit digest=%s", result[:12])
    return result
