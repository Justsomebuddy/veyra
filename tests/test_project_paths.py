"""Repository-path anchoring and no-CWD-regression checks."""

from __future__ import annotations

import ast
import logging
from pathlib import Path

import pytest

from src.core.formal_export_catalog import formal_export_specs, read_bound_lean_artifact
from src.core.paths import PROJECT_ROOT, TMP_DIR, lean_artifact, repository_path

logger = logging.getLogger(__name__)
_IDENTITY_FUNCTIONS = {
    "lean_coherent_towers_path",
    "lean_observer_patch_atlas_path",
    "lean_echo_export_path",
    "lean_cyclic_period_export_path",
    "lean_pythagorean_export_path",
    "lean_algebra_export_path",
    "lean_probability_export_path",
    "lean_statistics_export_path",
    "lean_combinatorics_export_path",
}


def test_repository_path_rejects_escape_and_host_specific_identifiers() -> None:
    """Only normalized relative POSIX identities may cross the path boundary."""
    logger.debug("test repository path rejection entry")
    for value in (
        "",
        ".",
        "../proofs/lean/X.lean",
        "/proofs/lean/X.lean",
        "proofs\\lean\\X.lean",
        "proofs//lean/X.lean",
        "proofs/./lean/X.lean",
        "proofs/lean/",
    ):
        with pytest.raises(ValueError, match="invalid-repository-path-identity"):
            repository_path(value)
    assert lean_artifact("VeyraEcho.lean") == PROJECT_ROOT / "proofs" / "lean" / "VeyraEcho.lean"
    assert TMP_DIR == PROJECT_ROOT / "data" / "tmp"
    logger.debug("test repository path rejection exit")


def test_formal_catalog_reads_from_outside_caller_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Logical proof identifiers resolve at I/O while reports remain portable."""
    logger.debug("test off-CWD formal catalog entry cwd=%s", tmp_path)
    monkeypatch.chdir(tmp_path)
    spec = formal_export_specs()[0]
    assert not spec.proof_path.is_absolute()
    payload, matched = read_bound_lean_artifact(spec)
    assert payload is not None and matched
    assert repository_path(spec.proof_path.as_posix()).is_file()
    logger.debug("test off-CWD formal catalog exit bytes=%d", len(payload))


@pytest.mark.requires_symlinks
def test_repository_path_rejects_existing_symlink_escape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An operator-selected root cannot redirect an artifact through a symlink."""
    logger.debug("test repository path symlink escape entry")
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "proofs").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr("src.core.paths.PROJECT_ROOT", root)
    with pytest.raises(ValueError, match="repository-path-escapes-root"):
        repository_path("proofs/lean/X.lean")
    logger.debug("test repository path symlink escape exit")


def _enclosing_function(parents: dict[ast.AST, ast.AST], node: ast.AST) -> str | None:
    """Return the closest containing function name for a syntax node."""
    logger.debug("test path AST enclosing function entry node=%s", type(node).__name__)
    current = parents.get(node)
    while current is not None and not isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
        current = parents.get(current)
    result = None if current is None else current.name
    logger.debug("test path AST enclosing function exit function=%s", result)
    return result


def test_core_has_no_unanchored_fixed_repository_io() -> None:
    """Reject new fixed proof/temp ``Path`` calls outside identity factories."""
    logger.debug("test static repository path audit entry")
    violations: list[str] = []
    core = PROJECT_ROOT / "src" / "core"
    files = tuple(
        path for path in core.rglob("*.py") if "__pycache__" not in path.parts
    )
    for path in sorted(files):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "Path":
                continue
            if len(node.args) != 1 or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
                continue
            value = node.args[0].value
            if not value.startswith(("proofs/", "data/tmp")):
                continue
            function = _enclosing_function(parents, node)
            if value.startswith("proofs/") and function in _IDENTITY_FUNCTIONS:
                continue
            violations.append(f"{path.relative_to(PROJECT_ROOT).as_posix()}:{node.lineno}:{value}")
    assert not violations, "unanchored repository paths:\n" + "\n".join(violations)
    logger.debug("test static repository path audit exit files=%d", len(files))
