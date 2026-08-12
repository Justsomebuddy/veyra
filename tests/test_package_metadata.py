"""Distribution metadata and dependency-contract checks."""

from __future__ import annotations

import logging
from pathlib import Path
import re
import tomllib
from types import MappingProxyType

import pytest
from setuptools import find_packages

import scripts.project_hygiene as hygiene
from scripts.verify_portable import steps as portable_steps
from scripts.project_hygiene import (
    HARD_LINE_LIMIT,
    LINE_LIMIT_EXCEPTIONS,
    TARGET_LINE_LIMIT,
    TEXT_NAMES,
    TEXT_SUFFIXES,
    line_limit,
    line_limit_exception_errors,
)

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]


def test_python_support_is_bounded_to_the_reviewed_minor_line():
    """Portable packaging spans 3.11 patches but never overclaims a new minor."""
    logger.debug("test Python support metadata entry")
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = metadata["project"]
    assert project["requires-python"] == ">=3.11,<3.12"
    assert project["dependencies"] == []
    assert "Programming Language :: Python :: 3.11" in project["classifiers"]
    assert "Programming Language :: Python :: Implementation :: CPython" in project["classifiers"]
    logger.debug("test Python support metadata exit")


def test_direct_tool_constraints_match_declared_extras():
    """Every direct Python tool has a named bounded requirement surface."""
    logger.debug("test direct tool constraints entry")
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    extras = metadata["project"]["optional-dependencies"]
    declared = {
        requirement.split("=", 1)[0].split("<", 1)[0].split(">", 1)[0]
        for requirements in extras.values()
        for requirement in requirements
    }
    constraints = {
        row.split("==", 1)[0]
        for row in (ROOT / "requirements/py311-tested.txt").read_text(encoding="utf-8").splitlines()
        if row and not row.startswith("#")
    }
    assert {"build", "cryptography", "pytest", "ruff", "tqdm", "ipykernel", "jupyterlab"} <= declared
    assert declared <= constraints
    assert {"setuptools", "wheel"} <= constraints
    ci = {
        row.split("==", 1)[0]
        for row in (ROOT / "requirements/ci-py311.txt").read_text(encoding="utf-8").splitlines()
        if row and not row.startswith("#")
    }
    assert {"pip", "setuptools", "wheel", "build", "pytest", "ruff", "tqdm"} <= ci
    logger.debug("test direct tool constraints exit")


def test_rust_toolchain_and_msrv_are_explicit():
    """The native crate records both reproduced and minimum compiler versions."""
    logger.debug("test Rust toolchain metadata entry")
    cargo = tomllib.loads((ROOT / "vam/native/Cargo.toml").read_text(encoding="utf-8"))
    toolchain = tomllib.loads((ROOT / "vam/native/rust-toolchain.toml").read_text(encoding="utf-8"))
    assert cargo["package"]["rust-version"] == "1.83"
    assert toolchain["toolchain"]["channel"] == "1.95.0"
    assert toolchain["toolchain"]["profile"] == "minimal"
    assert toolchain["toolchain"]["components"] == ["rustfmt"]
    logger.debug("test Rust toolchain metadata exit")


def test_wheel_package_discovery_is_explicit_and_bounded():
    """Documentation/native source directories cannot become namespace packages."""
    logger.debug("test wheel package discovery entry")
    packages = set(find_packages(where=ROOT, include=("src*", "veyra_sage*", "vam*")))
    assert packages == {
        "src",
        "src.core",
        "src.core.construction",
        "src.core.construction.finite_builder",
        "src.core.observer_discovery_v3",
        "src.core.observer_discovery_v3.dsl",
        "src.core.observer_discovery_v3.ledger",
        "src.core.observer_discovery_v3.lineage",
        "src.core.observer_discovery_v3.replay",
        "src.core.observer_discovery_v3.schema",
        "src.core.observer_discovery_v3.service",
        "src.core.observer_discovery_v3.transport",
        "src.core.observer_discovery_v3.worker",
        "vam",
        "vam.intrinsic",
        "vam.src",
        "veyra_sage",
    }
    logger.debug("test wheel package discovery exit count=%d", len(packages))


