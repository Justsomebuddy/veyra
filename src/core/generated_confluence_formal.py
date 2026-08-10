"""Captured private Lean TLGC theorem with pinned, live-bounded execution."""

from __future__ import annotations

from hashlib import sha256
import logging
from pathlib import Path
import re
import shutil
import tempfile
import time

from .formal_export_catalog import _strip_lean_comments
from .generated_confluence_common import exact_digest, exact_shape, exact_text, reject
from .generated_confluence_digest import digest, theorem_source_digest
from .generated_confluence_types import (
    GeneratedConfluenceTheoremSource,
    GeneratedFormalPhaseReceipt,
)
from .stream_completion_formal_attestation import ToolchainContract, attest_toolchain
from .stream_completion_formal_process import FormalPhaseReceipt, capture_phase

from .paths import TMP_DIR

logger = logging.getLogger(__name__)
FORMAL_VERSION = "p3-c1-formal-v2"
ARTIFACT_PATH = "proofs/lean/VeyraGeneratedConfluence.lean"
ARTIFACT_SHA256 = "6c11906659de1e3e87bd7d16a47a0993ebcf601e8e48263bfb606fde3734d8bf"
TOOLCHAIN_ID = "leanprover/lean4:v4.30.0-rc2"
ELAN_SHA256 = "19d38963260cfb376f1aab0f0fbcf4e80ec25c8bd0ba3b1797d95141d56ec55a"
LEAN_SHA256 = "3e0d0d3d801675359f2d4cf9815bfdb417b20b92fdd9d48b3b14c95bbae28bbf"
LEAN_VERSION = (
    "Lean (version 4.30.0-rc2, x86_64-unknown-linux-gnu, commit 3dc1a088b6d2d8eafe25a7cd7ec7b58d731bd7cc, Release)\n"
)
THEOREM_IDS = ("THM_P3C1_001_ranked_local_to_generated_confluence",)
TCB_DESCRIPTOR = (
    f"veyra.p3c1.lean-tcb.v2\0{TOOLCHAIN_ID}\0{ELAN_SHA256}\0{LEAN_SHA256}\0"
    f"{LEAN_VERSION}\0shared-deadline\0live-combined-output-cap\0fresh-private-capture"
)
TCB_DIGEST = sha256(TCB_DESCRIPTOR.encode()).hexdigest()
ATTESTATION_DIGEST = digest(
    "veyra.p3c1.toolchain-attestation.v1",
    (
        ("toolchain", TOOLCHAIN_ID.encode()),
        ("elan", ELAN_SHA256.encode()),
        ("lean", LEAN_SHA256.encode()),
        ("version", LEAN_VERSION.encode()),
        ("tcb", TCB_DIGEST.encode()),
    ),
)
AXIOM_ROW = (
    b"'VeyraGeneratedConfluence.THM_P3C1_001_ranked_local_to_generated_confluence' does not depend on any axioms"
)
MAX_OUTPUT = 1_048_576
TIMEOUT = 120


def generated_confluence_theorem_source() -> GeneratedConfluenceTheoremSource:
    """Return the sole exact source/toolchain/TCB identity."""
    logger.debug("generated_confluence_theorem_source entry")
    value = GeneratedConfluenceTheoremSource(
        FORMAL_VERSION,
        ARTIFACT_PATH,
        ARTIFACT_SHA256,
        THEOREM_IDS,
        TOOLCHAIN_ID,
        ELAN_SHA256,
        LEAN_SHA256,
        LEAN_VERSION,
        TCB_DIGEST,
        "",
    )
    result = GeneratedConfluenceTheoremSource(
        value.version,
        value.artifact_path,
        value.artifact_sha256,
        value.theorem_ids,
        value.toolchain_id,
        value.elan_sha256,
        value.lean_sha256,
        value.lean_version,
        value.tcb_digest,
        theorem_source_digest(value),
    )
    logger.debug("generated_confluence_theorem_source exit")
    return result


def snapshot_theorem_source(raw: GeneratedConfluenceTheoremSource) -> GeneratedConfluenceTheoremSource:
    """Reject nested source, theorem order, toolchain, or TCB drift."""
    logger.debug("snapshot_theorem_source entry")
    exact_shape(raw, GeneratedConfluenceTheoremSource, "generated-theorem-source")
    for name in ("version", "artifact_path", "toolchain_id", "lean_version"):
        exact_text(object.__getattribute__(raw, name), f"formal-{name}")
    for name in ("artifact_sha256", "elan_sha256", "lean_sha256", "tcb_digest", "source_digest"):
        exact_digest(object.__getattribute__(raw, name), f"formal-{name}")
    theorem_ids = object.__getattribute__(raw, "theorem_ids")
    if type(theorem_ids) is not tuple or any(type(item) is not str for item in theorem_ids):
        reject("generated-formal-theorem-ids-type-invalid")
    expected = generated_confluence_theorem_source()
    if raw != expected:
        reject("generated-theorem-source-drift")
    logger.debug("snapshot_theorem_source exit")
    return expected


