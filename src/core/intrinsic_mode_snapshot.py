"""Content-addressed immutable source snapshots for the R9 Lean chain."""
from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import re
import shutil
from types import MappingProxyType
from typing import Mapping
from uuid import uuid4

from .platform_posix import exclusive_file_lock

logger = logging.getLogger(__name__)
SNAPSHOT_NAMES = MappingProxyType({
    "lean_arithmetic": "VeyraNativeArithmetic.lean",
    "lean_semantics": "VeyraNativeSemantics.lean",
    "lean_intrinsic_runtime": "VeyraIntrinsicRuntime.lean",
    "lean_kernel": "VeyraProofKernel.lean",
    "lean_soundness": "VeyraProofSoundness.lean",
    "lean_r7_export": "VeyraProofResonance.lean",
    "lean_transport": "VeyraRecurrenceModeBridge.lean",
    "lean_export": "VeyraProofModeTransport.lean",
})
KEY_PATTERN = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class IntrinsicLeanSnapshot:
    """Exact captured paths and isolated object directory for one R9 check."""

    root: Path
    output_dir: Path
    paths: tuple[tuple[str, Path], ...]


def _verify(root: Path, sources: Mapping[str, bytes]) -> None:
    logger.debug("intrinsic_mode_snapshot._verify entry root=%s", root)
    for name, filename in SNAPSHOT_NAMES.items():
        try:
            actual = (root / filename).read_bytes()
        except OSError as exc:
            logger.error("intrinsic_mode_snapshot unreadable name=%s error=%s", name, exc)
            raise ValueError("r9-snapshot-unreadable") from exc
        if actual != sources[name]:
            logger.error("intrinsic_mode_snapshot mismatch name=%s", name)
            raise ValueError("r9-snapshot-mismatch")
    logger.debug("intrinsic_mode_snapshot._verify exit files=%d", len(SNAPSHOT_NAMES))


def _write(root: Path, sources: Mapping[str, bytes]) -> None:
    logger.debug("intrinsic_mode_snapshot._write entry root=%s", root)
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
        logger.error("intrinsic_mode_snapshot write failed error=%s", exc)
        shutil.rmtree(temporary, ignore_errors=True)
        raise ValueError("r9-snapshot-write-failed") from exc
    logger.debug("intrinsic_mode_snapshot._write exit root=%s", root)


def materialize_intrinsic_snapshot(
    build_dir: Path, sources: Mapping[str, bytes], key: str,
) -> IntrinsicLeanSnapshot:
    """Capture already-read bytes once so compilation never reopens originals."""
    logger.debug("materialize_intrinsic_snapshot entry key=%s", key)
    if not KEY_PATTERN.fullmatch(key) or tuple(sources) != tuple(SNAPSHOT_NAMES):
        logger.error("materialize_intrinsic_snapshot invalid input")
        raise ValueError("r9-snapshot-input-invalid")
    parent, output = build_dir / "snapshots", build_dir / "objects" / key
    try:
        parent.mkdir(parents=True, exist_ok=True)
        with (parent / ".materialize.lock").open("a+b") as lock:
            exclusive_file_lock(lock.fileno())
            root = parent / key
            if not root.exists():
                _write(root, sources)
            _verify(root, sources)
        output.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.error("materialize_intrinsic_snapshot filesystem error=%s", exc)
        raise ValueError("r9-snapshot-unavailable") from exc
    paths = tuple((name, root / filename) for name, filename in SNAPSHOT_NAMES.items())
    result = IntrinsicLeanSnapshot(root, output, paths)
    logger.debug("materialize_intrinsic_snapshot exit root=%s", result.root)
    return result