def test_conda_direct_ranges_match_python_metadata():
    """The conda profile mirrors the supported interpreter and direct ranges."""
    logger.debug("test conda ranges entry")
    environment = (ROOT / "environment.yml").read_text(encoding="utf-8")
    for requirement in (
        "python>=3.11,<3.12",
        "pytest>=8,<10",
        "ruff>=0.12,<1",
        "tqdm>=4.66,<5",
        "build>=1.2,<2",
        "cryptography>=45,<48",
        "setuptools>=77,<81",
        "wheel>=0.45,<0.47",
        "ipykernel>=6,<7",
        "jupyterlab>=4,<5",
    ):
        assert f"  - {requirement}" in environment
    logger.debug("test conda ranges exit")


def test_portable_verification_steps_are_time_bounded():
    """Hosted and local portable gates must not wait forever on a subprocess."""
    logger.debug("test portable timeouts entry")
    planned = portable_steps()
    assert planned
    assert all(0 < step.timeout_seconds <= 900 for step in planned)
    logger.debug("test portable timeouts exit count=%d", len(planned))


def test_portable_verification_includes_observer_realization_behavior():
    """The portable matrix must exercise the context-relative R16 behavior."""
    logger.debug("test portable observer realization coverage entry")
    portable_pytest = next(step for step in portable_steps() if step.name == "Portable pytest")
    assert "tests/test_observer_realization.py" in portable_pytest.command
    logger.debug("test portable observer realization coverage exit")


def test_hosted_matrix_is_fixed_bounded_and_immutable():
    """Portable CI must name hosts, Python patches, bounds, and action objects."""
    logger.debug("test hosted matrix contract entry")
    workflow = (ROOT / ".github/workflows/portable.yml").read_text(encoding="utf-8")
    for row in (
        "os: ubuntu-24.04",
        'python: "3.11.14"',
        "os: macos-14",
        "os: windows-2022",
        'python: "3.11.9"',
        "timeout-minutes: 30",
        "timeout-minutes: 20",
        'RUSTUP_TOOLCHAIN: "1.95.0"',
        "requirements/ci-py311.txt",
        "persist-credentials: false",
        "pip install --no-deps --requirement requirements/ci-py311.txt",
    ):
        assert row in workflow
    uses = re.findall(r"uses:\s+[^@\s]+@([^\s#]+)", workflow)
    assert uses and all(re.fullmatch(r"[0-9a-f]{40}", revision) for revision in uses)
    assert "pull_request_target" not in workflow
    logger.debug("test hosted matrix contract exit actions=%d", len(uses))


def test_ci_requirement_rows_are_exact_and_unique():
    """Hosted Python bootstrap rows are exact names with no silent duplicates."""
    logger.debug("test CI requirements exactness entry")
    rows = tuple(
        row
        for row in (ROOT / "requirements/ci-py311.txt").read_text(encoding="utf-8").splitlines()
        if row and not row.startswith("#")
    )
    names = tuple(row.split("==", 1)[0] for row in rows)
    assert all(re.fullmatch(r"[A-Za-z0-9_.-]+==[^=\s]+", row) for row in rows)
    assert len(names) == len(set(names))
    assert set(names) == {
        "pip",
        "setuptools",
        "wheel",
        "build",
        "packaging",
        "pyproject_hooks",
        "pytest",
        "iniconfig",
        "pluggy",
        "Pygments",
        "ruff",
        "tqdm",
        "colorama",
    }
    logger.debug("test CI requirements exactness exit rows=%d", len(rows))


def test_hygiene_covers_every_maintained_source_and_configuration_format():
    """LOC enforcement includes native, proof, shell, dependency, and CI text."""
    logger.debug("test hygiene format policy entry")
    assert {
        ".py",
        ".md",
        ".rs",
        ".lean",
        ".sh",
        ".toml",
        ".yml",
        ".yaml",
        ".txt",
        ".lock",
    } <= TEXT_SUFFIXES
    assert {"Makefile", "LICENSE"} <= TEXT_NAMES
    logger.debug("test hygiene format policy exit")


