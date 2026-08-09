"""Finite observer-gap separation rows for Veyra surprise research."""
from __future__ import annotations
from dataclasses import dataclass
import logging
from ..numbers.modes import Mode
from ..surprise import best_surprise_for_mode

logger = logging.getLogger(__name__)
BASELINE_FAMILIES = ("symbol-count entropy proxy", "lag-1/2 autocorrelation agreement", "LZ78 phrase count")

EXPANDED_BASELINE_FAMILIES = (
    *BASELINE_FAMILIES,
    "block-1/3 frequency entropy-rate proxy",
    "lag-1/4 autocorrelation agreement",
    "cyclic autocorrelation spectral proxy",
    "run-count compression proxy",
)

@dataclass(frozen=True)
class ClassicalBlindSignature:
    """A deliberately bounded classical baseline signature for one finite word."""
    word: str
    symbol_counts: tuple[tuple[str, int], ...]
    lag_agreements: tuple[int, ...]
    lz_phrase_count: int

    def comparable_key(self) -> tuple[tuple[tuple[str, int], ...], tuple[int, ...], int]:
        """Return the comparison key used by the S1 finite separation row."""
        logger.debug("ClassicalBlindSignature.comparable_key entry word=%s", self.word)
        result = (self.symbol_counts, self.lag_agreements, self.lz_phrase_count)
        logger.debug("ClassicalBlindSignature.comparable_key exit result=%r", result)
        return result

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready baseline row."""
        logger.debug("ClassicalBlindSignature.as_dict entry word=%s", self.word)
        result = {"word": self.word, "symbol_counts": self.symbol_counts, "lag_agreements": self.lag_agreements, "lz_phrase_count": self.lz_phrase_count}
        logger.debug("ClassicalBlindSignature.as_dict exit result=%r", result)
        return result

@dataclass(frozen=True)
class ExpandedClassicalSignature:
    """A stronger bounded baseline signature for counterexample pressure."""
    word: str
    block_counts: tuple[tuple[int, tuple[tuple[str, int], ...]], ...]
    lag_agreements: tuple[int, ...]
    cyclic_autocorr: tuple[int, ...]
    compression_counts: tuple[tuple[str, int], ...]

    def comparable_key(self) -> tuple[object, ...]:
        """Return the expanded comparison key."""
        logger.debug("ExpandedClassicalSignature.comparable_key entry word=%s", self.word)
        result = (self.block_counts, self.lag_agreements, self.cyclic_autocorr, self.compression_counts)
        logger.debug("ExpandedClassicalSignature.comparable_key exit result=%r", result)
        return result

@dataclass(frozen=True)
class BaselineAuditRow:
    """A row showing whether stronger classical baselines catch an S1 pair."""
    audit_id: str
    structured_word: str
    control_word: str
    expanded_equal: bool
    catching_observers: tuple[str, ...]
    status: str
    boundary: str

@dataclass(frozen=True)
class SurpriseSeparationRow:
    """A finite pair where baseline observers are blind but Veyra surprise separates."""
    separation_id: str
    structured_word: str
    control_word: str
    structured_signature: ClassicalBlindSignature
    control_signature: ClassicalBlindSignature
    baseline_family: tuple[str, ...]
    baseline_equal: bool
    structured_gap: float
    control_gap: float
    witness_part: str
    status: str
    boundary: str

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready separation row."""
        logger.debug("SurpriseSeparationRow.as_dict entry separation_id=%s", self.separation_id)
        result = {
            "separation_id": self.separation_id,
            "structured_word": self.structured_word,
            "control_word": self.control_word,
            "baseline_family": self.baseline_family,
            "baseline_equal": self.baseline_equal,
            "structured_gap": self.structured_gap,
            "control_gap": self.control_gap,
            "witness_part": self.witness_part,
            "status": self.status,
            "boundary": self.boundary,
        }
        logger.debug("SurpriseSeparationRow.as_dict exit result=%r", result)
        return result

