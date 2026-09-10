"""Pinned Lean, guarded compilation, and immutable snapshot helpers for R11."""
from __future__ import annotations

from hashlib import sha256
import logging
import os
from pathlib import Path
import re
import stat
import subprocess
from tempfile import TemporaryDirectory
from typing import Mapping

from .observer_core_manifest import (
    EXPECTED_LEAN_BINARY_SHA256,
    EXPECTED_LEAN_RUNTIME,
)
from .observer_core_bridge_report import valid_object_manifest
from .observer_core_objects import _EXPECTED_LEAN_OBJECT_ROWS, EXPECTED_LEAN_OBJECTS
from .observer_core_snapshot import (
    _SNAPSHOT_NAME_ROWS,
    SNAPSHOT_NAMES,
    ObserverLeanSnapshot,
    materialize_observer_snapshot,
    valid_snapshot_names,
    verify_observer_snapshot,
)
from .proof_core_codec import canonical_json
from .proof_elaboration_runtime_guard import ProtectedClosure, guarded_lean_run
from .proof_elaboration_toolchain import (
    LEAN_BINARY,
    TOOLCHAIN_ROOT,
    lean_runtime_digest,
    paths_digest,
    records_digest,
)

from .paths import PROJECT_ROOT

from .platform_posix import exclusive_file_lock, user_home

logger = logging.getLogger(__name__)
BUILD_DIR = PROJECT_ROOT / "data" / "tmp" / "r11-lean"
LEAN_TOOLCHAIN = "leanprover/lean4:v4.30.0-rc2"
LEAN_VERSION = "4.30.0-rc2"
STAGES = len(_SNAPSHOT_NAME_ROWS)
R11_GUARDED_DOMAIN = b"veyra-r11-guarded-input-v1\0"


def sha_digest(data: bytes) -> str:
    """Return a logged SHA-256 digest."""
    logger.debug("observer_core_bridge_io.sha_digest entry bytes=%d", len(data))
    result = sha256(data).hexdigest()
    logger.debug("observer_core_bridge_io.sha_digest exit result=%s", result)
    return result


def _runtime_identity() -> str:
    logger.debug("observer_core_bridge_io._runtime_identity entry")
    actual = lean_runtime_digest()
    if actual != EXPECTED_LEAN_RUNTIME:
        logger.error("observer_core_bridge_io runtime mismatch actual=%r", actual)
        raise ValueError("r11-lean-runtime-closure-mismatch")
    result = f"merkle={actual[0]}|files={actual[1]}|bytes={actual[2]}"
    logger.debug("observer_core_bridge_io._runtime_identity exit result=%s", result)
    return result


def lean_command() -> list[str]:
    """Resolve only the content-bound direct Lean binary."""
    logger.debug("observer_core_bridge_io.lean_command entry")
    try:
        valid = (
            LEAN_BINARY.is_file()
            and sha_digest(LEAN_BINARY.read_bytes()) == EXPECTED_LEAN_BINARY_SHA256
            and bool(_runtime_identity())
        )
    except (OSError, ValueError) as exc:
        logger.error("observer_core_bridge_io Lean unavailable=%s", exc)
        valid = False
    result = [str(LEAN_BINARY), "-DwarningAsError=true"] if valid else []
    logger.debug("observer_core_bridge_io.lean_command exit available=%s", bool(result))
    return result


def _clean_env(lean_paths: tuple[Path, ...] = ()) -> dict[str, str]:
    logger.debug("observer_core_bridge_io._clean_env entry paths=%d", len(lean_paths))
    result = {
        "HOME": str(user_home()),
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }
    if lean_paths:
        result["LEAN_PATH"] = os.pathsep.join(map(str, lean_paths))
    logger.debug("observer_core_bridge_io._clean_env exit keys=%r", tuple(result))
    return result


