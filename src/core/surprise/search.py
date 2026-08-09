"""Finite search ledger for observer-gap surprise under stronger baselines."""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from itertools import product
import logging
from ..numbers.modes import Mode
from ..surprise import best_surprise_for_mode
from .separation import EXPANDED_BASELINE_FAMILIES, expanded_classical_signature

logger = logging.getLogger(__name__)
PAIRWISE_BASELINE_FAMILIES = ("row count", "single-bit marginals", "pairwise joint marginals")

@dataclass(frozen=True)
class WordSurpriseScore:
    """One word with its best Veyra surprise score under the declared hidden observer."""
    word: str
    score: float
    witness_part: str

@dataclass(frozen=True)
class SurpriseSearchRow:
    """Bounded exhaustive search result against a declared classical baseline family."""
    search_id: str
    alphabet: tuple[str, ...]
    min_len: int
    max_len: int
    baseline_family: tuple[str, ...]
    scanned_words: int
    signature_groups: int
    colliding_signature_groups: int
    split_signature_groups: int
    robust_pairs: int
    status: str
    boundary: str

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready search row."""
        logger.debug("SurpriseSearchRow.as_dict entry search_id=%s", self.search_id)
        result = {
            "search_id": self.search_id,
            "alphabet": self.alphabet,
            "min_len": self.min_len,
            "max_len": self.max_len,
            "baseline_family": self.baseline_family,
            "scanned_words": self.scanned_words,
            "signature_groups": self.signature_groups,
            "colliding_signature_groups": self.colliding_signature_groups,
            "split_signature_groups": self.split_signature_groups,
            "robust_pairs": self.robust_pairs,
            "status": self.status,
            "boundary": self.boundary,
        }
        logger.debug("SurpriseSearchRow.as_dict exit result=%r", result)
        return result

@dataclass(frozen=True)
class PairwiseBaselineSignature:
    """Classical baseline signature for finite 3-bit tables under pairwise observers."""
    table_id: str
    row_count: int
    marginals: tuple[tuple[int, int, int], ...]
    pairwise_counts: tuple[tuple[tuple[int, int], tuple[tuple[str, int], ...]], ...]

    def comparable_key(self) -> tuple[object, ...]:
        """Return the comparison key for pairwise-blind hidden-correlation rows."""
        logger.debug("PairwiseBaselineSignature.comparable_key entry table_id=%s", self.table_id)
        result = (self.row_count, self.marginals, self.pairwise_counts)
        logger.debug("PairwiseBaselineSignature.comparable_key exit result=%r", result)
        return result

@dataclass(frozen=True)
class HiddenCorrelationRow:
    """Finite row where pairwise observers are blind but a global parity observer separates."""
    correlation_id: str
    structured_table: tuple[str, ...]
    control_table: tuple[str, ...]
    baseline_family: tuple[str, ...]
    baseline_equal: bool
    structured_parity_counts: tuple[tuple[str, int], ...]
    control_parity_counts: tuple[tuple[str, int], ...]
    structured_gap: int
    control_gap: int
    hidden_observer: str
    status: str
    boundary: str

def _binary_words(alphabet: tuple[str, ...], length: int) -> tuple[str, ...]:
    """Return all finite words of one length over the alphabet."""
    logger.debug("_binary_words entry alphabet=%r length=%d", alphabet, length)
    result = tuple("".join(chars) for chars in product(alphabet, repeat=length))
    logger.debug("_binary_words exit count=%d", len(result))
    return result

def _word_surprise_score(word: str) -> WordSurpriseScore:
    """Return the best surprise score and witness part for one word."""
    logger.debug("_word_surprise_score entry word=%s", word)
    witness = best_surprise_for_mode(Mode.from_word(word), ("a", "b"), max_part_len=3, max_edits=1, min_part_len=2)
    result = WordSurpriseScore(word, 0.0 if witness is None else witness.score, "" if witness is None else witness.part.word)
    logger.debug("_word_surprise_score exit result=%r", result)
    return result

def expanded_baseline_search_row(min_len: int = 4, max_len: int = 8, alphabet: tuple[str, ...] = ("a", "b")) -> SurpriseSearchRow:
    """Exhaustively search for expanded-baseline-blind surprise splits in a finite corpus."""
    logger.debug("expanded_baseline_search_row entry min_len=%d max_len=%d alphabet=%r", min_len, max_len, alphabet)
    if min_len < 1 or max_len < min_len:
        logger.error("expanded_baseline_search_row invalid bounds min_len=%d max_len=%d", min_len, max_len)
        raise ValueError("expected 1 <= min_len <= max_len")
    if alphabet != ("a", "b"):
        logger.error("expanded_baseline_search_row unsupported alphabet=%r", alphabet)
        raise ValueError("S3 search currently supports the binary alphabet ('a', 'b')")
    groups: dict[tuple[object, ...], list[WordSurpriseScore]] = defaultdict(list)
    scanned = 0
    for length in range(min_len, max_len + 1):
        for word in _binary_words(alphabet, length):
            scanned += 1
            key = expanded_classical_signature(word).comparable_key()
            groups[key].append(_word_surprise_score(word))
    collisions = sum(len(rows) > 1 for rows in groups.values())
    split_groups = 0; robust_pairs = 0
    for rows in groups.values():
        positives = [row for row in rows if row.score > 0]
        zeros = [row for row in rows if row.score == 0]
        if positives and zeros:
            split_groups += 1; robust_pairs += len(positives) * len(zeros)
    boundary = "finite binary search only; no-expanded-blind split here is not impossibility"
    status = "no-expanded-blind-surprise-split" if robust_pairs == 0 else "candidate-found"
    result = SurpriseSearchRow("S3-SEARCH-001", alphabet, min_len, max_len, EXPANDED_BASELINE_FAMILIES, scanned, len(groups), collisions, split_groups, robust_pairs, status, boundary)
    logger.debug("expanded_baseline_search_row exit result=%r", result)
    return result

def _validate_bit_table(table: tuple[str, ...]) -> None:
    """Validate a finite table of 3-bit rows."""
    logger.debug("_validate_bit_table entry rows=%d", len(table))
    if not table or any(len(row) != 3 or set(row) - {"0", "1"} for row in table):
        logger.error("_validate_bit_table invalid table=%r", table)
        raise ValueError("expected a non-empty table of 3-bit strings")
    logger.debug("_validate_bit_table exit ok")

def _marginal_counts(table: tuple[str, ...]) -> tuple[tuple[int, int, int], ...]:
    """Return per-column zero/one counts."""
    logger.debug("_marginal_counts entry rows=%d", len(table))
    _validate_bit_table(table)
    result = tuple((column, sum(row[column] == "0" for row in table), sum(row[column] == "1" for row in table)) for column in range(3))
    logger.debug("_marginal_counts exit result=%r", result)
    return result

def _pairwise_counts(table: tuple[str, ...]) -> tuple[tuple[tuple[int, int], tuple[tuple[str, int], ...]], ...]:
    """Return pairwise joint counts for all coordinate pairs."""
    logger.debug("_pairwise_counts entry rows=%d", len(table))
    _validate_bit_table(table)
    pairs = ((0, 1), (0, 2), (1, 2)); outcomes = ("00", "01", "10", "11")
    result = tuple((pair, tuple((bits, sum(row[pair[0]] + row[pair[1]] == bits for row in table)) for bits in outcomes)) for pair in pairs)
    logger.debug("_pairwise_counts exit result=%r", result)
    return result

def _parity_counts(table: tuple[str, ...]) -> tuple[tuple[str, int], ...]:
    """Return even/odd triple parity counts."""
    logger.debug("_parity_counts entry rows=%d", len(table))
    _validate_bit_table(table)
    even = sum(sum(int(bit) for bit in row) % 2 == 0 for row in table)
    result = (("even", even), ("odd", len(table) - even))
    logger.debug("_parity_counts exit result=%r", result)
    return result

def pairwise_baseline_signature(table_id: str, table: tuple[str, ...]) -> PairwiseBaselineSignature:
    """Return the finite pairwise baseline signature for one 3-bit table."""
    logger.debug("pairwise_baseline_signature entry table_id=%s rows=%d", table_id, len(table))
    result = PairwiseBaselineSignature(table_id, len(table), _marginal_counts(table), _pairwise_counts(table))
    logger.debug("pairwise_baseline_signature exit result=%r", result)
    return result

def xor_hidden_correlation_row() -> HiddenCorrelationRow:
    """Return the first non-local XOR/parity hidden-correlation separation row."""
    logger.debug("xor_hidden_correlation_row entry")
    structured = ("000", "000", "011", "011", "101", "101", "110", "110")
    control = ("000", "001", "010", "011", "100", "101", "110", "111")
    left = pairwise_baseline_signature("xor-even-duplicated", structured)
    right = pairwise_baseline_signature("full-cube-control", control)
    left_parity = _parity_counts(structured); right_parity = _parity_counts(control)
    baseline_equal = left.comparable_key() == right.comparable_key()
    structured_gap = abs(left_parity[0][1] - left_parity[1][1])
    control_gap = abs(right_parity[0][1] - right_parity[1][1])
    boundary = "finite pairwise-baseline separation only; triple parity is a classical high-order observer, not a universal impossibility"
    status = "pairwise-blind-hidden-correlation" if baseline_equal and structured_gap > control_gap else "blocked"
    result = HiddenCorrelationRow("S4-XOR-001", structured, control, PAIRWISE_BASELINE_FAMILIES, baseline_equal, left_parity, right_parity, structured_gap, control_gap, "triple parity observer", status, boundary)
    logger.debug("xor_hidden_correlation_row exit result=%r", result)
    return result

def hidden_correlation_rows() -> tuple[HiddenCorrelationRow, ...]:
    """Return finite non-local hidden-correlation surprise rows."""
    logger.debug("hidden_correlation_rows entry")
    result = (xor_hidden_correlation_row(),)
    logger.debug("hidden_correlation_rows exit count=%d", len(result))
    return result

def surprise_search_summary() -> dict[str, int]:
    """Return compact counters for the bounded expanded-baseline surprise search."""
    logger.debug("surprise_search_summary entry")
    row = expanded_baseline_search_row()
    hidden = hidden_correlation_rows()
    result = {
        "search_rows": 1,
        "scanned_words": row.scanned_words,
        "signature_groups": row.signature_groups,
        "colliding_signature_groups": row.colliding_signature_groups,
        "split_signature_groups": row.split_signature_groups,
        "robust_pairs": row.robust_pairs,
        "hidden_correlation_rows": len(hidden),
        "pairwise_blind_hidden_splits": sum(item.status == "pairwise-blind-hidden-correlation" for item in hidden),
        "overclaims": (0 if "not impossibility" in row.boundary else 1) + sum("not a universal" not in item.boundary for item in hidden),
    }
    logger.debug("surprise_search_summary exit result=%r", result)
    return result

def surprise_search_checklist() -> tuple[str, ...]:
    """Return the acceptance checklist for finite surprise search rows."""
    logger.debug("surprise_search_checklist entry")
    result = ("declare finite corpus", "declare baseline signature", "group baseline collisions", "compare Veyra gap inside collisions", "test non-local hidden-correlation families", "record negative results as bounded, not impossible")
    logger.debug("surprise_search_checklist exit count=%d", len(result))
    return result
