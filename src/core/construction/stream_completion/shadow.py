"""Bounded executable pressure shadows, never PΩ1 completion evidence."""

from __future__ import annotations

import logging

from .alphabet import snapshot_alphabet
from .common import reject
from .digest import digest, texts
from .types import BoundedStreamShadow, StreamAlphabetSource

logger = logging.getLogger(__name__)


def bounded_stream_shadow(
    alphabet: StreamAlphabetSource, depth: int,
) -> BoundedStreamShadow:
    """Evaluate constant witness restrictions and finite diagonal through one depth."""
    logger.debug("bounded_stream_shadow entry depth=%r", depth)
    alphabet = snapshot_alphabet(alphabet)
    if type(depth) is not int or not 0 <= depth <= 128:
        reject("bounded-shadow-depth-invalid")
    stream = tuple(alphabet.symbols[0] for _ in range(depth))
    restrictions = tuple(stream[:n] for n in range(depth + 1))
    diagonal = tuple(restrictions[k + 1][k] for k in range(depth))
    value = digest("veyra.pomega1.bounded-shadow.v1", (
        ("alphabet", alphabet.alphabet_digest.encode()),
        ("depth", depth.to_bytes(4, "big")), *texts("stream", stream),
        *tuple((f"restriction-{i}", "\x00".join(row).encode()) for i, row in enumerate(restrictions)),
        *texts("diagonal", diagonal),
    ))
    result = BoundedStreamShadow(
        alphabet.alphabet_digest, depth, stream, restrictions, diagonal, value,
    )
    logger.debug("bounded_stream_shadow exit rows=%d", len(restrictions))
    return result
