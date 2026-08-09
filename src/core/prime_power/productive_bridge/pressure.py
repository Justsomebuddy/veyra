"""Closed, bound, negative-only offset pressure source for P3-A1b."""

from __future__ import annotations

import logging

from ...padic.completion.prime import snapshot_prime
from ...padic.family_introduction.sources import TOOLCHAIN_ID, snapshot_integer
from .common import (
    digest, exact_digest, exact_int, exact_shape, exact_text, reject, signed_bytes,
)
from .types import OffsetResidueProgramSource

logger = logging.getLogger(__name__)
PRESSURE_VERSION = "p3a1b-pressure-program-v1"
PRESSURE_CONSTRUCTOR = "OFFSET_PRIME_POWER_RESIDUE(integer_source,prime_source,offset)"
PRESSURE_GRAMMAR_ID = "closed-negative-only-offset-v1"
PRESSURE_ARTIFACT_PATH = "proofs/lean/VeyraPrimePowerProductiveBridgePressure.lean"
PRESSURE_ARTIFACT_SHA256 = "bb21c6a16d19af66dbc58109bd8d4882619152e795115c15b5519445c3c1f7b5"
PRESSURE_THEOREM_IDS = (
    "THM_P3A1B_PRESSURE_001_total", "THM_P3A1B_PRESSURE_002_coherent",
)
PRESSURE_AXIOM_ROWS = (
    (PRESSURE_THEOREM_IDS[0], ()), (PRESSURE_THEOREM_IDS[1], ("propext",)),
)
MAX_OFFSET_BITS = 4096


def _program_digest(prime_digest: str, integer_digest: str, offset: int) -> str:
    """Bind the exact closed pressure syntax and its p/z/offset constants."""
    logger.debug("_program_digest entry")
    result = digest("veyra.p3a1b.pressure-program.v1", (
        ("version", PRESSURE_VERSION.encode()), ("constructor", PRESSURE_CONSTRUCTOR.encode()),
        ("grammar", PRESSURE_GRAMMAR_ID.encode()), ("prime", prime_digest.encode()),
        ("integer", integer_digest.encode()), ("offset", signed_bytes(offset, "offset", MAX_OFFSET_BITS)),
        ("artifact", PRESSURE_ARTIFACT_SHA256.encode()),
    ))
    logger.debug("_program_digest exit")
    return result


def offset_residue_program_source(prime, integer, offset: int) -> OffsetResidueProgramSource:
    """Construct one bound closed coherent offset program for negative pressure only."""
    logger.debug("offset_residue_program_source entry")
    p = snapshot_prime(prime)
    z = snapshot_integer(integer)
    off = exact_int(offset, "offset")
    if off == 0:
        reject("pressure-offset-must-be-nonzero")
    program = _program_digest(p.source_digest, z.source_digest, off)
    productivity = digest("veyra.p3a1b.pressure-productivity.v1", (
        ("program", program.encode()), ("artifact", PRESSURE_ARTIFACT_SHA256.encode()),
        ("theorem", PRESSURE_THEOREM_IDS[0].encode()),
    ))
    coherence = digest("veyra.p3a1b.pressure-coherence.v1", (
        ("program", program.encode()), ("artifact", PRESSURE_ARTIFACT_SHA256.encode()),
        ("theorem", PRESSURE_THEOREM_IDS[1].encode()),
    ))
    result = OffsetResidueProgramSource(
        PRESSURE_VERSION, PRESSURE_CONSTRUCTOR, PRESSURE_GRAMMAR_ID,
        p.source_digest, z.source_digest, off, PRESSURE_ARTIFACT_PATH,
        PRESSURE_ARTIFACT_SHA256, PRESSURE_THEOREM_IDS, TOOLCHAIN_ID,
        program, productivity, coherence,
    )
    logger.debug("offset_residue_program_source exit")
    return result


