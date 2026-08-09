"""Seeded larger separation corpus for observer-gap surprise (S1 corpus track).

Classifies a deterministic seeded corpus larger than the S3 496-word search
into baseline-blind pair rows and baseline-caught negative controls, with
obstruction rows for split-free slices. Finite boundaries only: no universal
classical-impossibility claim.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import logging
import random

from ..numbers.modes import Mode
from ..surprise import best_surprise_for_mode
from .separation import BASELINE_FAMILIES, classical_baseline_signature, expanded_classical_signature

logger = logging.getLogger(__name__)

DEFAULT_SEED = 20260708
DEFAULT_WORD_COUNT = 640
DEFAULT_MIN_LEN = 6
DEFAULT_MAX_LEN = 12
MAX_PAIR_ROWS = 16
MAX_CAUGHT_ROWS = 8

PAIR_BOUNDARY = "finite seeded-corpus separation against the three named S1 baselines only; no universal classical-impossibility claim"
CONTROL_BOUNDARY = "negative control: at least one named S1 baseline already separates this pair; no observer-gap claim"
OBSTRUCTION_BOUNDARY = "bounded negative corpus slice only; no split here is not impossibility"
SUMMARY_BOUNDARY = "exact counts for one finite seeded corpus against named S1 baselines only; no universal classical-impossibility claim"


@dataclass(frozen=True)
class CorpusPairRow:
    """One classified pair: baseline-blind split or baseline-caught control."""

    row_id: str
    kind: str
    structured_word: str
    control_word: str
    baseline_family: tuple[str, ...]
    baseline_equal: bool
    catching_baselines: tuple[str, ...]
    structured_gap: float
    control_gap: float
    witness_part: str
    status: str
    claim: str
    boundary: str

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready pair row."""
        return asdict(self)


@dataclass(frozen=True)
class CorpusObstructionRow:
    """Explicit obstruction row for a corpus slice with no surprise split."""

    row_id: str
    slice_name: str
    scanned_words: int
    colliding_groups: int
    split_pairs: int
    status: str
    claim: str
    boundary: str

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready obstruction row."""
        return asdict(self)


@dataclass(frozen=True)
class CorpusBuild:
    """Full deterministic classification of one seeded corpus."""

    seed: int
    min_len: int
    max_len: int
    words: tuple[str, ...]
    signature_groups: int
    colliding_groups: int
    positive_gap_words: int
    blind_pairs_found: int
    blind_rows: tuple[CorpusPairRow, ...]
    caught_rows: tuple[CorpusPairRow, ...]
    obstruction_rows: tuple[CorpusObstructionRow, ...]


@dataclass(frozen=True)
class CorpusSummaryRow:
    """Summary row with exact counts and a deterministic corpus digest."""

    summary_id: str
    seed: int
    min_len: int
    max_len: int
    corpus_words: int
    baseline_family: tuple[str, ...]
    signature_groups: int
    colliding_groups: int
    positive_gap_words: int
    blind_pairs_found: int
    blind_rows: int
    caught_rows: int
    obstruction_rows: int
    digest: str
    status: str
    claim: str
    boundary: str

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready summary row."""
        return asdict(self)


def generate_corpus(
    seed: int = DEFAULT_SEED, word_count: int = DEFAULT_WORD_COUNT, min_len: int = DEFAULT_MIN_LEN, max_len: int = DEFAULT_MAX_LEN
) -> tuple[str, ...]:
    """Return a deterministic seeded corpus of unique binary words."""
    logger.debug("generate_corpus entry seed=%d word_count=%d", seed, word_count)
    if min_len < 1 or max_len < min_len:
        logger.error("generate_corpus invalid bounds min_len=%d max_len=%d", min_len, max_len)
        raise ValueError("expected 1 <= min_len <= max_len")
    available = sum(2**length for length in range(min_len, max_len + 1))
    if word_count < 1 or word_count > available:
        logger.error("generate_corpus invalid word_count=%d available=%d", word_count, available)
        raise ValueError("expected 1 <= word_count <= available words")
    rng = random.Random(seed)
    words: set[str] = set()
    while len(words) < word_count:
        length = rng.randint(min_len, max_len)
        words.add("".join(rng.choice("ab") for _ in range(length)))
    logger.debug("generate_corpus exit count=%d", len(words))
    return tuple(sorted(words))


