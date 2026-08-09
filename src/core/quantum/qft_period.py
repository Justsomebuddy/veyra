"""Q8 finite QFT/period-finding rows for Q-Veyra."""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
import logging
from .veyra import A0, A1, AH, QAmp, QGate, QMode, R0, R1, Rad2

logger = logging.getLogger(__name__)
N4 = 4
BASIS4 = ("0", "1", "2", "3")
RHALF = Rad2(Fraction(1, 2))
AHALF = QAmp(RHALF)
AMIHALF = QAmp(R0, -RHALF)
AIHALF = QAmp(R0, RHALF)
AMHALF = QAmp(-RHALF)
PHASE_LABELS = {0: "1", 1: "i", 2: "-1", 3: "-i"}

@dataclass(frozen=True)
class QFTPeriodRow:
    """One finite period-to-frequency-shadow row for QFT_4."""
    row_id: str
    period: int
    offset: int
    support: tuple[str, ...]
    phase_orbit: tuple[str, ...]
    expected_frequencies: tuple[str, ...]
    observed_frequencies: tuple[str, ...]
    norm_preserved: bool
    status: str
    boundary: str

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready row."""
        logger.debug("QFTPeriodRow.as_dict entry row_id=%s", self.row_id)
        result = self.__dict__.copy()
        logger.debug("QFTPeriodRow.as_dict exit result=%r", result)
        return result

@dataclass(frozen=True)
class QFTOffsetEchoRow:
    """Offset states with same frequency distribution but different phases."""
    row_id: str
    period: int
    left_offset: int
    right_offset: int
    frequency_echo: bool
    phase_distinct: bool
    witness: str
    status: str
    boundary: str

@dataclass(frozen=True)
class QFTPeriodObstructionRow:
    """A non-periodic support row that blocks a claimed period shadow."""
    row_id: str
    claimed_period: int
    support: tuple[str, ...]
    expected_frequencies: tuple[str, ...]
    observed_frequencies: tuple[str, ...]
    witness: str
    status: str
    boundary: str

def qft4_gate() -> QGate:
    """Return exact four-point QFT over phases `1,i,-1,-i` with factor 1/2."""
    logger.debug("qft4_gate entry")
    result = QGate(
        "QFT4",
        (
            (AHALF, AHALF, AHALF, AHALF),
            (AHALF, AIHALF, AMHALF, AMIHALF),
            (AHALF, AMHALF, AHALF, AMHALF),
            (AHALF, AMIHALF, AMHALF, AIHALF),
        ),
    )
    logger.debug("qft4_gate exit result=%r", result)
    return result

def qft_period_state(period: int, offset: int = 0) -> QMode:
    """Return normalized `N=4` coset state with support `offset mod period`."""
    logger.debug("qft_period_state entry period=%d offset=%d", period, offset)
    if period not in (1, 2, 4) or not 0 <= offset < period:
        logger.error("qft_period_state invalid period=%d offset=%d", period, offset)
        raise ValueError("Q8 supports period in {1,2,4} and 0 <= offset < period")
    support = {str(index) for index in range(offset, N4, period)}
    amp = {4: AHALF, 2: AH, 1: A1}[len(support)]
    result = QMode(BASIS4, tuple(amp if label in support else A0 for label in BASIS4))
    logger.debug("qft_period_state exit support=%r norm=%r", support, result.norm2())
    return result

def qft_shadow(mode: QMode) -> tuple[tuple[str, Rad2], ...]:
    """Return QFT_4 measurement distribution for a finite mode."""
    logger.debug("qft_shadow entry basis=%r", mode.basis)
    result = qft4_gate().apply(mode).distribution()
    logger.debug("qft_shadow exit result=%r", result)
    return result

def expected_period_frequencies(period: int) -> tuple[str, ...]:
    """Return exact QFT support frequencies for a period dividing four."""
    logger.debug("expected_period_frequencies entry period=%d", period)
    if period not in (1, 2, 4):
        logger.error("expected_period_frequencies invalid period=%d", period)
        raise ValueError("period must divide four")
    result = tuple(str(index) for index in range(0, N4, N4 // period))
    logger.debug("expected_period_frequencies exit result=%r", result)
    return result

def observed_frequencies(mode: QMode) -> tuple[str, ...]:
    """Return nonzero QFT measurement frequencies for a finite mode."""
    logger.debug("observed_frequencies entry")
    result = tuple(label for label, prob in qft_shadow(mode) if not prob.is_zero())
    logger.debug("observed_frequencies exit result=%r", result)
    return result

def phase_orbit(period: int, offset: int) -> tuple[str, ...]:
    """Return phase labels attached to the expected period frequencies."""
    logger.debug("phase_orbit entry period=%d offset=%d", period, offset)
    result = tuple(PHASE_LABELS[(offset * int(freq)) % N4] for freq in expected_period_frequencies(period))
    logger.debug("phase_orbit exit result=%r", result)
    return result

def qft_period_row(period: int, offset: int = 0) -> QFTPeriodRow:
    """Return one finite period-finding QFT row."""
    logger.debug("qft_period_row entry period=%d offset=%d", period, offset)
    state = qft_period_state(period, offset)
    qft_state = qft4_gate().apply(state)
    expected = expected_period_frequencies(period)
    observed = observed_frequencies(state)
    ok = observed == expected and state.norm2() == R1 and qft_state.norm2() == R1
    result = QFTPeriodRow(f"Q8-PERIOD-{period}-OFFSET-{offset}", period, offset, tuple(label for label, amp in zip(BASIS4, state.amplitudes, strict=True) if not amp.is_zero()), phase_orbit(period, offset), expected, observed, ok, "ready" if ok else "blocked", "finite QFT_4 period shadow only; no Shor-scale period-finding claim")
    logger.debug("qft_period_row exit result=%r", result)
    return result

def qft_period_rows() -> tuple[QFTPeriodRow, ...]:
    """Return the finite Q8 period-to-frequency rows."""
    logger.debug("qft_period_rows entry")
    result = (qft_period_row(1), qft_period_row(2), qft_period_row(4))
    logger.debug("qft_period_rows exit count=%d", len(result))
    return result

def qft_offset_echo_row() -> QFTOffsetEchoRow:
    """Return row where period-2 offsets share measurement shadow but differ by phase."""
    logger.debug("qft_offset_echo_row entry")
    left = qft4_gate().apply(qft_period_state(2, 0))
    right = qft4_gate().apply(qft_period_state(2, 1))
    freq_echo = left.distribution() == right.distribution()
    phase_distinct = left.amplitudes != right.amplitudes
    result = QFTOffsetEchoRow("Q8-OFFSET-ECHO", 2, 0, 1, freq_echo, phase_distinct, "offset phase flips the k=2 amplitude while measurement probabilities echo", "ready" if freq_echo and phase_distinct else "blocked", "finite QFT_4 offset echo only")
    logger.debug("qft_offset_echo_row exit result=%r", result)
    return result

def qft_period_obstruction_row() -> QFTPeriodObstructionRow:
    """Return obstruction row for adjacent support falsely claimed as period two."""
    logger.debug("qft_period_obstruction_row entry")
    mode = QMode(BASIS4, (AH, AH, A0, A0))
    expected = expected_period_frequencies(2)
    observed = observed_frequencies(mode)
    result = QFTPeriodObstructionRow("Q8-PERIOD-OBSTRUCT", 2, ("0", "1"), expected, observed, "adjacent support leaks to odd frequencies under QFT_4", "ready" if observed != expected else "blocked", "finite false-period obstruction only")
    logger.debug("qft_period_obstruction_row exit result=%r", result)
    return result

def quantum_qft_period_summary() -> dict[str, int]:
    """Return compact Q8 counters."""
    logger.debug("quantum_qft_period_summary entry")
    rows = qft_period_rows(); echo = qft_offset_echo_row(); obstruction = qft_period_obstruction_row()
    result = {"period_rows": len(rows), "ready_period_rows": sum(row.status == "ready" for row in rows), "offset_echo_rows": int(echo.status == "ready"), "obstruction_rows": int(obstruction.status == "ready"), "frequency_hits": sum(row.expected_frequencies == row.observed_frequencies for row in rows), "overclaims": sum("finite" not in row.boundary for row in rows) + int("finite" not in echo.boundary) + int("finite" not in obstruction.boundary)}
    logger.debug("quantum_qft_period_summary exit result=%r", result)
    return result

def quantum_qft_period_checklist() -> tuple[str, ...]:
    """Return Q8 acceptance checklist."""
    logger.debug("quantum_qft_period_checklist entry")
    result = ("exact QFT_4 gate", "period states for periods 1/2/4", "frequency-support shadows match expected periods", "offset phase echo row", "false-period obstruction row", "no Shor-scale claim")
    logger.debug("quantum_qft_period_checklist exit count=%d", len(result))
    return result
