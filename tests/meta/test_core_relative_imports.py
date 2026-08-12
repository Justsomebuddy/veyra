"""Static resolution checks for every relative import in ``src/core``."""

from __future__ import annotations

import ast
import logging
from pathlib import Path

from src.core.paths import PROJECT_ROOT

logger = logging.getLogger(__name__)


def _core_module_index(core: Path) -> tuple[frozenset[str], frozenset[str]]:
    """Return importable module and regular-package names below ``src.core``."""
    logger.debug("meta core module index entry core=%s", core)
    modules: set[str] = set()
    packages = {""}
    for path in core.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(core)
        if path.name == "__init__.py":
            packages.add(".".join(relative.parent.parts))
        else:
            modules.add(".".join(relative.with_suffix("").parts))
    result = frozenset(modules), frozenset(packages)
    logger.debug("meta core module index exit modules=%d packages=%d", len(result[0]), len(result[1]))
    return result


def _relative_import_target(
    package: tuple[str, ...],
    node: ast.ImportFrom,
) -> tuple[str | None, str | None]:
    """Resolve an ``ImportFrom`` source or return one structural error."""
    logger.debug("meta relative import target entry level=%d module=%s", node.level, node.module)
    upward = node.level - 1
    if upward > len(package):
        error = f"relative level {node.level} reaches above src.core"
        logger.error("meta relative import target failed reason=%s", error)
        return None, error
    base = package[: len(package) - upward] if upward else package
    target_parts = base if node.module is None else (*base, *node.module.split("."))
    result = ".".join(target_parts)
    logger.debug("meta relative import target exit target=%s", result or "src.core")
    return result, None


def test_every_relative_import_in_core_resolves_statically() -> None:
    """Reject wrong dot depth and imports whose source module does not exist."""
    logger.debug("test core relative import resolution entry")
    root = PROJECT_ROOT.resolve()
    core = root / "src" / "core"
    modules, packages = _core_module_index(core)
    unresolved: list[str] = []
    checked = 0

    for path in sorted(core.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(core)
        package = relative.parent.parts
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or node.level == 0:
                continue
            checked += 1
            target, error = _relative_import_target(package, node)
            location = f"{path.relative_to(root).as_posix()}:{node.lineno}"
            if error is not None:
                unresolved.append(f"{location} -> {error}")
                continue
            assert target is not None
            # ``from . import name`` imports from the package itself.  ``name``
            # can legally be an attribute re-export, so only the source package
            # is statically decidable.  For ``from .module import name``, the
            # named source must be an actual module or package.
            if target not in packages and (node.module is None or target not in modules):
                unresolved.append(f"{location} -> src.core{'.' if target else ''}{target}")

    if not checked:
        logger.error("test core relative import resolution found no relative imports")
    if unresolved:
        logger.error("test core relative import resolution unresolved=%d", len(unresolved))
    assert checked, "expected src/core to contain relative imports"
    assert not unresolved, "unresolved relative imports:\n" + "\n".join(unresolved)
    logger.debug("test core relative import resolution exit checked=%d", checked)
