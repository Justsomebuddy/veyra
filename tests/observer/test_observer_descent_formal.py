from __future__ import annotations

import subprocess
from pathlib import Path
from src.core.paths import PROJECT_ROOT
import pytest

pytestmark = pytest.mark.requires_lean


ROOT = PROJECT_ROOT
LEAN_SOURCE = ROOT / "proofs" / "lean" / "VeyraObserverDescent.lean"
LEAN_TOOLCHAIN = "leanprover/lean4:v4.30.0-rc2"


def test_r16_lean_source_names_three_scoped_results():
    source = LEAN_SOURCE.read_text(encoding="utf-8")
    assert "THM_R16_001_residual_chain_partition" in source
    assert "THM_R16_002_residual_synergy_disjoint" in source
    assert "THM_R16_003_zero_synergy_chain_rule" in source
    assert "remain outside this Lean file" in source


def test_r16_lean_partition_artifact_compiles_with_pinned_toolchain():
    result = subprocess.run(
        (
            "elan",
            "run",
            LEAN_TOOLCHAIN,
            "lean",
            "-DwarningAsError=true",
            str(LEAN_SOURCE),
        ),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
