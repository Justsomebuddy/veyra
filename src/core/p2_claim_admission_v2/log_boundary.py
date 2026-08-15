"""Thread-local first-position redaction for authoritative lower replay."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import logging
from threading import RLock
from typing import Iterator

logger = logging.getLogger(__name__)
_LOWER_LOGGERS = (logging.getLogger("src.core.proof_core_codec"),)
_REPLAY_DEPTH: ContextVar[int] = ContextVar("veyra_p2_claim_admission_replay_depth", default=0)
_BOUNDARY_LOCK = RLock()


class _ReplayRedactionFilter(logging.Filter):
    """Replace value-bearing proof-codec records only in the active sibling call."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Preserve fixed routing metadata without digest or payload arguments."""
        if _REPLAY_DEPTH.get() <= 0:
            return True
        record.msg = "p2 claim-admission replay event logger=%s function=%s level=%s"
        record.args = (record.name, record.funcName, record.levelname)
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        return True


_REPLAY_FILTER = _ReplayRedactionFilter()


@contextmanager
def protected_replay_logs() -> Iterator[None]:
    """Install and exactly restore a first-position targeted replay redactor."""
    logger.debug("protected_replay_logs entry")
    outermost = _REPLAY_DEPTH.get() == 0
    if outermost:
        _BOUNDARY_LOCK.acquire()
        for lower_logger in _LOWER_LOGGERS:
            lower_logger.filters.insert(0, _REPLAY_FILTER)
    token = _REPLAY_DEPTH.set(_REPLAY_DEPTH.get() + 1)
    try:
        yield
    except Exception as exc:
        logger.error("protected_replay_logs error type=%s", type(exc).__name__)
        raise
    finally:
        _REPLAY_DEPTH.reset(token)
        if outermost:
            for lower_logger in _LOWER_LOGGERS:
                lower_logger.removeFilter(_REPLAY_FILTER)
            _BOUNDARY_LOCK.release()
        logger.debug("protected_replay_logs exit")
