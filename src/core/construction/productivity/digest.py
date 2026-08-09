"""Tagged, counted commitments and O(n) D1 output encoding."""

from __future__ import annotations

from hashlib import sha256
import logging

from .types import PeriodicPrefixStage

logger = logging.getLogger(__name__)
_MAGIC = b"VEYRA-P1-D1-STAGE\x00"


def tagged_digest(domain: str, fields: tuple[tuple[str, bytes], ...]) -> str:
    """Hash a domain-separated exact tagged field stream."""
    logger.debug("tagged_digest entry domain=%s fields=%d", domain, len(fields))
    digest = sha256()
    _token(digest, b"domain", domain.encode())
    _token(digest, b"field-count", len(fields).to_bytes(8, "big"))
    for tag, value in fields:
        _token(digest, tag.encode(), value)
    result = digest.hexdigest()
    logger.debug("tagged_digest exit domain=%s", domain)
    return result


def _token(digest: object, tag: bytes, value: bytes) -> None:
    logger.debug("_token entry tag=%d value=%d", len(tag), len(value))
    digest.update(len(tag).to_bytes(4, "big"))  # type: ignore[attr-defined]
    digest.update(tag)  # type: ignore[attr-defined]
    digest.update(len(value).to_bytes(8, "big"))  # type: ignore[attr-defined]
    digest.update(value)  # type: ignore[attr-defined]
    logger.debug("_token exit")


def program_digest(version: str, alphabet: tuple[str, ...], period: tuple[str, ...]) -> str:
    """Commit syntax identity only; no policy, source, run, or target."""
    logger.debug("program_digest entry")
    fields = [
        ("version", version.encode()),
        ("alphabet-count", len(alphabet).to_bytes(8, "big")),
    ]
    fields.extend((f"alphabet-{i}", item.encode()) for i, item in enumerate(alphabet))
    fields.append(("period-count", len(period).to_bytes(8, "big")))
    fields.extend((f"period-{i}", item.encode()) for i, item in enumerate(period))
    result = tagged_digest("veyra.p1d1.program.v1", tuple(fields))
    logger.debug("program_digest exit")
    return result


def policy_digest(version: str, max_depth: int, max_output_bytes: int) -> str:
    """Commit operational caps independently of program identity."""
    logger.debug("policy_digest entry")
    result = tagged_digest("veyra.p1d1.policy.v1", (
        ("version", version.encode()), ("max-depth", max_depth.to_bytes(8, "big")),
        ("max-output-bytes", max_output_bytes.to_bytes(8, "big")),
    ))
    logger.debug("policy_digest exit")
    return result


def generator_digest(program: str, basis: str, law: str, encoding: str) -> str:
    """Bind structural productivity without any execution policy."""
    logger.debug("generator_digest entry")
    result = tagged_digest("veyra.p1d1.generator.v1", (
        ("program", program.encode()), ("basis", basis.encode()),
        ("law", law.encode()), ("encoding", encoding.encode()),
    ))
    logger.debug("generator_digest exit")
    return result


def source_digest(generator: str, policy: str) -> str:
    """Bind the productive identity to one operational source policy."""
    logger.debug("source_digest entry")
    result = tagged_digest("veyra.p1d1.source.v1", (
        ("generator", generator.encode()), ("policy", policy.encode()),
    ))
    logger.debug("source_digest exit")
    return result


def run_digest(source: str, policy: str, operation: str, depths: tuple[int, ...]) -> str:
    """Commit one exact demanded run independently of its outcome."""
    logger.debug("run_digest entry operation=%s depths=%d", operation, len(depths))
    fields = [
        ("source", source.encode()), ("policy", policy.encode()),
        ("operation", operation.encode()), ("depth-count", len(depths).to_bytes(8, "big")),
    ]
    fields.extend((f"depth-{i}", _nat_bytes(item)) for i, item in enumerate(depths))
    result = tagged_digest("veyra.p1d1.run.v1", tuple(fields))
    logger.debug("run_digest exit")
    return result


def refusal_digest(
    operation: str, run: str, failed_bound: str, required: int, allowed: int,
) -> str:
    """Commit exact resource refusal semantics without a partial output channel."""
    logger.debug("refusal_digest entry operation=%s", operation)
    result = tagged_digest("veyra.p1d1.refusal.v1", (
        ("operation", operation.encode()), ("run", run.encode()),
        ("failed-bound", failed_bound.encode()), ("required", _nat_bytes(required)),
        ("allowed", _nat_bytes(allowed)),
    ))
    logger.debug("refusal_digest exit")
    return result


def _nat_bytes(value: int) -> bytes:
    logger.debug("_nat_bytes entry bits=%d", value.bit_length())
    width = max(1, (value.bit_length() + 7) // 8)
    result = value.to_bytes(width, "big")
    logger.debug("_nat_bytes exit bytes=%d", len(result))
    return result


def required_output_bytes(depth: int, period: tuple[str, ...], encoding: str) -> int:
    """Compute exact encoded size in O(period), before output allocation."""
    logger.debug("required_output_bytes entry depth=%d", depth)
    encoded = tuple(item.encode() for item in period)
    cycles, remainder = divmod(depth, len(encoded))
    symbol_bytes = cycles * sum(4 + len(item) for item in encoded)
    symbol_bytes += sum(4 + len(item) for item in encoded[:remainder])
    result = len(_MAGIC) + 8 + 4 + len(encoding.encode()) + 8 + symbol_bytes
    logger.debug("required_output_bytes exit bytes=%d", result)
    return result


def encode_stage(stage: PeriodicPrefixStage) -> bytes:
    """Encode exactly one demanded finite row in O(n), never a prefix tower."""
    logger.debug("encode_stage entry depth=%d", stage.depth)
    data = bytearray(_MAGIC)
    data.extend(stage.depth.to_bytes(8, "big"))
    encoding = stage.output_encoding_id.encode()
    data.extend(len(encoding).to_bytes(4, "big"))
    data.extend(encoding)
    data.extend(len(stage.symbols).to_bytes(8, "big"))
    for symbol in stage.symbols:
        payload = symbol.encode()
        data.extend(len(payload).to_bytes(4, "big"))
        data.extend(payload)
    result = bytes(data)
    logger.debug("encode_stage exit bytes=%d", len(result))
    return result


def output_digest(stage: PeriodicPrefixStage) -> str:
    """Commit the canonical finite stage output."""
    logger.debug("output_digest entry")
    result = sha256(encode_stage(stage)).hexdigest()
    logger.debug("output_digest exit")
    return result


def execution_trace_digest(
    program: str, generator: str, source: str, run: str,
    stage: PeriodicPrefixStage, output: str,
) -> str:
    """Stream every emitted index/symbol row without materializing a trace."""
    logger.debug("execution_trace_digest entry depth=%d", stage.depth)
    digest = sha256()
    _token(digest, b"domain", b"veyra.p1d1.trace.v1")
    _token(digest, b"field-count", (6 + 2 * stage.depth).to_bytes(8, "big"))
    for tag, value in (
        (b"program", program.encode()), (b"generator", generator.encode()),
        (b"source", source.encode()), (b"run", run.encode()),
        (b"step-count", _nat_bytes(stage.depth)), (b"output", output.encode()),
    ):
        _token(digest, tag, value)
    for index, symbol in enumerate(stage.symbols):
        _token(digest, b"step-index", _nat_bytes(index))
        _token(digest, b"step-symbol", symbol.encode())
    result = digest.hexdigest()
    logger.debug("execution_trace_digest exit")
    return result
