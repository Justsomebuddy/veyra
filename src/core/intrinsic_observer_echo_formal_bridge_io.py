"""Pinned Lean, snapshots, and report binding helpers for R13.2."""
from __future__ import annotations

from hashlib import sha256
import logging
import os
from pathlib import Path
import re
import subprocess
from typing import Mapping

from .intrinsic_observer_echo_formal_manifest import (
    EXPECTED_LEAN_BINARY_SHA256,
    EXPECTED_LEAN_RUNTIME,
    TCB_SCHEMA,
)
from .intrinsic_observer_echo_formal_snapshot import (
    _SNAPSHOT_NAME_ROWS,
    IntrinsicObserverEchoLeanSnapshot,
    materialize_intrinsic_observer_echo_snapshot,
)
from .proof_core_codec import canonical_json
from .proof_elaboration_runtime_guard import guarded_lean_run
from .proof_elaboration_toolchain import LEAN_BINARY, TOOLCHAIN_ROOT, lean_runtime_digest

from .paths import PROJECT_ROOT

from .platform_posix import user_home

logger = logging.getLogger(__name__)
BUILD_DIR = PROJECT_ROOT / "data" / "tmp" / "r13-lean"
LEAN_TOOLCHAIN = "leanprover/lean4:v4.30.0-rc2"
LEAN_VERSION = "4.30.0-rc2"
STAGES = len(_SNAPSHOT_NAME_ROWS)


def sha_digest(data: bytes) -> str:
    """Return one logged SHA-256 digest."""
    logger.debug("r13_bridge_io.sha_digest entry bytes=%d", len(data))
    result = sha256(data).hexdigest()
    logger.debug("r13_bridge_io.sha_digest exit digest=%s", result)
    return result


def _runtime_identity() -> str:
    """Require the exact reviewed Lean runtime closure."""
    logger.debug("r13_bridge_io._runtime_identity entry")
    actual = lean_runtime_digest()
    if actual != EXPECTED_LEAN_RUNTIME:
        raise ValueError("r13.2-lean-runtime-closure-mismatch")
    result = f"merkle={actual[0]}|files={actual[1]}|bytes={actual[2]}"
    logger.debug("r13_bridge_io._runtime_identity exit")
    return result


def lean_command() -> list[str]:
    """Resolve only the content-bound direct Lean binary."""
    logger.debug("r13_bridge_io.lean_command entry")
    try:
        valid = (
            LEAN_BINARY.is_file()
            and sha_digest(LEAN_BINARY.read_bytes()) == EXPECTED_LEAN_BINARY_SHA256
            and bool(_runtime_identity())
        )
    except (OSError, ValueError):
        logger.exception("R13 pinned Lean unavailable")
        valid = False
    result = [str(LEAN_BINARY), "-DwarningAsError=true"] if valid else []
    logger.debug("r13_bridge_io.lean_command exit available=%s", bool(result))
    return result


def _clean_env(lean_paths: tuple[Path, ...] = ()) -> dict[str, str]:
    """Create the closed compilation environment."""
    logger.debug("r13_bridge_io._clean_env entry paths=%d", len(lean_paths))
    result = {
        "HOME": str(user_home()),
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }
    if lean_paths:
        result["LEAN_PATH"] = os.pathsep.join(map(str, lean_paths))
    logger.debug("r13_bridge_io._clean_env exit")
    return result


def toolchain_identity(command: list[str]) -> str:
    """Bind Lean content and runtime closure without a host-local path."""
    logger.debug("r13_bridge_io.toolchain_identity entry")
    try:
        proc = guarded_lean_run(
            command + ["--version"],
            cwd=TOOLCHAIN_ROOT,
            env=_clean_env(),
            timeout=30,
            expected=EXPECTED_LEAN_RUNTIME,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError("r13.2-pinned-lean-version-timeout") from exc
    version = (proc.stdout or proc.stderr).strip()
    match = re.fullmatch(r"Lean \(version ([^,\s)]+)(?:,.*)?\)", version)
    if proc.returncode or match is None or match.group(1) != LEAN_VERSION:
        raise ValueError("r13.2-pinned-lean-version-mismatch")
    metadata = Path(command[0]).stat()
    result = (
        f"{version}|toolchain={LEAN_TOOLCHAIN}|binary={Path(command[0]).name}|"
        f"sha256={EXPECTED_LEAN_BINARY_SHA256}|{_runtime_identity()}|"
        f"size={metadata.st_size}"
    )
    logger.debug("r13_bridge_io.toolchain_identity exit")
    return result


def snapshot_key(
    digests: Mapping[str, str],
    phase: str,
    source_elaboration: str,
    r11: str,
    r12: str,
    evidence: str,
    registry: str,
    effect: str,
    toolchain: str,
) -> str:
    """Bind all phase, parent, effect, source, and toolchain identities."""
    logger.debug("r13_bridge_io.snapshot_key entry")
    result = sha_digest(canonical_json({
        "schema": "veyra-intrinsic-observer-echo-snapshot-r13.2-v1",
        "sources": dict(digests),
        "phase": phase,
        "source_elaboration": source_elaboration,
        "r11": r11,
        "r12": r12,
        "executable_evidence": evidence,
        "effect_registry": registry,
        "effect": effect,
        "toolchain": toolchain,
    }).encode())
    logger.debug("r13_bridge_io.snapshot_key exit digest=%s", result)
    return result


def materialize_snapshot(
    sources: Mapping[str, bytes],
    digests: Mapping[str, str],
    bindings: tuple[str, str, str, str, str, str, str],
    toolchain: str,
) -> IntrinsicObserverEchoLeanSnapshot:
    """Materialize the exact eleven-stage R13 source snapshot."""
    logger.debug("r13_bridge_io.materialize_snapshot entry")
    key = snapshot_key(digests, *bindings, toolchain)
    lean_sources = {name: sources[name] for name, _ in _SNAPSHOT_NAME_ROWS}
    result = materialize_intrinsic_observer_echo_snapshot(BUILD_DIR, lean_sources, key)
    logger.debug("r13_bridge_io.materialize_snapshot exit")
    return result


def binding_digest(data: Mapping[str, object]) -> str:
    """Bind one validated complete report body."""
    logger.debug("r13_bridge_io.binding_digest entry")
    result = sha_digest(canonical_json({"schema": TCB_SCHEMA, **dict(data)}).encode())
    logger.debug("r13_bridge_io.binding_digest exit digest=%s", result)
    return result
