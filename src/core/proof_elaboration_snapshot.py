"""Content-addressed immutable source snapshots for the R10 Lean chain."""
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
    "lean_r9_export": "VeyraProofModeTransport.lean",
    "lean_elaboration": "VeyraElaborationSemantics.lean",
    "lean_export": "VeyraProofElaboration.lean",
})
KEY_PATTERN = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class ElaborationLeanSnapshot:
    """Exact captured source paths and isolated output directory."""

    root: Path
    output_dir: Path
    paths: tuple[tuple[str, Path], ...]


def _verify(root: Path, sources: Mapping[str, bytes]) -> None:
    logger.debug("proof_elaboration_snapshot._verify entry root=%s", root)
    for name, filename in SNAPSHOT_NAMES.items():
        try:
            actual = (root / filename).read_bytes()
        except OSError as exc:
            logger.error("proof_elaboration_snapshot unreadable name=%s", name)
            raise ValueError("r10-snapshot-unreadable") from exc
        if actual != sources[name]:
            logger.error("proof_elaboration_snapshot mismatch name=%s", name)
            raise ValueError("r10-snapshot-mismatch")
    logger.debug("proof_elaboration_snapshot._verify exit files=%d", len(SNAPSHOT_NAMES))


def _write(root: Path, sources: Mapping[str, bytes]) -> None:
    logger.debug("proof_elaboration_snapshot._write entry root=%s", root)
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
        logger.error("proof_elaboration_snapshot write failed error=%s", exc)
        shutil.rmtree(temporary, ignore_errors=True)
        raise ValueError("r10-snapshot-write-failed") from exc
    logger.debug("proof_elaboration_snapshot._write exit root=%s", root)


def materialize_elaboration_snapshot(
    build_dir: Path, sources: Mapping[str, bytes], key: str,
) -> ElaborationLeanSnapshot:
    """Capture already-read bytes once and verify every cached snapshot read."""
    logger.debug("materialize_elaboration_snapshot entry key=%s", key)
    if not KEY_PATTERN.fullmatch(key) or tuple(sources) != tuple(SNAPSHOT_NAMES):
        logger.error("materialize_elaboration_snapshot invalid input")
        raise ValueError("r10-snapshot-input-invalid")
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
        logger.error("materialize_elaboration_snapshot filesystem error=%s", exc)
        raise ValueError("r10-snapshot-unavailable") from exc
    paths = tuple((name, root / filename) for name, filename in SNAPSHOT_NAMES.items())
    result = ElaborationLeanSnapshot(root, output, paths)
    logger.debug("materialize_elaboration_snapshot exit root=%s", result.root)
    return result


def verify_elaboration_snapshot(
    snapshot: ElaborationLeanSnapshot, sources: Mapping[str, bytes],
) -> None:
    """Reverify exact captured bytes before a lock-held compiler read."""
    logger.debug("verify_elaboration_snapshot entry type=%s", type(snapshot).__name__)
    if (
        type(snapshot) is not ElaborationLeanSnapshot
        or tuple(sources) != tuple(SNAPSHOT_NAMES)
        or not KEY_PATTERN.fullmatch(snapshot.root.name)
    ):
        logger.error("verify_elaboration_snapshot invalid input")
        raise ValueError("r10-snapshot-verification-input-invalid")
    _verify(snapshot.root, sources)
    logger.debug("verify_elaboration_snapshot exit root=%s", snapshot.root)
