"""Captured sources, pinned toolchain attestation, and bounded Lean execution."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
import re
import shutil
import tempfile
import time

from .formal_export_catalog import _strip_lean_comments
from .stream_completion_alphabet import BRIDGE_THEOREM_IDS
from .stream_completion_common import exact_digest, exact_shape, reject, sha
from .stream_completion_digest import digest, texts
from .stream_completion_formal_attestation import (
    ToolchainAttestationOutcome, ToolchainContract, attest_toolchain,
)
from .stream_completion_formal_process import FormalPhaseReceipt, capture_phase
from .stream_completion_types import (
    FormalAlphabetPresentation, FormalExecutionFailureKind,
    StreamCompletionTheoremSource,
)

from .paths import TMP_DIR

logger = logging.getLogger(__name__)
FORMAL_VERSION = "pomega1-formal-v1"
ARTIFACT_PATH = "proofs/lean/VeyraStreamCompletion.lean"
ARTIFACT_SHA256 = "98a69a3e0d5886ffb4746e9fc203eff515cdeec99d4f5c820fb4ebd8220751cd"
REPRESENTATION_ID = "Fin-n-functions-compatible-family-Nat-stream-v1"
TOOLCHAIN_ID = "leanprover/lean4:v4.30.0-rc2"
LEAN_VERSION = (
    "Lean (version 4.30.0-rc2, x86_64-unknown-linux-gnu, "
    "commit 3dc1a088b6d2d8eafe25a7cd7ec7b58d731bd7cc, Release)\n"
)
ELAN_SHA256 = "19d38963260cfb376f1aab0f0fbcf4e80ec25c8bd0ba3b1797d95141d56ec55a"
LEAN_BINARY_SHA256 = "3e0d0d3d801675359f2d4cf9815bfdb417b20b92fdd9d48b3b14c95bbae28bbf"
SCP_THEOREM_IDS = (
    "THM_POMEGA1_001_truncation_identity",
    "THM_POMEGA1_002_truncation_composition",
    "THM_POMEGA1_003_rho_formation_congruence",
    "THM_POMEGA1_004_stream_restriction_compatible",
    "THM_POMEGA1_005_diagonal_realization_depth",
    "THM_POMEGA1_006_universal_realization",
    "THM_POMEGA1_007_coordinate_agreement",
    "THM_POMEGA1_008_joint_separation",
    "THM_POMEGA1_009_relative_uniqueness",
    "THM_POMEGA1_010_nonvacuity_inhabitance",
    "THM_POMEGA1_011_scp_introduction",
)
THEOREM_IDS = SCP_THEOREM_IDS + BRIDGE_THEOREM_IDS
TCB_DESCRIPTOR = (
    f"veyra.pomega1.lean-tcb.v2\0{TOOLCHAIN_ID}\0{ELAN_SHA256}\0"
    f"{LEAN_BINARY_SHA256}\0{LEAN_VERSION}\0bounded-process-group-capture\0"
    "captured-private-generic-and-instance\0continuity-reread"
)
TCB_DIGEST = sha(TCB_DESCRIPTOR.encode())
TOOLCHAIN_ATTESTATION_DIGEST = digest("veyra.pomega1.toolchain-attestation.v1", (
    ("toolchain", TOOLCHAIN_ID.encode()), ("elan", ELAN_SHA256.encode()),
    ("lean", LEAN_BINARY_SHA256.encode()), ("version", LEAN_VERSION.encode()),
))
TheoremAxiomRows = tuple[tuple[str, tuple[str, ...]], ...]


@dataclass(frozen=True)
class CompileOutcome:
    kind: FormalExecutionFailureKind | None
    output: bytes
    return_codes: tuple[int, ...]
    theorem_axiom_rows: TheoremAxiomRows = ()
    attestation_digest: str = TOOLCHAIN_ATTESTATION_DIGEST
    phase_receipts: tuple[FormalPhaseReceipt, ...] = ()


def stream_completion_theorem_source() -> StreamCompletionTheoremSource:
    """Construct the sole exact 15-theorem source identity."""
    logger.debug("stream_completion_theorem_source entry")
    value = digest("veyra.pomega1.formal-source.v1", (
        ("version", FORMAL_VERSION.encode()), ("artifact", ARTIFACT_PATH.encode()),
        ("artifact-sha", ARTIFACT_SHA256.encode()), *texts("theorem", THEOREM_IDS),
        ("representation", REPRESENTATION_ID.encode()),
        ("toolchain", TOOLCHAIN_ID.encode()), ("tcb", TCB_DIGEST.encode()),
    ))
    result = StreamCompletionTheoremSource(
        FORMAL_VERSION, ARTIFACT_PATH, ARTIFACT_SHA256, THEOREM_IDS,
        REPRESENTATION_ID, TOOLCHAIN_ID, TCB_DIGEST, value,
    )
    logger.debug("stream_completion_theorem_source exit")
    return result


def snapshot_theorem_source(value: StreamCompletionTheoremSource) -> StreamCompletionTheoremSource:
    """Reject alternate theorem order, representation, toolchain, or TCB."""
    logger.debug("snapshot_theorem_source entry")
    exact_shape(value, StreamCompletionTheoremSource, "stream-theorem-source")
    try:
        if type(value.theorem_ids) is not tuple or len(value.theorem_ids) != 15:
            reject("stream-theorem-count-invalid")
        if any(type(item) is not str for item in value.theorem_ids):
            reject("stream-theorem-id-type-invalid")
        if any(type(getattr(value, name)) is not str for name in (
            "version", "artifact_path_id", "representation_id", "toolchain_id",
        )):
            reject("stream-theorem-source-scalar-type-invalid")
        for name in ("artifact_sha256", "tcb_digest", "source_digest"):
            exact_digest(getattr(value, name), name.replace("_", "-"))
    except AttributeError:
        reject("stream-theorem-source-missing-fields")
    expected = stream_completion_theorem_source()
    if value != expected:
        reject("stream-theorem-source-drift")
    logger.debug("snapshot_theorem_source exit")
    return expected


def capture_generic_source(source: StreamCompletionTheoremSource) -> bytes:
    """Bound, read once, authenticate, and symbol-check generic formal bytes."""
    logger.debug("capture_generic_source entry")
    source = snapshot_theorem_source(source)
    payload = _read_bounded_source(Path(source.artifact_path_id))
    if payload is None:
        reject("stream-artifact-unavailable")
    if len(payload) > 2 * 1024 * 1024:
        reject("stream-artifact-hard-size-invalid")
    if sha(payload) != source.artifact_sha256:
        reject("stream-artifact-drift")
    _check_symbols(payload, SCP_THEOREM_IDS, "generic")
    logger.debug("capture_generic_source exit bytes=%d", len(payload))
    return payload


def _read_bounded_source(path: Path) -> bytes | None:
    """Read at most one byte beyond the hard formal-source cap."""
    logger.debug("_read_bounded_source entry file=%s", path.name)
    try:
        with path.open("rb") as handle:
            result = handle.read(2 * 1024 * 1024 + 1)
    except OSError as exc:
        logger.error("_read_bounded_source failed error=%s", exc)
        return None
    logger.debug("_read_bounded_source exit bytes=%d", len(result))
    return result


def _check_symbols(payload: bytes, names: tuple[str, ...], label: str) -> None:
    """Require exact ordered declarations after stripping Lean comments."""
    logger.debug("_check_symbols entry label=%s", label)
    try:
        clean = _strip_lean_comments(payload.decode("utf-8", errors="strict"))
    except UnicodeError:
        reject(f"{label}-formal-invalid-utf8")
    found = tuple(re.findall(
        r"(?m)^[ \t]*(?:theorem|lemma)[ \t]+(THM_POMEGA1_[A-Za-z0-9_]+)(?=[ \t\r\n:(])",
        clean,
    ))
    if found != names or re.search(r"\b(?:sorry|admit)\b", clean):
        reject(f"{label}-formal-symbol-set-drift")
    logger.debug("_check_symbols exit label=%s count=%d", label, len(found))


def validate_captured_sources(generic: bytes, presentation: FormalAlphabetPresentation) -> None:
    """Validate source identity before executable preflight or compilation."""
    logger.debug("validate_captured_sources entry")
    if type(generic) is not bytes or len(generic) > 2 * 1024 * 1024 or sha(generic) != ARTIFACT_SHA256:
        reject("captured-generic-source-invalid")
    instance = presentation.generated_instance_bytes
    if type(instance) is not bytes or len(instance) > 2 * 1024 * 1024:
        reject("captured-instance-source-invalid")
    if sha(instance) != presentation.generated_instance_sha256:
        reject("captured-instance-source-drift")
    _check_symbols(instance, BRIDGE_THEOREM_IDS, "alphabet")
    logger.debug("validate_captured_sources exit")


def _parse_axiom_rows(payload: bytes) -> TheoremAxiomRows | None:
    """Parse exactly fifteen ordered, duplicate-free #print axioms rows."""
    logger.debug("_parse_axiom_rows entry bytes=%d", len(payload))
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeError:
        logger.error("_parse_axiom_rows invalid utf8")
        return None
    pattern = re.compile(
        r"(?m)^'(THM_POMEGA1_[A-Za-z0-9_]+)' (does not depend on any axioms|depends on axioms: \[([^\]]*)\])$"
    )
    matches = tuple(pattern.findall(text))
    if tuple(row[0] for row in matches) != THEOREM_IDS or len(matches) != 15:
        logger.error("_parse_axiom_rows theorem row set mismatch")
        return None
    rows = []
    for name, phrase, body in matches:
        closure = () if phrase == "does not depend on any axioms" else tuple(body.split(", "))
        if any(re.fullmatch(r"[A-Za-z0-9_.]+", item) is None for item in closure):
            logger.error("_parse_axiom_rows invalid axiom id")
            return None
        rows.append((name, closure))
    result = tuple(rows)
    logger.debug("_parse_axiom_rows exit rows=%d", len(result))
    return result


