"""Typed, shared-budget toolchain attestation for PΩ1."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import time

from .formal_process import (
    FormalPhaseReceipt, capture_phase, file_sha,
)
from .types import FormalExecutionFailureKind

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolchainContract:
    toolchain_id: str
    elan_sha256: str
    lean_sha256: str
    version_output: bytes
    attestation_digest: str


@dataclass(frozen=True)
class ToolchainAttestationOutcome:
    kind: FormalExecutionFailureKind | None
    output: bytes
    return_codes: tuple[int, ...]
    phase_receipts: tuple[FormalPhaseReceipt, ...]
    attestation_digest: str
    lean_path: Path | None


def _failure(
    kind: FormalExecutionFailureKind, output: bytes, codes: list[int],
    receipts: list[FormalPhaseReceipt], contract: ToolchainContract,
) -> ToolchainAttestationOutcome:
    """Construct one typed attestation failure without reclassification."""
    logger.debug("_failure entry kind=%s", kind.value)
    result = ToolchainAttestationOutcome(
        kind, output, tuple(codes), tuple(receipts), contract.attestation_digest, None,
    )
    logger.debug("_failure exit kind=%s", kind.value)
    return result


def attest_toolchain(
    elan: str, deadline: float, max_output: int, contract: ToolchainContract,
) -> ToolchainAttestationOutcome:
    """Attest elan/path/binary/version under one deadline and live byte budget."""
    logger.debug("attest_toolchain entry budget=%d", max_output)
    codes: list[int] = []
    receipts: list[FormalPhaseReceipt] = []
    combined = bytearray()
    if time.monotonic() >= deadline:
        logger.error("attest_toolchain deadline before elan hash")
        return _failure(FormalExecutionFailureKind.TIMEOUT, b"", codes, receipts, contract)
    if file_sha(Path(elan)) != contract.elan_sha256:
        logger.error("attest_toolchain elan identity mismatch")
        return _failure(FormalExecutionFailureKind.COMPILE_ERROR, b"", codes, receipts, contract)
    if time.monotonic() >= deadline:
        logger.error("attest_toolchain deadline after elan hash")
        return _failure(FormalExecutionFailureKind.TIMEOUT, b"", codes, receipts, contract)
    env = dict(os.environ)
    env["ELAN_TOOLCHAIN"] = contract.toolchain_id
    which = capture_phase(
        "elan-which", [elan, "which", "lean"], None, deadline,
        max_output - len(combined), env,
    )
    codes.append(which.return_code)
    receipts.append(which.receipt)
    combined.extend(which.output)
    if which.kind is not None:
        return _failure(which.kind, bytes(combined), codes, receipts, contract)
    try:
        lean = Path(which.output.decode("utf-8", errors="strict").strip())
    except UnicodeError:
        logger.error("attest_toolchain invalid lean path output")
        return _failure(FormalExecutionFailureKind.COMPILE_ERROR, bytes(combined), codes, receipts, contract)
    if time.monotonic() >= deadline:
        logger.error("attest_toolchain deadline before lean hash")
        return _failure(FormalExecutionFailureKind.TIMEOUT, bytes(combined), codes, receipts, contract)
    if file_sha(lean) != contract.lean_sha256:
        logger.error("attest_toolchain lean identity mismatch")
        return _failure(FormalExecutionFailureKind.COMPILE_ERROR, bytes(combined), codes, receipts, contract)
    if time.monotonic() >= deadline:
        logger.error("attest_toolchain deadline after lean hash")
        return _failure(FormalExecutionFailureKind.TIMEOUT, bytes(combined), codes, receipts, contract)
    version = capture_phase(
        "lean-version", [elan, "run", contract.toolchain_id, "lean", "--version"],
        None, deadline, max_output - len(combined),
    )
    codes.append(version.return_code)
    receipts.append(version.receipt)
    combined.extend(version.output)
    if version.kind is not None:
        return _failure(version.kind, bytes(combined), codes, receipts, contract)
    if version.output != contract.version_output:
        logger.error("attest_toolchain version mismatch")
        return _failure(FormalExecutionFailureKind.COMPILE_ERROR, bytes(combined), codes, receipts, contract)
    result = ToolchainAttestationOutcome(
        None, bytes(combined), tuple(codes), tuple(receipts),
        contract.attestation_digest, lean,
    )
    logger.debug("attest_toolchain exit bytes=%d", len(combined))
    return result
