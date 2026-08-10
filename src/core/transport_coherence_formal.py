"""Pinned captured Lean proofs for finite GTCP and separate symbolic Nat-op."""

from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import logging
from pathlib import Path
import re
import shutil
import tempfile
import time
from .formal_export_catalog import _strip_lean_comments
from .stream_completion_formal_attestation import ToolchainContract, attest_toolchain
from .stream_completion_formal_process import capture_phase
from .transport_coherence_common import digest, exact_digest, exact_shape, exact_text, reject
from .transport_coherence_types import FormalFailureKind, TransportTheoremSource

from .paths import TMP_DIR

logger = logging.getLogger(__name__)
FORMAL_VERSION = "p3-c2-formal-v1"
ARTIFACT_PATH = "proofs/lean/VeyraTransportCoherence.lean"
ARTIFACT_SHA256 = "4804c5637e89530a4a00ec6ad905c20d0a93c2b63fb941f1cffc70d7a3c7e395"
THEOREM_IDS = (
    "THM_P3C2_001_ranked_local_to_generated_transport",
    "THM_P3C2_002_natop_reduction_identity",
    "THM_P3C2_003_natop_reduction_composition",
)
TOOLCHAIN_ID = "leanprover/lean4:v4.30.0-rc2"
ELAN_SHA256 = "19d38963260cfb376f1aab0f0fbcf4e80ec25c8bd0ba3b1797d95141d56ec55a"
LEAN_SHA256 = "3e0d0d3d801675359f2d4cf9815bfdb417b20b92fdd9d48b3b14c95bbae28bbf"
LEAN_VERSION = (
    "Lean (version 4.30.0-rc2, x86_64-unknown-linux-gnu, commit 3dc1a088b6d2d8eafe25a7cd7ec7b58d731bd7cc, Release)\n"
)
TCB_DIGEST = digest(
    "veyra.p3c2.tcb.v1",
    (
        ("toolchain", TOOLCHAIN_ID.encode()),
        ("elan", ELAN_SHA256.encode()),
        ("lean", LEAN_SHA256.encode()),
        ("version", LEAN_VERSION.encode()),
        ("process", b"shared-deadline-live-output-cap-private-captured-source"),
    ),
)
ATTESTATION_DIGEST = digest("veyra.p3c2.attestation.v1", (("tcb", TCB_DIGEST.encode()),))
EXPECTED_AXIOMS = (
    b"'VeyraTransportCoherence.THM_P3C2_001_ranked_local_to_generated_transport' does not depend on any axioms",
    b"'VeyraTransportCoherence.NatOp.THM_P3C2_002_natop_reduction_identity' depends on axioms: [propext]",
    b"'VeyraTransportCoherence.NatOp.THM_P3C2_003_natop_reduction_composition' depends on axioms: [propext]",
)


@dataclass(frozen=True)
class FormalOutcome:
    kind: FormalFailureKind | None
    receipt_digest: str
    phase_count: int
    output_digest: str


def transport_theorem_source() -> TransportTheoremSource:
    """Construct the sole exact three-theorem source identity."""
    logger.debug("transport_theorem_source entry")
    value = digest(
        "veyra.p3c2.theorem-source.v1",
        (
            ("version", FORMAL_VERSION.encode()),
            ("path", ARTIFACT_PATH.encode()),
            ("sha", ARTIFACT_SHA256.encode()),
            *((f"theorem-{i}", x.encode()) for i, x in enumerate(THEOREM_IDS)),
            ("toolchain", TOOLCHAIN_ID.encode()),
            ("tcb", TCB_DIGEST.encode()),
        ),
    )
    result = TransportTheoremSource(
        FORMAL_VERSION, ARTIFACT_PATH, ARTIFACT_SHA256, THEOREM_IDS, TOOLCHAIN_ID, TCB_DIGEST, value
    )
    logger.debug("transport_theorem_source exit")
    return result


