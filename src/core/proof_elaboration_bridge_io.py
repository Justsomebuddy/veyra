"""Pinned toolchain, immutable snapshot, and digest helpers for R10."""
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

from .proof_core_codec import canonical_json
from .proof_elaboration_manifest import (
    EXPECTED_LEAN_BINARY_SHA256, EXPECTED_LEAN_RUNTIME,
)
from .proof_elaboration_objects import EXPECTED_LEAN_OBJECTS
from .proof_elaboration_runtime_guard import ProtectedClosure, guarded_lean_run
from .proof_elaboration_snapshot import (
    SNAPSHOT_NAMES, ElaborationLeanSnapshot, materialize_elaboration_snapshot,
    verify_elaboration_snapshot,
)
from .proof_elaboration_toolchain import (
    GUARDED_INPUT_DOMAIN, LEAN_BINARY, TOOLCHAIN_ROOT, lean_runtime_digest,
    paths_digest, records_digest,
)

from .paths import PROJECT_ROOT

from .platform_posix import exclusive_file_lock, user_home

logger = logging.getLogger(__name__)
BUILD_DIR = PROJECT_ROOT / "data" / "tmp" / "r10-lean"
LEAN_TOOLCHAIN = "leanprover/lean4:v4.30.0-rc2"
LEAN_VERSION = "4.30.0-rc2"
STAGES = len(SNAPSHOT_NAMES)


def sha_digest(data: bytes) -> str:
    """Return a logged SHA-256 digest for immutable evidence."""
    logger.debug("proof_elaboration_bridge_io.sha_digest entry bytes=%d", len(data))
    result = sha256(data).hexdigest()
    logger.debug("proof_elaboration_bridge_io.sha_digest exit result=%s", result)
    return result


def _runtime_identity() -> str:
    logger.debug("proof_elaboration_bridge_io._runtime_identity entry")
    actual = lean_runtime_digest()
    if actual != EXPECTED_LEAN_RUNTIME:
        logger.error("proof_elaboration_bridge_io runtime closure mismatch actual=%r", actual)
        raise ValueError("r10-lean-runtime-closure-mismatch")
    result = f"merkle={actual[0]}|files={actual[1]}|bytes={actual[2]}"
    logger.debug("proof_elaboration_bridge_io._runtime_identity exit result=%s", result)
    return result


def lean_command() -> list[str]:
    """Resolve only the allowlisted, content-bound direct Lean binary."""
    logger.debug("proof_elaboration_bridge_io.lean_command entry")
    try:
        valid = (
            LEAN_BINARY.is_file()
            and sha_digest(LEAN_BINARY.read_bytes()) == EXPECTED_LEAN_BINARY_SHA256
            and bool(_runtime_identity())
        )
    except (OSError, ValueError) as exc:
        logger.error("proof_elaboration_bridge_io Lean binary unreadable=%s", exc)
        valid = False
    result = [str(LEAN_BINARY), "-DwarningAsError=true"] if valid else []
    logger.debug("proof_elaboration_bridge_io.lean_command exit available=%s", bool(result))
    return result


