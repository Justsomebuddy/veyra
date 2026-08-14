"""Cross-platform import and explicit capability-boundary checks."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import subprocess
import sys

import pytest

import src.platform_capabilities as capabilities_module
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


def test_theorem_toolchain_is_narrower_than_portable_python(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production promotion requires the exact runtime and direct Lean binary."""
    logger.debug("test theorem toolchain boundary entry")
    monkeypatch.setattr(capabilities_module, "_posix_lock_available", lambda: True)
    monkeypatch.setattr(
        capabilities_module,
        "_linux_process_primitives_available",
        lambda: True,
    )
    monkeypatch.setattr(capabilities_module, "_inotify_available", lambda: True)
    monkeypatch.setattr(
        capabilities_module,
        "_exact_direct_lean_available",
        lambda: True,
    )
    monkeypatch.setattr(
        capabilities_module,
        "_exact_elan_lean_available",
        lambda: True,
    )
    exact = capability_status(
        Capability.THEOREM_PROOF_TOOLCHAIN,
        platform_name="linux",
        machine="x86_64",
        version=(3, 11, 14),
    )
    portable_patch = capability_status(
        Capability.THEOREM_PROOF_TOOLCHAIN,
        platform_name="linux",
        machine="x86_64",
        version=(3, 11, 9),
    )
    assert exact.available
    assert "direct-lean-4.30.0-rc2" in exact.detail
    assert "r9-elan-route-present" in exact.detail
    assert capability_status(Capability.PORTABLE_PYTHON, version=(3, 11, 9)).available
    assert not portable_patch.available
    logger.debug("test theorem toolchain boundary exit")


def test_theorem_toolchain_requires_direct_and_r9_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Neither the manager nor direct binary alone enables theorem promotion."""
    logger.debug("test theorem direct Lean requirement entry")
    monkeypatch.setattr(capabilities_module, "_posix_lock_available", lambda: True)
    monkeypatch.setattr(
        capabilities_module,
        "_linux_process_primitives_available",
        lambda: True,
    )
    monkeypatch.setattr(capabilities_module, "_inotify_available", lambda: True)
    monkeypatch.setattr(capabilities_module, "_exact_direct_lean_available", lambda: False)
    monkeypatch.setattr(capabilities_module, "_exact_elan_lean_available", lambda: True)
    status = capability_status(
        Capability.THEOREM_PROOF_TOOLCHAIN,
        platform_name="linux",
        machine="x86_64",
        version=(3, 11, 14),
    )
    assert not status.available
    assert "direct-lean-4.30.0-rc2" in status.detail
    monkeypatch.setattr(capabilities_module, "_exact_direct_lean_available", lambda: True)
    monkeypatch.setattr(capabilities_module, "_exact_elan_lean_available", lambda: False)
    r9_missing = capability_status(
        Capability.THEOREM_PROOF_TOOLCHAIN,
        platform_name="linux",
        machine="x86_64",
        version=(3, 11, 14),
    )
    assert not r9_missing.available
    assert "r9-elan-route" in r9_missing.detail
    logger.debug("test theorem direct Lean requirement exit")


@pytest.mark.parametrize(
    ("reported", "expected"),
    (
        (
            "Lean (version 4.30.0-rc2, x86_64-unknown-linux-gnu, "
            "commit 3dc1a088, Release)",
            True,
        ),
        ("Lean (version 4.30.0-rc20, x86_64-unknown-linux-gnu)", False),
        ("fake version 4.30.0-rc2", False),
    ),
)
def test_exact_lean_probe_rejects_version_substrings(
    monkeypatch: pytest.MonkeyPatch,
    reported: str,
    expected: bool,
) -> None:
    """The prerequisite probe parses one exact Lean version record."""
    logger.debug("test exact Lean version probe entry expected=%s", expected)

    def completed(*_args, **_kwargs) -> subprocess.CompletedProcess[str]:
        logger.debug("test exact Lean version fake subprocess entry")
        result = subprocess.CompletedProcess([], 0, reported, "")
        logger.debug("test exact Lean version fake subprocess exit")
        return result

    monkeypatch.setattr(capabilities_module.subprocess, "run", completed)
    assert capabilities_module._lean_version_matches(["/fake/lean"], "test") is expected
    logger.debug("test exact Lean version probe exit")


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


def test_public_import_does_not_build_bytecode_bound_theorem_registry() -> None:
    """Importing the portable barrel leaves executable contract validation lazy."""
    logger.debug("test lazy theorem registry import entry")
    script = "\n".join(
        (
            "import importlib",
            "import src.core",
            "contracts = importlib.import_module('src.core.layer_theorem_contracts')",
            "assert contracts._THEOREM_CONTRACTS is None",
            "assert src.core.TheoremContractCapabilityBlocked is not None",
            "print('lazy-theorem-registry-ok')",
        )
    )
    result = _run(script)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "lazy-theorem-registry-ok"
    logger.debug("test lazy theorem registry import exit")


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
    assert capabilities_module._pinned_lean_binary() == (
        user_home()
        / ".elan/toolchains/leanprover--lean4---v4.30.0-rc2/bin/lean"
    )
    logger.debug("test hardened user home exit")
