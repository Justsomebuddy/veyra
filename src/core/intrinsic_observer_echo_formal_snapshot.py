"""Content-addressed immutable Lean source snapshots for R13.2."""
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
    ("lean_intrinsic_vam", "VeyraIntrinsicVamBridge.lean"),
    ("lean_intrinsic_observer_echo", "VeyraIntrinsicObserverEcho.lean"),
    ("lean_export", "VeyraIntrinsicObserverEchoExport.lean"),
)
SNAPSHOT_NAMES = MappingProxyType(dict(_SNAPSHOT_NAME_ROWS))
_KEY = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True, slots=True)
class IntrinsicObserverEchoLeanSnapshot:
    """Exact captured paths and isolated fresh-object output parent."""

    root: Path
    output_dir: Path
    paths: tuple[tuple[str, Path], ...]


def valid_snapshot_names(manifest: object) -> bool:
    """Validate identity, order, uniqueness, and safe flat filenames."""
    logger.debug("r13_snapshot.valid_snapshot_names entry")
    try:
        rows = tuple(SNAPSHOT_NAMES.items())
    except RuntimeError:
        return False
    result = (
        manifest is SNAPSHOT_NAMES
        and rows == _SNAPSHOT_NAME_ROWS
        and len({name for name, _ in rows}) == len(rows)
        and len({filename for _, filename in rows}) == len(rows)
        and all(
            type(name) is str
            and type(filename) is str
            and Path(filename).name == filename
            and filename.endswith(".lean")
            for name, filename in rows
        )
    )
    logger.debug("r13_snapshot.valid_snapshot_names exit result=%s", result)
    return result


def require_valid_snapshot_layout() -> None:
    """Reject local snapshot-root drift before any parent replay."""
    logger.debug("r13_snapshot.require_valid_snapshot_layout entry")
    if not valid_snapshot_names(SNAPSHOT_NAMES):
        raise ValueError("r13.2-snapshot-name-manifest-invalid")
    logger.debug("r13_snapshot.require_valid_snapshot_layout exit")


def _verify(root: Path, sources: Mapping[str, bytes]) -> None:
    """Re-read every immutable snapshot byte."""
    logger.debug("r13_snapshot._verify entry root=%s", root)
    for name, filename in _SNAPSHOT_NAME_ROWS:
        try:
            actual = (root / filename).read_bytes()
        except OSError as exc:
            raise ValueError("r13.2-snapshot-unreadable") from exc
        if actual != sources[name]:
            raise ValueError("r13.2-snapshot-mismatch")
    logger.debug("r13_snapshot._verify exit")


def _write(root: Path, sources: Mapping[str, bytes]) -> None:
    """Atomically create one read-only immutable snapshot."""
    logger.debug("r13_snapshot._write entry root=%s", root)
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
        shutil.rmtree(temporary, ignore_errors=True)
        raise ValueError("r13.2-snapshot-write-failed") from exc
    logger.debug("r13_snapshot._write exit")


def materialize_intrinsic_observer_echo_snapshot(
    build_dir: Path,
    sources: Mapping[str, bytes],
    key: str,
) -> IntrinsicObserverEchoLeanSnapshot:
    """Capture exact bytes once and reverify every cache use."""
    logger.debug("materialize_r13_snapshot entry key=%s", key)
    names = tuple(name for name, _ in _SNAPSHOT_NAME_ROWS)
    if (
        not valid_snapshot_names(SNAPSHOT_NAMES)
        or type(build_dir) is not type(Path())
        or not build_dir.is_absolute()
        or type(key) is not str
        or _KEY.fullmatch(key) is None
        or tuple(sources) != names
    ):
        raise ValueError("r13.2-snapshot-input-invalid")
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
        raise ValueError("r13.2-snapshot-unavailable") from exc
    result = IntrinsicObserverEchoLeanSnapshot(
        root,
        output,
        tuple((name, root / filename) for name, filename in _SNAPSHOT_NAME_ROWS),
    )
    logger.debug("materialize_r13_snapshot exit root=%s", root)
    return result


def verify_intrinsic_observer_echo_snapshot(
    snapshot: object,
    sources: Mapping[str, bytes],
) -> None:
    """Recheck canonical snapshot layout and bytes before compilation."""
    logger.debug("verify_r13_snapshot entry")
    names, path_type = tuple(name for name, _ in _SNAPSHOT_NAME_ROWS), type(Path())
    if type(snapshot) is not IntrinsicObserverEchoLeanSnapshot:
        raise ValueError("r13.2-snapshot-verification-input-invalid")
    expected = tuple((name, snapshot.root / filename) for name, filename in _SNAPSHOT_NAME_ROWS)
    if (
        not valid_snapshot_names(SNAPSHOT_NAMES)
        or type(snapshot.root) is not path_type
        or type(snapshot.output_dir) is not path_type
        or tuple(sources) != names
        or not snapshot.root.is_absolute()
        or _KEY.fullmatch(snapshot.root.name) is None
        or snapshot.output_dir != snapshot.root.parent.parent / "objects" / snapshot.root.name
        or type(snapshot.paths) is not tuple
        or snapshot.paths != expected
    ):
        raise ValueError("r13.2-snapshot-verification-input-invalid")
    _verify(snapshot.root, sources)
    logger.debug("verify_r13_snapshot exit")
