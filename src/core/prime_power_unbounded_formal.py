"""Pinned private Lean replay for the P3-N6-E equality/injection source."""
from __future__ import annotations
from dataclasses import dataclass
import logging
import os
from pathlib import Path
import re
import shutil
import tempfile
import time
from .padic.completion.formal import ELAN_SHA256, LEAN_BINARY_SHA256, LEAN_VERSION
from .prime_power_unbounded_common import digest, reject, sha
from .prime_power_unbounded_capture import capture_fixed_source, project_tmp_path
from .prime_power_unbounded_execution_continuity import (
    RuntimeFileSnapshotV1,
    continuity_set_holds,
    snapshot_runtime_file,
)
from .prime_power_unbounded_sources import E_THEOREM_IDS, theorem_source
from .prime_power_unbounded_types import (
    N6FormalFailureKind,
    N6Lane,
    N6PolicyV1,
    N6TheoremSourceV1,
)
from .prime_power_unbounded_sources import snapshot_policy, snapshot_theorem_source
from .construction.stream_completion.formal_attestation import ToolchainContract, attest_toolchain
from .construction.stream_completion.formal_process import FormalPhaseReceipt, capture_phase
from .construction.stream_completion.types import FormalExecutionFailureKind
logger = logging.getLogger(__name__)
EXTERNAL_RUNTIME_TCB_BOUNDARIES = (
    "lean-owned-dynamic-shared-objects",
    "lean-init-std-olean-import-closure",
    "system-dynamic-loader-and-libraries",
    "active-same-uid-restored-compiler-path-swap",
)

@dataclass(frozen=True, slots=True)
class N6ECompileOutcome:
    """Immutable success/failure transcript for one exact E-lane replay."""

    kind: N6FormalFailureKind | None
    output: bytes
    return_codes: tuple[int, ...]
    theorem_axiom_rows: tuple[tuple[str, tuple[str, ...]], ...]
    attestation_digest: str
    phase_receipts: tuple[FormalPhaseReceipt, ...]

def formal_run_digest(outcome: N6ECompileOutcome) -> str:
    """Bind attestation, output, codes, and every phase receipt into one run ID."""
    logger.debug("formal_run_digest entry")
    if type(outcome) is not N6ECompileOutcome:
        reject("n6-formal-outcome-exact-type-required")
    rows: list[tuple[str, bytes]] = [
        ("kind", b"" if outcome.kind is None else outcome.kind.value.encode()),
        ("output", sha(outcome.output).encode()),
        ("attestation", outcome.attestation_digest.encode()),
    ]
    rows.extend(
        (f"return-code-{index}", code.to_bytes(8, "big", signed=True))
        for index, code in enumerate(outcome.return_codes)
    )
    for index, receipt in enumerate(outcome.phase_receipts):
        prefix = f"phase-{index}"
        rows.extend((
            (f"{prefix}-name", receipt.phase.encode()),
            (f"{prefix}-return-code", receipt.return_code.to_bytes(8, "big", signed=True)),
            (f"{prefix}-output-bytes", receipt.output_bytes.to_bytes(8, "big")),
            (f"{prefix}-output-digest", receipt.output_digest.encode()),
            (f"{prefix}-failure", b"" if receipt.failure_kind is None
             else receipt.failure_kind.value.encode()),
        ))
    result = digest("veyra.p3n6.e-formal-run.v1", tuple(rows))
    logger.debug("formal_run_digest exit phases=%d", len(outcome.phase_receipts))
    return result

def _read(path_text: str, expected_sha: str) -> bytes:
    """Read one exact regular source within the fixed per-file cap."""
    logger.debug("_read entry file=%s", Path(path_text).name)
    payload = capture_fixed_source(path_text, expected_sha)
    logger.debug("_read exit file=%s bytes=%d", Path(path_text).name, len(payload))
    return payload

def _symbols(payload: bytes) -> None:
    """Require the exact complete N6 theorem set and no proof placeholders."""
    logger.debug("_symbols entry bytes=%d", len(payload))
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeError:
        reject("n6-formal-source-invalid-utf8")
    found = tuple(re.findall(
        r"(?m)^\s*theorem\s+(THM_P3N6_[A-Za-z0-9_]+)(?=[\s:(])", text,
    ))
    expected = (
        "THM_P3N6_001_prefix_indistinguishable",
        "THM_P3N6_002_next_depth_distinguishes",
        "THM_P3N6_003_power_carrier_injective",
        "THM_P3N6_004_power_carrier_eqc_injective",
        "THM_P3N6_005_carrier_equality_adapter",
    )
    if found != expected or re.search(r"\b(?:sorry|admit)\b", text):
        reject("n6-formal-symbol-set-drift")
    logger.debug("_symbols exit count=%d", len(found))

