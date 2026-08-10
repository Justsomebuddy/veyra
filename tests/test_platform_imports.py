"""Cross-platform import and explicit capability-boundary checks."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import subprocess
import sys

import pytest

from src.core.platform_posix import exclusive_file_lock, user_home
from src.platform_capabilities import Capability, capability_status

logger = logging.getLogger(__name__)


def _run(script: str) -> subprocess.CompletedProcess[str]:
    """Run an isolated interpreter with a bounded wait and retained diagnostics."""
    logger.debug("platform import subprocess entry bytes=%d", len(script))
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        text=True,
        timeout=60,
    )
    logger.debug("platform import subprocess exit rc=%d", result.returncode)
    return result


def test_capability_contract_rejects_unsupported_platform_shapes() -> None:
    """Linux hardening is never inferred for Windows, macOS, or Linux ARM."""
    logger.debug("test unsupported platform capability entry")
    for platform_name, machine in (("win32", "AMD64"), ("darwin", "arm64"), ("linux", "aarch64")):
        status = capability_status(
            Capability.LINUX_HARDENING,
            platform_name=platform_name,
            machine=machine,
        )
        assert not status.available
        assert status.detail == "requires-linux-x86_64-posix-inotify"
    logger.debug("test unsupported platform capability exit")


def test_portable_python_capability_is_bounded_to_cpython_311() -> None:
    """Portable packaging may span 3.11 patches but not Python minor versions."""
    logger.debug("test portable Python capability entry")
    assert capability_status(Capability.PORTABLE_PYTHON, version=(3, 11, 9)).available
    assert not capability_status(Capability.PORTABLE_PYTHON, version=(3, 12, 0)).available
    logger.debug("test portable Python capability exit")


def test_public_import_needs_no_posix_modules_and_hardening_fails_closed() -> None:
    """A Windows-shaped import neither installs shims nor enables Linux proof guards."""
    logger.debug("test Windows-shaped public import entry")
    script = "\n".join(
        (
            "import sys",
            "from importlib.abc import MetaPathFinder",
            "class BlockPosix(MetaPathFinder):",
            "    def find_spec(self, fullname, path=None, target=None):",
            "        if fullname in {'fcntl', 'pwd', 'resource'}:",
            "            raise ModuleNotFoundError(fullname)",
            "        return None",
            "for name in ('fcntl', 'pwd', 'resource'): sys.modules.pop(name, None)",
            "sys.meta_path.insert(0, BlockPosix())",
            "import src.core",
            "import veyra_sage.all",
            "from src.core.platform_posix import apply_process_limits",
            "from src.platform_capabilities import CapabilityUnavailableError",
            "try:",
            "    apply_process_limits(1, 1024)",
            "except CapabilityUnavailableError as exc:",
            "    assert 'linux-x86_64-hardening' in str(exc)",
            "else:",
            "    raise AssertionError('Linux hardening did not fail closed')",
            "assert not {'fcntl', 'pwd', 'resource'}.intersection(sys.modules)",
            "print('portable-import-ok')",
        )
    )
    result = _run(script)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "portable-import-ok"
    logger.debug("test Windows-shaped public import exit")


@pytest.mark.requires_linux_hardening
def test_complete_lane_has_native_linux_hardening() -> None:
    """The unfiltered complete lane requires the documented hardened host."""
    logger.debug("test native Linux hardening capability entry")
    assert capability_status(Capability.LINUX_HARDENING).available
    logger.debug("test native Linux hardening capability exit")


@pytest.mark.requires_lean_candidate
def test_lean_candidate_is_named_as_a_prerequisite_not_attestation() -> None:
    """Candidate discovery never claims full content-bound Lean attestation."""
    logger.debug("test Lean candidate capability entry")
    status = capability_status(Capability.LEAN_TOOLCHAIN_CANDIDATE)
    assert status.available
    assert status.detail == "lean-candidate-present-full-attestation-required"
    logger.debug("test Lean candidate capability exit")


@pytest.mark.requires_real_sage
def test_complete_lane_has_real_sage() -> None:
    """The complete lane must not silently substitute the pure-Python facade."""
    logger.debug("test real Sage capability entry")
    assert capability_status(Capability.SAGE_RUNTIME).available
    logger.debug("test real Sage capability exit")


@pytest.mark.requires_native_rust
def test_complete_lane_has_native_rust() -> None:
    """The complete lane requires the reproduced Rust 1.95 toolchain."""
    logger.debug("test native Rust capability entry")
    assert capability_status(Capability.RUST_1_95).available
    logger.debug("test native Rust capability exit")


@pytest.mark.requires_posix_file_locks
def test_native_posix_lock_capability_executes(tmp_path: Path) -> None:
    """The complete host lane exercises the real lock adapter, not a fake module."""
    logger.debug("test native POSIX lock entry")
    path = tmp_path / "lock"
    with path.open("w", encoding="utf-8") as stream:
        exclusive_file_lock(stream.fileno())
    logger.debug("test native POSIX lock exit")


@pytest.mark.requires_linux_hardening
def test_hardened_user_home_ignores_environment_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Lean/runtime roots use the account database, never attacker-controlled HOME."""
    logger.debug("test hardened user home entry")
    import pwd

    monkeypatch.setenv("HOME", str(tmp_path))
    assert user_home() == Path(pwd.getpwuid(os.getuid()).pw_dir)
    logger.debug("test hardened user home exit")
