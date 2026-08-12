"""Static custody checks for repository paths embedded in ``src/core``.

The filesystem alone is not evidence that a cited artifact belongs to the
repository: an ignored or locally generated file could otherwise make the
check pass.  Non-generated identities therefore have to exist *and* be held
by the Git index.  Deliberately generated roots are explicit and narrow.
"""

from __future__ import annotations

import ast
import logging
import os
from pathlib import Path, PurePosixPath
import re
import subprocess

from src.core.paths import PROJECT_ROOT

logger = logging.getLogger(__name__)

REPOSITORY_PATH_LITERAL = re.compile(
    r"^(?:data|docs|experimental|notebooks|proofs|scripts|src|tests|vam|veyra_sage)"
    r"/[A-Za-z0-9_./-]+$"
)

# These trees are products, never source evidence.  A literal below one of
# them may legitimately be absent before its producer runs and untracked when
# it exists.  Keep this list exact rather than allowing arbitrary ``data/``.
GENERATED_REPOSITORY_ROOTS = frozenset(
    {
        "data/processed",
        "data/tmp",
        "notebooks/generated",
        "vam/native/target",
    }
)


def _tracked_repository_paths(root: Path) -> frozenset[str]:
    """Return normalized paths held by the source checkout's Git index."""
    logger.debug("meta tracked repository paths entry root=%s", root)
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--cached", "-z"],
            capture_output=True,
            check=True,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        logger.error("meta tracked repository paths failed error=%s", type(exc).__name__)
        raise
    tracked = frozenset(os.fsdecode(item) for item in result.stdout.split(b"\0") if item)
    logger.debug("meta tracked repository paths exit count=%d", len(tracked))
    return tracked


def _path_literals(tree: ast.AST) -> tuple[tuple[int, str], ...]:
    """Return repository-shaped string constants from one parsed module."""
    logger.debug("meta repository path literal scan entry")
    result = tuple(
        (node.lineno, node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and REPOSITORY_PATH_LITERAL.fullmatch(node.value)
    )
    logger.debug("meta repository path literal scan exit count=%d", len(result))
    return result


def _normalized_identity(literal: str) -> str | None:
    """Normalize a trailing slash while rejecting dot-segment identities."""
    logger.debug("meta repository identity normalization entry chars=%d", len(literal))
    trimmed = literal.rstrip("/")
    identity = PurePosixPath(trimmed)
    if (
        not trimmed
        or identity.as_posix() != trimmed
        or any(part in {"", ".", ".."} for part in identity.parts)
    ):
        logger.error("meta repository identity normalization rejected identity=%r", literal)
        return None
    result = identity.as_posix()
    logger.debug("meta repository identity normalization exit identity=%s", result)
    return result


def _is_generated_identity(identity: str) -> bool:
    """Return whether an identity belongs to an explicitly generated tree."""
    logger.debug("meta generated identity check entry identity=%s", identity)
    result = any(identity == root or identity.startswith(f"{root}/") for root in GENERATED_REPOSITORY_ROOTS)
    logger.debug("meta generated identity check exit generated=%s", result)
    return result


def _is_tracked_identity(identity: str, tracked: frozenset[str]) -> bool:
    """Accept an indexed file or a directory containing indexed files."""
    logger.debug("meta tracked identity check entry identity=%s", identity)
    prefix = f"{identity}/"
    result = identity in tracked or any(path.startswith(prefix) for path in tracked)
    logger.debug("meta tracked identity check exit tracked=%s", result)
    return result


def test_core_repository_path_literals_are_custodied() -> None:
    """Require every non-generated repository literal to exist and be tracked."""
    logger.debug("test core repository path custody entry")
    root = PROJECT_ROOT.resolve()
    core = root / "src" / "core"
    tracked = _tracked_repository_paths(root)
    violations: list[str] = []
    checked = 0

    for path in sorted(core.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for lineno, literal in _path_literals(tree):
            identity = _normalized_identity(literal)
            location = f"{path.relative_to(root).as_posix()}:{lineno} -> {literal}"
            if identity is None:
                violations.append(f"non-canonical: {location}")
                continue
            if _is_generated_identity(identity):
                continue
            checked += 1
            target = root.joinpath(*PurePosixPath(identity).parts)
            if not target.exists():
                violations.append(f"missing: {location}")
            elif not _is_tracked_identity(identity, tracked):
                violations.append(f"untracked: {location}")

    if not checked:
        logger.error("test core repository path custody found no eligible literals")
    if violations:
        logger.error("test core repository path custody violations=%d", len(violations))
    assert checked, "expected src/core to cite non-generated repository paths"
    assert not violations, "uncustodied repository paths in src/core:\n" + "\n".join(violations)
    logger.debug("test core repository path custody exit checked=%d", checked)
