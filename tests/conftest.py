"""Shared anchors and environment gating for the test suite.

Tests address repository artifacts through these fixtures rather than through
the process working directory, so the suite behaves identically whether it is
started from the repository root, a subdirectory, or a build sandbox.

Two markers gate work that needs more than Python. `requires_lean` covers
anything reaching the pinned Lean toolchain; `requires_linux` covers the
Linux-only kernel interfaces the proof TCB uses. Both skip rather than fail
when the environment cannot provide them, so a missing toolchain is reported as
absent instead of masquerading as a broken proof.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)


def repository_root() -> Path:
    """Directory holding `pyproject.toml`, found by walking upward."""
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "pyproject.toml").is_file():
            return candidate
    raise RuntimeError("repository root not found")


REPO_ROOT = repository_root()


def lean_toolchain_available() -> bool:
    """Report whether the pinned, content-bound Lean binary is usable here."""
    try:
        from src.core.observer_core_bridge_io import lean_command
    except Exception:  # noqa: BLE001 - absence is the answer we want
        logger.debug("lean_toolchain_available: bridge import failed")
        return False
    try:
        return bool(lean_command())
    except Exception:  # noqa: BLE001
        logger.debug("lean_toolchain_available: probe failed")
        return False


def linux_interfaces_available() -> bool:
    """Report whether the Linux-only kernel interfaces are present."""
    return sys.platform.startswith("linux")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip toolchain-gated and Linux-gated items when unavailable."""
    del config
    gates = (
        ("requires_lean", lean_toolchain_available(),
         "needs the pinned Lean toolchain"),
        ("requires_linux", linux_interfaces_available(),
         "needs Linux-only kernel interfaces"),
    )
    for name, available, reason in gates:
        if available:
            continue
        skip = pytest.mark.skip(reason=reason)
        for item in items:
            if item.get_closest_marker(name) is not None:
                item.add_marker(skip)


@pytest.fixture(scope="session")
def lean_available() -> bool:
    """Whether the pinned Lean toolchain can run here."""
    return lean_toolchain_available()


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Repository root."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def lean_dir(repo_root: Path) -> Path:
    """Directory holding the checked Lean sources."""
    return repo_root / "proofs" / "lean"


@pytest.fixture(scope="session")
def tmp_artifacts(repo_root: Path) -> Path:
    """Untracked root for generated intermediate artifacts."""
    return repo_root / "data" / "tmp"