def _word_gap(word: str) -> tuple[float, str]:
    """Return the best Veyra edit-lift surprise gap and witness part for one word."""
    witness = best_surprise_for_mode(Mode.from_word(word), ("a", "b"), max_part_len=3, max_edits=1, min_part_len=2)
    return (0.0, "") if witness is None else (witness.score, witness.part.word)


def _baseline_key(word: str) -> tuple[object, ...]:
    """Return the declared S1 baseline comparison key for one word."""
    return classical_baseline_signature(word).comparable_key()


def _catching_baselines(left: str, right: str) -> tuple[str, ...]:
    """Return the declared S1 baselines that separate a word pair."""
    left_sig = classical_baseline_signature(left)
    right_sig = classical_baseline_signature(right)
    rows: list[str] = []
    if left_sig.symbol_counts != right_sig.symbol_counts:
        rows.append("symbol-count entropy proxy")
    if left_sig.lag_agreements != right_sig.lag_agreements:
        rows.append("lag-1/2 autocorrelation agreement")
    if left_sig.lz_phrase_count != right_sig.lz_phrase_count:
        rows.append("LZ78 phrase count")
    return tuple(rows)


def _split_counts(
    words: tuple[str, ...], gaps: dict[str, tuple[float, str]], key_fn: Callable[[str], tuple[object, ...]]
) -> tuple[int, int, int]:
    """Return group count, colliding groups, and surprise-split pairs under one signature."""
    groups: dict[tuple[object, ...], list[str]] = defaultdict(list)
    for word in words:
        groups[key_fn(word)].append(word)
    splits = 0
    for rows in groups.values():
        positives = [word for word in rows if gaps[word][0] > 0]
        zeros = [word for word in rows if gaps[word][0] == 0]
        splits += len(positives) * len(zeros)
    return len(groups), sum(len(rows) > 1 for rows in groups.values()), splits


def _obstruction_rows(
    words: tuple[str, ...], gaps: dict[str, tuple[float, str]], min_len: int, max_len: int
) -> tuple[CorpusObstructionRow, ...]:
    """Return obstruction rows for corpus slices where no surprise split exists."""
    slices = [
        ("expanded-signature whole corpus", words, lambda word: expanded_classical_signature(word).comparable_key())
    ]
    slices += [
        (f"length-{length} slice", tuple(word for word in words if len(word) == length), _baseline_key)
        for length in range(min_len, max_len + 1)
    ]
    rows: list[CorpusObstructionRow] = []
    for slice_name, slice_words, key_fn in slices:
        _, colliding, splits = _split_counts(slice_words, gaps, key_fn)
        if splits == 0:
            rows.append(CorpusObstructionRow(
                "", slice_name, len(slice_words), colliding, 0, "obstruction", "obstruction", OBSTRUCTION_BOUNDARY
            ))
    return tuple(replace(row, row_id=f"S7-CORPUS-O{index:03d}") for index, row in enumerate(rows, start=1))