def toolchain_identity(command: list[str]) -> str:
    """Bind exact Lean content/runtime without host-local filesystem metadata."""
    logger.debug("observer_core_bridge_io.toolchain_identity entry")
    try:
        proc = guarded_lean_run(
            command + ["--version"], cwd=TOOLCHAIN_ROOT, env=_clean_env(),
            timeout=30, expected=EXPECTED_LEAN_RUNTIME,
        )
    except subprocess.TimeoutExpired as exc:
        logger.error("observer_core_bridge_io toolchain identity timed out")
        raise ValueError("r11-pinned-lean-version-timeout") from exc
    version = (proc.stdout or proc.stderr).strip()
    match = re.fullmatch(r"Lean \(version ([^,\s)]+)(?:,.*)?\)", version)
    if proc.returncode or match is None or match.group(1) != LEAN_VERSION:
        raise ValueError("r11-pinned-lean-version-mismatch")
    metadata = Path(command[0]).stat()
    result = (
        f"{version}|toolchain={LEAN_TOOLCHAIN}|binary={Path(command[0]).name}|"
        f"sha256={EXPECTED_LEAN_BINARY_SHA256}|{_runtime_identity()}|"
        f"size={metadata.st_size}"
    )
    logger.debug("observer_core_bridge_io.toolchain_identity exit result=%s", result)
    return result


def snapshot_key(
    digests: Mapping[str, str], artifact: str, r10: str, toolchain: str,
) -> str:
    """Bind live sources, canonical artifact, verified R10, and toolchain."""
    logger.debug("observer_core_bridge_io.snapshot_key entry")
    result = sha_digest(canonical_json({
        "schema": "veyra-observer-core-snapshot-v1",
        "sources": dict(digests), "artifact": artifact,
        "r10": r10, "toolchain": toolchain,
    }).encode())
    logger.debug("observer_core_bridge_io.snapshot_key exit result=%s", result)
    return result


def materialize_snapshot(
    sources: Mapping[str, bytes], digests: Mapping[str, str],
    artifact: str, r10: str, toolchain: str,
) -> ObserverLeanSnapshot:
    """Materialize and reverify the exact nine-stage R11 snapshot."""
    logger.debug("observer_core_bridge_io.materialize_snapshot entry")
    key = snapshot_key(digests, artifact, r10, toolchain)
    lean_sources = {name: sources[name] for name, _ in _SNAPSHOT_NAME_ROWS}
    result = materialize_observer_snapshot(BUILD_DIR, lean_sources, key)
    logger.debug("observer_core_bridge_io.materialize_snapshot exit root=%s", result.root)
    return result


def _reviewed_closure(
    label: str, root: Path, records: tuple[tuple[Path, int, bytes], ...],
) -> ProtectedClosure:
    logger.debug("observer_core_bridge_io._reviewed_closure entry label=%s", label)
    result = ProtectedClosure(
        label, tuple(path for path, _, _ in records), root, R11_GUARDED_DOMAIN,
        records_digest(records, root, R11_GUARDED_DOMAIN), exact_parents=True,
    )
    logger.debug("observer_core_bridge_io._reviewed_closure exit files=%d", len(records))
    return result


def _source_closure(
    snapshot: ObserverLeanSnapshot, sources: Mapping[str, bytes],
) -> ProtectedClosure:
    logger.debug("observer_core_bridge_io._source_closure entry")
    records = tuple(
        (snapshot.root / filename, len(sources[name]), sha256(sources[name]).digest())
        for name, filename in _SNAPSHOT_NAME_ROWS
    )
    result = _reviewed_closure("r11-snapshot-source", snapshot.root, records)
    logger.debug("observer_core_bridge_io._source_closure exit")
    return result


def _object_closure(
    run_root: Path, objects: tuple[tuple[str, Path], ...],
) -> ProtectedClosure:
    logger.debug("observer_core_bridge_io._object_closure entry files=%d", len(objects))
    reviewed = dict(_EXPECTED_LEAN_OBJECT_ROWS)
    records = tuple(
        (path, reviewed[name][1], bytes.fromhex(reviewed[name][2]))
        for name, path in objects
    )
    result = _reviewed_closure("r11-prior-object", run_root, records)
    logger.debug("observer_core_bridge_io._object_closure exit")
    return result


def _validate_fresh_object(run_root: Path, name: str, path: Path) -> None:
    logger.debug("observer_core_bridge_io._validate_fresh_object entry name=%s", name)
    object_names = tuple(name for name, _ in _SNAPSHOT_NAME_ROWS[:-1])
    if not valid_object_manifest(EXPECTED_LEAN_OBJECTS, object_names):
        raise ValueError("r11-lean-object-manifest-shape-mismatch")
    filename, size, digest = dict(_EXPECTED_LEAN_OBJECT_ROWS)[name]
    try:
        entries, metadata = tuple(path.parent.iterdir()), path.lstat()
    except OSError as exc:
        raise ValueError("r11-lean-object-unreadable") from exc
    if (
        path.name != filename or entries != (path,)
        or not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1
    ):
        raise ValueError("r11-lean-object-shape-mismatch")
    expected = records_digest(
        ((path, size, bytes.fromhex(digest)),), run_root, R11_GUARDED_DOMAIN,
    )
    if paths_digest((path,), run_root, R11_GUARDED_DOMAIN) != expected:
        raise ValueError("r11-lean-object-digest-mismatch")
    logger.debug("observer_core_bridge_io._validate_fresh_object exit name=%s", name)


