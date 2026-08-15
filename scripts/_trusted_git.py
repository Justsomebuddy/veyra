"""Run the narrow Git operations used by repository scripts safely.

This module is private to ``scripts``.  It deliberately resolves only fixed
administrator-controlled Git installation paths instead of consulting PATH,
the registry, or Git-specific environment overrides.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import stat
import subprocess

logger = logging.getLogger(__name__)

_POSIX_CANDIDATES = (
    Path("/usr/bin/git"),
    Path("/usr/local/bin/git"),
    Path("/opt/local/bin/git"),
)
_WINDOWS_CANDIDATES = (
    Path(r"C:\Program Files\Git\bin\git.exe"),
    Path(r"C:\Program Files\Git\cmd\git.exe"),
)
_WINDOWS_REPARSE_POINT = 0x400
_IS_WINDOWS = os.name == "nt"


@dataclass(frozen=True)
class _PathIdentity:
    """Security-relevant lstat identity for one executable or ancestor."""

    device: int
    inode: int
    mode: int
    uid: int | None
    gid: int | None
    size: int
    modified_ns: int
    changed_ns: int
    file_attributes: int


def _candidate_paths() -> tuple[Path, ...]:
    """Return the fixed candidate set for the active platform."""
    logger.debug("trusted_git candidate selection entry")
    result = _WINDOWS_CANDIDATES if _IS_WINDOWS else _POSIX_CANDIDATES
    logger.debug("trusted_git candidate selection exit count=%d", len(result))
    return result


def _path_chain(executable: Path) -> tuple[Path, ...]:
    """Return an executable followed by every filesystem ancestor."""
    logger.debug("trusted_git path chain entry")
    result = (executable, *executable.parents)
    logger.debug("trusted_git path chain exit count=%d", len(result))
    return result


def _identity(info: os.stat_result) -> _PathIdentity:
    """Detach the security-relevant portion of one lstat result."""
    logger.debug("trusted_git identity capture entry")
    result = _PathIdentity(
        device=info.st_dev,
        inode=info.st_ino,
        mode=info.st_mode,
        uid=getattr(info, "st_uid", None),
        gid=getattr(info, "st_gid", None),
        size=info.st_size,
        modified_ns=info.st_mtime_ns,
        changed_ns=info.st_ctime_ns,
        file_attributes=getattr(info, "st_file_attributes", 0),
    )
    logger.debug("trusted_git identity capture exit")
    return result


def _snapshot(executable: Path) -> tuple[_PathIdentity, ...]:
    """Validate and snapshot one executable plus its trust ancestors."""
    logger.debug("trusted_git executable validation entry")
    chain = _path_chain(executable)
    identities: list[_PathIdentity] = []
    for index, path in enumerate(chain):
        info = path.lstat()
        identity = _identity(info)
        if stat.S_ISLNK(identity.mode):
            logger.error("trusted_git executable validation rejected reason=symlink")
            raise RuntimeError("trusted-git-untrusted")
        if _IS_WINDOWS:
            if identity.file_attributes & _WINDOWS_REPARSE_POINT:
                logger.error("trusted_git executable validation rejected reason=reparse")
                raise RuntimeError("trusted-git-untrusted")
        elif identity.uid != 0 or identity.mode & 0o022 or (index == 0 and not identity.mode & 0o111):
            logger.error("trusted_git executable validation rejected reason=metadata")
            raise RuntimeError("trusted-git-untrusted")
        if index == 0 and not stat.S_ISREG(identity.mode):
            logger.error("trusted_git executable validation rejected reason=type")
            raise RuntimeError("trusted-git-untrusted")
        if index > 0 and not stat.S_ISDIR(identity.mode):
            logger.error("trusted_git executable validation rejected reason=ancestor-type")
            raise RuntimeError("trusted-git-untrusted")
        identities.append(identity)
    result = tuple(identities)
    logger.debug("trusted_git executable validation exit count=%d", len(result))
    return result


def _resolve_executable() -> tuple[Path, tuple[_PathIdentity, ...]]:
    """Return the first admitted fixed-path Git executable and its snapshot."""
    logger.debug("trusted_git resolver entry")
    for candidate in _candidate_paths():
        try:
            snapshot = _snapshot(candidate)
        except (OSError, RuntimeError):
            continue
        logger.debug("trusted_git resolver exit admitted=true")
        return candidate, snapshot
    logger.error("trusted_git resolver failed reason=no-admitted-candidate")
    raise RuntimeError("trusted-git-unavailable")


def _environment() -> dict[str, str]:
    """Preserve user config locations while removing executable-control input."""
    logger.debug("trusted_git environment construction entry")
    result = {
        key: value
        for key, value in os.environ.items()
        if (normalized := key.upper()) != "PATH" and not normalized.startswith(("GIT_", "LD_", "DYLD_"))
    }
    result["GIT_OPTIONAL_LOCKS"] = "0"
    result["GIT_TERMINAL_PROMPT"] = "0"
    logger.debug("trusted_git environment construction exit entries=%d", len(result))
    return result


def _run(root: Path, arguments: tuple[str, ...], timeout: int) -> subprocess.CompletedProcess[bytes]:
    """Run one fixed Git operation and reject executable identity drift."""
    logger.debug("trusted_git runner entry argc=%d timeout=%d", len(arguments), timeout)
    try:
        repository = root.resolve(strict=True)
    except OSError:
        logger.error("trusted_git runner failed reason=repository-unavailable")
        raise RuntimeError("trusted-git-repository-unavailable") from None
    executable, before = _resolve_executable()
    try:
        immediately_before = _snapshot(executable)
    except (OSError, RuntimeError):
        logger.error("trusted_git runner failed reason=identity-drift")
        raise RuntimeError("trusted-git-identity-drift") from None
    if before != immediately_before:
        logger.error("trusted_git runner failed reason=identity-drift")
        raise RuntimeError("trusted-git-identity-drift")
    command = (
        str(executable),
        "--no-pager",
        "-C",
        os.fspath(repository),
        "-c",
        "core.fsmonitor=false",
        *arguments,
    )
    process: subprocess.CompletedProcess[bytes] | None = None
    execution_failed = False
    try:
        process = subprocess.run(
            command,
            cwd=executable.parent,
            env=_environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        execution_failed = True
    try:
        after = _snapshot(executable)
    except (OSError, RuntimeError):
        after = None
    if after is None or before != after:
        logger.error("trusted_git runner failed reason=identity-drift")
        raise RuntimeError("trusted-git-identity-drift") from None
    if execution_failed or process is None:
        logger.error("trusted_git runner failed reason=execution")
        raise RuntimeError("trusted-git-execution-failed") from None
    logger.debug("trusted_git runner exit rc=%d bytes=%d", process.returncode, len(process.stdout))
    return process


def git_inventory(root: Path) -> tuple[bytes, ...]:
    """Return tracked and non-ignored untracked paths as exact Git bytes."""
    logger.debug("trusted_git inventory entry")
    process = _run(
        Path(root),
        ("ls-files", "-z", "--cached", "--others", "--exclude-standard"),
        30,
    )
    if process.returncode:
        logger.error("trusted_git inventory failed reason=git-status")
        raise RuntimeError("trusted-git-inventory-failed")
    result = tuple(item for item in process.stdout.split(b"\0") if item)
    logger.debug("trusted_git inventory exit count=%d", len(result))
    return result


def git_check_ignore(root: Path, relative: str) -> bool:
    """Return Git's ignore decision for one repository-relative identity."""
    logger.debug("trusted_git ignore check entry")
    process = _run(Path(root), ("check-ignore", "-q", "--", relative), 10)
    if process.returncode == 0:
        logger.debug("trusted_git ignore check exit ignored=true")
        return True
    if process.returncode == 1:
        logger.debug("trusted_git ignore check exit ignored=false")
        return False
    logger.error("trusted_git ignore check failed reason=git-status")
    raise RuntimeError("trusted-git-ignore-failed")


__all__ = ("git_check_ignore", "git_inventory")
