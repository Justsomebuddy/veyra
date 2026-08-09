from __future__ import annotations

from pathlib import Path
import re

from vam.src.optimizer_proofs import check_lean_optimizer_export
from src.core.paths import PROJECT_ROOT
import pytest

pytestmark = pytest.mark.requires_lean

ROOT = PROJECT_ROOT
LEAN_FILE = ROOT / "proofs/lean/VeyraOptimizer.lean"


def test_vam_optimizer_lean_artifact_has_no_sorry_and_keeps_boundary() -> None:
    text = LEAN_FILE.read_text(encoding="utf-8")

    assert re.search(r"\bsorry\b", text) is None
    assert "theorem observerAlias_lookup_invariant" in text
    assert "theorem compressIdempotent_sameObserver_local_law" in text
    assert "theorem compressIdempotent_visibleUseObserver_local_law" in text
    assert "theorem compressAlias_samePair_local_law" in text
    assert "theorem compressIdempotent_differentObserver_reject_local_law" in text
    assert "theorem compressIdempotent_obstructionBoundary_reject_local_law" in text
    assert "theorem deadShadow_unusedLookup_local_law" in text
    assert "abbrev ObserverKind := String" in text
    assert "abbrev CompressDecl := Reg × Reg × Reg" in text
    assert "abbrev ShadowKind := String" in text
    assert "abbrev ShadowDecl := Reg × ShadowKind" in text
    assert "abbrev VisibleUseDecl := Reg × Reg" in text
    assert "def lookupCompress" in text
    assert "def compressAliasStep" in text
    assert "def lookupShadow" in text
    assert "def deadShadowDrop" in text
    assert "def rewriteVisibleUse" in text
    assert "checked local-law artifact only" in text.lower()
    assert "seven bounded local laws" in text.lower()
    forbidden_boundary_terms = (
        "whole-pass",
        "whole pass",
        "whole-optimizer",
        "whole optimizer",
        "global semantic equivalence",
        "vamd",
        "speed",
    )
    lowered = text.lower()
    for term in forbidden_boundary_terms:
        assert term not in lowered


def test_vam_optimizer_observer_alias_lean_file_checks() -> None:
    result = check_lean_optimizer_export(LEAN_FILE)

    assert result.status == "checked", result.stderr or result.stdout
