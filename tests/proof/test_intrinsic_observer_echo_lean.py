"""Direct pinned-Lean acceptance for the standalone R13 semantic nucleus."""
from __future__ import annotations

import logging
import os
from pathlib import Path
import pwd
import re
import subprocess
from hashlib import sha256

from src.core.intrinsic_vam_formal_bridge_io import lean_command
from src.core.intrinsic_vam_formal_snapshot import _SNAPSHOT_NAME_ROWS
from src.core.paths import PROJECT_ROOT
import pytest

pytestmark = pytest.mark.requires_lean


LOGGER = logging.getLogger(__name__)
ROOT = PROJECT_ROOT
LEAN_DIR = ROOT / "proofs/lean"
LEAN_SOURCE = LEAN_DIR / "VeyraIntrinsicObserverEcho.lean"
FORBIDDEN = re.compile(r"\b(?:sorryAx|sorry|admit|axiom|unsafe)\b")
THEOREM_ROWS = (
    ("THM-R13-001", "THM_R13_001_captured_unit_weave_accepted"),
    ("THM-R13-002", "THM_R13_002_unit_weave_semantics_and_image"),
    ("THM-R13-003", "THM_R13_003_ready_intrinsic_unit_weave_echo"),
    ("THM-R13-004", "THM_R13_004_tail_silence_two_sided_domain_blocked"),
    ("THM-R13-005", "THM_R13_005_crest_nonreflection"),
)
EXPECTED_SOURCE_SHA256 = "d9b86a1de1f1ea558a60f730adb5587c64ae540730b72593f694d3f19ab91df0"


def _compile_stage(
    command: list[str],
    source: Path,
    output: Path,
    prior: tuple[Path, ...],
) -> str:
    """Compile one source using only prior fresh objects."""
    LOGGER.info("R13 direct Lean stage start source=%s prior=%d", source.name, len(prior))
    output.parent.mkdir()
    env = {
        "HOME": pwd.getpwuid(os.getuid()).pw_dir,
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }
    if prior:
        env["LEAN_PATH"] = os.pathsep.join(str(path.parent) for path in prior)
    try:
        completed = subprocess.run(
            command + ["-R", str(LEAN_DIR), "-o", str(output), str(source)],
            cwd=LEAN_DIR,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )
        diagnostics = completed.stdout + completed.stderr
        assert completed.returncode == 0, diagnostics
        assert "warning:" not in diagnostics.lower()
        assert output.is_file() and output.stat().st_size > 0
    except Exception:
        LOGGER.exception("R13 direct Lean stage failed source=%s", source.name)
        raise
    result = f"{source.stem}:rc={completed.returncode}"
    LOGGER.info("R13 direct Lean stage complete result=%s", result)
    return result


def _direct_compile_chain(output_root: Path) -> tuple[str, ...]:
    """Fresh-compile the R7/R9/R11/R12 parents and standalone R13 target."""
    LOGGER.info("R13 direct Lean compile start")
    command = lean_command()
    assert command, "r13-pinned-lean-not-found"
    sources = tuple(LEAN_DIR / filename for _, filename in _SNAPSHOT_NAME_ROWS[:-1])
    sources += (LEAN_SOURCE,)
    prior: list[Path] = []
    diagnostics: list[str] = []
    for index, source in enumerate(sources, 1):
        output = output_root / f"{index:02d}-{source.stem}" / f"{source.stem}.olean"
        diagnostics.append(_compile_stage(command, source, output, tuple(prior)))
        prior.append(output)
    result = tuple(diagnostics)
    LOGGER.info("R13 direct Lean compile complete stages=%d", len(result))
    return result


def test_intrinsic_observer_echo_source_has_exact_ids_and_no_placeholders() -> None:
    LOGGER.info("R13 Lean source audit start")
    try:
        source = LEAN_SOURCE.read_text(encoding="utf-8")
        assert sha256(source.encode()).hexdigest() == EXPECTED_SOURCE_SHA256
        assert tuple(row[0] for row in THEOREM_ROWS) == tuple(
            f"THM-R13-{index:03d}" for index in range(1, 6)
        )
        assert tuple(re.findall(r"^theorem\s+(\w+)", source, re.MULTILINE)) == tuple(
            row[1] for row in THEOREM_ROWS
        )
        assert FORBIDDEN.search(source) is None
        assert "surface-parser acceptance remains" in source
        assert "THM_R7_001_check_sound emptyEnv" in source
        assert "exact capturedUnitWeaveSemantics value" in source
        assert "observeIntrinsic observer (intrinsicMode value)" in source
        assert "observerBound : observerBounded observer" in source
        assert "valueBound : r11RecurrenceBounded value" in source
        assert "outcomeBound : echoOutcomeBounded" in source
        assert "THM_R12_008_echo_transport observer value value observerBound" in source
        assert "some (.domainBlocked" in source
        assert "THM_R12_003_lower_recurrence_injective" in source
        assert "echo_transport_universal" not in source
        assert "lower_recurrence_injective_universal" not in source
    except Exception:
        LOGGER.exception("R13 Lean source audit failed")
        raise
    LOGGER.info("R13 Lean source audit complete theorems=%d", len(THEOREM_ROWS))


def test_intrinsic_observer_echo_compiles_with_direct_pinned_lean(
    tmp_path: Path,
) -> None:
    LOGGER.info("R13 pinned compile test start root=%s", tmp_path)
    diagnostics = _direct_compile_chain(tmp_path)
    assert len(diagnostics) == 10
    assert diagnostics[-1] == "VeyraIntrinsicObserverEcho:rc=0"
    LOGGER.info("R13 pinned compile test complete")