def check_generated_confluence_theorem(
    raw: GeneratedConfluenceTheoremSource,
) -> tuple[str, tuple[GeneratedFormalPhaseReceipt, ...]]:
    """Freshly attest and compile captured bytes under one deadline/output cap."""
    logger.debug("check_generated_confluence_theorem entry")
    source = snapshot_theorem_source(raw)
    payload = _capture_artifact(source)
    elan = shutil.which("elan")
    if elan is None:
        reject("generated-formal-elan-unavailable")
    deadline = time.monotonic() + TIMEOUT
    contract = ToolchainContract(
        source.toolchain_id,
        source.elan_sha256,
        source.lean_sha256,
        source.lean_version.encode(),
        ATTESTATION_DIGEST,
    )
    attested = attest_toolchain(elan, deadline, MAX_OUTPUT, contract)
    if attested.kind is not None or attested.lean_path is None:
        reject(f"generated-formal-attestation-{None if attested.kind is None else attested.kind.value}")
    output = bytearray(attested.output)
    receipts = [_convert_phase(row) for row in attested.phase_receipts]
    root = TMP_DIR
    try:
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="p3c1-lean-", dir=root) as directory:
            target = Path(directory) / f"{source.artifact_sha256}.lean"
            target.write_bytes(payload)
            target.chmod(0o600)
            phase = capture_phase(
                "lean-compile",
                [str(attested.lean_path), "-DwarningAsError=true", target.name],
                target.parent,
                deadline,
                MAX_OUTPUT - len(output),
            )
    except OSError as exc:
        logger.error("check_generated_confluence_theorem temp failure error=%s", exc)
        reject("generated-formal-temp-failure")
    output.extend(phase.output)
    receipts.append(_convert_phase(phase.receipt))
    if phase.kind is not None or phase.output.count(AXIOM_ROW) != 1:
        reject(f"generated-formal-compile-{None if phase.kind is None else phase.kind.value}")
    _continuity_check(source, payload)
    receipt = digest(
        "veyra.p3c1.formal-receipt.v2",
        (
            ("source", source.source_digest.encode()),
            ("attestation", ATTESTATION_DIGEST.encode()),
            ("output", sha256(output).hexdigest().encode()),
            *tuple(
                ("phase", f"{row.phase}:{row.return_code}:{row.output_bytes}:{row.output_digest}".encode())
                for row in receipts
            ),
        ),
    )
    logger.debug("check_generated_confluence_theorem exit phases=%d", len(receipts))
    return receipt, tuple(receipts)


def _capture_artifact(source: GeneratedConfluenceTheoremSource) -> bytes:
    logger.debug("_capture_artifact entry")
    try:
        payload = Path(source.artifact_path).read_bytes()
    except OSError as exc:
        logger.error("_capture_artifact read failure error=%s", exc)
        reject("generated-formal-artifact-unavailable")
    if len(payload) > 1_048_576 or sha256(payload).hexdigest() != source.artifact_sha256:
        reject("generated-formal-artifact-drift")
    _check_symbols(payload)
    logger.debug("_capture_artifact exit bytes=%d", len(payload))
    return payload


def _check_symbols(payload: bytes) -> None:
    logger.debug("_check_symbols entry")
    try:
        clean = _strip_lean_comments(payload.decode("utf-8", errors="strict"))
    except UnicodeError:
        reject("generated-formal-invalid-utf8")
    found = tuple(re.findall(r"(?m)^\s*theorem\s+(THM_P3C1_[A-Za-z0-9_]+)", clean))
    if found != THEOREM_IDS or re.search(r"\b(?:sorry|admit)\b", clean):
        reject("generated-formal-symbol-drift")
    required = ("rankY", "rankZ", "rankW", "pathYQ", "pathZR", "pathQT")
    if any(name not in clean for name in required):
        reject("generated-formal-structural-proof-drift")
    logger.debug("_check_symbols exit")


def _convert_phase(row: FormalPhaseReceipt) -> GeneratedFormalPhaseReceipt:
    logger.debug("_convert_phase entry phase=%s", row.phase)
    result = GeneratedFormalPhaseReceipt(
        row.phase,
        row.return_code,
        row.output_bytes,
        row.output_digest,
    )
    logger.debug("_convert_phase exit phase=%s", row.phase)
    return result


def _continuity_check(source: GeneratedConfluenceTheoremSource, before: bytes) -> None:
    logger.debug("_continuity_check entry")
    try:
        after = Path(source.artifact_path).read_bytes()
    except OSError as exc:
        logger.error("_continuity_check read failure error=%s", exc)
        reject("generated-formal-continuity-failed")
    if before != after or sha256(after).hexdigest() != source.artifact_sha256:
        reject("generated-formal-continuity-failed")
    logger.debug("_continuity_check exit")
