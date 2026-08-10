"""Fresh guarded Lean stage/object compilation for R13.2."""
from __future__ import annotations

from hashlib import sha256
import logging
from pathlib import Path
import stat
import subprocess
from tempfile import TemporaryDirectory
from typing import Mapping

from .intrinsic_observer_echo_formal_bridge_io import _clean_env, _runtime_identity
from .intrinsic_observer_echo_formal_manifest import EXPECTED_LEAN_RUNTIME
from .intrinsic_observer_echo_formal_objects import (
    _EXPECTED_R13_OBJECT_ROWS,
    EXPECTED_R13_OBJECTS,
)
from .intrinsic_observer_echo_formal_report import valid_object_manifest
from .intrinsic_observer_echo_formal_snapshot import (
    _SNAPSHOT_NAME_ROWS,
    IntrinsicObserverEchoLeanSnapshot,
    verify_intrinsic_observer_echo_snapshot,
)
from .proof_elaboration_runtime_guard import ProtectedClosure, guarded_lean_run
from .proof_elaboration_toolchain import TOOLCHAIN_ROOT, paths_digest, records_digest

from .platform_posix import exclusive_file_lock

logger = logging.getLogger(__name__)
STAGES = len(_SNAPSHOT_NAME_ROWS)
_GUARDED_DOMAIN = b"veyra-r13.2-guarded-input-v1\0"


def _reviewed_closure(
    label: str,
    root: Path,
    records: tuple[tuple[Path, int, bytes], ...],
) -> ProtectedClosure:
    """Build one exact protected source/object closure."""
    logger.debug("r13_compile._reviewed_closure entry label=%s", label)
    result = ProtectedClosure(
        label,
        tuple(path for path, _, _ in records),
        root,
        _GUARDED_DOMAIN,
        records_digest(records, root, _GUARDED_DOMAIN),
        exact_parents=True,
    )
    logger.debug("r13_compile._reviewed_closure exit")
    return result


def _source_closure(
    snapshot: IntrinsicObserverEchoLeanSnapshot,
    sources: Mapping[str, bytes],
) -> ProtectedClosure:
    """Protect all eleven exact snapshot sources."""
    logger.debug("r13_compile._source_closure entry")
    records = tuple(
        (snapshot.root / filename, len(sources[name]), sha256(sources[name]).digest())
        for name, filename in _SNAPSHOT_NAME_ROWS
    )
    result = _reviewed_closure("r13.2-snapshot-source", snapshot.root, records)
    logger.debug("r13_compile._source_closure exit")
    return result


def _object_closure(
    run_root: Path,
    objects: tuple[tuple[str, Path], ...],
) -> ProtectedClosure:
    """Protect every exact fresh prior object."""
    logger.debug("r13_compile._object_closure entry count=%d", len(objects))
    reviewed = dict(_EXPECTED_R13_OBJECT_ROWS)
    result = _reviewed_closure(
        "r13.2-prior-object",
        run_root,
        tuple(
            (path, reviewed[name][1], bytes.fromhex(reviewed[name][2]))
            for name, path in objects
        ),
    )
    logger.debug("r13_compile._object_closure exit")
    return result


def _validate_fresh_object(run_root: Path, name: str, path: Path) -> None:
    """Require the exact reviewed singleton object output."""
    logger.debug("r13_compile._validate_fresh_object entry name=%s", name)
    object_names = tuple(name for name, _ in _SNAPSHOT_NAME_ROWS[:-1])
    if not valid_object_manifest(EXPECTED_R13_OBJECTS, object_names):
        raise ValueError("r13.2-lean-object-manifest-shape-mismatch")
    filename, size, digest = dict(_EXPECTED_R13_OBJECT_ROWS)[name]
    try:
        entries, metadata = tuple(path.parent.iterdir()), path.lstat()
    except OSError as exc:
        raise ValueError("r13.2-lean-object-unreadable") from exc
    if (
        path.name != filename
        or entries != (path,)
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
    ):
        raise ValueError("r13.2-lean-object-shape-mismatch")
    expected = records_digest(
        ((path, size, bytes.fromhex(digest)),), run_root, _GUARDED_DOMAIN,
    )
    if paths_digest((path,), run_root, _GUARDED_DOMAIN) != expected:
        raise ValueError("r13.2-lean-object-digest-mismatch")
    logger.debug("r13_compile._validate_fresh_object exit")


