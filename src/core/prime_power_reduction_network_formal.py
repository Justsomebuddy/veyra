"""Exact continuity and bounded fresh private Lean replay for P3-N2."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import re
import shutil
import tempfile
import time

from .formal_export_catalog import _strip_lean_comments
from .padic_completion_formal import ELAN_SHA256, LEAN_BINARY_SHA256, LEAN_VERSION
from .prime_power_reduction_network_common import (
    PrimePowerReductionValidationError, digest, reject, sha,
)
from .prime_power_reduction_network_sources import AXIOM_ROWS, THEOREM_IDS, TOOLCHAIN_ID
from .prime_power_reduction_network_types import FormalFailureKind
from .stream_completion_formal_attestation import ToolchainContract, attest_toolchain
from .stream_completion_formal_process import FormalPhaseReceipt, capture_phase

from .paths import TMP_DIR

logger = logging.getLogger(__name__)
ATTESTATION_DIGEST = digest("veyra.p3n2.attestation.v1", (
    ("toolchain", TOOLCHAIN_ID.encode()), ("elan", ELAN_SHA256.encode()),
    ("lean", LEAN_BINARY_SHA256.encode()), ("version", LEAN_VERSION.encode()),
))


@dataclass(frozen=True)
class CompileOutcome:
    kind: FormalFailureKind | None
    output: bytes
    return_codes: tuple[int, ...]
    axiom_rows: tuple[tuple[str, tuple[str, ...]], ...]
    attestation_digest: str
    phase_receipts: tuple[FormalPhaseReceipt, ...]


def _read(path: str) -> bytes:
    """Read at most one byte beyond the exact per-file hard cap."""
    logger.debug("_read entry path=%s", path)
    try:
        with Path(path).open("rb") as handle:
            value = handle.read(2 * 1024 * 1024 + 1)
    except OSError:
        reject("n2-formal-artifact-unavailable")
    if len(value) > 2 * 1024 * 1024:
        reject("n2-formal-artifact-too-large")
    logger.debug("_read exit bytes=%d", len(value))
    return value


def _symbols(payload: bytes) -> None:
    """Require exact N2 theorem declarations and no proof placeholders."""
    logger.debug("_symbols entry")
    try:
        clean = _strip_lean_comments(payload.decode("utf-8", errors="strict"))
    except UnicodeError:
        reject("n2-formal-invalid-utf8")
    found = tuple(re.findall(r"(?m)^\s*theorem\s+(THM_P3N2_[A-Za-z0-9_]+)(?=[\s:(])", clean))
    if found != THEOREM_IDS or re.search(r"\b(?:sorry|admit)\b", clean):
        reject("n2-formal-symbol-set-drift")
    forbidden = ("VeyraPPCPBundle", "THM_POMEGA2_017", "VeyraTransportCoherence")
    if any(item in clean for item in forbidden):
        reject("n2-forbidden-completion-or-c2-premise")
    logger.debug("_symbols exit count=%d", len(found))


def capture_sources(package) -> tuple[bytes, bytes, bytes]:
    """Capture exact raw PΩ2, direct N1, and dedicated stronger N2 bytes."""
    logger.debug("capture_sources entry")
    paths = (package.theorem.pomega2_path, package.theorem.n1_path, package.theorem.artifact_path)
    expected = (package.theorem.pomega2_sha256, package.theorem.n1_sha256,
                package.theorem.artifact_sha256)
    values = tuple(_read(path) for path in paths)
    if tuple(sha(value) for value in values) != expected:
        reject("n2-captured-source-continuity-drift")
    _symbols(values[2])
    logger.debug("capture_sources exit bytes=%d", sum(map(len, values)))
    return values


def continuity_holds(package, captured) -> bool:
    """Re-read all three files after replay and compare exact bytes."""
    logger.debug("continuity_holds entry")
    try:
        result = type(captured) is tuple and capture_sources(package) == captured
    except PrimePowerReductionValidationError:
        logger.exception("continuity_holds failed")
        return False
    logger.debug("continuity_holds exit result=%s", result)
    return result


def _map_kind(kind) -> FormalFailureKind | None:
    """Map shared operational failures without semantic reclassification."""
    logger.debug("_map_kind entry")
    result = None if kind is None else FormalFailureKind(kind.value)
    logger.debug("_map_kind exit kind=%s", None if result is None else result.value)
    return result


def _parse(payload: bytes):
    """Parse the exact ordered seven theorem axiom closures."""
    logger.debug("_parse entry bytes=%d", len(payload))
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeError:
        logger.error("_parse invalid utf8")
        return None
    pattern = r"(?m)^'([^']+)' (does not depend on any axioms|depends on axioms: \[([^\]]*)\])$"
    rows = tuple((name, () if phrase.startswith("does not") else tuple(body.split(", ")))
                 for name, phrase, body in re.findall(pattern, text)
                 if name.startswith("THM_P3N2_"))
    result = rows if rows == AXIOM_ROWS else None
    logger.debug("_parse exit valid=%s", result is not None)
    return result


def compile_sources(captured, timeout: int, max_output: int) -> CompileOutcome:
    """Attest and compile three immutable phases under one deadline/live cap."""
    logger.debug("compile_sources entry timeout=%d cap=%d", timeout, max_output)
    if type(captured) is not tuple or len(captured) != 3 or any(type(x) is not bytes for x in captured):
        reject("n2-captured-source-shape-invalid")
    elan = shutil.which("elan")
    if elan is None:
        return CompileOutcome(FormalFailureKind.COMPILE_ERROR, b"", (), (), ATTESTATION_DIGEST, ())
    deadline = time.monotonic() + timeout
    contract = ToolchainContract(TOOLCHAIN_ID, ELAN_SHA256, LEAN_BINARY_SHA256,
                                 LEAN_VERSION.encode(), ATTESTATION_DIGEST)
    attested = attest_toolchain(elan, deadline, max_output, contract)
    output, codes = bytearray(attested.output), list(attested.return_codes)
    receipts = list(attested.phase_receipts)
    if attested.kind is not None:
        return CompileOutcome(_map_kind(attested.kind), bytes(output), tuple(codes), (),
                              attested.attestation_digest, tuple(receipts))
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="p3n2-", dir=TMP_DIR) as directory:
        private = Path(directory)
        names = ("VeyraPadicCompletion.lean", "VeyraPadicFamilyIntroduction.lean",
                 "VeyraPrimePowerReductionNetwork.lean")
        for name, payload in zip(names, captured, strict=True):
            (private / name).write_bytes(payload)
            (private / name).chmod(0o400)
        env = dict(os.environ, LEAN_PATH=str(private.resolve()))
        for index, name in enumerate(names):
            command = [elan, "run", TOOLCHAIN_ID, "lean", "-DwarningAsError=true"]
            if index < 2:
                command.extend(("-o", name.replace(".lean", ".olean")))
            command.append(name)
            part = capture_phase(name, command, private, deadline, max_output - len(output), env)
            output.extend(part.output)
            codes.append(part.return_code)
            receipts.append(part.receipt)
            if part.kind is not None:
                return CompileOutcome(_map_kind(part.kind), bytes(output), tuple(codes), (),
                                      attested.attestation_digest, tuple(receipts))
    rows = _parse(bytes(output))
    kind = None if rows is not None else FormalFailureKind.COMPILE_ERROR
    result = CompileOutcome(kind, bytes(output), tuple(codes), () if rows is None else rows,
                            attested.attestation_digest, tuple(receipts))
    logger.debug("compile_sources exit kind=%s", None if kind is None else kind.value)
    return result
