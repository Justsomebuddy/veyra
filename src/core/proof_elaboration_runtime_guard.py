"""Linux inotify plus pre/post Merkle guard for R10 Lean subprocesses."""
from __future__ import annotations

import ctypes
from dataclasses import dataclass
import logging
import os
from pathlib import Path
import stat
import struct
import subprocess
from typing import Mapping

from src.platform_capabilities import Capability, require_capability

from .proof_elaboration_toolchain import (
    RUNTIME_DOMAIN, TOOLCHAIN_ROOT, paths_digest, runtime_closure_paths,
)

logger = logging.getLogger(__name__)
_IN_NONBLOCK = getattr(os, "O_NONBLOCK", 0)
_IN_CLOEXEC = getattr(os, "O_CLOEXEC", 0)
_EVENT = struct.Struct("iIII")
_FILE_MASK = (
    0x00000002  # IN_MODIFY
    | 0x00000004  # IN_ATTRIB
    | 0x00000008  # IN_CLOSE_WRITE
    | 0x00000400  # IN_DELETE_SELF
    | 0x00000800  # IN_MOVE_SELF
)
_DIRECTORY_MASK = (
    _FILE_MASK
    | 0x00000040  # IN_MOVED_FROM
    | 0x00000080  # IN_MOVED_TO
    | 0x00000100  # IN_CREATE
    | 0x00000200  # IN_DELETE
)
_ANCESTOR_MASK = 0x00000004 | 0x00000400 | 0x00000800
_FATAL_MASK = _DIRECTORY_MASK | 0x00002000 | 0x00004000 | 0x00008000


@dataclass(frozen=True)
class ProtectedClosure:
    """One path-root-domain closure and its independently reviewed digest."""

    label: str
    paths: tuple[Path, ...]
    root: Path
    domain: bytes
    expected: tuple[str, int, int]
    exact_parents: bool = False
    absent_paths: tuple[Path, ...] = ()


@dataclass(frozen=True)
class RuntimeWatch:
    """One open inotify queue and its exact path watch map."""

    fd: int
    watched: tuple[tuple[int, Path, bool], ...]


def _inotify_libc() -> ctypes.CDLL:
    """Load and type the Linux inotify functions only when the lane is used."""
    logger.debug("proof_elaboration_runtime_guard._inotify_libc entry")
    require_capability(Capability.LINUX_HARDENING)
    libc = ctypes.CDLL(None, use_errno=True)
    libc.inotify_init1.argtypes = [ctypes.c_int]
    libc.inotify_init1.restype = ctypes.c_int
    libc.inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
    libc.inotify_add_watch.restype = ctypes.c_int
    logger.debug("proof_elaboration_runtime_guard._inotify_libc exit")
    return libc


def _watch_specs(closures: tuple[ProtectedClosure, ...]) -> dict[Path, tuple[int, bool]]:
    logger.debug("proof_elaboration_runtime_guard._watch_specs entry closures=%d", len(closures))
    specs: dict[Path, tuple[int, bool]] = {}
    for closure in closures:
        if not closure.label or not closure.paths or not closure.root.is_absolute():
            raise ValueError("r10-protected-closure-invalid")
        for path in closure.paths:
            path.relative_to(closure.root)
            specs[path] = (_FILE_MASK, False)
            parent = path.parent
            mask, _ = specs.get(parent, (0, True))
            specs[parent] = (mask | _DIRECTORY_MASK, True)
            ancestor = parent.parent
            while True:
                mask, _ = specs.get(ancestor, (0, True))
                specs[ancestor] = (mask | _ANCESTOR_MASK, True)
                if ancestor == ancestor.parent:
                    break
                ancestor = ancestor.parent
        for path in closure.absent_paths:
            path.relative_to(closure.root)
            parent = path.parent
            mask, _ = specs.get(parent, (0, True))
            specs[parent] = (mask | _DIRECTORY_MASK, True)
            ancestor = parent.parent
            while True:
                mask, _ = specs.get(ancestor, (0, True))
                specs[ancestor] = (mask | _ANCESTOR_MASK, True)
                if ancestor == ancestor.parent:
                    break
                ancestor = ancestor.parent
    logger.debug("proof_elaboration_runtime_guard._watch_specs exit watches=%d", len(specs))
    return specs