def _attest_toolchain(
    elan: str, deadline: float, max_output: int,
) -> ToolchainAttestationOutcome:
    """Return a typed attestation outcome under the compile run's shared bounds."""
    logger.debug("_attest_toolchain entry budget=%d", max_output)
    contract = ToolchainContract(
        TOOLCHAIN_ID, ELAN_SHA256, LEAN_BINARY_SHA256, LEAN_VERSION.encode(),
        TOOLCHAIN_ATTESTATION_DIGEST,
    )
    result = attest_toolchain(elan, deadline, max_output, contract)
    logger.debug(
        "_attest_toolchain exit kind=%s",
        None if result.kind is None else result.kind.value,
    )
    return result


def compile_captured_sources(
    generic: bytes, instance: bytes, timeout: int, max_output: int,
) -> CompileOutcome:
    """Attest and compile captured bytes with one deadline and combined live cap."""
    logger.debug("compile_captured_sources entry")
    elan = shutil.which("elan")
    deadline = time.monotonic() + timeout
    if elan is None:
        logger.error("compile_captured_sources elan unavailable")
        return CompileOutcome(FormalExecutionFailureKind.COMPILE_ERROR, b"", ())
    attestation = _attest_toolchain(elan, deadline, max_output)
    if attestation.kind is not None:
        logger.error(
            "compile_captured_sources attestation failed kind=%s", attestation.kind.value,
        )
        return CompileOutcome(
            attestation.kind, attestation.output, attestation.return_codes, (),
            attestation.attestation_digest, attestation.phase_receipts,
        )
    root = TMP_DIR
    codes = list(attestation.return_codes)
    receipts = list(attestation.phase_receipts)
    combined = bytearray(attestation.output)
    try:
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="pomega1-", dir=root) as directory:
            private = Path(directory)
            paths = (private / "generic.lean", private / "alphabet.lean")
            for path, payload in zip(paths, (generic, instance), strict=True):
                path.write_bytes(payload)
                path.chmod(0o400)
            for path in paths:
                phase = "generic-compile" if path is paths[0] else "instance-compile"
                captured = capture_phase(
                    phase,
                    [elan, "run", TOOLCHAIN_ID, "lean", "-DwarningAsError=true", path.name],
                    private, deadline, max_output - len(combined),
                )
                codes.append(captured.return_code)
                receipts.append(captured.receipt)
                combined.extend(captured.output)
                if captured.kind is not None:
                    return CompileOutcome(
                        captured.kind, bytes(combined), tuple(codes), (),
                        attestation.attestation_digest, tuple(receipts),
                    )
    except OSError as exc:
        logger.error("compile_captured_sources filesystem error=%s", exc)
        return CompileOutcome(
            FormalExecutionFailureKind.COMPILE_ERROR, bytes(combined), tuple(codes), (),
            attestation.attestation_digest, tuple(receipts),
        )
    rows = _parse_axiom_rows(bytes(combined))
    if rows is None:
        return CompileOutcome(
            FormalExecutionFailureKind.COMPILE_ERROR, bytes(combined), tuple(codes), (),
            attestation.attestation_digest, tuple(receipts),
        )
    logger.debug("compile_captured_sources exit codes=%s", codes)
    return CompileOutcome(
        None, bytes(combined), tuple(codes), rows,
        attestation.attestation_digest, tuple(receipts),
    )


def continuity_holds(generic: bytes) -> bool:
    """Bounded reread of original after compile and exact byte comparison."""
    logger.debug("continuity_holds entry")
    after = _read_bounded_source(Path(ARTIFACT_PATH))
    if after is None:
        logger.error("continuity_holds reread failed")
        return False
    result = len(after) <= 2 * 1024 * 1024 and type(generic) is bytes and after == generic
    logger.debug("continuity_holds exit result=%s", result)
    return result
