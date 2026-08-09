"""De Bruijn trail rows for observer-gap surprise."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)
DEBRUIJN_BASELINE_FAMILIES = ("length", "alphabet", "cyclic window counts up to order 3")

@dataclass(frozen=True)
class DeBruijnBaselineSignature:
    """Finite signature containing cyclic window-count baselines."""
    word_id: str
    word: str
    max_window: int
    window_counts: tuple[tuple[int, tuple[tuple[str, int], ...]], ...]

    def comparable_key(self) -> tuple[object, ...]:
        """Return the de Bruijn baseline comparison key."""
        logger.debug("DeBruijnBaselineSignature.comparable_key entry word_id=%s", self.word_id)
        result = (len(self.word), tuple(sorted(set(self.word))), self.max_window, self.window_counts)
        logger.debug("DeBruijnBaselineSignature.comparable_key exit result=%r", result)
        return result

@dataclass(frozen=True)
class DeBruijnTrailRow:
    """Finite row where local window counts match but trail adjacency separates."""
    row_id: str
    structured_word: str
    control_word: str
    baseline_family: tuple[str, ...]
    baseline_equal: bool
    structured_trail: tuple[tuple[str, str], ...]
    control_trail: tuple[tuple[str, str], ...]
    common_transitions: int
    divergent_transitions: int
    hidden_observer: str
    status: str
    boundary: str

def _validate_binary_cycle(word: str) -> None:
    """Validate a non-empty binary cyclic word."""
    logger.debug("_validate_binary_cycle entry word=%s", word)
    if not word or set(word) - {"0", "1"}:
        logger.error("_validate_binary_cycle invalid word=%r", word)
        raise ValueError("expected a non-empty binary word")
    logger.debug("_validate_binary_cycle exit ok")

def cyclic_windows(word: str, width: int) -> tuple[str, ...]:
    """Return cyclic windows of a fixed width."""
    logger.debug("cyclic_windows entry word=%s width=%d", word, width)
    _validate_binary_cycle(word)
    if width < 1 or width > len(word):
        logger.error("cyclic_windows invalid width=%d len=%d", width, len(word))
        raise ValueError("expected 1 <= width <= len(word)")
    n = len(word)
    result = tuple("".join(word[(index + offset) % n] for offset in range(width)) for index in range(n))
    logger.debug("cyclic_windows exit count=%d", len(result))
    return result

def cyclic_window_count_signature(word: str, max_window: int = 3) -> tuple[tuple[int, tuple[tuple[str, int], ...]], ...]:
    """Return sorted cyclic window counts for widths 1..max_window."""
    logger.debug("cyclic_window_count_signature entry word=%s max_window=%d", word, max_window)
    _validate_binary_cycle(word)
    if max_window < 1 or max_window >= len(word):
        logger.error("cyclic_window_count_signature invalid max_window=%d len=%d", max_window, len(word))
        raise ValueError("expected 1 <= max_window < len(word)")
    result = tuple((width, tuple(sorted(Counter(cyclic_windows(word, width)).items()))) for width in range(1, max_window + 1))
    logger.debug("cyclic_window_count_signature exit groups=%d", len(result))
    return result

def debruijn_baseline_signature(word_id: str, word: str, max_window: int = 3) -> DeBruijnBaselineSignature:
    """Return the finite de Bruijn local-window baseline signature."""
    logger.debug("debruijn_baseline_signature entry word_id=%s word=%s max_window=%d", word_id, word, max_window)
    result = DeBruijnBaselineSignature(word_id, word, max_window, cyclic_window_count_signature(word, max_window))
    logger.debug("debruijn_baseline_signature exit result=%r", result)
    return result

def debruijn_trail_adjacencies(word: str, edge_width: int = 3) -> tuple[tuple[str, str], ...]:
    """Return cyclic adjacency pairs between consecutive de Bruijn edges."""
    logger.debug("debruijn_trail_adjacencies entry word=%s edge_width=%d", word, edge_width)
    windows = cyclic_windows(word, edge_width)
    result = tuple((windows[index], windows[(index + 1) % len(windows)]) for index in range(len(windows)))
    logger.debug("debruijn_trail_adjacencies exit count=%d", len(result))
    return result

def _transition_overlap(left: tuple[tuple[str, str], ...], right: tuple[tuple[str, str], ...]) -> tuple[int, int]:
    """Return common and divergent transition counts for two trails."""
    logger.debug("_transition_overlap entry left=%d right=%d", len(left), len(right))
    left_counts = Counter(left); right_counts = Counter(right)
    common = sum((left_counts & right_counts).values())
    divergent = sum((left_counts - right_counts).values()) + sum((right_counts - left_counts).values())
    logger.debug("_transition_overlap exit common=%d divergent=%d", common, divergent)
    return common, divergent

def debruijn_trail_hidden_row() -> DeBruijnTrailRow:
    """Return S6: same order-3 de Bruijn local counts, different trail order."""
    logger.debug("debruijn_trail_hidden_row entry")
    structured = "00010111"
    control = "00011101"
    left = debruijn_baseline_signature("db-a", structured)
    right = debruijn_baseline_signature("db-b", control)
    baseline_equal = left.comparable_key() == right.comparable_key()
    left_trail = debruijn_trail_adjacencies(structured)
    right_trail = debruijn_trail_adjacencies(control)
    common, divergent = _transition_overlap(left_trail, right_trail)
    boundary = "finite order-3 de Bruijn-window separation only; trail adjacency is a classical order-4 graph observer, not a universal impossibility"
    status = "window-blind-trail-split" if baseline_equal and divergent > 0 else "blocked"
    result = DeBruijnTrailRow("S6-DEBRUIJN-001", structured, control, DEBRUIJN_BASELINE_FAMILIES, baseline_equal, left_trail, right_trail, common, divergent, "de Bruijn trail-adjacency observer", status, boundary)
    logger.debug("debruijn_trail_hidden_row exit result=%r", result)
    return result

def debruijn_hidden_summary() -> dict[str, int]:
    """Return compact S6 de Bruijn hidden-trail counters."""
    logger.debug("debruijn_hidden_summary entry")
    row = debruijn_trail_hidden_row()
    result = {"rows": 1, "baseline_equal": int(row.baseline_equal), "hidden_splits": int(row.status == "window-blind-trail-split"), "common_transitions": row.common_transitions, "divergent_transitions": row.divergent_transitions, "overclaims": 0 if "not a universal" in row.boundary else 1}
    logger.debug("debruijn_hidden_summary exit result=%r", result)
    return result

def debruijn_hidden_checklist() -> tuple[str, ...]:
    """Return the acceptance checklist for S6 de Bruijn rows."""
    logger.debug("debruijn_hidden_checklist entry")
    result = ("declare cyclic words", "match cyclic window counts up to order 3", "compare trail adjacency", "name order-4 graph observer", "state finite non-impossibility boundary")
    logger.debug("debruijn_hidden_checklist exit count=%d", len(result))
    return result