def _open_watch(closures: tuple[ProtectedClosure, ...]) -> RuntimeWatch:
    logger.debug("proof_elaboration_runtime_guard._open_watch entry closures=%d", len(closures))
    libc = _inotify_libc()
    fd = libc.inotify_init1(_IN_NONBLOCK | _IN_CLOEXEC)
    if fd < 0:
        error = ctypes.get_errno()
        logger.error("proof_elaboration_runtime_guard inotify_init1 errno=%d", error)
        raise ValueError("r10-runtime-watch-init-failed")
    watched: list[tuple[int, Path, bool]] = []
    try:
        for path, (mask, is_directory) in sorted(_watch_specs(closures).items(), key=lambda row: str(row[0])):
            wd = libc.inotify_add_watch(fd, os.fsencode(path), mask)
            if wd < 0:
                error = ctypes.get_errno()
                logger.error("proof_elaboration_runtime_guard add_watch path=%s errno=%d", path, error)
                raise ValueError("r10-runtime-watch-add-failed")
            watched.append((wd, path, is_directory))
    except BaseException:
        os.close(fd)
        raise
    result = RuntimeWatch(fd, tuple(watched))
    logger.debug("proof_elaboration_runtime_guard._open_watch exit watches=%d", len(watched))
    return result


def _verify_watched_directories(watch: RuntimeWatch) -> None:
    logger.debug("proof_elaboration_runtime_guard._verify_watched_directories entry")
    for _, path, is_directory in watch.watched:
        if is_directory:
            try:
                metadata = path.lstat()
            except OSError as exc:
                raise ValueError("r10-runtime-watch-directory-remapped") from exc
            if not stat.S_ISDIR(metadata.st_mode):
                raise ValueError("r10-runtime-watch-directory-remapped")
    logger.debug("proof_elaboration_runtime_guard._verify_watched_directories exit")


def _verify_exact_parent_shapes(closures: tuple[ProtectedClosure, ...]) -> None:
    logger.debug("proof_elaboration_runtime_guard._verify_exact_parent_shapes entry")
    for closure in closures:
        if not closure.exact_parents:
            continue
        parents: dict[Path, set[Path]] = {}
        for path in closure.paths:
            parents.setdefault(path.parent, set()).add(path)
        try:
            valid = all(set(parent.iterdir()) == expected for parent, expected in parents.items())
        except OSError as exc:
            raise ValueError(f"r10-{closure.label}-parent-shape-mismatch") from exc
        if not valid:
            raise ValueError(f"r10-{closure.label}-parent-shape-mismatch")
    logger.debug("proof_elaboration_runtime_guard._verify_exact_parent_shapes exit")


def _verify_required_absence(closures: tuple[ProtectedClosure, ...]) -> None:
    logger.debug("proof_elaboration_runtime_guard._verify_required_absence entry")
    for closure in closures:
        if any(os.path.lexists(path) for path in closure.absent_paths):
            raise ValueError(f"r10-{closure.label}-forbidden-path-present")
    logger.debug("proof_elaboration_runtime_guard._verify_required_absence exit")


def _drain_events(watch: RuntimeWatch) -> tuple[str, ...]:
    logger.debug("proof_elaboration_runtime_guard._drain_events entry fd=%d", watch.fd)
    watched = {wd: path for wd, path, _ in watch.watched}
    events: list[str] = []
    while True:
        try:
            data = os.read(watch.fd, 1024 * 1024)
        except BlockingIOError:
            break
        except OSError as exc:
            logger.error("proof_elaboration_runtime_guard watch read failed=%s", exc)
            raise ValueError("r10-runtime-watch-read-failed") from exc
        if not data:
            break
        offset = 0
        while offset + _EVENT.size <= len(data):
            wd, mask, _cookie, name_len = _EVENT.unpack_from(data, offset)
            offset += _EVENT.size
            raw_name = data[offset:offset + name_len]
            offset += name_len
            name = os.fsdecode(raw_name.split(b"\0", 1)[0])
            parent = watched.get(wd, Path("<queue>"))
            if mask & _FATAL_MASK:
                events.append(f"{parent / name}:0x{mask:08x}")
        if offset != len(data):
            logger.error("proof_elaboration_runtime_guard malformed event queue")
            raise ValueError("r10-runtime-watch-event-malformed")
    result = tuple(events)
    logger.debug("proof_elaboration_runtime_guard._drain_events exit events=%d", len(result))
    return result