def capture_e_sources(source: N6TheoremSourceV1) -> tuple[bytes, bytes, bytes]:
    """Capture exact PΩ2, N1 and N6 bytes in private compile order."""
    logger.debug("capture_e_sources entry")
    checked = snapshot_theorem_source(source, N6Lane.E_POWER_INJECTION)
    specs = (
        ("proofs/lean/VeyraPadicCompletion.lean",
         "28052d0260b1535e484ddd8e70f97fea945ca3ff9a23c358bb45d209a071a18f"),
        ("proofs/lean/VeyraPadicFamilyIntroduction.lean",
         "b8540c65b555bd8407d558b3a16cc7cd25ab27ca636083451162f1a8a5490b48"),
        ("proofs/lean/VeyraPrimePowerUnbounded.lean",
         "d35ead8dca26e0a07842ad830a143dab36b94b6ff201e79fd16dce9a81305b1c"),
    )
    if (checked.artifact_path_id, checked.artifact_sha256) != specs[-1]:
        reject("n6-formal-owned-source-binding-drift")
    captured = tuple(_read(path, digest) for path, digest in specs)
    _symbols(captured[-1])
    result = (captured[0], captured[1], captured[2])
    logger.debug("capture_e_sources exit sources=%d bytes=%d", 3, sum(map(len, result)))
    return result

def continuity_holds(
    source: N6TheoremSourceV1, captured: tuple[bytes, bytes, bytes],
) -> bool:
    """Reopen all sources and compare exact bytes after formal execution."""
    logger.debug("continuity_holds entry")
    try:
        result = capture_e_sources(source) == captured
    except Exception:
        logger.error("continuity_holds source recapture failed")
        return False
    logger.debug("continuity_holds exit result=%s", result)
    return result

def _kind(value: FormalExecutionFailureKind | None) -> N6FormalFailureKind | None:
    """Map the shared runner failure vocabulary without semantic promotion."""
    logger.debug("_kind entry")
    result = None if value is None else N6FormalFailureKind(value.value)
    logger.debug("_kind exit result=%s", None if result is None else result.value)
    return result

def _axioms(output: bytes) -> tuple[tuple[str, tuple[str, ...]], ...] | None:
    """Parse and require the exact ordered E theorem axiom closure."""
    logger.debug("_axioms entry bytes=%d", len(output))
    text = output.decode("utf-8", errors="replace")
    pattern = re.compile(
        r"(?m)^'([^']+)' (does not depend on any axioms|depends on axioms: \[([^\]]*)\])$"
    )
    matches = tuple(
        (name, phrase, body) for name, phrase, body in pattern.findall(text)
        if name in E_THEOREM_IDS
    )
    if tuple(name for name, _, _ in matches) != E_THEOREM_IDS:
        logger.error("_axioms duplicate, missing, or reordered E rows")
        return None
    found = {
        name: (() if phrase.startswith("does not") else tuple(sorted(body.split(", "))))
        for name, phrase, body in matches
    }
    expected = theorem_source(N6Lane.E_POWER_INJECTION).theorem_axiom_rows
    result = tuple((name, found[name]) for name in E_THEOREM_IDS) if all(
        name in found for name in E_THEOREM_IDS
    ) else None
    if result != expected:
        logger.error("_axioms exact E rows missing or drifted")
        return None
    logger.debug("_axioms exit rows=%d", len(result))
    return result

def _failure(
    kind: N6FormalFailureKind, output: bytes, codes: list[int],
    attestation: str, receipts: list[FormalPhaseReceipt],
) -> N6ECompileOutcome:
    """Construct one non-promoting formal failure transcript."""
    logger.debug("_failure entry kind=%s", kind.value)
    result = N6ECompileOutcome(
        kind, output, tuple(codes), (), attestation, tuple(receipts),
    )
    logger.debug("_failure exit kind=%s", kind.value)
    return result


