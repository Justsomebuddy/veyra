"""Content-addressed immutable source snapshots for the R11 Lean chain."""
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
_SNAPSHOT_NAME_ROWS = (
    ("lean_arithmetic", "VeyraNativeArithmetic.lean"),
    ("lean_semantics", "VeyraNativeSemantics.lean"),
    ("lean_intrinsic_runtime", "VeyraIntrinsicRuntime.lean"),
    ("lean_kernel", "VeyraProofKernel.lean"),
    ("lean_soundness", "VeyraProofSoundness.lean"),
    ("lean_transport", "VeyraRecurrenceModeBridge.lean"),
    ("lean_observer_core", "VeyraObserverCore.lean"),
    ("lean_observer_proof", "VeyraObserverProof.lean"),
    ("lean_export", "VeyraObserverExport.lean"),
)
SNAPSHOT_NAMES = MappingProxyType(dict(_SNAPSHOT_NAME_ROWS))
KEY_PATTERN = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class ObserverLeanSnapshot:
    """Exact captured source paths and an isolated object-cache directory."""

    root: Path
    output_dir: Path
    paths: tuple[tuple[str, Path], ...]


def valid_snapshot_names(manifest: object) -> bool:
    """Accept only the live trusted proxy while it equals exact immutable rows."""
    logger.debug("valid_snapshot_names entry type=%s", type(manifest).__name__)
    if manifest is not SNAPSHOT_NAMES:
        logger.debug("valid_snapshot_names exit rejected identity")
        return False
    try:
        rows = tuple(SNAPSHOT_NAMES.items())
    except RuntimeError:
        logger.error("valid_snapshot_names rejected concurrent backing mutation")
        return False
    result = (
        all(type(row) is tuple and len(row) == 2 and all(type(item) is str for item in row) for row in rows)
        and len({name for name, _ in rows}) == len(rows)
        and len({filename for _, filename in rows}) == len(rows)
        and all(Path(filename).name == filename and filename.endswith(".lean") for _, filename in rows)
        and rows == _SNAPSHOT_NAME_ROWS
    )
    logger.debug("valid_snapshot_names exit result=%s", result)
    return result


def require_valid_snapshot_layout() -> None:
    """Reject unless the live trusted snapshot layout is exactly canonical."""
    logger.debug("require_valid_snapshot_layout entry")
    if not valid_snapshot_names(SNAPSHOT_NAMES):
        logger.error("require_valid_snapshot_layout rejected trusted layout")
        raise ValueError("r11-snapshot-name-manifest-invalid")
    logger.debug("require_valid_snapshot_layout exit")


def _verify(root: Path, sources: Mapping[str, bytes]) -> None:
    logger.debug("observer_core_snapshot._verify entry root=%s", root)
    for name, filename in _SNAPSHOT_NAME_ROWS:
        try:
            actual = (root / filename).read_bytes()
        except OSError as exc:
            logger.error("observer_core_snapshot unreadable name=%s", name)
            raise ValueError("r11-snapshot-unreadable") from exc
        if actual != sources[name]:
            logger.error("observer_core_snapshot mismatch name=%s", name)
            raise ValueError("r11-snapshot-mismatch")
    logger.debug("observer_core_snapshot._verify exit files=%d", len(_SNAPSHOT_NAME_ROWS))


def _write(root: Path, sources: Mapping[str, bytes]) -> None:
    logger.debug("observer_core_snapshot._write entry root=%s", root)
    temporary = root.parent / f".{root.name}.{os.getpid()}.{uuid4().hex}"
    try:
        temporary.mkdir(mode=0o700)
        for name, filename in _SNAPSHOT_NAME_ROWS:
            path = temporary / filename
            path.write_bytes(sources[name])
            path.chmod(0o400)
        temporary.chmod(0o500)
        temporary.rename(root)
    except (KeyError, OSError) as exc:
        logger.error("observer_core_snapshot write failed error=%s", exc)
        shutil.rmtree(temporary, ignore_errors=True)
        raise ValueError("r11-snapshot-write-failed") from exc
    logger.debug("observer_core_snapshot._write exit root=%s", root)


def materialize_observer_snapshot(
    build_dir: Path, sources: Mapping[str, bytes], key: str,
) -> ObserverLeanSnapshot:
    """Capture already-read bytes once and reverify every cached snapshot read."""
    logger.debug("materialize_observer_snapshot entry key=%s", key)
    names = tuple(name for name, _ in _SNAPSHOT_NAME_ROWS)
    if (not valid_snapshot_names(SNAPSHOT_NAMES) or type(build_dir) is not type(Path()) or not build_dir.is_absolute()
            or type(key) is not str or not KEY_PATTERN.fullmatch(key) or tuple(sources) != names):
        logger.error("materialize_observer_snapshot invalid input")
        raise ValueError("r11-snapshot-input-invalid")
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
        logger.error("materialize_observer_snapshot filesystem error=%s", exc)
        raise ValueError("r11-snapshot-unavailable") from exc
    paths = tuple((name, root / filename) for name, filename in _SNAPSHOT_NAME_ROWS)
    result = ObserverLeanSnapshot(root, output, paths)
    logger.debug("materialize_observer_snapshot exit root=%s", result.root)
    return result


def verify_observer_snapshot(
    snapshot: ObserverLeanSnapshot, sources: Mapping[str, bytes],
) -> None:
    """Reverify exact captured bytes before a lock-held compiler read."""
    logger.debug("verify_observer_snapshot entry type=%s", type(snapshot).__name__)
    names = tuple(name for name, _ in _SNAPSHOT_NAME_ROWS)
    path_type = type(Path())
    if (
        not valid_snapshot_names(SNAPSHOT_NAMES) or type(snapshot) is not ObserverLeanSnapshot
        or type(snapshot.root) is not path_type or type(snapshot.output_dir) is not path_type
    ):
        logger.error("verify_observer_snapshot invalid input")
        raise ValueError("r11-snapshot-verification-input-invalid")
    expected_paths = tuple((name, snapshot.root / filename) for name, filename in _SNAPSHOT_NAME_ROWS)
    if (
        tuple(sources) != names or not snapshot.root.is_absolute()
        or not KEY_PATTERN.fullmatch(snapshot.root.name)
        or snapshot.output_dir != snapshot.root.parent.parent / "objects" / snapshot.root.name
        or type(snapshot.paths) is not tuple
        or any(type(row) is not tuple or len(row) != 2 or type(row[0]) is not str
               or type(row[1]) is not path_type for row in snapshot.paths)
        or snapshot.paths != expected_paths
    ):
        logger.error("verify_observer_snapshot invalid canonical paths")
        raise ValueError("r11-snapshot-verification-input-invalid")
    _verify(snapshot.root, sources)
    logger.debug("verify_observer_snapshot exit root=%s", snapshot.root)
