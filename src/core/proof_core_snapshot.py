"""Content-addressed, read-only Lean source snapshots for the R7 bridge."""
from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import re
import shutil
from typing import Mapping
from uuid import uuid4

from .platform_posix import exclusive_file_lock

logger = logging.getLogger(__name__)
SNAPSHOT_NAMES = {
    "arithmetic": "VeyraNativeArithmetic.lean",
    "kernel": "VeyraProofKernel.lean",
    "soundness": "VeyraProofSoundness.lean",
    "export": "VeyraProofResonance.lean",
}
KEY_PATTERN = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class LeanSourceSnapshot:
    """Paths to captured sources and their isolated object directory."""

    root: Path
    output_dir: Path
    paths: tuple[tuple[str, Path], ...]


def _verify_snapshot(root: Path, sources: Mapping[str, bytes]) -> None:
    logger.debug("proof_core_snapshot._verify_snapshot entry root=%s", root)
    for name, filename in SNAPSHOT_NAMES.items():
        path = root / filename
        try:
            actual = path.read_bytes()
        except OSError as exc:
            logger.error("proof_core_snapshot._verify_snapshot read error path=%s error=%s", path, exc)
            raise ValueError("lean-source-snapshot-unreadable") from exc
        if actual != sources[name]:
            logger.error("proof_core_snapshot._verify_snapshot mismatch name=%s", name)
            raise ValueError("lean-source-snapshot-mismatch")
    logger.debug("proof_core_snapshot._verify_snapshot exit files=%d", len(SNAPSHOT_NAMES))


def _write_snapshot(root: Path, sources: Mapping[str, bytes]) -> None:
    logger.debug("proof_core_snapshot._write_snapshot entry root=%s", root)
    temporary = root.parent / f".{root.name}.{os.getpid()}.{uuid4().hex}"
    try:
        temporary.mkdir(mode=0o700)
        for name, filename in SNAPSHOT_NAMES.items():
            path = temporary / filename
            path.write_bytes(sources[name])
            path.chmod(0o400)
        temporary.chmod(0o500)
        temporary.rename(root)
    except (KeyError, OSError) as exc:
        logger.error("proof_core_snapshot._write_snapshot error root=%s error=%s", root, exc)
        shutil.rmtree(temporary, ignore_errors=True)
        raise ValueError("lean-source-snapshot-write-failed") from exc
    logger.debug("proof_core_snapshot._write_snapshot exit root=%s", root)


def materialize_lean_snapshot(
    build_dir: Path, sources: Mapping[str, bytes], key: str,
) -> LeanSourceSnapshot:
    """Capture the already-read bytes once; compilation never reopens originals."""
    logger.debug("materialize_lean_snapshot entry build_dir=%s key=%s", build_dir, key)
    if not KEY_PATTERN.fullmatch(key) or set(sources) != set(SNAPSHOT_NAMES):
        logger.error("materialize_lean_snapshot invalid key or source set")
        raise ValueError("lean-source-snapshot-input-invalid")
    snapshot_parent = build_dir / "snapshots"
    output_dir = build_dir / "objects" / key
    try:
        snapshot_parent.mkdir(parents=True, exist_ok=True)
        lock_path = snapshot_parent / ".materialize.lock"
        with lock_path.open("a+b") as lock:
            exclusive_file_lock(lock.fileno())
            root = snapshot_parent / key
            if not root.exists():
                _write_snapshot(root, sources)
            _verify_snapshot(root, sources)
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.error("materialize_lean_snapshot filesystem error=%s", exc)
        raise ValueError("lean-source-snapshot-unavailable") from exc
    paths = tuple((name, root / filename) for name, filename in SNAPSHOT_NAMES.items())
    result = LeanSourceSnapshot(root, output_dir, paths)
    logger.debug("materialize_lean_snapshot exit root=%s", result.root)
    return result
