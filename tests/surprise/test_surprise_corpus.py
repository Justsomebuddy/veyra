"""Tests for the seeded S1 observer-gap surprise separation corpus."""
from __future__ import annotations

from collections import defaultdict

import pytest

from src.core.modes import Mode
from src.core.surprise import best_surprise_for_mode
from src.core.surprise_corpus import (
    CorpusBuild,
    build_corpus,
    corpus_digest,
    corpus_obstruction_rows,
    generate_corpus,
    surprise_corpus_checklist,
    surprise_corpus_rows,
    surprise_corpus_summary,
)
from src.core.surprise_separation import (
    BASELINE_FAMILIES,
    classical_baseline_signature,
    expanded_classical_signature,
)

EXPECTED_DIGEST = "e6fabdf7aecdc59866edb687fa76d8ea07c0a2c36185a2fb98796cce425d4c06"


@pytest.fixture(scope="module")
def build() -> CorpusBuild:
    """Build the default seeded corpus once for the whole test module."""
    return build_corpus()


def _word_gap(word: str) -> float:
    """Independently recompute the Veyra edit-lift surprise gap for one word."""
    witness = best_surprise_for_mode(Mode.from_word(word), ("a", "b"), max_part_len=3, max_edits=1, min_part_len=2)
    return 0.0 if witness is None else witness.score


def _expected_catching(left: str, right: str) -> tuple[str, ...]:
    """Independently derive the declared baselines separating a word pair."""
    left_sig = classical_baseline_signature(left)
    right_sig = classical_baseline_signature(right)
    rows = []
    if left_sig.symbol_counts != right_sig.symbol_counts:
        rows.append("symbol-count entropy proxy")
    if left_sig.lag_agreements != right_sig.lag_agreements:
        rows.append("lag-1/2 autocorrelation agreement")
    if left_sig.lz_phrase_count != right_sig.lz_phrase_count:
        rows.append("LZ78 phrase count")
    return tuple(rows)


def test_generate_corpus_is_seeded_larger_and_binary():
    first = generate_corpus()
    second = generate_corpus()
    assert first == second
    assert len(first) == 640
    assert len(set(first)) == 640
    assert len(first) > 496  # larger than the S3 496-word search
    assert all(set(word) <= {"a", "b"} for word in first)
    assert all(6 <= len(word) <= 12 for word in first)
    assert generate_corpus(seed=1) != first
    assert generate_corpus(seed=20260708, word_count=32) != generate_corpus(seed=1, word_count=32)


def test_build_and_digest_are_deterministic(build: CorpusBuild):
    again = build_corpus()
    assert again == build
    assert corpus_digest(again) == corpus_digest(build) == EXPECTED_DIGEST
    other = build_corpus(seed=1)
    assert corpus_digest(other) != EXPECTED_DIGEST


def test_summary_row_has_exact_counts(build: CorpusBuild):
    summary = surprise_corpus_summary()
    assert summary.summary_id == "S7-CORPUS-SUMMARY"
    assert summary.seed == 20260708
    assert summary.min_len == 6
    assert summary.max_len == 12
    assert summary.corpus_words == 640
    assert summary.baseline_family == BASELINE_FAMILIES
    assert summary.signature_groups == 479
    assert summary.colliding_groups == 120
    assert summary.positive_gap_words == 110
    assert summary.blind_pairs_found == 7
    assert summary.blind_rows == 7
    assert summary.caught_rows == 8
    assert summary.obstruction_rows == 5
    assert summary.digest == EXPECTED_DIGEST == corpus_digest(build)
    assert summary.status == "classified"
    assert summary.claim == "executable-certificate"
    assert "no universal" in summary.boundary


def test_baseline_blind_rows_cross_check_against_imported_baselines(build: CorpusBuild):
    blind = list(build.blind_rows)
    assert len(blind) == 7
    assert [row.row_id for row in blind] == [f"S7-CORPUS-B{index:03d}" for index in range(1, 8)]
    first = blind[0]
    assert (first.structured_word, first.control_word) == ("abbabbbb", "bbbabbba")
    assert (first.structured_gap, first.control_gap, first.witness_part) == (4.0, 0.0, "abb")
    for row in blind:
        left = classical_baseline_signature(row.structured_word)
        right = classical_baseline_signature(row.control_word)
        assert left.comparable_key() == right.comparable_key()
        assert row.baseline_equal is True
        assert row.catching_baselines == ()
        assert row.baseline_family == BASELINE_FAMILIES
        witness = best_surprise_for_mode(
            Mode.from_word(row.structured_word), ("a", "b"), max_part_len=3, max_edits=1, min_part_len=2
        )
        control = best_surprise_for_mode(
            Mode.from_word(row.control_word), ("a", "b"), max_part_len=3, max_edits=1, min_part_len=2
        )
        assert witness is not None and witness.score == row.structured_gap
        assert witness.part.word == row.witness_part
        assert control is None and row.control_gap == 0.0
        assert row.structured_gap > 0.0
        assert row.status == "separated"
        assert row.claim == "executable-certificate"
        assert "no universal" in row.boundary