def compile_e_sources(
    source: N6TheoremSourceV1,
    policy: N6PolicyV1,
    captured: tuple[bytes, bytes, bytes],
) -> N6ECompileOutcome:
    """Attest and compile exact private E sources under one bounded deadline."""
    logger.debug("compile_e_sources entry")
    def finish_failure(
        kind: N6FormalFailureKind, output: bytes, codes: list[int],
        attestation: str, receipts: list[FormalPhaseReceipt],
    ) -> N6ECompileOutcome:
        logger.debug("compile_e_sources exit state=failure kind=%s", kind.value)
        return _failure(kind, output, codes, attestation, receipts)
    checked_source = snapshot_theorem_source(source, N6Lane.E_POWER_INJECTION)
    checked_policy = snapshot_policy(policy)
    if type(captured) is not tuple or len(captured) != 3:
        reject("n6-formal-captured-shape-invalid")
    expected_hashes = (
        "28052d0260b1535e484ddd8e70f97fea945ca3ff9a23c358bb45d209a071a18f",
        "b8540c65b555bd8407d558b3a16cc7cd25ab27ca636083451162f1a8a5490b48",
        checked_source.artifact_sha256,
    )
    if any(type(item) is not bytes for item in captured) or tuple(map(sha, captured)) != expected_hashes:
        reject("n6-formal-captured-byte-drift")
    _symbols(captured[-1])
    elan = shutil.which("elan")
    if elan is None:
        logger.error("compile_e_sources elan unavailable")
        return finish_failure(N6FormalFailureKind.COMPILE_ERROR, b"", [],
                              checked_source.tcb_digest, [])
    elan_snapshot = snapshot_runtime_file(Path(elan), ELAN_SHA256)
    if elan_snapshot is None:
        logger.error("compile_e_sources elan launcher continuity capture failed")
        return finish_failure(N6FormalFailureKind.COMPILE_ERROR, b"", [],
                              checked_source.tcb_digest, [])
    deadline = time.monotonic() + checked_policy.timeout_seconds
    contract = ToolchainContract(
        checked_source.toolchain_id, ELAN_SHA256, LEAN_BINARY_SHA256,
        LEAN_VERSION.encode(), checked_source.tcb_digest,
    )
    attested = attest_toolchain(elan, deadline, checked_policy.max_output_bytes, contract)
    output = bytearray(attested.output)
    codes = list(attested.return_codes)
    receipts = list(attested.phase_receipts)
    if attested.kind is not None:
        return finish_failure(_kind(attested.kind) or N6FormalFailureKind.COMPILE_ERROR,
                              bytes(output), codes, attested.attestation_digest, receipts)
    if attested.lean_path is None:
        logger.error("compile_e_sources attested lean path absent")
        return finish_failure(N6FormalFailureKind.COMPILE_ERROR, bytes(output), codes,
                              attested.attestation_digest, receipts)
    lean_snapshot = snapshot_runtime_file(attested.lean_path, LEAN_BINARY_SHA256)
    runtime_snapshots = (elan_snapshot, lean_snapshot) if lean_snapshot else ()
    if not runtime_snapshots or not continuity_set_holds(runtime_snapshots):
        logger.error("compile_e_sources launcher continuity failed after attestation")
        return finish_failure(N6FormalFailureKind.CONTINUITY_DRIFT, bytes(output), codes,
                              attested.attestation_digest, receipts)
    try:
        root = project_tmp_path()
        with tempfile.TemporaryDirectory(prefix="p3n6e-", dir=root) as directory:
            private = Path(directory)
            names = (
                "VeyraPadicCompletion.lean", "VeyraPadicFamilyIntroduction.lean",
                "VeyraPrimePowerUnbounded.lean",
            )
            private_snapshots: list[RuntimeFileSnapshotV1] = []
            for name, payload in zip(names, captured, strict=True):
                path = private / name
                path.write_bytes(payload)
                path.chmod(0o400)
                snapshot = snapshot_runtime_file(path, sha(payload))
                if snapshot is None:
                    raise OSError("private-source-continuity-capture-failed")
                private_snapshots.append(snapshot)
            all_snapshots = runtime_snapshots + tuple(private_snapshots)
            env = dict(os.environ, LEAN_PATH=str(private))
            for index, name in enumerate(names):
                if not continuity_set_holds(all_snapshots):
                    return finish_failure(N6FormalFailureKind.CONTINUITY_DRIFT, bytes(output),
                                          codes, attested.attestation_digest, receipts)
                command = [elan, "run", checked_source.toolchain_id, "lean",
                           "-DwarningAsError=true"]
                if index < len(names) - 1:
                    command += ["-o", name.replace(".lean", ".olean")]
                command.append(name)
                phase = capture_phase(
                    f"p3n6e-compile-{index}", command, private, deadline,
                    checked_policy.max_output_bytes - len(output), env,
                )
                output.extend(phase.output)
                codes.append(phase.return_code)
                receipts.append(phase.receipt)
                if not continuity_set_holds(all_snapshots):
                    return finish_failure(N6FormalFailureKind.CONTINUITY_DRIFT, bytes(output),
                                          codes, attested.attestation_digest, receipts)
                if phase.kind is not None:
                    return finish_failure(_kind(phase.kind) or N6FormalFailureKind.COMPILE_ERROR,
                                          bytes(output), codes, attested.attestation_digest, receipts)
    except OSError:
        logger.error("compile_e_sources private filesystem failure")
        return finish_failure(N6FormalFailureKind.COMPILE_ERROR, bytes(output), codes,
                              attested.attestation_digest, receipts)
    rows = _axioms(bytes(output))
    if rows is None:
        return finish_failure(N6FormalFailureKind.COMPILE_ERROR, bytes(output), codes,
                              attested.attestation_digest, receipts)
    if not continuity_holds(checked_source, captured):
        return finish_failure(N6FormalFailureKind.CONTINUITY_DRIFT, bytes(output), codes,
                              attested.attestation_digest, receipts)
    result = N6ECompileOutcome(
        None, bytes(output), tuple(codes), rows,
        attested.attestation_digest, tuple(receipts),
    )
    logger.debug("compile_e_sources exit state=success rows=%d", len(rows))
    return result
