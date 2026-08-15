"""Deterministic structural-only execution reports for VAMI frames."""

from __future__ import annotations

import json
import logging
import struct
import zlib
from typing import cast

from vam.src.intrinsic_ir import IntrinsicIRError, intrinsic_ir_data

from .codec import INTRINSIC_PROFILE, IntrinsicCodecError, decode_intrinsic_frame

logger = logging.getLogger(__name__)
_HEADER = struct.Struct(">4sHII")


def _metrics(value: dict[str, object]) -> tuple[int, int]:
    """Count semantic IR nodes and obstruction nodes without recursion."""
    logger.debug("_metrics entry tag=%s", value.get("tag"))
    stack: list[dict[str, object]] = [value]
    nodes = obstructions = 0
    while stack:
        node = stack.pop()
        nodes += 1
        tag = node["tag"]
        if tag == "obstruction":
            obstructions += 1
        elif tag == "recurrence":
            children = list(cast(list[dict[str, object]], node["tacts"]))
            if node["anchor"] is not None:
                children.append(node["anchor"])  # type: ignore[arg-type]
            stack.extend(reversed(children))
        elif tag == "recurrence-value":
            stack.append(node["recurrence"])  # type: ignore[arg-type]
        elif tag in {"pair-value", "mismatch"}:
            stack.extend((node["right"], node["left"]))  # type: ignore[arg-type]
        elif tag in {"ready", "echo"}:
            stack.append(node["value"])  # type: ignore[arg-type]
        elif tag == "blocked":
            stack.extend(reversed(cast(list[dict[str, object]], node["obstructions"])))
        elif tag == "domain-blocked":
            stack.extend(reversed(cast(list[dict[str, object]], node["right"])))
            stack.extend(reversed(cast(list[dict[str, object]], node["left"])))
    logger.debug("_metrics exit nodes=%d obstructions=%d", nodes, obstructions)
    return nodes, obstructions


def execute_intrinsic_ir(value: object) -> dict[str, object]:
    """Validate and structurally execute one intrinsic IR without evidence."""
    logger.debug("execute_intrinsic_ir entry")
    try:
        data = intrinsic_ir_data(value)
    except IntrinsicIRError as error:
        logger.error("intrinsic runtime rejected message=%s", error)
        raise IntrinsicCodecError("payload", str(error)) from error
    rendered = data["value"]
    if type(rendered) is not dict:
        logger.error("execute_intrinsic_ir rejected reason=rendered-value-not-exact-dict")
        raise IntrinsicCodecError("payload", "intrinsic runtime value must be exact dict")
    nodes, obstructions = _metrics(rendered)
    tag = rendered["tag"]
    status = "blocked" if tag in {"blocked", "domain-blocked"} else "mismatch" if tag == "mismatch" else "ready" if tag in {"ready", "echo"} else "decoded"
    result = {
        "status": status,
        "tag": tag,
        "nodes": nodes,
        "obstructions": obstructions,
        "value": rendered,
        "evidence_accepted": False,
        "promotion_ready": False,
        "taxonomy_changed": False,
    }
    logger.debug("execute_intrinsic_ir exit tag=%s status=%s", tag, status)
    return result


def inspect_intrinsic_frame(blob: object) -> dict[str, object]:
    """Decode and structurally execute one canonical VAMI frame."""
    logger.debug("inspect_intrinsic_frame entry")
    if type(blob) is not bytes:
        logger.error("inspect_intrinsic_frame rejected reason=frame-not-exact-bytes")
        raise IntrinsicCodecError("payload", "VAMI frame must be exact bytes")
    value = decode_intrinsic_frame(blob)
    _, version, size, checksum = _HEADER.unpack(blob[: _HEADER.size])
    result = {
        "ok": True,
        "profile": INTRINSIC_PROFILE,
        "frame": {"magic": "VAMI", "version": version, "size": size, "crc32": f"{checksum:08x}"},
        "execution": execute_intrinsic_ir(value),
    }
    logger.debug("inspect_intrinsic_frame exit size=%d crc32=%08x", size, checksum)
    return result


def intrinsic_error_data(error: object) -> dict[str, object]:
    """Render one stable VAMI error report without leaking dynamic state."""
    logger.debug("intrinsic_error_data entry type=%s", type(error).__name__)
    if type(error) is not IntrinsicCodecError:
        logger.error("intrinsic_error_data rejected type=%s", type(error).__name__)
        raise TypeError("expected exact IntrinsicCodecError")
    result = {"ok": False, "profile": INTRINSIC_PROFILE, "error": {"kind": error.kind, "message": str(error)}}
    logger.debug("intrinsic_error_data exit kind=%s", error.kind)
    return result


def canonical_intrinsic_report_json(value: object) -> str:
    """Recompute and serialize a report from exact trusted frame/error input."""
    logger.debug("canonical_intrinsic_report_json entry type=%s", type(value).__name__)
    if type(value) is bytes:
        report = inspect_intrinsic_frame(value)
    elif type(value) is IntrinsicCodecError:
        report = intrinsic_error_data(value)
    else:
        logger.error("canonical_intrinsic_report_json rejected type=%s", type(value).__name__)
        raise TypeError("expected exact VAMI bytes or IntrinsicCodecError")
    result = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    logger.debug("canonical_intrinsic_report_json exit bytes=%d crc32=%08x", len(result), zlib.crc32(result.encode()) & 0xFFFFFFFF)
    return result