def _runtime_absences() -> tuple[Path, ...]:
    """List forbidden loader/runtime shadow paths."""
    logger.debug("r13_compile._runtime_absences entry")
    library, lean_library = TOOLCHAIN_ROOT / "lib", TOOLCHAIN_ROOT / "lib/lean"
    lean_names = (
        "libInit_shared.so", "libleanshared.so", "libleanshared_1.so",
        "libleanshared_2.so",
    )
    os_names = ("libc.so.6", "libpthread.so.0", "libdl.so.2", "libm.so.6", "librt.so.1")
    result = tuple(lean_library / row[0] for _, row in _EXPECTED_R13_OBJECT_ROWS) + (
        library / "glibc-hwcaps",
        lean_library / "glibc-hwcaps",
        *(library / name for name in (*lean_names, *os_names)),
        *(lean_library / name for name in os_names),
    )
    logger.debug("r13_compile._runtime_absences exit count=%d", len(result))
    return result


def compile_snapshot(
    command: list[str],
    snapshot: IntrinsicObserverEchoLeanSnapshot,
    sources: Mapping[str, bytes],
) -> tuple[bool, str]:
    """Fresh-compile eleven stages under runtime/source/object guards."""
    logger.debug("r13_compile.compile_snapshot entry stages=%d", STAGES)
    diagnostics: list[str] = []
    lean_sources = {name: sources[name] for name, _ in _SNAPSHOT_NAME_ROWS}
    try:
        with (snapshot.root.parent / ".materialize.lock").open("a+b") as lock:
            exclusive_file_lock(lock.fileno())
            _runtime_identity()
            verify_intrinsic_observer_echo_snapshot(snapshot, lean_sources)
            source_closure = _source_closure(snapshot, lean_sources)
            names = tuple(name for name, _ in _SNAPSHOT_NAME_ROWS[:-1])
            if not valid_object_manifest(EXPECTED_R13_OBJECTS, names):
                raise ValueError("r13.2-lean-object-manifest-shape-mismatch")
            with TemporaryDirectory(prefix="compile-", dir=snapshot.output_dir) as run:
                run_root = Path(run)
                prior: list[tuple[str, Path]] = []
                for index, (name, filename) in enumerate(_SNAPSHOT_NAME_ROWS, 1):
                    source = snapshot.root / filename
                    stage = run_root / f"{index:02d}-{source.stem}"
                    stage.mkdir(mode=0o700)
                    output_path = stage / f"{source.stem}.olean"
                    output = [] if index == STAGES else ["-o", str(output_path)]
                    protected = [source_closure]
                    if prior:
                        protected.append(_object_closure(run_root, tuple(prior)))
                    proc = guarded_lean_run(
                        command + ["-R", str(snapshot.root)] + output + [str(source)],
                        cwd=snapshot.root,
                        env=_clean_env(tuple(path.parent for _, path in prior)),
                        timeout=120,
                        expected=EXPECTED_LEAN_RUNTIME,
                        protected=tuple(protected),
                        absent_runtime=_runtime_absences(),
                    )
                    combined = (proc.stderr or "") + (proc.stdout or "")
                    diagnostics.append(f"{index}/{STAGES}:{source.stem}:rc={proc.returncode}")
                    if proc.returncode or "warning:" in combined.lower():
                        return False, ";".join(diagnostics) + ":" + combined.strip()[-600:]
                    if index != STAGES:
                        _validate_fresh_object(run_root, name, output_path)
                        prior.append((name, output_path))
    except (KeyError, OSError, subprocess.TimeoutExpired, ValueError) as exc:
        logger.error("R13 formal compile blocked=%s", exc)
        return False, str(exc)
    result = ";".join(diagnostics)
    logger.debug("r13_compile.compile_snapshot exit")
    return True, result
