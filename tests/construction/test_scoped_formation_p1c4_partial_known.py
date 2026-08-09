"""Three-valued G4 partial-knowledge regressions for P1-C4."""

from src.core.observer_core_kernel import tail_observer
from src.core.observer_core_semantics import echo as native_echo
from src.core.observer_core_types import Mark, MarkValue, Mismatch
from src.core.observer_patch_atlas import (
    local_observer_section, observer_patch, observer_patch_atlas,
)
from src.core.proof_core_types import Silence
from src.core.scoped_formation import ScopedFormationStatus, scoped_formation_judgment
from src.core.scoped_formation_g4 import _derived_blocks, _positive_contradictions
from src.core.scoped_formation_types import G4ResponseRow

from scoped_formation_fixture import scoped_formation_fixture


def test_echo_blocked_split_partial_triangle_is_open_without_fabricated_contradiction(monkeypatch):
    """ECHO(ab)+BLOCKED(bc)+SPLIT(ca) supplies neither bc equality nor bc split."""
    rule, scope = scoped_formation_fixture(include_translated=False)
    blocked = native_echo(tail_observer(), Silence(), Silence())
    split = Mismatch(MarkValue(Mark.PULSE), MarkValue(Mark.SILENT))
    calls = 0

    def selective(observer, left, right):
        nonlocal calls
        calls += 1
        if calls == 1:
            return native_echo(observer, left, right)
        if calls == 3:
            return split
        return blocked

    monkeypatch.setattr("src.core.scoped_formation_g4.echo", selective)
    result = scoped_formation_judgment(rule, scope)
    assert result.g4.status is ScopedFormationStatus.OPEN
    assert result.g4.contradiction_rows == ()
    assert result.status is ScopedFormationStatus.OPEN


def test_partial_triangle_positive_catalog_has_no_crossed_split():
    """The explicit ternary catalog keeps blocked evidence out of both relations."""
    established = ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE
    digest = "0" * 64
    rows = [
        G4ResponseRow("triangle", "o", "a", "b", established, "echo", digest, digest, digest),
        G4ResponseRow("triangle", "o", "a", "c", established, "split", digest, digest, digest),
        G4ResponseRow("triangle", "o", "b", "c", ScopedFormationStatus.OPEN, "blocked", digest, digest, digest),
    ]
    atlas = observer_patch_atlas(
        ("a", "b", "c"), (observer_patch("triangle", ("a", "b", "c")),),
    )
    blocks = _derived_blocks(("a", "b", "c"), rows, ("o",))
    sections = (local_observer_section(atlas, "triangle", blocks),)
    assert blocks == (("a", "b"), ("c",))
    assert _positive_contradictions(atlas, sections, rows) == ()
