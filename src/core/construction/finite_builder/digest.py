"""Length-prefixed commitments for provisional P1-B finite replay."""

from __future__ import annotations

from hashlib import sha256
import logging

_LEGACY_MODULE = "src.core.finite_builder_digest"
logger = logging.getLogger(_LEGACY_MODULE)


def _digest_tokens(tokens: tuple[bytes, ...]) -> str:
    """Hash an exact tuple of bytes using self-delimiting lengths."""
    logger.debug("_digest_tokens entry")
    if type(tokens) is not tuple or any(type(token) is not bytes for token in tokens):
        logger.error("_digest_tokens exact gate rejected")
        raise ValueError("invalid-finite-builder-digest-input")
    digest = sha256()
    for token in tokens:
        digest.update(len(token).to_bytes(4, "big"))
        digest.update(token)
    result = digest.hexdigest()
    logger.debug("_digest_tokens exit tokens=%d", len(tokens))
    return result


def _seed_digest(seed_id: str, canonical: bytes) -> str:
    """Commit one exact seed identifier and recurrence encoding."""
    logger.debug("_seed_digest entry")
    if type(seed_id) is not str or type(canonical) is not bytes:
        logger.error("_seed_digest exact gate rejected")
        raise ValueError("invalid-seed-digest-input")
    result = _digest_tokens((
        b"kind", b"p1b-seed", b"seed-id", seed_id.encode("utf-8"),
        b"canonical", canonical,
    ))
    logger.debug("_seed_digest exit")
    return result


def _program_digest(
    builder_id: str,
    output_stage_id: str,
    observer_ids: tuple[str, ...],
    canonical: bytes,
    seed_ids: tuple[str, ...],
) -> str:
    """Commit one exact closed builder and output shell."""
    logger.debug("_program_digest entry")
    if (
        type(builder_id) is not str
        or type(output_stage_id) is not str
        or type(observer_ids) is not tuple
        or type(canonical) is not bytes
        or type(seed_ids) is not tuple
        or any(type(item) is not str for item in (*observer_ids, *seed_ids))
    ):
        logger.error("_program_digest exact gate rejected")
        raise ValueError("invalid-program-digest-input")
    observer_rows = tuple(
        token for item in observer_ids for token in (b"observer-id", item.encode("utf-8"))
    )
    seed_rows = tuple(
        token for item in seed_ids for token in (b"seed-id", item.encode("utf-8"))
    )
    tokens = (
        b"kind", b"p1b-program", b"builder-id", builder_id.encode("utf-8"),
        b"stage-id", output_stage_id.encode("utf-8"), b"observer-count",
        str(len(observer_ids)).encode("ascii"), *observer_rows, b"canonical", canonical,
        b"seed-count", str(len(seed_ids)).encode("ascii"), *seed_rows,
    )
    result = _digest_tokens(tokens)
    logger.debug("_program_digest exit")
    return result


def _source_digest(
    binding_id: str,
    doctrine_fingerprint: str,
    program_digest: str,
    seed_ids: tuple[str, ...],
    seed_digests: tuple[str, ...],
) -> str:
    """Commit exact doctrine/program/seed membership, not chronology."""
    logger.debug("_source_digest entry")
    if type(seed_ids) is not tuple or type(seed_digests) is not tuple:
        logger.error("_source_digest tuple gate rejected")
        raise ValueError("invalid-source-digest-input")
    if any(type(item) is not str for item in (
        binding_id, doctrine_fingerprint, program_digest, *seed_ids, *seed_digests,
    )) or len(seed_ids) != len(seed_digests):
        logger.error("_source_digest exact gate rejected")
        raise ValueError("invalid-source-digest-input")
    seed_rows = tuple(
        token
        for seed_id, seed_digest in zip(seed_ids, seed_digests, strict=True)
        for token in (
            b"seed-id", seed_id.encode("utf-8"),
            b"seed-digest", seed_digest.encode("ascii"),
        )
    )
    tokens = (
        b"kind", b"p1b-source", b"binding-id", binding_id.encode("utf-8"),
        b"doctrine", doctrine_fingerprint.encode("ascii"), b"program-digest",
        program_digest.encode("ascii"), b"seed-count",
        str(len(seed_ids)).encode("ascii"), *seed_rows,
    )
    result = _digest_tokens(tokens)
    logger.debug("_source_digest exit")
    return result


def _trace_digest(
    source_digest: str,
    stage_commitment: str,
    recurrence_commitment: str,
    nodes: int,
    pulse_depth: int,
) -> str:
    """Commit deterministic replay semantics without object identity."""
    logger.debug("_trace_digest entry")
    if (
        type(source_digest) is not str
        or type(stage_commitment) is not str
        or type(recurrence_commitment) is not str
        or type(nodes) is not int
        or type(pulse_depth) is not int
    ):
        logger.error("_trace_digest exact gate rejected")
        raise ValueError("invalid-trace-digest-input")
    result = _digest_tokens((
        b"kind", b"p1b-trace", b"source", source_digest.encode("ascii"),
        b"stage", stage_commitment.encode("ascii"), b"recurrence",
        recurrence_commitment.encode("ascii"), b"nodes", str(nodes).encode("ascii"),
        b"pulse-depth", str(pulse_depth).encode("ascii"),
    ))
    logger.debug("_trace_digest exit")
    return result


for _legacy_function in (
    _digest_tokens,
    _seed_digest,
    _program_digest,
    _source_digest,
    _trace_digest,
):
    _legacy_function.__module__ = _LEGACY_MODULE
del _legacy_function, _LEGACY_MODULE