def test_hygiene_uses_reviewed_target_and_hard_maximum() -> None:
    """LOC exceptions must be explicit, justified, and never exceed 2000."""
    logger.debug("test hygiene line-limit policy entry")
    assert TARGET_LINE_LIMIT == 1000
    assert HARD_LINE_LIMIT == 2000
    assert line_limit(Path("src/core/example.py")) == TARGET_LINE_LIMIT
    for identity, (limit, justification) in LINE_LIMIT_EXCEPTIONS.items():
        assert identity == Path(identity).as_posix()
        assert TARGET_LINE_LIMIT < limit <= HARD_LINE_LIMIT
        assert justification.strip()
    logger.debug(
        "test hygiene line-limit policy exit exceptions=%d",
        len(LINE_LIMIT_EXCEPTIONS),
    )


def test_hygiene_accepts_one_justified_bounded_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A cohesive path may exceed the target only through reviewed metadata."""
    logger.debug("test hygiene valid exception entry")
    monkeypatch.setattr(
        hygiene,
        "LINE_LIMIT_EXCEPTIONS",
        MappingProxyType(
            {
                "src/core/cohesive_example.py": (
                    1500,
                    "splitting would separate the audited state machine from its invariants",
                )
            }
        ),
    )
    assert hygiene.line_limit(Path("src/core/cohesive_example.py")) == 1500
    logger.debug("test hygiene valid exception exit")


@pytest.mark.parametrize(
    ("limit", "justification"),
    ((2001, "too large"), (1500, "")),
)
def test_hygiene_rejects_unbounded_or_unjustified_exceptions(
    monkeypatch: pytest.MonkeyPatch,
    limit: int,
    justification: str,
) -> None:
    """The hard maximum and non-empty rationale are fail-closed constraints."""
    logger.debug(
        "test hygiene invalid exception entry limit=%d justification=%s",
        limit,
        bool(justification),
    )
    monkeypatch.setattr(
        hygiene,
        "LINE_LIMIT_EXCEPTIONS",
        MappingProxyType({"src/core/invalid_example.py": (limit, justification)}),
    )
    with pytest.raises(RuntimeError, match="invalid-line-limit-exception"):
        hygiene.line_limit(Path("src/core/invalid_example.py"))
    logger.debug("test hygiene invalid exception exit")


@pytest.mark.parametrize("identity", ("../escape.py", "/absolute.py", "src\\host.py"))
def test_hygiene_rejects_non_repository_exception_identities(
    monkeypatch: pytest.MonkeyPatch,
    identity: str,
) -> None:
    """Exception identities must be normalized repository-relative POSIX paths."""
    logger.debug("test hygiene invalid identity entry identity=%r", identity)
    monkeypatch.setattr(
        hygiene,
        "LINE_LIMIT_EXCEPTIONS",
        MappingProxyType({identity: (1500, "test rationale")}),
    )
    files = (hygiene.ROOT / "src/core/example.py",)
    assert line_limit_exception_errors(files) == (f"invalid-line-limit-identity:{identity}",)
    logger.debug("test hygiene invalid identity exit")


def test_hygiene_rejects_stale_exception_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every exception must name one file in the maintained hygiene inventory."""
    logger.debug("test hygiene stale exception entry")
    identity = "src/core/not_in_inventory.py"
    monkeypatch.setattr(
        hygiene,
        "LINE_LIMIT_EXCEPTIONS",
        MappingProxyType({identity: (1500, "test rationale")}),
    )
    files = (hygiene.ROOT / "src/core/example.py",)
    assert line_limit_exception_errors(files) == (f"stale-line-limit-exception:{identity}",)
    logger.debug("test hygiene stale exception exit")


def test_hygiene_rejects_exception_after_file_returns_to_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An exception is stale once its maintained file no longer exceeds 1000."""
    logger.debug("test hygiene unneeded exception entry")
    identity = "README.md"
    monkeypatch.setattr(
        hygiene,
        "LINE_LIMIT_EXCEPTIONS",
        MappingProxyType({identity: (1500, "test rationale")}),
    )
    files = (hygiene.ROOT / identity,)
    assert line_limit_exception_errors(files) == (f"unneeded-line-limit-exception:{identity}",)
    logger.debug("test hygiene unneeded exception exit")
