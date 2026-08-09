from __future__ import annotations

import subprocess
from pathlib import Path
from src.core.paths import PROJECT_ROOT
import pytest

pytestmark = pytest.mark.requires_lean


ROOT = PROJECT_ROOT
LEAN_SOURCE = ROOT / "proofs" / "lean" / "VeyraQuantumTensor.lean"
LEAN_TOOLCHAIN = "leanprover/lean4:v4.30.0-rc2"
THEOREM_IDS = (
    "THM_Q11_001_born_rule_normalized",
    "THM_Q11_002_tensor_born_normalized",
    "THM_Q11_003_tensor_unitary",
    "THM_Q11_004_compose_unitary",
)


def test_q11_lean_source_names_four_scoped_results():
    source = LEAN_SOURCE.read_text(encoding="utf-8")
    assert all(
        (f"theorem {theorem_id}" in source or f"def {theorem_id}" in source)
        and f"#check {theorem_id}" in source
        for theorem_id in THEOREM_IDS
    )
    assert "does not formalize analytic" in source


def test_q11_lean_artifact_compiles_with_pinned_toolchain():
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
