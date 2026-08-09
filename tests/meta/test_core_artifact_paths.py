"""Every repository path written into `src/core` as a literal must exist.

Certificates decide capability from `.exists()` checks against repository
paths. A path that no longer resolves does not raise: the gate simply reports
a weaker capability, so relocating a file silently downgrades a certificate
instead of failing it. Nothing else in the suite notices, because the
certificate still runs and still returns a Certificate.

This check reads the literals statically and requires each one to resolve.
"""
from __future__ import annotations

import ast
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

REPOSITORY_PATH = re.compile(
    r"^(tests|vam|docs|data|scripts|veyra_sage|proofs|notebooks|experimental|src)"
    r"/[A-Za-z0-9_./-]+$"
)

# Paths that are deliberately absent when the check runs.
EXPECTED_ABSENT = frozenset({
    # Generated output; created by `make tables` / `make notebooks`, untracked.
    "data/processed",
    "data/processed/",
    "notebooks/generated",
    "notebooks/generated/",
})


def _path_literals(tree: ast.AST) -> list[tuple[int, str]]:
    """Return every string literal shaped like a repository-relative path."""
    logger.debug("_path_literals entry")
    result = [
        (node.lineno, node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and REPOSITORY_PATH.match(node.value)
    ]
    logger.debug("_path_literals exit count=%d", len(result))
    return result


def test_core_repository_path_literals_resolve(repo_root: Path) -> None:
    """Reject a `src/core` literal naming a repository file that is absent."""
    logger.debug("test_core_repository_path_literals_resolve entry")
    dangling: list[str] = []
    checked = 0

    for path in sorted((repo_root / "src" / "core").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for lineno, literal in _path_literals(tree):
            if literal in EXPECTED_ABSENT:
                continue
            checked += 1
            if not (repo_root / literal).exists():
                dangling.append(
                    f"{path.relative_to(repo_root)}:{lineno} -> {literal}"
                )

    assert checked, "expected src/core to cite repository paths"
    assert not dangling, (
        "repository paths cited in src/core that do not exist:\n"
        + "\n".join(dangling)
    )
    logger.debug(
        "test_core_repository_path_literals_resolve exit checked=%d", checked
    )
