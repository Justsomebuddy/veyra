"""The tracked tree carries no assistant-attribution tokens, and the hygiene scan detects planted ones."""

from __future__ import annotations

import os
from pathlib import Path

from scripts import project_hygiene as hygiene

ROOT = Path(__file__).resolve().parents[1]


def test_tracked_tree_and_paths_are_attribution_free() -> None:
    files = hygiene.tracked_text_files()
    names = tuple(os.fsdecode(raw) for raw in hygiene.git_inventory(hygiene.ROOT))
    assert files and names
    assert hygiene.attribution_violations(files, names) == ()


def test_scan_detects_a_planted_token_in_text_and_in_a_path(tmp_path: Path) -> None:
    token = hygiene._attribution_tokens()[0]
    planted = tmp_path / "note.md"
    planted.write_text(f"reviewed with {token.upper()} yesterday\n", encoding="utf-8")
    clean = tmp_path / "clean.md"
    clean.write_text("nothing to see\n", encoding="utf-8")
    found = hygiene.attribution_violations((planted, clean), (f"docs/{token}-notes.md", "docs/fine.md"))
    assert len(found) == 2
    assert found[0].startswith("repository path carries an assistant-attribution token: docs/")
    assert found[1].startswith("assistant-attribution token in") and found[1].endswith(":1")


def test_tokens_are_assembled_not_spelled_in_the_checker_source() -> None:
    source = (ROOT / "scripts" / "project_hygiene.py").read_text(encoding="utf-8").lower()
    for token in hygiene._attribution_tokens():
        assert token not in source