def _lz78_phrase_count(word: str) -> int:
    """Return a tiny deterministic LZ78-style phrase count for a finite word."""
    logger.debug("_lz78_phrase_count entry word=%s", word)
    seen: set[str] = set(); phrases = 0; index = 0
    while index < len(word):
        end = index + 1
        while end <= len(word) and word[index:end] in seen:
            end += 1
        seen.add(word[index:min(end, len(word))]); phrases += 1; index = end
    logger.debug("_lz78_phrase_count exit phrases=%d", phrases)
    return phrases

def classical_baseline_signature(word: str, alphabet: tuple[str, ...] = ("a", "b"), max_lag: int = 2) -> ClassicalBlindSignature:
    """Return the bounded classical signature used for current separation claims."""
    logger.debug("classical_baseline_signature entry word=%s max_lag=%d", word, max_lag)
    if not word:
        logger.error("classical_baseline_signature empty word")
        raise ValueError("word must be non-empty")
    counts = tuple((symbol, word.count(symbol)) for symbol in alphabet)
    lags = tuple(sum(1 for index in range(len(word) - lag) if word[index] == word[index + lag]) for lag in range(1, max_lag + 1))
    result = ClassicalBlindSignature(word, counts, lags, _lz78_phrase_count(word))
    logger.debug("classical_baseline_signature exit result=%r", result)
    return result

def canonical_surprise_separation_row() -> SurpriseSeparationRow:
    """Return the first finite observer-gap separation benchmark row."""
    logger.debug("canonical_surprise_separation_row entry")
    structured = "aabaabb"; control = "abbaaab"
    structured_sig = classical_baseline_signature(structured); control_sig = classical_baseline_signature(control)
    witness = best_surprise_for_mode(Mode.from_word(structured), ("a", "b"), max_part_len=3, max_edits=1, min_part_len=2)
    control_witness = best_surprise_for_mode(Mode.from_word(control), ("a", "b"), max_part_len=3, max_edits=1, min_part_len=2)
    baseline_equal = structured_sig.comparable_key() == control_sig.comparable_key()
    structured_gap = 0.0 if witness is None else witness.score
    control_gap = 0.0 if control_witness is None else control_witness.score
    status = "separated" if baseline_equal and witness is not None and control_witness is None else "blocked"
    boundary = "finite S1 separation against three named baselines only; no universal classical-impossibility claim"
    result = SurpriseSeparationRow("S1-OGS-001", structured, control, structured_sig, control_sig, BASELINE_FAMILIES, baseline_equal, structured_gap, control_gap, "" if witness is None else witness.part.word, status, boundary)
    logger.debug("canonical_surprise_separation_row exit result=%r", result)
    return result

def surprise_separation_rows() -> tuple[SurpriseSeparationRow, ...]:
    """Return finite observer-gap separation rows."""
    logger.debug("surprise_separation_rows entry")
    result = (canonical_surprise_separation_row(),)
    logger.debug("surprise_separation_rows exit count=%d", len(result))
    return result


def _block_counts(word: str, width: int) -> tuple[tuple[str, int], ...]:
    """Return sorted finite block counts for one block width."""
    logger.debug("_block_counts entry word=%s width=%d", word, width)
    counts = {word[index:index + width]: 0 for index in range(max(0, len(word) - width + 1))}
    for index in range(max(0, len(word) - width + 1)):
        block = word[index:index + width]
        counts[block] = counts.get(block, 0) + 1
    result = tuple(sorted(counts.items()))
    logger.debug("_block_counts exit count=%d", len(result))
    return result

def _run_count(word: str) -> int:
    """Return the number of maximal constant-symbol runs."""
    logger.debug("_run_count entry word=%s", word)
    result = 1 + sum(word[index] != word[index - 1] for index in range(1, len(word)))
    logger.debug("_run_count exit result=%d", result)
    return result

