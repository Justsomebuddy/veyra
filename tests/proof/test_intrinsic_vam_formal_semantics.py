"""Direct pinned-Lean acceptance tests for the R12.5 semantic bridge."""
from __future__ import annotations

import logging
import os
from pathlib import Path
import pwd
import re
import subprocess

from src.core.intrinsic_vam_formal_bridge_io import lean_command
from src.core.intrinsic_vam_formal_lean_render import THEOREM_ROWS
from src.core.intrinsic_vam_formal_snapshot import _SNAPSHOT_NAME_ROWS
from src.core.paths import PROJECT_ROOT
import pytest

pytestmark = pytest.mark.requires_lean


LOGGER = logging.getLogger(__name__)
ROOT = PROJECT_ROOT
LEAN_DIR = ROOT / "proofs/lean"
LEAN_SOURCE = LEAN_DIR / "VeyraIntrinsicVamBridge.lean"
FORBIDDEN = re.compile(r"\b(?:sorryAx|sorry|admit|axiom|unsafe)\b")


def _direct_compile_chain(output_root: Path) -> tuple[str, ...]:
    """Fresh-compile the reviewed chain through the intrinsic bridge."""
    LOGGER.info("R12.5 direct Lean compile start stages=%d", len(_SNAPSHOT_NAME_ROWS) - 1)
    command = lean_command()
    assert command, "r12.5-pinned-lean-not-found"
    prior: list[Path] = []
    diagnostics: list[str] = []
    for index, (_, filename) in enumerate(_SNAPSHOT_NAME_ROWS[:-1], 1):
        source = LEAN_DIR / filename
        stage = output_root / f"{index:02d}-{source.stem}"
        stage.mkdir()
        output = stage / f"{source.stem}.olean"
        env = {
            "HOME": pwd.getpwuid(os.getuid()).pw_dir,
            "PATH": "/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
        }
        if prior:
            env["LEAN_PATH"] = os.pathsep.join(str(path.parent) for path in prior)
        completed = subprocess.run(
            command + ["-R", str(LEAN_DIR), "-o", str(output), str(source)],
            cwd=LEAN_DIR,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )
        diagnostics.append(f"{index}/{len(_SNAPSHOT_NAME_ROWS) - 1}:{source.stem}:rc={completed.returncode}")
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert "warning:" not in (completed.stdout + completed.stderr).lower()
        assert output.is_file() and output.stat().st_size > 0
        prior.append(output)
    LOGGER.info("R12.5 direct Lean compile complete stages=%d", len(prior))
    return tuple(diagnostics)


def test_intrinsic_vam_lean_source_has_exact_theorems_and_no_placeholders() -> None:
    LOGGER.info("R12.5 Lean source audit start")
    source = LEAN_SOURCE.read_text(encoding="utf-8")
    assert tuple(theorem for theorem, _ in THEOREM_ROWS) == tuple(
        f"THM-R12-{index:03d}" for index in range(1, 10)
    )
    assert all(f"theorem {symbol}" in source for _, symbol in THEOREM_ROWS)
    assert FORBIDDEN.search(source) is None
    assert "lowerEchoOutcomeIR" in source
    assert "domainBlocked left right" in source
    assert "path := [.applyTail]" in source
    bounded_signatures = {
        THEOREM_ROWS[0][1]: ("recurrenceBounded",),
        THEOREM_ROWS[1][1]: ("recurrenceBounded",),
        THEOREM_ROWS[2][1]: ("recurrenceBounded left", "recurrenceBounded right"),
        THEOREM_ROWS[3][1]: ("value.path.length + 1 ≤ 128",),
        THEOREM_ROWS[4][1]: ("responseBounded", "observationBounded"),
        THEOREM_ROWS[5][1]: ("observerBounded", "responseBounded", "observationBounded"),
        THEOREM_ROWS[6][1]: ("observerBounded", "r11RecurrenceBounded", "observationBounded"),
        THEOREM_ROWS[7][1]: ("observerBounded", "r11RecurrenceBounded", "echoOutcomeBounded"),
    }
    for symbol, predicates in bounded_signatures.items():
        signature = source.split(f"theorem {symbol}", 1)[1].split(":=", 1)[0]
        assert all(predicate in signature for predicate in predicates)
    assert all(limit in source for limit in ("≤ 2047", "≤ 2048", "≤ 4096", "≤ 128"))
    LOGGER.info("R12.5 Lean source audit complete theorems=%d", len(THEOREM_ROWS))


def test_intrinsic_vam_semantics_compile_with_direct_pinned_lean(tmp_path: Path) -> None:
    diagnostics = _direct_compile_chain(tmp_path)
    assert diagnostics[-1] == "9/9:VeyraIntrinsicVamBridge:rc=0"
