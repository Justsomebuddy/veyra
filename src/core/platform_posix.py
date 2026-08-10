"""Narrow lazy adapters for optional POSIX primitives."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from src.platform_capabilities import Capability, require_capability

logger = logging.getLogger(__name__)


def exclusive_file_lock(file_descriptor: int) -> None:
    """Acquire the reviewed blocking exclusive lock on a file descriptor."""
    logger.debug("platform_posix.exclusive_file_lock entry fd=%d", file_descriptor)
    require_capability(Capability.POSIX_FILE_LOCKS)
    import fcntl

    fcntl.flock(file_descriptor, fcntl.LOCK_EX)
    logger.debug("platform_posix.exclusive_file_lock exit fd=%d", file_descriptor)


def user_home() -> Path:
    """Return passwd-backed home on POSIX, with import-only fallback elsewhere."""
    logger.debug("platform_posix.user_home entry")
    try:
        import pwd
    except ImportError:
        result = Path.home()
        source = "portable-fallback"
    else:
        result = Path(pwd.getpwuid(os.getuid()).pw_dir)
        source = "account-database"
    logger.debug("platform_posix.user_home exit source=%s path=%s", source, result)
    return result


def apply_process_limits(pid: int, address_space: int) -> tuple[tuple[int, int], tuple[int, int]]:
    """Apply and read back the Linux R14 address-space/core limits."""
    logger.debug("platform_posix.apply_process_limits entry pid=%d as=%d", pid, address_space)
    require_capability(Capability.LINUX_HARDENING)
    import resource

    resource.prlimit(pid, resource.RLIMIT_AS, (address_space, address_space))
    resource.prlimit(pid, resource.RLIMIT_CORE, (0, 0))
    result = resource.prlimit(pid, resource.RLIMIT_AS), resource.prlimit(pid, resource.RLIMIT_CORE)
    logger.debug("platform_posix.apply_process_limits exit pid=%d result=%r", pid, result)
    return result