def _cyclic_autocorr(word: str) -> tuple[int, ...]:
    """Return exact binary cyclic autocorrelation as a spectral-power proxy."""
    logger.debug("_cyclic_autocorr entry word=%s", word)
    values = tuple(1 if char == "a" else -1 for char in word)
    result = tuple(sum(values[index] * values[(index + lag) % len(values)] for index in range(len(values))) for lag in range(1, len(values)))
    logger.debug("_cyclic_autocorr exit count=%d", len(result))
    return result

def expanded_classical_signature(word: str, max_block: int = 3, max_lag: int = 4) -> ExpandedClassicalSignature:
    """Return a stronger finite baseline signature for S1 counterexample audits."""
    logger.debug("expanded_classical_signature entry word=%s", word)
    if not word:
        logger.error("expanded_classical_signature empty word")
        raise ValueError("word must be non-empty")
    blocks = tuple((width, _block_counts(word, width)) for width in range(1, max_block + 1))
    lags = tuple(sum(1 for index in range(len(word) - lag) if word[index] == word[index + lag]) for lag in range(1, min(max_lag, len(word) - 1) + 1))
    compression = (("lz78", _lz78_phrase_count(word)), ("runs", _run_count(word)))
    result = ExpandedClassicalSignature(word, blocks, lags, _cyclic_autocorr(word), compression)
    logger.debug("expanded_classical_signature exit result=%r", result)
    return result

def _catching_observers(left: ExpandedClassicalSignature, right: ExpandedClassicalSignature) -> tuple[str, ...]:
    """Return expanded observers that distinguish a pair."""
    logger.debug("_catching_observers entry left=%s right=%s", left.word, right.word)
    rows: list[str] = []
    if left.block_counts != right.block_counts:
        rows.append("block-frequency entropy-rate proxy")
    if left.lag_agreements != right.lag_agreements:
        rows.append("higher-lag autocorrelation")
    if left.cyclic_autocorr != right.cyclic_autocorr:
        rows.append("cyclic spectral proxy")
    if left.compression_counts != right.compression_counts:
        rows.append("compression proxy")
    result = tuple(rows)
    logger.debug("_catching_observers exit result=%r", result)
    return result

def expanded_baseline_audit_rows() -> tuple[BaselineAuditRow, ...]:
    """Return rows where stronger baselines pressure or catch S1 claims."""
    logger.debug("expanded_baseline_audit_rows entry")
    base = canonical_surprise_separation_row()
    left = expanded_classical_signature(base.structured_word)
    right = expanded_classical_signature(base.control_word)
    catching = _catching_observers(left, right)
    boundary = "finite counterexample pressure: stronger classical baselines catch this S1 toy pair"
    row = BaselineAuditRow("S2-AUDIT-001", base.structured_word, base.control_word, left.comparable_key() == right.comparable_key(), catching, "caught" if catching else "still-blind", boundary)
    result = (row,)
    logger.debug("expanded_baseline_audit_rows exit count=%d", len(result))
    return result

def surprise_separation_summary() -> dict[str, int]:
    """Return compact S1 separation counters."""
    logger.debug("surprise_separation_summary entry")
    rows = surprise_separation_rows()
    audits = expanded_baseline_audit_rows()
    result = {
        "rows": len(rows),
        "baseline_blind": sum(row.baseline_equal for row in rows),
        "separated": sum(row.status == "separated" for row in rows),
        "baseline_families": len(BASELINE_FAMILIES),
        "expanded_families": len(EXPANDED_BASELINE_FAMILIES),
        "audit_rows": len(audits),
        "caught_by_expanded": sum(row.status == "caught" for row in audits),
        "overclaims": sum("universal" not in row.boundary for row in rows),
    }
    logger.debug("surprise_separation_summary exit result=%r", result)
    return result

def surprise_separation_checklist() -> tuple[str, ...]:
    """Return the current observer-gap separation acceptance checklist."""
    logger.debug("surprise_separation_checklist entry")
    result = ("declare finite baseline family", "provide baseline-blind pair", "show positive Veyra gap only on structured side", "expand baselines and record caught counterexamples", "state no universal classical-impossibility claim")
    logger.debug("surprise_separation_checklist exit count=%d", len(result))
    return result