def _clean_env(lean_paths: tuple[Path, ...] = ()) -> dict[str, str]:
    logger.debug("proof_elaboration_bridge_io._clean_env entry lean_paths=%d", len(lean_paths))
    home = str(user_home())
    result = {
        "HOME": home, "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }
    if lean_paths:
        result["LEAN_PATH"] = os.pathsep.join(map(str, lean_paths))
    logger.debug("proof_elaboration_bridge_io._clean_env exit keys=%r", tuple(result))
    return result


def toolchain_identity(command: list[str]) -> str:
    """Bind exact Lean content/runtime without host-local filesystem metadata."""
    logger.debug("proof_elaboration_bridge_io.toolchain_identity entry")
    try:
        proc = guarded_lean_run(
            command + ["--version"], cwd=TOOLCHAIN_ROOT, env=_clean_env(),
            timeout=30, expected=EXPECTED_LEAN_RUNTIME,
        )
    except subprocess.TimeoutExpired as exc:
        logger.error("proof_elaboration_bridge_io toolchain identity timed out")
        raise ValueError("r10-pinned-lean-version-timeout") from exc
    version = (proc.stdout or proc.stderr).strip()
    match = re.fullmatch(r"Lean \(version ([^,\s)]+)(?:,.*)?\)", version)
    if proc.returncode or match is None or match.group(1) != LEAN_VERSION:
        logger.error("proof_elaboration_bridge_io toolchain mismatch version=%r", version)
        raise ValueError("r10-pinned-lean-version-mismatch")
    stat = Path(command[0]).stat()
    runtime = _runtime_identity()
    result = (
        f"{version}|toolchain={LEAN_TOOLCHAIN}|binary={Path(command[0]).name}|"
        f"sha256={EXPECTED_LEAN_BINARY_SHA256}|{runtime}|size={stat.st_size}"
    )
    logger.debug("proof_elaboration_bridge_io.toolchain_identity exit result=%s", result)
    return result


def snapshot_key(digests: Mapping[str, str], artifact: str, r9: str, toolchain: str) -> str:
    """Bind all live sources and prerequisite evidence into the snapshot key."""
    logger.debug("proof_elaboration_bridge_io.snapshot_key entry")
    result = sha_digest(canonical_json({
        "schema": "veyra-proof-elaboration-snapshot-v1", "sources": dict(digests),
        "artifact": artifact, "r9": r9, "toolchain": toolchain,
    }).encode())
    logger.debug("proof_elaboration_bridge_io.snapshot_key exit result=%s", result)
    return result


def materialize_snapshot(
    sources: Mapping[str, bytes], digests: Mapping[str, str],
    artifact: str, r9: str, toolchain: str,
) -> ElaborationLeanSnapshot:
    """Materialize and reverify the exact ten-stage Lean source snapshot."""
    logger.debug("proof_elaboration_bridge_io.materialize_snapshot entry")
    key = snapshot_key(digests, artifact, r9, toolchain)
    lean_sources = {name: sources[name] for name in SNAPSHOT_NAMES}
    result = materialize_elaboration_snapshot(BUILD_DIR, lean_sources, key)
    logger.debug("proof_elaboration_bridge_io.materialize_snapshot exit root=%s", result.root)
    return result


def _reviewed_closure(
    label: str, root: Path, records: tuple[tuple[Path, int, bytes], ...],
) -> ProtectedClosure:
    logger.debug("proof_elaboration_bridge_io._reviewed_closure entry label=%s", label)
    result = ProtectedClosure(
        label, tuple(path for path, _, _ in records), root, GUARDED_INPUT_DOMAIN,
        records_digest(records, root, GUARDED_INPUT_DOMAIN), exact_parents=True,
    )
    logger.debug("proof_elaboration_bridge_io._reviewed_closure exit files=%d", len(records))
    return result


def _source_closure(
    snapshot: ElaborationLeanSnapshot, sources: Mapping[str, bytes],
) -> ProtectedClosure:
    logger.debug("proof_elaboration_bridge_io._source_closure entry")
    records = tuple(
        (path, len(sources[name]), sha256(sources[name]).digest())
        for name, path in snapshot.paths
    )
    result = _reviewed_closure("snapshot-source", snapshot.root, records)
    logger.debug("proof_elaboration_bridge_io._source_closure exit")
    return result


def _object_closure(
    run_root: Path, objects: tuple[tuple[str, Path], ...],
) -> ProtectedClosure:
    logger.debug("proof_elaboration_bridge_io._object_closure entry files=%d", len(objects))
    records = tuple(
        (path, EXPECTED_LEAN_OBJECTS[name][1], bytes.fromhex(EXPECTED_LEAN_OBJECTS[name][2]))
        for name, path in objects
    )
    result = _reviewed_closure("prior-object", run_root, records)
    logger.debug("proof_elaboration_bridge_io._object_closure exit")
    return result


def _validate_fresh_object(run_root: Path, name: str, path: Path) -> None:
    logger.debug("proof_elaboration_bridge_io._validate_fresh_object entry name=%s", name)
    filename, size, digest = EXPECTED_LEAN_OBJECTS[name]
    try:
        entries = tuple(path.parent.iterdir())
        regular = stat.S_ISREG(path.lstat().st_mode)
    except OSError as exc:
        raise ValueError("r10-lean-object-unreadable") from exc
    if path.name != filename or entries != (path,) or not regular:
        raise ValueError("r10-lean-object-shape-mismatch")
    expected = records_digest(
        ((path, size, bytes.fromhex(digest)),), run_root, GUARDED_INPUT_DOMAIN,
    )
    if paths_digest((path,), run_root, GUARDED_INPUT_DOMAIN) != expected:
        raise ValueError("r10-lean-object-digest-mismatch")
    logger.debug("proof_elaboration_bridge_io._validate_fresh_object exit name=%s", name)


def _default_runtime_absences() -> tuple[Path, ...]:
    logger.debug("proof_elaboration_bridge_io._default_runtime_absences entry")
    library, lean_library = TOOLCHAIN_ROOT / "lib", TOOLCHAIN_ROOT / "lib/lean"
    lean_names = (
        "libInit_shared.so", "libleanshared.so", "libleanshared_1.so",
        "libleanshared_2.so",
    )
    os_names = ("libc.so.6", "libpthread.so.0", "libdl.so.2", "libm.so.6", "librt.so.1")
    result = tuple(lean_library / row[0] for row in EXPECTED_LEAN_OBJECTS.values()) + (
        library / "glibc-hwcaps", lean_library / "glibc-hwcaps",
        *(library / name for name in (*lean_names, *os_names)),
        *(lean_library / name for name in os_names),
    )
    logger.debug("proof_elaboration_bridge_io._default_runtime_absences exit paths=%d", len(result))
    return result


def compile_snapshot(
    command: list[str], snapshot: ElaborationLeanSnapshot,
    sources: Mapping[str, bytes],
) -> tuple[bool, str]:
    """Reverify and compile captured bytes while holding the snapshot lock."""
    logger.debug("proof_elaboration_bridge_io.compile_snapshot entry stages=%d", len(snapshot.paths))
    diagnostics = []
    lean_sources = {name: sources[name] for name in SNAPSHOT_NAMES}
    try:
        with (snapshot.root.parent / ".materialize.lock").open("a+b") as lock:
            exclusive_file_lock(lock.fileno())
            _runtime_identity()
            verify_elaboration_snapshot(snapshot, lean_sources)
            source_closure = _source_closure(snapshot, lean_sources)
            expected_names = tuple(SNAPSHOT_NAMES)[:-1]
            if tuple(EXPECTED_LEAN_OBJECTS) != expected_names:
                raise ValueError("r10-lean-object-manifest-shape-mismatch")
            with TemporaryDirectory(prefix="compile-", dir=snapshot.output_dir) as run:
                run_root = Path(run)
                prior: list[tuple[str, Path]] = []
                for index, (name, source) in enumerate(snapshot.paths, 1):
                    stage_dir = run_root / f"{index:02d}-{source.stem}"
                    stage_dir.mkdir(mode=0o700)
                    output_path = stage_dir / f"{source.stem}.olean"
                    output = [] if index == STAGES else ["-o", str(output_path)]
                    protected = [source_closure]
                    if prior:
                        protected.append(_object_closure(run_root, tuple(prior)))
                    try:
                        proc = guarded_lean_run(
                            command + ["-R", str(snapshot.root)] + output + [str(source)],
                            cwd=snapshot.root,
                            env=_clean_env(tuple(path.parent for _, path in prior)),
                            timeout=120, expected=EXPECTED_LEAN_RUNTIME,
                            protected=tuple(protected),
                            absent_runtime=_default_runtime_absences(),
                        )
                    except subprocess.TimeoutExpired:
                        logger.error("proof_elaboration_bridge_io Lean timeout stage=%s", source.stem)
                        return False, ";".join(diagnostics) + f":{source.stem}:timeout"
                    combined = (proc.stderr or "") + (proc.stdout or "")
                    diagnostics.append(f"{index}/{STAGES}:{source.stem}:rc={proc.returncode}")
                    if proc.returncode or "warning:" in combined.lower():
                        logger.error("proof_elaboration_bridge_io Lean blocked stage=%s", source.stem)
                        return False, ";".join(diagnostics) + ":" + combined.strip()[-600:]
                    if index != STAGES:
                        _validate_fresh_object(run_root, name, output_path)
                        prior.append((name, output_path))
    except (KeyError, OSError, ValueError) as exc:
        logger.error("proof_elaboration_bridge_io snapshot compile blocked=%s", exc)
        return False, str(exc)
    result = ";".join(diagnostics)
    logger.debug("proof_elaboration_bridge_io.compile_snapshot exit diagnostics=%s", result)
    return True, result


def binding_digest(
    tcb_schema: str, theorem_ids: tuple[str, ...], digests: Mapping[str, str],
    snapshot: str, artifact: str, r9: str, toolchain: str,
) -> str:
    """Bind the exact checked report fields into one canonical digest."""
    logger.debug("proof_elaboration_bridge_io.binding_digest entry")
    result = sha_digest(canonical_json({
        "schema": "veyra-proof-elaboration-binding-v1", "tcb_schema": tcb_schema,
        "theorems": list(theorem_ids), "sources": dict(digests), "snapshot": snapshot,
        "artifact": artifact, "r9": r9, "toolchain": toolchain,
    }).encode())
    logger.debug("proof_elaboration_bridge_io.binding_digest exit result=%s", result)
    return result
