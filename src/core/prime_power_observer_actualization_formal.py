"""Repository-contained capture and private four-phase Lean replay for P3-N0."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import logging
import os
from pathlib import Path
import re
import shutil
import tempfile
import time

from .prime_power_observer_actualization_common import reject
from .prime_power_observer_actualization_attestation import (
    ARTIFACT_PATH, AXIOM_ROWS, THEOREM_IDS, TOOLCHAIN_ID,
    n0_theorem_source, validate_theorem_source,
)
from .prime_power_observer_actualization_common import digest, indexed
from .prime_power_observer_actualization_evidence_types import (
    N0FormalAttestation, N0PhaseReceipt,
)
from .prime_power_observer_actualization_types import FormalFailureKind, N0Source
from .stream_completion_formal_process import capture_phase

from .paths import PROJECT_ROOT, TMP_DIR

logger = logging.getLogger(__name__)

HARD_FILE_BYTES = 2 * 1024 * 1024
HARD_AGGREGATE_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True)
class N0CompileOutcome:
    kind: FormalFailureKind | None
    output: bytes
    return_codes: tuple[int, ...]
    attestation: N0FormalAttestation | None


def _sha(payload: bytes) -> str:
    """Hash captured immutable bytes."""
    logger.debug("_sha entry bytes=%d", len(payload))
    result = hashlib.sha256(payload).hexdigest()
    logger.debug("_sha exit")
    return result


def _symbols(payload: bytes) -> None:
    """Require the exact theorem declarations and forbid proof placeholders."""
    logger.debug("_symbols entry")
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeError:
        reject("n0-formal-invalid-utf8")
    found = tuple(re.findall(
        r"(?m)^\s*theorem\s+(THM_P3N0_[A-Za-z0-9_]+)(?=[\s:(])", text,
    ))
    if found != THEOREM_IDS or re.search(r"\b(?:sorry|admit)\b", text):
        reject("n0-formal-symbol-set-or-placeholder-drift")
    logger.debug("_symbols exit count=%d", len(found))


def _axiom_output(payload: bytes) -> None:
    """Require Lean's reported N0 axiom rows to equal the pinned closure."""
    logger.debug("_axiom_output entry")
    text = payload.decode("utf-8", errors="replace")
    for theorem, axioms in AXIOM_ROWS:
        expected = f"'{theorem}' depends on axioms: [{', '.join(axioms)}]"
        if expected not in text:
            reject("n0-formal-axiom-row-drift")
    logger.debug("_axiom_output exit")


def _capture_one(root: Path, path: str, expected: str, cap: int) -> bytes:
    """Fail closed on absolute/traversal/symlink/device/escape/SHA drift."""
    logger.debug("_capture_one entry path=%s", path)
    if type(path) is not str or not path or len(path.encode()) > 256:
        reject("n0-source-path-invalid")
    relative = Path(path)
    if relative.is_absolute() or ".." in relative.parts:
        reject("n0-source-path-escape")
    candidate = root / relative
    try:
        stat = candidate.lstat()
        resolved = candidate.resolve(strict=True)
    except OSError:
        reject("n0-source-path-unavailable")
    if candidate.is_symlink() or not candidate.is_file() or not stat.st_mode:
        reject("n0-source-not-regular-file")
    try:
        resolved.relative_to(root)
    except ValueError:
        reject("n0-source-resolution-escape")
    with resolved.open("rb") as handle:
        payload = handle.read(cap + 1)
    if len(payload) > cap:
        reject("n0-source-captured-byte-cap")
    if _sha(payload) != expected:
        reject("n0-source-pinned-sha-mismatch")
    logger.debug("_capture_one exit bytes=%d", len(payload))
    return payload


def capture_size_required(source: N0Source) -> int:
    """Lstat every allowlisted file and sum sizes before opening any source."""
    logger.debug("capture_size_required entry")
    if type(source) is not N0Source:
        reject("n0-capture-size-source-exact-type-required")
    paths, _, root = _source_catalog(source)
    total = 0
    for path in paths:
        candidate = root / path
        try:
            stat = candidate.lstat()
        except OSError:
            reject("n0-source-path-unavailable")
        if candidate.is_symlink() or not candidate.is_file() or stat.st_size > HARD_FILE_BYTES:
            reject("n0-source-preopen-kind-or-file-cap")
        total += stat.st_size
        if total > HARD_AGGREGATE_BYTES:
            reject("n0-source-preopen-hard-aggregate-cap")
    logger.debug("capture_size_required exit bytes=%d", total)
    return total


def _source_catalog(source):
    """Return the exact four-file catalog after theorem-source validation."""
    logger.debug("_source_catalog entry")
    validate_theorem_source(source.theorem_source)
    theorem = source.strict_package.raw_package.theorem
    paths = (theorem.pomega2_path, theorem.n1_path, theorem.artifact_path,
             source.theorem_source.artifact_path)
    expected = (theorem.pomega2_sha256, theorem.n1_sha256,
                theorem.artifact_sha256, source.theorem_source.artifact_sha256)
    allowlist = (
        "proofs/lean/VeyraPadicCompletion.lean",
        "proofs/lean/VeyraPadicFamilyIntroduction.lean",
        "proofs/lean/VeyraPrimePowerReductionNetwork.lean", ARTIFACT_PATH,
    )
    if paths != allowlist:
        reject("n0-source-allowlist-drift")
    root = PROJECT_ROOT
    logger.debug("_source_catalog exit")
    return paths, expected, root


