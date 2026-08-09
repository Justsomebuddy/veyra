"""K-wise hidden-correlation rows for observer-gap surprise."""
from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations, product
import logging

logger = logging.getLogger(__name__)
KWISE_BASELINE_FAMILIES = ("row count", "all coordinate marginals up to order 3")

@dataclass(frozen=True)
class KWiseBaselineSignature:
    """Finite baseline signature containing all joint counts up to max_order."""
    table_id: str
    width: int
    max_order: int
    row_count: int
    joint_counts: tuple[tuple[tuple[int, ...], tuple[tuple[str, int], ...]], ...]

    def comparable_key(self) -> tuple[object, ...]:
        """Return the k-wise baseline comparison key."""
        logger.debug("KWiseBaselineSignature.comparable_key entry table_id=%s", self.table_id)
        result = (self.width, self.max_order, self.row_count, self.joint_counts)
        logger.debug("KWiseBaselineSignature.comparable_key exit result=%r", result)
        return result

@dataclass(frozen=True)
class KWiseHiddenCorrelationRow:
    """Finite row where k-wise observers are blind but global parity separates."""
    correlation_id: str
    width: int
    max_blind_order: int
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

def bit_words(width: int) -> tuple[str, ...]:
    """Return all binary words of a fixed width."""
    logger.debug("bit_words entry width=%d", width)
    if width < 1:
        logger.error("bit_words invalid width=%d", width)
        raise ValueError("width must be positive")
    result = tuple("".join(bits) for bits in product("01", repeat=width))
    logger.debug("bit_words exit count=%d", len(result))
    return result

def _validate_table(table: tuple[str, ...], width: int) -> None:
    """Validate a non-empty binary table of fixed width."""
    logger.debug("_validate_table entry width=%d rows=%d", width, len(table))
    if width < 1 or not table or any(len(row) != width or set(row) - {"0", "1"} for row in table):
        logger.error("_validate_table invalid width=%d table=%r", width, table)
        raise ValueError("expected a non-empty fixed-width binary table")
    logger.debug("_validate_table exit ok")

def _joint_counts(table: tuple[str, ...], subset: tuple[int, ...]) -> tuple[tuple[str, int], ...]:
    """Return joint outcome counts for one coordinate subset."""
    logger.debug("_joint_counts entry subset=%r rows=%d", subset, len(table))
    outcomes = tuple("".join(bits) for bits in product("01", repeat=len(subset)))
    result = tuple((bits, sum("".join(row[index] for index in subset) == bits for row in table)) for bits in outcomes)
    logger.debug("_joint_counts exit outcomes=%d", len(result))
    return result

def kwise_baseline_signature(table_id: str, table: tuple[str, ...], width: int = 4, max_order: int = 3) -> KWiseBaselineSignature:
    """Return all joint counts up to max_order for a finite binary table."""
    logger.debug("kwise_baseline_signature entry table_id=%s width=%d max_order=%d", table_id, width, max_order)
    _validate_table(table, width)
    if max_order < 1 or max_order >= width:
        logger.error("kwise_baseline_signature invalid max_order=%d width=%d", max_order, width)
        raise ValueError("expected 1 <= max_order < width")
    rows = []
    for order in range(1, max_order + 1):
        for subset in combinations(range(width), order):
            rows.append((subset, _joint_counts(table, subset)))
    result = KWiseBaselineSignature(table_id, width, max_order, len(table), tuple(rows))
    logger.debug("kwise_baseline_signature exit groups=%d", len(result.joint_counts))
    return result

def global_parity_counts(table: tuple[str, ...], width: int = 4) -> tuple[tuple[str, int], ...]:
    """Return even/odd global parity counts for a binary table."""
    logger.debug("global_parity_counts entry width=%d rows=%d", width, len(table))
    _validate_table(table, width)
    even = sum(sum(int(bit) for bit in row) % 2 == 0 for row in table)
    result = (("even", even), ("odd", len(table) - even))
    logger.debug("global_parity_counts exit result=%r", result)
    return result

def kwise_parity_hidden_correlation_row() -> KWiseHiddenCorrelationRow:
    """Return the S5 3-wise-blind / 4-wise-parity hidden-correlation row."""
    logger.debug("kwise_parity_hidden_correlation_row entry")
    even_rows = tuple(row for row in bit_words(4) if sum(int(bit) for bit in row) % 2 == 0)
    structured = tuple(item for row in even_rows for item in (row, row))
    control = bit_words(4)
    left = kwise_baseline_signature("even-parity-4bit-duplicated", structured)
    right = kwise_baseline_signature("full-4bit-cube", control)
    left_parity = global_parity_counts(structured); right_parity = global_parity_counts(control)
    baseline_equal = left.comparable_key() == right.comparable_key()
    structured_gap = abs(left_parity[0][1] - left_parity[1][1]); control_gap = abs(right_parity[0][1] - right_parity[1][1])
    boundary = "finite 3-wise-baseline separation only; global parity is a classical 4-wise observer, not a universal impossibility"
    status = "3-wise-blind-hidden-correlation" if baseline_equal and structured_gap > control_gap else "blocked"
    result = KWiseHiddenCorrelationRow("S5-KWISE-001", 4, 3, structured, control, KWISE_BASELINE_FAMILIES, baseline_equal, left_parity, right_parity, structured_gap, control_gap, "4-wise global parity observer", status, boundary)
    logger.debug("kwise_parity_hidden_correlation_row exit result=%r", result)
    return result

def kwise_hidden_correlation_summary() -> dict[str, int]:
    """Return compact counters for the S5 k-wise hidden-correlation row."""
    logger.debug("kwise_hidden_correlation_summary entry")
    row = kwise_parity_hidden_correlation_row()
    result = {"rows": 1, "width": row.width, "max_blind_order": row.max_blind_order, "baseline_equal": int(row.baseline_equal), "hidden_splits": int(row.status == "3-wise-blind-hidden-correlation"), "structured_gap": row.structured_gap, "control_gap": row.control_gap, "overclaims": 0 if "not a universal" in row.boundary else 1}
    logger.debug("kwise_hidden_correlation_summary exit result=%r", result)
    return result

def kwise_hidden_correlation_checklist() -> tuple[str, ...]:
    """Return the acceptance checklist for k-wise hidden-correlation rows."""
    logger.debug("kwise_hidden_correlation_checklist entry")
    result = ("declare width and k", "match all marginals up to k", "measure global parity gap", "name high-order classical observer", "state finite non-impossibility boundary")
    logger.debug("kwise_hidden_correlation_checklist exit count=%d", len(result))
    return result