def test_baseline_caught_rows_are_negative_controls(build: CorpusBuild):
    caught = list(build.caught_rows)
    assert len(caught) == 8
    assert [row.row_id for row in caught] == [f"S7-CORPUS-C{index:03d}" for index in range(1, 9)]
    for row in caught:
        left = classical_baseline_signature(row.structured_word)
        right = classical_baseline_signature(row.control_word)
        assert left.comparable_key() != right.comparable_key()
        assert row.baseline_equal is False
        assert row.catching_baselines
        assert set(row.catching_baselines) <= set(BASELINE_FAMILIES)
        assert row.catching_baselines == _expected_catching(row.structured_word, row.control_word)
        assert row.status == "caught"
        assert row.claim == "executable-certificate"
        assert "no observer-gap claim" in row.boundary
    gaps = {(row.structured_word, row.control_word) for row in caught}
    assert len(gaps) == 8


def test_both_row_kinds_are_present_in_pair_rows(build: CorpusBuild):
    rows = surprise_corpus_rows()
    kinds = {row.kind for row in rows}
    assert kinds == {"baseline-blind", "baseline-caught"}
    assert len(rows) == 15
    assert all(row.claim == "executable-certificate" for row in rows)


def test_obstruction_rows_are_well_formed(build: CorpusBuild):
    rows = corpus_obstruction_rows()
    assert rows == build.obstruction_rows
    assert [row.row_id for row in rows] == [f"S7-CORPUS-O{index:03d}" for index in range(1, 6)]
    assert [(row.slice_name, row.scanned_words, row.colliding_groups) for row in rows] == [
        ("expanded-signature whole corpus", 640, 14),
        ("length-6 slice", 53, 16),
        ("length-9 slice", 108, 19),
        ("length-10 slice", 113, 22),
        ("length-11 slice", 117, 17),
    ]
    for row in rows:
        assert row.split_pairs == 0
        assert row.scanned_words > 0
        assert row.colliding_groups >= 0
        assert row.status == "obstruction"
        assert row.claim == "obstruction"
        assert "not impossibility" in row.boundary


def test_expanded_slice_obstruction_recomputes_independently(build: CorpusBuild):
    groups: dict[tuple[object, ...], list[str]] = defaultdict(list)
    for word in build.words:
        groups[expanded_classical_signature(word).comparable_key()].append(word)
    colliding = sum(len(rows) > 1 for rows in groups.values())
    splits = 0
    for rows in groups.values():
        positives = [word for word in rows if _word_gap(word) > 0]
        zeros = [word for word in rows if _word_gap(word) == 0]
        splits += len(positives) * len(zeros)
    assert colliding == 14
    assert splits == 0
    obstruction = build.obstruction_rows[0]
    assert obstruction.slice_name == "expanded-signature whole corpus"
    assert obstruction.colliding_groups == colliding
    assert obstruction.split_pairs == splits


def test_length_slices_with_splits_have_no_obstruction_row(build: CorpusBuild):
    obstructed = {row.slice_name for row in build.obstruction_rows}
    assert "length-7 slice" not in obstructed
    assert "length-8 slice" not in obstructed
    assert "length-12 slice" not in obstructed
    blind_lengths = {len(row.structured_word) for row in build.blind_rows}
    assert blind_lengths == {7, 8, 12}


def test_checklist_names_seed_baselines_and_boundary():
    text = "\n".join(surprise_corpus_checklist())
    assert "seed" in text
    assert "496" in text
    assert "baseline" in text
    assert "obstruction" in text
    assert "no universal" in text


def test_generate_corpus_rejects_bad_parameters():
    with pytest.raises(ValueError):
        generate_corpus(min_len=0)
    with pytest.raises(ValueError):
        generate_corpus(min_len=9, max_len=6)
    with pytest.raises(ValueError):
        generate_corpus(word_count=0)
    with pytest.raises(ValueError):
        generate_corpus(word_count=100, min_len=1, max_len=2)
    with pytest.raises(ValueError):
        build_corpus(max_pair_rows=-1)
    with pytest.raises(ValueError):
        build_corpus(max_caught_rows=-1)
