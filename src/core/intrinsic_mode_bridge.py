"""Fail-closed reviewed Python/native/Lean bridge for R9 intrinsic transport."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import logging
import os
import re
import shutil
import subprocess
from types import MappingProxyType
from typing import Mapping

from .intrinsic_mode_lean_render import (
    REQUIRED_DIGESTS, THEOREM_IDS, render_mode_transport_lean,
)
from .intrinsic_mode_manifest import EXPECTED_R9_TCB_DIGESTS, TCB_SCHEMA
from .intrinsic_mode_snapshot import SNAPSHOT_NAMES, materialize_intrinsic_snapshot
from .proof_core_bridge import (
    ProofCoreBridgeReport, proof_core_bridge_report, verify_proof_core_bridge_report,
)
from .proof_core_codec import canonical_json
from .proof_core_manifest import EXPECTED_LEAN_BINARY_SHA256
from .proof_core_resonance import intrinsic_resonance_theorem

from .paths import PROJECT_ROOT

logger = logging.getLogger(__name__)
LEAN_DIR = PROJECT_ROOT / "proofs" / "lean"
BUILD_DIR = PROJECT_ROOT / "data" / "tmp" / "r9-lean"
LEAN_TOOLCHAIN = "leanprover/lean4:v4.30.0-rc2"
LEAN_VERSION = "4.30.0-rc2"
PLACEHOLDER = re.compile(r"\b(?:sorryAx|sorry|admit|axiom|unsafe)\b")
SOURCE_PATHS = MappingProxyType({
    "python_transport": PROJECT_ROOT / "src/core/intrinsic_mode_transport.py",
    "python_laws": PROJECT_ROOT / "src/core/intrinsic_mode_laws.py",
    "python_renderer": PROJECT_ROOT / "src/core/intrinsic_mode_lean_render.py",
    "python_snapshot": PROJECT_ROOT / "src/core/intrinsic_mode_snapshot.py",
    "python_bridge": PROJECT_ROOT / "src/core/intrinsic_mode_bridge.py",
    "native_runtime": PROJECT_ROOT / "src/core/native_runtime.py",
    "intrinsic_arithmetic": PROJECT_ROOT / "src/core/intrinsic_arithmetic.py",
    "proof_core_types": PROJECT_ROOT / "src/core/proof_core_types.py",
    "lean_arithmetic": LEAN_DIR / "VeyraNativeArithmetic.lean",
    "lean_semantics": LEAN_DIR / "VeyraNativeSemantics.lean",
    "lean_intrinsic_runtime": LEAN_DIR / "VeyraIntrinsicRuntime.lean",
    "lean_kernel": LEAN_DIR / "VeyraProofKernel.lean",
    "lean_soundness": LEAN_DIR / "VeyraProofSoundness.lean",
    "lean_r7_export": LEAN_DIR / "VeyraProofResonance.lean",
    "lean_transport": LEAN_DIR / "VeyraRecurrenceModeBridge.lean",
    "lean_export": LEAN_DIR / "VeyraProofModeTransport.lean",
})
LEAN_STAGE_COUNT = len(SNAPSHOT_NAMES)
CHECKED_DIAGNOSTICS = ";".join(
    f"{index}/{LEAN_STAGE_COUNT}:{Path(filename).stem}:rc=0"
    for index, filename in enumerate(SNAPSHOT_NAMES.values(), 1)
)
CHECKED_BOUNDARY = (
    "Recurrence equivalent only to the fixed-anchor unary IntrinsicMode image; "
    "no generic Mode, labels, cyclic phase, weighted, approximate, or shadow bridge"
)


@dataclass(frozen=True)
class IntrinsicModeBridgeReport:
    """Exact evidence exposed by one checked R9 bridge execution."""

    status: str
    theorem_ids: tuple[str, ...]
    r7_artifact_digest: str
    r7_bridge_digest: str
    source_digests: tuple[tuple[str, str], ...]
    binding_digest: str
    r7_artifact_checked: bool
    manifest_checked: bool
    source_bound: bool
    lean_checked: bool
    toolchain: str
    diagnostics: str
    boundary: str


def _sha(data: bytes) -> str:
    logger.debug("intrinsic_mode_bridge._sha entry bytes=%d", len(data))
    result = sha256(data).hexdigest()
    logger.debug("intrinsic_mode_bridge._sha exit result=%s", result)
    return result


def _read_sources(paths: Mapping[str, Path]) -> dict[str, bytes]:
    logger.debug("intrinsic_mode_bridge._read_sources entry paths=%d", len(paths))
    if tuple(paths) != tuple(SOURCE_PATHS):
        logger.error("intrinsic_mode_bridge invalid source path keys")
        raise ValueError("r9-source-path-set-invalid")
    try:
        result = {name: Path(path).read_bytes() for name, path in paths.items()}
    except OSError as exc:
        logger.error("intrinsic_mode_bridge source unreadable error=%s", exc)
        raise ValueError("r9-source-unreadable") from exc
    logger.debug("intrinsic_mode_bridge._read_sources exit")
    return result


def _lean_command() -> list[str]:
    logger.debug("intrinsic_mode_bridge._lean_command entry")
    elan = shutil.which("elan")
    if not elan:
        logger.error("intrinsic_mode_bridge pinned elan unavailable")
        return []
    resolved = subprocess.run(
        [elan, "which", "lean"], cwd=PROJECT_ROOT,
        text=True, capture_output=True, check=False,
    )
    lean_path = Path(resolved.stdout.strip()) if resolved.returncode == 0 else Path()
    try:
        lean_bytes = lean_path.read_bytes() if lean_path.is_file() else b""
    except OSError:
        lean_bytes = b""
    if not lean_bytes or _sha(lean_bytes) != EXPECTED_LEAN_BINARY_SHA256:
        logger.error("intrinsic_mode_bridge pinned Lean content unavailable")
        return []
    result = [str(lean_path), "-DwarningAsError=true"]
    logger.debug("intrinsic_mode_bridge._lean_command exit result=%r", result)
    return result


def _toolchain_identity(command: list[str]) -> str:
    logger.debug("intrinsic_mode_bridge._toolchain_identity entry")
    proc = subprocess.run(command + ["--version"], text=True, capture_output=True, check=False)
    version = (proc.stdout or proc.stderr).strip()
    match = re.fullmatch(r"Lean \(version ([^,\s)]+)(?:,.*)?\)", version)
    if proc.returncode or match is None or match.group(1) != LEAN_VERSION:
        logger.error("intrinsic_mode_bridge toolchain mismatch version=%r", version)
        raise ValueError("r9-pinned-lean-version-mismatch")
    lean_path = Path(command[0])
    try:
        lean_bytes = lean_path.read_bytes()
    except OSError as exc:
        raise ValueError("r9-pinned-lean-binary-unavailable") from exc
    if _sha(lean_bytes) != EXPECTED_LEAN_BINARY_SHA256:
        raise ValueError("r9-pinned-lean-binary-digest-mismatch")
    result = (
        f"{version}|toolchain={LEAN_TOOLCHAIN}|binary=lean|"
        f"sha256={EXPECTED_LEAN_BINARY_SHA256}|size={len(lean_bytes)}"
    )
    logger.debug("intrinsic_mode_bridge._toolchain_identity exit result=%s", result)
    return result


def _blocked(reason: str, artifact: str = "") -> IntrinsicModeBridgeReport:
    logger.error("intrinsic_mode_bridge blocked reason=%s", reason)
    return IntrinsicModeBridgeReport(
        "blocked", (), artifact, "", (), "", False, False, False, False,
        LEAN_TOOLCHAIN, reason,
        "no R9 certificate without R7 replay, reviewed hashes, snapshot, and pinned Lean",
    )


def _validate_inputs(
    sources: Mapping[str, bytes], r7: ProofCoreBridgeReport,
) -> tuple[dict[str, str], str]:
    logger.debug("intrinsic_mode_bridge._validate_inputs entry")
    if not verify_proof_core_bridge_report(r7):
        raise ValueError("r9-r7-bridge-rejected")
    digests = {name: _sha(source) for name, source in sources.items()}
    render_digests = {name: digests[name] for name in REQUIRED_DIGESTS}
    expected_export = render_mode_transport_lean(
        intrinsic_resonance_theorem().artifact.proof_digest, render_digests,
    ).encode()
    if sources["lean_export"] != expected_export:
        raise ValueError("r9-generated-lean-source-drift")
    lean_source = b"\n".join(sources[name] for name in SNAPSHOT_NAMES)
    matches = tuple(sorted(set(PLACEHOLDER.findall(lean_source.decode("utf-8")))))
    if matches:
        raise ValueError("r9-forbidden-lean-placeholder:" + ",".join(matches))
    if digests != EXPECTED_R9_TCB_DIGESTS:
        raise ValueError("r9-reviewed-tcb-drift")
    logger.debug("intrinsic_mode_bridge._validate_inputs exit")
    return digests, r7.binding_digest


def _compile(command: list[str], snapshot) -> tuple[bool, str]:
    logger.debug("intrinsic_mode_bridge._compile entry sources=%d", len(snapshot.paths))
    env = {**os.environ, "LEAN_PATH": str(snapshot.output_dir)}
    diagnostics = []
    for index, (_, source) in enumerate(snapshot.paths, 1):
        output = [] if index == len(snapshot.paths) else ["-o", str(snapshot.output_dir / f"{source.stem}.olean")]
        proc = subprocess.run(
            command + ["-R", str(snapshot.root)] + output + [str(source)],
            cwd=snapshot.root, env=env, text=True, capture_output=True, check=False,
        )
        combined = (proc.stderr or "") + (proc.stdout or "")
        diagnostics.append(f"{index}/{LEAN_STAGE_COUNT}:{source.stem}:rc={proc.returncode}")
        if proc.returncode or "warning:" in combined.lower():
            return False, ";".join(diagnostics) + ":" + combined.strip()[-600:]
    result = ";".join(diagnostics)
    logger.debug("intrinsic_mode_bridge._compile exit diagnostics=%s", result)
    return True, result


def _binding(digests: Mapping[str, str], artifact: str, r7_bridge: str, toolchain: str) -> str:
    logger.debug("intrinsic_mode_bridge._binding entry")
    result = _sha(canonical_json({
        "schema": "veyra-intrinsic-mode-binding-v1", "tcb_schema": TCB_SCHEMA,
        "theorems": list(THEOREM_IDS), "sources": dict(digests), "r7_artifact": artifact,
        "r7_bridge": r7_bridge, "toolchain": toolchain,
    }).encode())
    logger.debug("intrinsic_mode_bridge._binding exit result=%s", result)
    return result


def check_intrinsic_mode_bridge(
    source_paths: Mapping[str, Path] | None = None,
) -> IntrinsicModeBridgeReport:
    """Read once, validate the reviewed TCB, snapshot, and compile eight Lean sources."""
    logger.debug("check_intrinsic_mode_bridge entry custom=%s", source_paths is not None)
    artifact = intrinsic_resonance_theorem().artifact.proof_digest
    try:
        sources = _read_sources(SOURCE_PATHS if source_paths is None else source_paths)
        r7 = proof_core_bridge_report()
        digests, r7_bridge = _validate_inputs(sources, r7)
        command = _lean_command()
        if not command:
            raise ValueError("r9-pinned-elan-not-found")
        toolchain = _toolchain_identity(command)
        snapshot_key = _sha(canonical_json({
            "schema": "veyra-intrinsic-snapshot-v1", "sources": digests,
            "r7": r7_bridge, "toolchain": toolchain,
        }).encode())
        lean_sources = {name: sources[name] for name in SNAPSHOT_NAMES}
        snapshot = materialize_intrinsic_snapshot(BUILD_DIR, lean_sources, snapshot_key)
        lean_checked, diagnostics = _compile(command, snapshot)
        if not lean_checked:
            raise ValueError(diagnostics)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return _blocked(str(exc), artifact)
    result = IntrinsicModeBridgeReport(
        "checked", THEOREM_IDS, artifact, r7_bridge, tuple(digests.items()),
        _binding(digests, artifact, r7_bridge, toolchain), True, True, True, True,
        toolchain, diagnostics, CHECKED_BOUNDARY,
    )
    logger.debug("check_intrinsic_mode_bridge exit binding=%s", result.binding_digest)
    return result


def verify_intrinsic_mode_bridge_report(report: object) -> bool:
    """Independently rehash all trust inputs exposed by a cached checked report."""
    logger.debug("verify_intrinsic_mode_bridge_report entry type=%s", type(report).__name__)
    if type(report) is not IntrinsicModeBridgeReport or report.status != "checked":
        return False
    try:
        sources = _read_sources(SOURCE_PATHS)
        r7 = proof_core_bridge_report()
        digests, r7_bridge = _validate_inputs(sources, r7)
        command = _lean_command()
        if not command:
            return False
        toolchain = _toolchain_identity(command)
    except (OSError, UnicodeDecodeError, ValueError):
        logger.exception("verify_intrinsic_mode_bridge_report trust failure")
        return False
    artifact = intrinsic_resonance_theorem().artifact.proof_digest
    expected = IntrinsicModeBridgeReport(
        "checked", THEOREM_IDS, artifact, r7_bridge, tuple(digests.items()),
        _binding(digests, artifact, r7_bridge, toolchain), True, True, True, True,
        toolchain, CHECKED_DIAGNOSTICS, CHECKED_BOUNDARY,
    )
    result = report == expected
    if not result:
        logger.error("verify_intrinsic_mode_bridge_report exact report mismatch")
    logger.debug("verify_intrinsic_mode_bridge_report exit result=%s", result)
    return result


def _default_trust_key() -> str:
    logger.debug("intrinsic_mode_bridge._default_trust_key entry")
    try:
        sources = _read_sources(SOURCE_PATHS)
        r7 = proof_core_bridge_report()
        command = _lean_command()
        if not command:
            raise ValueError("r9-pinned-elan-not-found")
        result = _sha(canonical_json({
            "sources": {name: _sha(source) for name, source in sources.items()},
            "r7": [r7.artifact_digest, r7.binding_digest],
            "toolchain": _toolchain_identity(command),
        }).encode())
    except (OSError, ValueError) as exc:
        result = "blocked:" + str(exc)
    logger.debug("intrinsic_mode_bridge._default_trust_key exit result=%s", result)
    return result


@lru_cache(maxsize=8)
def _cached_default_report(trust_key: str) -> IntrinsicModeBridgeReport:
    logger.debug("intrinsic_mode_bridge._cached_default_report entry key=%s", trust_key)
    result = check_intrinsic_mode_bridge()
    logger.debug("intrinsic_mode_bridge._cached_default_report exit status=%s", result.status)
    return result


def intrinsic_mode_bridge_report() -> IntrinsicModeBridgeReport:
    """Rehash live inputs every call and cache compilation only by their exact key."""
    logger.debug("intrinsic_mode_bridge_report entry")
    result = _cached_default_report(_default_trust_key())
    if result.status == "checked" and not verify_intrinsic_mode_bridge_report(result):
        result = _blocked("cached-r9-bridge-integrity-mismatch", result.r7_artifact_digest)
    logger.debug("intrinsic_mode_bridge_report exit status=%s", result.status)
    return result
