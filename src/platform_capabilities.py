"""Typed host-capability reporting for portable and hardened Veyra lanes."""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
from enum import Enum
from importlib import import_module
from importlib.util import find_spec
import logging
import platform as host_platform
from pathlib import Path
import shutil
import subprocess
import sys

logger = logging.getLogger(__name__)


class Capability(str, Enum):
    """Capabilities used to select explicit verification lanes."""

    PORTABLE_PYTHON = "portable-python"
    POSIX_FILE_LOCKS = "posix-file-locks"
    LINUX_HARDENING = "linux-x86_64-hardening"
    LEAN_TOOLCHAIN_CANDIDATE = "lean-toolchain-candidate"
    SAGE_RUNTIME = "sage-runtime"
    RUST_1_95 = "rust-1.95-toolchain"


@dataclass(frozen=True, slots=True)
class CapabilityStatus:
    """One explicit available/unavailable host capability result."""

    capability: Capability
    available: bool
    detail: str


class CapabilityUnavailableError(RuntimeError):
    """A requested platform/toolchain capability is genuinely unavailable."""


def _module_available(name: str) -> bool:
    """Return whether an importable module has a discoverable specification."""
    logger.debug("capabilities._module_available entry name=%s", name)
    try:
        result = find_spec(name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        result = False
    logger.debug("capabilities._module_available exit name=%s available=%s", name, result)
    return result


def _inotify_available() -> bool:
    """Probe the two libc symbols required by the hardened runtime guard."""
    logger.debug("capabilities._inotify_available entry")
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        result = hasattr(libc, "inotify_init1") and hasattr(libc, "inotify_add_watch")
    except OSError:
        result = False
    logger.debug("capabilities._inotify_available exit available=%s", result)
    return result


def _command_path(name: str) -> str | None:
    """Resolve a command in PATH or the conventional per-user rustup directory."""
    logger.debug("capabilities._command_path entry name=%s", name)
    discovered = shutil.which(name)
    fallback = shutil.which(name, path=str(Path.home() / ".cargo" / "bin"))
    result = discovered or fallback
    logger.debug("capabilities._command_path exit name=%s available=%s", name, result is not None)
    return result


def _posix_lock_available() -> bool:
    """Probe the real constants and call surface used by the lock adapter."""
    logger.debug("capabilities._posix_lock_available entry")
    if not _module_available("fcntl"):
        return False
    module = import_module("fcntl")
    result = callable(getattr(module, "flock", None)) and hasattr(module, "LOCK_EX")
    logger.debug("capabilities._posix_lock_available exit available=%s", result)
    return result


def _linux_process_primitives_available() -> bool:
    """Probe the exact account and resource APIs used by hardened workers."""
    logger.debug("capabilities._linux_process_primitives_available entry")
    if not all(_module_available(name) for name in ("pwd", "resource")):
        return False
    pwd = import_module("pwd")
    resource = import_module("resource")
    result = (
        callable(getattr(pwd, "getpwuid", None))
        and callable(getattr(resource, "prlimit", None))
        and hasattr(resource, "RLIMIT_AS")
        and hasattr(resource, "RLIMIT_CORE")
    )
    logger.debug("capabilities._linux_process_primitives_available exit available=%s", result)
    return result


def _rust_1_95_available() -> bool:
    """Require rustup-selected Cargo and rustc 1.95 instead of any compiler."""
    logger.debug("capabilities._rust_1_95_available entry")
    cargo_path, rustc_path = _command_path("cargo"), _command_path("rustc")
    if cargo_path is None or rustc_path is None:
        return False
    try:
        cargo = subprocess.run(
            [cargo_path, "+1.95.0", "--version"],
            capture_output=True,
            check=False,
            text=True,
            timeout=15,
        )
        rustc = subprocess.run(
            [rustc_path, "+1.95.0", "--version"],
            capture_output=True,
            check=False,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    result = cargo.returncode == 0 and cargo.stdout.startswith("cargo 1.95.0 ") and rustc.returncode == 0 and rustc.stdout.startswith("rustc 1.95.0 ")
    logger.debug("capabilities._rust_1_95_available exit available=%s", result)
    return result


def capability_status(
    capability: Capability,
    *,
    platform_name: str | None = None,
    machine: str | None = None,
    version: tuple[int, int, int] | None = None,
) -> CapabilityStatus:
    """Evaluate one capability without converting unexpected failures to skips."""
    logger.debug("capabilities.capability_status entry capability=%s", capability.value)
    selected_platform = sys.platform if platform_name is None else platform_name
    selected_machine = host_platform.machine() if machine is None else machine
    selected_version = sys.version_info[:3] if version is None else version
    is_cpython_311 = sys.implementation.name == "cpython" and selected_version[:2] == (3, 11)
    is_linux_x86 = selected_platform.startswith("linux") and selected_machine.lower() in {"amd64", "x86_64"}

    if capability is Capability.PORTABLE_PYTHON:
        available = is_cpython_311
        detail = "cpython-3.11" if available else "requires-cpython-3.11"
    elif capability is Capability.POSIX_FILE_LOCKS:
        available = _posix_lock_available()
        detail = "fcntl-flock-available" if available else "fcntl-flock-unavailable"
    elif capability is Capability.LINUX_HARDENING:
        primitives = _posix_lock_available() and _linux_process_primitives_available()
        available = is_linux_x86 and primitives and _inotify_available()
        detail = "linux-x86_64-posix-inotify" if available else "requires-linux-x86_64-posix-inotify"
    elif capability is Capability.LEAN_TOOLCHAIN_CANDIDATE:
        hardened = capability_status(
            Capability.LINUX_HARDENING,
            platform_name=selected_platform,
            machine=selected_machine,
            version=selected_version,
        ).available
        available = hardened and selected_version == (3, 11, 14) and shutil.which("elan") is not None
        detail = "lean-candidate-present-full-attestation-required" if available else "requires-linux-x86_64-cpython-3.11.14-elan"
    elif capability is Capability.SAGE_RUNTIME:
        available = _module_available("sage.all") and import_module("sage.all") is not None
        detail = "sage-imported" if available else "sage-unavailable"
    elif capability is Capability.RUST_1_95:
        available = _rust_1_95_available()
        detail = "cargo-rustc-1.95" if available else "rust-1.95-unavailable"
    else:  # pragma: no cover - Enum makes this unreachable for typed callers.
        raise ValueError("unknown-platform-capability")
    result = CapabilityStatus(capability, available, detail)
    logger.debug("capabilities.capability_status exit result=%r", result)
    return result


def require_capability(capability: Capability) -> CapabilityStatus:
    """Return an available capability or raise its narrow typed boundary."""
    logger.debug("capabilities.require_capability entry capability=%s", capability.value)
    result = capability_status(capability)
    if not result.available:
        logger.error("capabilities unavailable capability=%s detail=%s", capability.value, result.detail)
        raise CapabilityUnavailableError(f"{capability.value}:{result.detail}")
    logger.debug("capabilities.require_capability exit capability=%s", capability.value)
    return result
