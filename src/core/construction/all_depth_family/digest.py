"""Tagged length-prefixed commitments for P1-D3 identities."""

from __future__ import annotations

from hashlib import sha256
import logging

logger = logging.getLogger(__name__)


def frame(domain: str, fields: tuple[tuple[str, bytes], ...]) -> bytes:
    logger.debug("frame entry domain=%s fields=%d", domain, len(fields))
    out = bytearray(b"VEYRA-P1-D3\x00")
    token(out, b"domain", domain.encode())
    token(out, b"count", len(fields).to_bytes(8, "big"))
    for tag, value in fields:
        token(out, tag.encode(), value)
    result = bytes(out)
    logger.debug("frame exit domain=%s bytes=%d", domain, len(result))
    return result


def token(out: bytearray, tag: bytes, value: bytes) -> None:
    logger.debug("token entry tag=%d value=%d", len(tag), len(value))
    out.extend(len(tag).to_bytes(4, "big"))
    out.extend(tag)
    out.extend(len(value).to_bytes(8, "big"))
    out.extend(value)
    logger.debug("token exit")


def digest(domain: str, fields: tuple[tuple[str, bytes], ...]) -> str:
    logger.debug("digest entry domain=%s", domain)
    result = sha256(frame(domain, fields)).hexdigest()
    logger.debug("digest exit domain=%s", domain)
    return result


def text_rows(prefix: str, values: tuple[str, ...]) -> tuple[tuple[str, bytes], ...]:
    logger.debug("text_rows entry prefix=%s count=%d", prefix, len(values))
    result = ((f"{prefix}-count", len(values).to_bytes(8, "big")),) + tuple(
        (f"{prefix}-{i}", value.encode()) for i, value in enumerate(values)
    )
    logger.debug("text_rows exit prefix=%s", prefix)
    return result


def spec_digest(
    version: str, doctrine_version: str, doctrine: str, alphabet_digest: str,
    natural: str, encoding: str, validator: str, relation: str, restriction: str,
    relation_laws: tuple[str, ...], restriction_laws: tuple[str, ...], family_eq: str,
) -> str:
    logger.debug("spec_digest entry")
    fields = (
        ("version", version.encode()), ("doctrine-version", doctrine_version.encode()),
        ("doctrine", doctrine.encode()), ("alphabet", alphabet_digest.encode()),
        ("natural", natural.encode()), ("encoding", encoding.encode()),
        ("validator", validator.encode()), ("relation", relation.encode()),
        ("restriction", restriction.encode()),
        *text_rows("relation-law", relation_laws),
        *text_rows("restriction-law", restriction_laws), ("family-eq", family_eq.encode()),
    )
    result = digest("veyra.p1d3.spec.v1", fields)
    logger.debug("spec_digest exit")
    return result


def ledger_digest(
    version: str, foundation: str, tcb: str,
    rows: tuple[tuple[str, str, tuple[str, ...]], ...], closure: tuple[str, ...],
) -> str:
    logger.debug("ledger_digest entry rows=%d", len(rows))
    encoded = tuple(
        (f"row-{i}", frame("veyra.p1d3.ledger-row.v1", (
            ("id", name.encode()), ("kind", kind.encode()), *text_rows("dep", deps),
        ))) for i, (name, kind, deps) in enumerate(rows)
    )
    result = digest("veyra.p1d3.ledger.v1", (
        ("version", version.encode()), ("foundation", foundation.encode()),
        ("tcb", tcb.encode()), ("row-count", len(rows).to_bytes(8, "big")), *encoded,
        *text_rows("closure", closure),
    ))
    logger.debug("ledger_digest exit")
    return result


def formal_digest(
    version: str, foundation: str, artifact: str, artifact_sha: str,
    theorem_ids: tuple[str, ...], axiom_closure: tuple[str, ...], toolchain: str, tcb: str,
) -> str:
    logger.debug("formal_digest entry")
    result = digest("veyra.p1d3.formal-source.v1", (
        ("version", version.encode()), ("foundation", foundation.encode()),
        ("artifact", artifact.encode()), ("artifact-sha", artifact_sha.encode()),
        *text_rows("theorem", theorem_ids), *text_rows("axiom", axiom_closure),
        ("toolchain", toolchain.encode()), ("tcb", tcb.encode()),
    ))
    logger.debug("formal_digest exit")
    return result


def term_digest(
    version: str, constructor: str, program_digest: str | None,
    symbolic_term: bytes, spec: str,
) -> str:
    logger.debug("term_digest entry")
    result = digest("veyra.p1d3.family-term.v1", (
        ("version", version.encode()), ("constructor", constructor.encode()),
        ("program", b"none" if program_digest is None else program_digest.encode()),
        ("symbolic-term", symbolic_term), ("spec", spec.encode()),
    ))
    logger.debug("term_digest exit")
    return result


def hypothesis_digest(domain: str, fields: tuple[tuple[str, bytes], ...]) -> str:
    logger.debug("hypothesis_digest entry domain=%s", domain)
    result = digest(f"veyra.p1d3.hypothesis.{domain}.v1", fields)
    logger.debug("hypothesis_digest exit")
    return result


def introduction_digest(kind: str, source_fields: tuple[tuple[str, bytes], ...]) -> str:
    logger.debug("introduction_digest entry kind=%s", kind)
    result = digest(f"veyra.p1d3.introduction.{kind}.v1", source_fields)
    logger.debug("introduction_digest exit")
    return result


def source_digest(kind: str, spec: str, term: str, evidence: str, capability: str) -> str:
    logger.debug("source_digest entry")
    result = digest("veyra.p1d3.source.v1", (
        ("kind", kind.encode()), ("spec", spec.encode()), ("term", term.encode()),
        ("evidence", evidence.encode()), ("capability", capability.encode()),
    ))
    logger.debug("source_digest exit")
    return result


def judgment_digest(fields: tuple[tuple[str, bytes], ...]) -> str:
    logger.debug("judgment_digest entry")
    result = digest("veyra.p1d3.judgment.v1", fields)
    logger.debug("judgment_digest exit")
    return result


def projection_run_digest(
    source: str, family: str, evidence: str, policy: str, depth: int,
) -> str:
    logger.debug("projection_run_digest entry")
    result = digest("veyra.p1d3.projection-run.v1", (
        ("source", source.encode()), ("family", family.encode()),
        ("evidence", evidence.encode()), ("policy", policy.encode()),
        ("depth", depth.to_bytes(8, "big")),
    ))
    logger.debug("projection_run_digest exit")
    return result


def projection_result_digest(fields: tuple[tuple[str, bytes], ...]) -> str:
    logger.debug("projection_result_digest entry")
    result = digest("veyra.p1d3.projection-result.v1", fields)
    logger.debug("projection_result_digest exit")
    return result
