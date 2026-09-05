"""AST guard: no host arithmetic on the decision paths of the number-theory lanes.

The docs/02 vocabulary (resonance, phase obstruction, indecomposable rhythm,
shared echo/closure) is only honest if the code that decides those judgments
does not quietly call host `%`, `//`, `**`, `pow`, `gcd`, `divmod` or
`primes.is_prime_int`. Each lane module declares the functions that carry host
arithmetic on purpose in a module-level `SHADOW_LICENSED` tuple (docs/06 §3);
functions whose name contains ``shadow`` are licensed by name. Everything else
is checked here, permanently.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

LANES = (
    "src.core.resonance_arithmetic",
    "src.core.necklace_congruence",
    "src.core.orbit_partition",
    "src.core.native_number_theorems",
    "src.core.doctrinal_induction",
)
FORBIDDEN_OPERATORS = (ast.Mod, ast.FloorDiv, ast.Pow)
FORBIDDEN_CALLS = ("pow", "divmod", "gcd", "lcm", "is_prime_int", "isqrt")


def _is_string_format(node: ast.BinOp) -> bool:
    return isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Constant) and isinstance(node.left.value, str)


def _call_name(node: ast.Call) -> str:
    target = node.func
    if isinstance(target, ast.Attribute):
        return target.attr
    if isinstance(target, ast.Name):
        return target.id
    return ""


def _violations(module_name: str) -> list[str]:
    module = importlib.import_module(module_name)
    licensed = set(getattr(module, "SHADOW_LICENSED", ()))
    source = Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    found: list[str] = []
    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if function.name in licensed or "shadow" in function.name:
            continue
        for node in ast.walk(function):
            if isinstance(node, ast.BinOp) and isinstance(node.op, FORBIDDEN_OPERATORS) and not _is_string_format(node):
                found.append(f"{module_name}.{function.name}:{node.lineno} operator {type(node.op).__name__}")
            if isinstance(node, ast.Call) and _call_name(node) in FORBIDDEN_CALLS:
                found.append(f"{module_name}.{function.name}:{node.lineno} call {_call_name(node)}")
    return found


@pytest.mark.parametrize("module_name", LANES)
def test_no_host_arithmetic_on_decision_paths(module_name: str) -> None:
    violations = _violations(module_name)
    assert violations == [], "\n".join(violations)


def test_shadow_license_lists_are_explicit() -> None:
    for module_name in LANES:
        module = importlib.import_module(module_name)
        licensed = getattr(module, "SHADOW_LICENSED", ())
        assert isinstance(licensed, tuple)
        for name in licensed:
            assert hasattr(module, name), f"{module_name}.{name} licensed but absent"


def test_guard_detects_a_planted_violation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    planted = tmp_path / "planted_lane.py"
    planted.write_text(
        "SHADOW_LICENSED = ('licensed_shadow',)\n"
        "def licensed_shadow(a, b):\n    return a % b\n"
        "def deciding(a, b):\n    return a % b == 0\n"
        "def formatting(a):\n    return '%d' % a\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    violations = _violations("planted_lane")
    assert violations == ["planted_lane.deciding:5 operator Mod"]