def _default_runtime_absences() -> tuple[Path, ...]:
    logger.debug("observer_core_bridge_io._default_runtime_absences entry")
    library, lean_library = TOOLCHAIN_ROOT / "lib", TOOLCHAIN_ROOT / "lib/lean"
    lean_names = (
        "libInit_shared.so", "libleanshared.so", "libleanshared_1.so",
        "libleanshared_2.so",
    )
    os_names = ("libc.so.6", "libpthread.so.0", "libdl.so.2", "libm.so.6", "librt.so.1")
    result = tuple(lean_library / row[0] for _, row in _EXPECTED_LEAN_OBJECT_ROWS) + (
        library / "glibc-hwcaps", lean_library / "glibc-hwcaps",
        *(library / name for name in (*lean_names, *os_names)),
        *(lean_library / name for name in os_names),
    )
    logger.debug("observer_core_bridge_io._default_runtime_absences exit count=%d", len(result))
    return result


def compile_snapshot(
    command: list[str], snapshot: ObserverLeanSnapshot, sources: Mapping[str, bytes],
) -> tuple[bool, str]:
    """Fresh-compile every captured stage under runtime/source/object guards."""
    logger.debug("observer_core_bridge_io.compile_snapshot entry stages=%d", STAGES)
    diagnostics: list[str] = []
    if not valid_snapshot_names(SNAPSHOT_NAMES):
        logger.error("observer_core_bridge_io rejected snapshot name manifest")
        return False, "r11-snapshot-name-manifest-invalid"
    lean_sources = {name: sources[name] for name, _ in _SNAPSHOT_NAME_ROWS}
    try:
        with (snapshot.root.parent / ".materialize.lock").open("a+b") as lock:
            exclusive_file_lock(lock.fileno())
            _runtime_identity()
            verify_observer_snapshot(snapshot, lean_sources)
            source_closure = _source_closure(snapshot, lean_sources)
            object_names = tuple(name for name, _ in _SNAPSHOT_NAME_ROWS[:-1])
            if not valid_object_manifest(EXPECTED_LEAN_OBJECTS, object_names):
                raise ValueError("r11-lean-object-manifest-shape-mismatch")
            with TemporaryDirectory(prefix="compile-", dir=snapshot.output_dir) as run:
                run_root, prior = Path(run), []
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
                        timeout=120, expected=EXPECTED_LEAN_RUNTIME,
                        protected=tuple(protected),
                        absent_runtime=_default_runtime_absences(),
                    )
                    combined = (proc.stderr or "") + (proc.stdout or "")
                    diagnostics.append(f"{index}/{STAGES}:{source.stem}:rc={proc.returncode}")
                    if proc.returncode or "warning:" in combined.lower():
                        return False, ";".join(diagnostics) + ":" + combined.strip()[-600:]
                    if index != STAGES:
                        _validate_fresh_object(run_root, name, output_path)
                        prior.append((name, output_path))
    except (KeyError, OSError, subprocess.TimeoutExpired, ValueError) as exc:
        logger.error("observer_core_bridge_io compile blocked=%s", exc)
        return False, str(exc)
    result = ";".join(diagnostics)
    logger.debug("observer_core_bridge_io.compile_snapshot exit diagnostics=%s", result)
    return True, result


def binding_digest(
    tcb_schema: str, bridge_id: str, theorem_ids: tuple[str, ...],
    digests: Mapping[str, str], snapshot: str, artifact: str,
    r10: str, toolchain: str,
) -> str:
    """Bind every checked R11 report field into one canonical digest."""
    logger.debug("observer_core_bridge_io.binding_digest entry")
    result = sha_digest(canonical_json({
        "schema": "veyra-observer-core-binding-v1", "tcb_schema": tcb_schema,
        "bridge_id": bridge_id, "theorems": list(theorem_ids), "sources": dict(digests),
        "snapshot": snapshot, "artifact": artifact, "r10": r10,
        "toolchain": toolchain,
    }).encode())
    logger.debug("observer_core_bridge_io.binding_digest exit result=%s", result)
    return result