def build_corpus(
    seed: int = DEFAULT_SEED, word_count: int = DEFAULT_WORD_COUNT,
    min_len: int = DEFAULT_MIN_LEN, max_len: int = DEFAULT_MAX_LEN,
    max_pair_rows: int = MAX_PAIR_ROWS, max_caught_rows: int = MAX_CAUGHT_ROWS,
) -> CorpusBuild:
    """Classify one seeded corpus into blind rows, caught rows, and obstructions."""
    logger.debug("build_corpus entry seed=%d word_count=%d", seed, word_count)
    if max_pair_rows < 0 or max_caught_rows < 0:
        logger.error("build_corpus invalid caps max_pair_rows=%d max_caught_rows=%d", max_pair_rows, max_caught_rows)
        raise ValueError("row caps must be non-negative")
    words = generate_corpus(seed, word_count, min_len, max_len)
    gaps = {word: _word_gap(word) for word in words}
    groups: dict[tuple[object, ...], list[str]] = defaultdict(list)
    for word in words:
        groups[_baseline_key(word)].append(word)
    keys = sorted(groups)
    found = [
        (structured, control)
        for key in keys
        for structured in [word for word in groups[key] if gaps[word][0] > 0]
        for control in [word for word in groups[key] if gaps[word][0] == 0]
    ]
    blind: list[CorpusPairRow] = []
    for index, (structured, control) in enumerate(found[:max_pair_rows], start=1):
        blind.append(CorpusPairRow(
            f"S7-CORPUS-B{index:03d}", "baseline-blind", structured, control, BASELINE_FAMILIES,
            _baseline_key(structured) == _baseline_key(control), (), gaps[structured][0], gaps[control][0],
            gaps[structured][1], "separated", "executable-certificate", PAIR_BOUNDARY,
        ))
    caught: list[CorpusPairRow] = []
    for index in range(min(len(keys) - 1, max_caught_rows)):
        left, right = groups[keys[index]][0], groups[keys[index + 1]][0]
        caught.append(CorpusPairRow(
            f"S7-CORPUS-C{index + 1:03d}", "baseline-caught", left, right, BASELINE_FAMILIES,
            _baseline_key(left) == _baseline_key(right), _catching_baselines(left, right), gaps[left][0], gaps[right][0],
            "", "caught", "executable-certificate", CONTROL_BOUNDARY,
        ))
    logger.debug("build_corpus exit blind=%d caught=%d", len(blind), len(caught))
    return CorpusBuild(
        seed, min_len, max_len, words, len(groups), sum(len(rows) > 1 for rows in groups.values()),
        sum(gaps[word][0] > 0 for word in words), len(found), tuple(blind), tuple(caught),
        _obstruction_rows(words, gaps, min_len, max_len),
    )


def corpus_digest(build: CorpusBuild) -> str:
    """Return a deterministic SHA-256 digest binding parameters and all rows."""
    payload = {
        "seed": build.seed, "min_len": build.min_len, "max_len": build.max_len, "words": build.words,
        "blind_rows": [row.as_dict() for row in build.blind_rows],
        "caught_rows": [row.as_dict() for row in build.caught_rows],
        "obstruction_rows": [row.as_dict() for row in build.obstruction_rows],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def surprise_corpus_rows(
    seed: int = DEFAULT_SEED, word_count: int = DEFAULT_WORD_COUNT, min_len: int = DEFAULT_MIN_LEN, max_len: int = DEFAULT_MAX_LEN
) -> tuple[CorpusPairRow, ...]:
    """Return classified pair rows (baseline-blind first, then baseline-caught)."""
    build = build_corpus(seed, word_count, min_len, max_len)
    return (*build.blind_rows, *build.caught_rows)


def corpus_obstruction_rows(
    seed: int = DEFAULT_SEED, word_count: int = DEFAULT_WORD_COUNT, min_len: int = DEFAULT_MIN_LEN, max_len: int = DEFAULT_MAX_LEN
) -> tuple[CorpusObstructionRow, ...]:
    """Return obstruction rows for corpus slices where no surprise split exists."""
    return build_corpus(seed, word_count, min_len, max_len).obstruction_rows


def surprise_corpus_summary(
    seed: int = DEFAULT_SEED, word_count: int = DEFAULT_WORD_COUNT, min_len: int = DEFAULT_MIN_LEN, max_len: int = DEFAULT_MAX_LEN
) -> CorpusSummaryRow:
    """Return the summary row with exact counts and the corpus digest."""
    logger.debug("surprise_corpus_summary entry seed=%d", seed)
    build = build_corpus(seed, word_count, min_len, max_len)
    result = CorpusSummaryRow(
        "S7-CORPUS-SUMMARY", build.seed, build.min_len, build.max_len, len(build.words),
        BASELINE_FAMILIES, build.signature_groups, build.colliding_groups, build.positive_gap_words,
        build.blind_pairs_found, len(build.blind_rows), len(build.caught_rows), len(build.obstruction_rows),
        corpus_digest(build), "classified", "executable-certificate", SUMMARY_BOUNDARY,
    )
    logger.debug("surprise_corpus_summary exit result=%r", result)
    return result


def surprise_corpus_checklist() -> tuple[str, ...]:
    """Return the acceptance checklist for the seeded separation corpus."""
    return (
        "declare seed and corpus bounds",
        "keep corpus larger than the S3 496-word search",
        "classify baseline-blind and baseline-caught pairs",
        "cross-check every split against the named classical baselines",
        "record obstruction rows for split-free slices",
        "state no universal classical-impossibility claim",
    )
