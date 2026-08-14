"""Thread-local redaction boundary for authoritative lower-layer replay."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import logging
from threading import RLock
from typing import Iterator


logger = logging.getLogger(__name__)
_LOWER_LOGGERS = tuple(
    logging.getLogger(name)
    for name in (
        "src.core.proof_core_codec",
        "src.core.observer_descent",
        "src.core.observer_descent_validation",
    )
)
_REPLAY_LOG_DEPTH: ContextVar[int] = ContextVar("veyra_p1a_replay_log_depth", default=0)
_BOUNDARY_LOCK = RLock()


class _ReplayRedactionFilter(logging.Filter):
    """Redact value-bearing records in the active thread-local replay."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Retain only fixed routing metadata while sibling replay is active."""
        # Logging here would recurse through this filter.  The replacement
        # record is itself the fixed audit marker for the lower-layer event.
        if _REPLAY_LOG_DEPTH.get() <= 0:
            return True
        record.msg = "p1a authoritative replay event logger=%s function=%s level=%s"
        record.args = (record.name, record.funcName, record.levelname)
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        return True


_REPLAY_FILTER = _ReplayRedactionFilter()


@contextmanager
def protected_replay_logs() -> Iterator[None]:
    """Redact repr-bearing proof-codec records for one public sibling call."""
    logger.debug("p1a protected replay logs entry")
    outermost = _REPLAY_LOG_DEPTH.get() == 0
    if outermost:
        _BOUNDARY_LOCK.acquire()
        for lower_logger in _LOWER_LOGGERS:
            # Logger filters run in list order.  Install the redactor first so
            # pre-existing audit filters cannot observe the raw lower record.
            lower_logger.filters.insert(0, _REPLAY_FILTER)
    token = _REPLAY_LOG_DEPTH.set(_REPLAY_LOG_DEPTH.get() + 1)
    try:
        yield
    except Exception as exc:
        logger.error("p1a protected replay logs error type=%s", type(exc).__name__)
        raise
    finally:
        _REPLAY_LOG_DEPTH.reset(token)
        if outermost:
            for lower_logger in _LOWER_LOGGERS:
                lower_logger.removeFilter(_REPLAY_FILTER)
            _BOUNDARY_LOCK.release()
        logger.debug("p1a protected replay logs exit")