def snapshot_offset_program(value: OffsetResidueProgramSource) -> OffsetResidueProgramSource:
    """Validate every primitive before hashing, comparing, or encoding it."""
    logger.debug("snapshot_offset_program entry")
    raw = exact_shape(value, OffsetResidueProgramSource, "pressure-program")
    text_names = (
        "version", "constructor", "grammar_id", "prime_digest", "integer_digest",
        "artifact_path_id", "artifact_sha256", "toolchain_id", "program_digest",
        "productivity_evidence_digest", "coherence_evidence_digest",
    )
    for name in text_names:
        exact_text(raw[name], f"pressure-{name}")
    for name in (
        "prime_digest", "integer_digest", "artifact_sha256", "program_digest",
        "productivity_evidence_digest", "coherence_evidence_digest",
    ):
        exact_digest(raw[name], f"pressure-{name}")
    offset = exact_int(raw["offset"], "pressure-offset")
    ids = raw["theorem_ids"]
    if type(ids) is not tuple or any(type(x) is not str for x in ids):
        reject("pressure-theorem-ids-invalid")
    expected = offset_residue_program_source_from_digests(
        raw["prime_digest"], raw["integer_digest"], offset,
    )
    if value != expected:
        reject("pressure-program-source-drift")
    logger.debug("snapshot_offset_program exit")
    return expected


def offset_residue_program_source_from_digests(
        prime_digest: str, integer_digest: str, offset: int) -> OffsetResidueProgramSource:
    """Rebuild a validated source without constructing foreign p/z DTOs."""
    logger.debug("offset_residue_program_source_from_digests entry")
    exact_digest(prime_digest, "pressure-prime-digest")
    exact_digest(integer_digest, "pressure-integer-digest")
    off = exact_int(offset, "pressure-offset")
    if off == 0:
        reject("pressure-offset-must-be-nonzero")
    program = _program_digest(prime_digest, integer_digest, off)
    productivity = digest("veyra.p3a1b.pressure-productivity.v1", (
        ("program", program.encode()), ("artifact", PRESSURE_ARTIFACT_SHA256.encode()),
        ("theorem", PRESSURE_THEOREM_IDS[0].encode()),
    ))
    coherence = digest("veyra.p3a1b.pressure-coherence.v1", (
        ("program", program.encode()), ("artifact", PRESSURE_ARTIFACT_SHA256.encode()),
        ("theorem", PRESSURE_THEOREM_IDS[1].encode()),
    ))
    result = OffsetResidueProgramSource(
        PRESSURE_VERSION, PRESSURE_CONSTRUCTOR, PRESSURE_GRAMMAR_ID,
        prime_digest, integer_digest, off, PRESSURE_ARTIFACT_PATH,
        PRESSURE_ARTIFACT_SHA256, PRESSURE_THEOREM_IDS, TOOLCHAIN_ID,
        program, productivity, coherence,
    )
    logger.debug("offset_residue_program_source_from_digests exit")
    return result


def canonical_pressure_bytes(value: OffsetResidueProgramSource) -> bytes:
    """Return exact bounded bytes for pressure preflight charging."""
    logger.debug("canonical_pressure_bytes entry")
    source = snapshot_offset_program(value)
    rows = (
        ("version", source.version.encode()), ("constructor", source.constructor.encode()),
        ("grammar", source.grammar_id.encode()), ("prime", source.prime_digest.encode()),
        ("integer", source.integer_digest.encode()),
        ("offset", signed_bytes(source.offset, "pressure-offset", MAX_OFFSET_BITS)),
        ("artifact", source.artifact_path_id.encode()), ("artifact-sha", source.artifact_sha256.encode()),
        *((f"theorem-{i}", name.encode()) for i, name in enumerate(source.theorem_ids)),
        ("toolchain", source.toolchain_id.encode()), ("program", source.program_digest.encode()),
        ("productivity", source.productivity_evidence_digest.encode()),
        ("coherence", source.coherence_evidence_digest.encode()),
    )
    result = b"".join(len(a.encode()).to_bytes(8, "big") + a.encode()
                      + len(b).to_bytes(8, "big") + b for a, b in rows)
    logger.debug("canonical_pressure_bytes exit bytes=%d", len(result))
    return result
