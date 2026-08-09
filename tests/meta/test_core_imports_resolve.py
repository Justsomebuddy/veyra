"""Every relative import inside `src/core` must name a module that exists.

A relocated module leaves behind relative imports whose dot depth no longer
matches the package they sit in. Python only reports that when the importing
module is first executed, so a broken link can hide behind an untaken branch or
a function-local import. This check resolves every relative import statically.
"""
from __future__ import annotations

import ast
import importlib
import logging
from pathlib import Path
import sys

logger = logging.getLogger(__name__)


def test_legacy_alias_preserves_canonical_module_metadata() -> None:
    """An alias must not corrupt relative imports on its shared module object."""
    canonical_name = "src.core.registry.theorem_language"
    legacy_name = "src.core.theorem_language_validation"
    canonical = importlib.import_module(canonical_name)
    sys.modules.pop(legacy_name, None)

    legacy = importlib.import_module(legacy_name)

    assert legacy is canonical
    assert canonical.__package__ == "src.core.registry"
    assert canonical.__spec__ is not None
    assert canonical.__spec__.name == canonical_name
    assert canonical.__spec__.parent == canonical.__package__


def _module_and_package_names(core: Path) -> tuple[set[str], set[str]]:
    logger.debug("_module_and_package_names entry core=%s", core)
    modules = {
        ".".join(path.relative_to(core).with_suffix("").parts)
        for path in core.rglob("*.py")
        if "__pycache__" not in path.parts
    }
    packages = {
        ".".join(directory.relative_to(core).parts)
        for directory in core.rglob("*")
        if directory.is_dir() and directory.name != "__pycache__"
    }
    logger.debug(
        "_module_and_package_names exit modules=%d packages=%d",
        len(modules),
        len(packages),
    )
    return modules, packages


def test_every_relative_import_in_core_resolves(repo_root: Path) -> None:
    """Reject a relative import whose target does not exist."""
    logger.debug("test_every_relative_import_in_core_resolves entry")
    core = repo_root / "src" / "core"
    modules, packages = _module_and_package_names(core)
    unresolved: list[str] = []
    checked = 0

    for path in sorted(core.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        package = path.relative_to(core).with_suffix("").parts[:-1]
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.ImportFrom) or node.level == 0:
                continue
            checked += 1
            upward = node.level - 1
            if upward > len(package):
                unresolved.append(
                    f"{path.relative_to(repo_root)}:{node.lineno} "
                    f"reaches above src/core"
                )
                continue
            base = package[: len(package) - upward] if upward else package
            if node.module is None:
                # `from . import name` takes a submodule or a re-exported
                # attribute; only the submodule form is decidable statically.
                for alias in node.names:
                    candidate = ".".join([*base, alias.name])
                    if candidate in modules or candidate in packages:
                        continue
                    if f"{'.'.join(base)}.__init__".lstrip(".") in modules or not base:
                        continue
                    unresolved.append(
                        f"{path.relative_to(repo_root)}:{node.lineno} -> {candidate}"
                    )
                continue
            target = ".".join([*base, node.module])
            if target in modules or target in packages or f"{target}.__init__" in modules:
                continue
            unresolved.append(
                f"{path.relative_to(repo_root)}:{node.lineno} -> {target}"
            )

    assert checked, "expected src/core to contain relative imports"
    assert not unresolved, "unresolved relative imports:\n" + "\n".join(unresolved)
    logger.debug(
        "test_every_relative_import_in_core_resolves exit checked=%d", checked
    )
