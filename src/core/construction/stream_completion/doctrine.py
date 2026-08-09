"""The sole allowlisted PΩ1 stream doctrine."""

from __future__ import annotations

import logging

from .common import exact_digest, exact_shape, reject
from .digest import digest
from .types import StreamCompletionDoctrine

logger = logging.getLogger(__name__)
DOCTRINE_FIELDS = (
    "pomega1-stream-doctrine-v1", "veyra.stream.fin.v1", "Nat",
    "Fin-n-to-Fin-cardinality", "all-compatible-prefix-families",
    "Nat-to-Fin-cardinality", "finite-take", "Lean-Eq",
    "stream-completion-principle-v1",
)


def stream_completion_doctrine() -> StreamCompletionDoctrine:
    """Construct the exact doctrine record."""
    logger.debug("stream_completion_doctrine entry")
    value = digest("veyra.pomega1.doctrine.v1", tuple(
        (f"field-{i}", item.encode()) for i, item in enumerate(DOCTRINE_FIELDS)
    ))
    result = StreamCompletionDoctrine(*DOCTRINE_FIELDS, value)
    logger.debug("stream_completion_doctrine exit")
    return result


def snapshot_doctrine(value: StreamCompletionDoctrine) -> StreamCompletionDoctrine:
    """Reject alternate IDs/equality/representation and rebuild identity."""
    logger.debug("snapshot_doctrine entry")
    exact_shape(value, StreamCompletionDoctrine, "stream-doctrine")
    try:
        names = tuple(field for field in value.__dict__ if field != "doctrine_digest")
        if any(type(getattr(value, name)) is not str for name in names):
            reject("stream-doctrine-scalar-type-invalid")
        exact_digest(value.doctrine_digest, "stream-doctrine-digest")
    except AttributeError:
        reject("stream-doctrine-missing-fields")
    expected = stream_completion_doctrine()
    if value != expected:
        reject("stream-doctrine-drift")
    logger.debug("snapshot_doctrine exit")
    return expected
