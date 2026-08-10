"""Checked Lean bridge for general strict native Veyra semantics."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PurePosixPath
import logging
import shutil
import subprocess

from .paths import repository_path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NativeFormalBridgeReport:
    path: str
    status: str
    theorem_ids: tuple[str, ...]
    semantic_scope: str
    boundary: str
    diagnostics: str


@lru_cache(maxsize=1)
def native_formal_bridge_report() -> NativeFormalBridgeReport:
    """Check the native constructor/evaluator semantics with Lean."""
    logger.debug("native_formal_bridge_report entry")
    identity = PurePosixPath("proofs/lean/VeyraNativeSemantics.lean")
    path = repository_path(identity)
    command = _lean_command()
    symbols = tuple(f"THM_R4_{index:03d}" for index in range(1, 8))
    if not command:
        logger.error("native_formal_bridge_report blocked lean-not-found")
        return NativeFormalBridgeReport(identity.as_posix(), "blocked", (), "strict native semantics", "Lean unavailable", "lean-not-found")
    missing = _missing_symbols(path, symbols)
    proc = subprocess.run(command + [str(path)], text=True, capture_output=True, check=False) if not missing else None
    status = "checked" if proc is not None and proc.returncode == 0 else "blocked"
    theorem_ids = tuple(f"THM-R4-{index:03d}" for index in range(1, 8)) if status == "checked" else ()
    boundary = "general over labels and tact lists, including anchored silence, for the mirrored native constructor subset; not a proof of every shadow module"
    diagnostics = "missing-symbols:" + ",".join(missing) if missing else ((proc.stderr or proc.stdout).strip() if proc else "lean-not-run")
    scope = "Rez/Nod/Tact/Breath/Mode syntax, anchored silence, breath contiguity, closed mode formation, echo mismatch obstruction"
    result = NativeFormalBridgeReport(identity.as_posix(), status, theorem_ids, scope, boundary, diagnostics)
    if status == "blocked": logger.error("native_formal_bridge_report blocked diagnostics=%s", diagnostics[-240:])
    logger.debug("native_formal_bridge_report exit status=%s", status); return result


@lru_cache(maxsize=1)
def intrinsic_arithmetic_lean_status() -> str:
    """Check the independent inductive recurrence arithmetic bridge."""
    logger.debug("intrinsic_arithmetic_lean_status entry")
    command = _lean_command()
    path = repository_path("proofs/lean/VeyraNativeArithmetic.lean")
    if not command:
        logger.error("intrinsic_arithmetic_lean_status blocked lean-not-found"); return "blocked"
    missing = _missing_symbols(path, ("THM_R3_001", "THM_R3_002"))
    proc = subprocess.run(command + [str(path)], text=True, capture_output=True, check=False) if not missing else None
    result = "checked" if proc is not None and proc.returncode == 0 else "blocked"
    diagnostics = "missing-symbols:" + ",".join(missing) if missing else ((proc.stderr or proc.stdout) if proc else "lean-not-run")
    if result == "blocked": logger.error("intrinsic_arithmetic_lean_status blocked diagnostics=%s", diagnostics[-240:])
    logger.debug("intrinsic_arithmetic_lean_status exit status=%s", result); return result


def _missing_symbols(path: Path, symbols: tuple[str, ...]) -> tuple[str, ...]:
    logger.debug("native_formal_bridge._missing_symbols entry path=%s symbols=%d", path, len(symbols))
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.error("native_formal_bridge._missing_symbols read error=%s", exc)
        return symbols
    result = tuple(symbol for symbol in symbols if f"theorem {symbol}" not in source)
    if result: logger.error("native_formal_bridge._missing_symbols missing=%r", result)
    logger.debug("native_formal_bridge._missing_symbols exit missing=%d", len(result)); return result


def _lean_command() -> list[str]:
    logger.debug("native_formal_bridge._lean_command entry")
    elan = shutil.which("elan")
    if elan:
        result = [elan, "run", "leanprover/lean4:v4.30.0-rc2", "lean"]
    else:
        lean = shutil.which("lean"); result = [lean] if lean else []
    logger.debug("native_formal_bridge._lean_command exit result=%r", result); return result