def guarded_closures_run(
    command: list[str], *, cwd: Path, env: Mapping[str, str], timeout: int,
    closures: tuple[ProtectedClosure, ...],
) -> subprocess.CompletedProcess[str]:
    """Watch every closure before pre-hash; reject event or digest drift."""
    logger.debug("guarded_closures_run entry command=%r closures=%d", command, len(closures))
    watch = _open_watch(closures)
    result: subprocess.CompletedProcess[str] | None = None
    operation_error: BaseException | None = None
    integrity_error: ValueError | None = None
    try:
        _verify_watched_directories(watch)
        _verify_exact_parent_shapes(closures)
        _verify_required_absence(closures)
        for closure in closures:
            before = paths_digest(closure.paths, closure.root, closure.domain)
            if before != closure.expected:
                raise ValueError(f"r10-{closure.label}-pre-digest-mismatch")
        try:
            result = subprocess.run(
                command, cwd=cwd, env=dict(env), text=True, capture_output=True,
                check=False, timeout=timeout,
            )
        except BaseException as exc:
            operation_error = exc
        after = tuple(
            (closure.label, paths_digest(closure.paths, closure.root, closure.domain))
            for closure in closures
        )
        events = _drain_events(watch)
        drift = tuple(
            (label, actual) for (label, actual), closure in zip(after, closures)
            if actual != closure.expected
        )
        if drift or events:
            logger.error(
                "guarded_closures_run integrity drift after=%r events=%r", drift, events[:8],
            )
            integrity_error = ValueError("r10-runtime-integrity-drift")
    finally:
        os.close(watch.fd)
    if integrity_error is not None:
        raise integrity_error
    if operation_error is not None:
        raise operation_error
    if result is None:
        raise ValueError("r10-runtime-guard-missing-result")
    logger.debug("guarded_closures_run exit rc=%d", result.returncode)
    return result


def guarded_subprocess_run(
    command: list[str], *, cwd: Path, env: Mapping[str, str], timeout: int,
    paths: tuple[Path, ...], root: Path, expected: tuple[str, int, int],
) -> subprocess.CompletedProcess[str]:
    """Compatibility wrapper for one runtime-domain protected closure."""
    logger.debug("guarded_subprocess_run entry command=%r files=%d", command, len(paths))
    result = guarded_closures_run(
        command, cwd=cwd, env=env, timeout=timeout,
        closures=(ProtectedClosure("runtime", paths, root, RUNTIME_DOMAIN, expected),),
    )
    logger.debug("guarded_subprocess_run exit rc=%d", result.returncode)
    return result


def guarded_lean_run(
    command: list[str], *, cwd: Path, env: Mapping[str, str], timeout: int,
    expected: tuple[str, int, int],
    protected: tuple[ProtectedClosure, ...] = (),
    absent_runtime: tuple[Path, ...] = (),
) -> subprocess.CompletedProcess[str]:
    """Guard the freshly enumerated full Lean runtime closure for one stage."""
    logger.debug("guarded_lean_run entry")
    runtime = ProtectedClosure(
        "runtime", runtime_closure_paths(), TOOLCHAIN_ROOT, RUNTIME_DOMAIN, expected,
        absent_paths=absent_runtime,
    )
    result = guarded_closures_run(
        command, cwd=cwd, env=env, timeout=timeout, closures=(runtime, *protected),
    )
    logger.debug("guarded_lean_run exit rc=%d", result.returncode)
    return result