def capture_sources(source: N0Source) -> tuple[bytes, bytes, bytes, bytes]:
    """Capture exact PΩ2/N1/N2/N0 bytes from a fixed repository allowlist."""
    logger.debug("capture_sources entry")
    if type(source) is not N0Source:
        reject("n0-capture-source-exact-type-required")
    paths, expected, root = _source_catalog(source)
    required = capture_size_required(source)
    if required > source.policy.max_captured_bytes:
        reject("n0-source-preopen-policy-aggregate-cap")
    values, remaining = [], min(HARD_AGGREGATE_BYTES, source.policy.max_captured_bytes)
    for path, pin in zip(paths, expected, strict=True):
        payload = _capture_one(root, path, pin, min(HARD_FILE_BYTES, remaining))
        values.append(payload)
        remaining -= len(payload)
    values = tuple(values)
    _symbols(values[-1])
    logger.debug("capture_sources exit bytes=%d", sum(map(len, values)))
    return values


def continuity_holds(source: N0Source, captured) -> bool:
    """Detect post-capture source drift without converting it to semantic OPEN."""
    logger.debug("continuity_holds entry")
    try:
        result = type(captured) is tuple and capture_sources(source) == captured
    except Exception:
        logger.exception("continuity_holds rejected")
        result = False
    logger.debug("continuity_holds exit result=%s", result)
    return result


def compile_sources(captured, timeout: int, max_output: int) -> N0CompileOutcome:
    """Compile four private immutable phases under one deadline and output cap."""
    logger.debug("compile_sources entry timeout=%d output=%d", timeout, max_output)
    if (type(captured) is not tuple or len(captured) != 4
            or any(type(item) is not bytes for item in captured)):
        reject("n0-captured-source-shape-invalid")
    if type(timeout) is not int or type(max_output) is not int:
        reject("n0-formal-cap-type-invalid")
    elan = shutil.which("elan")
    if elan is None:
        logger.error("compile_sources terminal compile-error elan-missing")
        return N0CompileOutcome(FormalFailureKind.COMPILE_ERROR, b"", (), None)
    names = (
        "VeyraPadicCompletion.lean", "VeyraPadicFamilyIntroduction.lean",
        "VeyraPrimePowerReductionNetwork.lean",
        "VeyraPrimePowerObserverActualization.lean",
    )
    output, codes, receipts, deadline = bytearray(), [], [], time.monotonic() + timeout
    root = TMP_DIR
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="p3n0-", dir=root) as directory:
        private = Path(directory)
        for name, payload in zip(names, captured, strict=True):
            (private / name).write_bytes(payload)
        env = dict(os.environ, LEAN_PATH=str(private.resolve()))
        for index, name in enumerate(names):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                logger.error("compile_sources terminal timeout phase=%d", index)
                return N0CompileOutcome(FormalFailureKind.TIMEOUT, bytes(output), tuple(codes), None)
            command = [elan, "run", TOOLCHAIN_ID, "lean", "-DwarningAsError=true"]
            if index < len(names) - 1:
                command.extend(("-o", name.replace(".lean", ".olean")))
            command.append(name)
            part = capture_phase(name, command, private, deadline,
                                 max_output - len(output), env)
            output.extend(part.output)
            codes.append(part.return_code)
            receipt_digest = digest("veyra.p3n0.phase-receipt.v2", (
                ("index", str(index).encode()), ("name", name.encode()),
                ("captured", _sha(captured[index]).encode()),
                ("return", str(part.return_code).encode()),
                ("output", _sha(part.output).encode()),
            ))
            receipts.append(N0PhaseReceipt(
                index, name, _sha(captured[index]), part.return_code,
                _sha(part.output), receipt_digest,
            ))
            if part.kind is not None:
                logger.error("compile_sources terminal kind=%s phase=%d", part.kind.value, index)
                return N0CompileOutcome(FormalFailureKind(part.kind.value),
                                        bytes(output), tuple(codes), None)
    _axiom_output(receipts and part.output or b"")
    hashes = tuple(_sha(item) for item in captured)
    attestation_digest = digest("veyra.p3n0.formal-attestation.v2", (
        ("theorem-source", n0_theorem_source().source_digest.encode()),
        *indexed("captured", hashes), *indexed("receipt", (x.receipt_digest for x in receipts)),
    ))
    attestation = N0FormalAttestation(
        n0_theorem_source().source_digest, hashes, tuple(receipts), attestation_digest,
    )
    result = N0CompileOutcome(None, bytes(output), tuple(codes), attestation)
    logger.debug("compile_sources exit")
    return result