def capture_theorem_source(source: TransportTheoremSource) -> bytes:
    """Capture exact source bytes and verify symbols before execution."""
    logger.debug("capture_theorem_source entry")
    exact_shape(source, TransportTheoremSource, "transport-theorem-source")
    for name in ("version", "artifact_path", "toolchain_id"):
        exact_text(object.__getattribute__(source, name), f"transport-theorem-{name}")
    for name in ("artifact_sha256", "tcb_digest", "source_digest"):
        exact_digest(object.__getattribute__(source, name), f"transport-theorem-{name}")
    theorem_ids = object.__getattribute__(source, "theorem_ids")
    if type(theorem_ids) is not tuple or any(type(x) is not str for x in theorem_ids):
        reject("transport-theorem-ids-invalid")
    if source != transport_theorem_source():
        reject("transport-theorem-source-drift")
    try:
        payload = Path(source.artifact_path).read_bytes()
    except OSError:
        reject("transport-theorem-artifact-unavailable")
    if len(payload) > 1024 * 1024 or sha256(payload).hexdigest() != source.artifact_sha256:
        reject("transport-theorem-artifact-drift")
    try:
        clean = _strip_lean_comments(payload.decode("utf-8", errors="strict"))
    except UnicodeError:
        reject("transport-theorem-invalid-utf8")
    found = tuple(re.findall(r"(?m)^theorem\s+(THM_P3C2_[A-Za-z0-9_]+)", clean))
    required = ("rankY", "rankZ", "rankW", "pathYU", "pathZV", "pathUT", "eqY", "eqZ", "eqW", "NatOp")
    if found != THEOREM_IDS or re.search(r"\b(?:sorry|admit)\b", clean) or any(x not in clean for x in required):
        reject("transport-theorem-symbol-or-structure-drift")
    logger.debug("capture_theorem_source exit bytes=%d", len(payload))
    return payload


def check_transport_theorems(source: TransportTheoremSource, timeout: int, max_output: int) -> FormalOutcome:
    """Freshly attest and compile exact captured bytes under shared hard budgets."""
    logger.debug("check_transport_theorems entry")
    if (
        type(timeout) is not int
        or type(max_output) is not int
        or not 1 <= timeout <= 300
        or not 1 <= max_output <= 4 * 1024 * 1024
    ):
        reject("transport-formal-bound-invalid")
    payload = capture_theorem_source(source)
    elan = shutil.which("elan")
    if elan is None:
        return _failure(FormalFailureKind.COMPILE_ERROR, b"", 0)
    deadline = time.monotonic() + timeout
    contract = ToolchainContract(TOOLCHAIN_ID, ELAN_SHA256, LEAN_SHA256, LEAN_VERSION.encode(), ATTESTATION_DIGEST)
    attested = attest_toolchain(elan, deadline, max_output, contract)
    output = bytearray(attested.output)
    phases = len(attested.phase_receipts)
    if attested.kind is not None or attested.lean_path is None:
        return _failure(_kind(attested.kind), bytes(output), phases)
    try:
        root = TMP_DIR
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="p3c2-lean-", dir=root) as directory:
            target = Path(directory) / "VeyraTransportCoherence.lean"
            target.write_bytes(payload)
            target.chmod(0o400)
            part = capture_phase(
                "p3c2-lean-compile",
                [str(attested.lean_path), "-DwarningAsError=true", target.name],
                target.parent,
                deadline,
                max_output - len(output),
            )
            output.extend(part.output)
            phases += 1
    except OSError:
        return _failure(FormalFailureKind.COMPILE_ERROR, bytes(output), phases)
    if part.kind is not None:
        return _failure(_kind(part.kind), bytes(output), phases)
    if any(bytes(output).count(row) != 1 for row in EXPECTED_AXIOMS):
        return _failure(FormalFailureKind.COMPILE_ERROR, bytes(output), phases)
    try:
        after = Path(source.artifact_path).read_bytes()
    except OSError:
        return _failure(FormalFailureKind.CONTINUITY_DRIFT, bytes(output), phases)
    if after != payload:
        return _failure(FormalFailureKind.CONTINUITY_DRIFT, bytes(output), phases)
    outsha = sha256(output).hexdigest()
    receipt = digest(
        "veyra.p3c2.formal-receipt.v1",
        (
            ("source", source.source_digest.encode()),
            ("attestation", ATTESTATION_DIGEST.encode()),
            ("output", outsha.encode()),
            ("phases", phases.to_bytes(8, "big")),
        ),
    )
    result = FormalOutcome(None, receipt, phases, outsha)
    logger.debug("check_transport_theorems exit phases=%d", phases)
    return result


def _kind(value: object) -> FormalFailureKind:
    """Map shared formal failure kinds without semantic reclassification."""
    logger.debug("_kind entry")
    result = FormalFailureKind.COMPILE_ERROR if value is None else FormalFailureKind(value.value)
    logger.debug("_kind exit kind=%s", result.value)
    return result


def _failure(kind: FormalFailureKind, output: bytes, phases: int) -> FormalOutcome:
    """Construct one nonmathematical bounded formal failure."""
    logger.debug("_failure entry phases=%d", phases)
    logger.error("formal failure kind=%s", kind.value)
    attempt = digest(
        "veyra.p3c2.formal-failure.v1",
        (
            ("kind", kind.value.encode()),
            ("output", sha256(output).hexdigest().encode()),
            ("phases", phases.to_bytes(8, "big")),
        ),
    )
    result = FormalOutcome(kind, attempt, phases, sha256(output).hexdigest())
    logger.debug("_failure exit")
    return result
