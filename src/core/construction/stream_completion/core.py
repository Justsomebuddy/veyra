"""Public exact PΩ1 completed-stream carrier surface."""

from __future__ import annotations

import logging

from .alphabet import (
    BRIDGE_THEOREM_IDS, formal_alphabet_presentation, stream_alphabet_source,
)
from .common import StreamCompletionValidationError
from .doctrine import stream_completion_doctrine
from .formal import (
    ARTIFACT_PATH, ARTIFACT_SHA256, SCP_THEOREM_IDS, TCB_DIGEST, THEOREM_IDS,
    TOOLCHAIN_ID, stream_completion_theorem_source,
)
from .ledger import AXIOM_CLOSURE, stream_completion_ledger
from .package import (
    stream_completion_package, stream_completion_policy,
)
from .result_validation import validate_stream_completion_result
from .runtime import stream_completion_judgment
from .shadow import bounded_stream_shadow
from .types import *  # noqa: F403

logger = logging.getLogger(__name__)

__all__ = [
    "ARTIFACT_PATH", "ARTIFACT_SHA256", "AXIOM_CLOSURE", "BRIDGE_THEOREM_IDS",
    "SCP_THEOREM_IDS", "StreamCompletionValidationError", "TCB_DIGEST",
    "THEOREM_IDS", "TOOLCHAIN_ID", "bounded_stream_shadow", "formal_alphabet_presentation",
    "stream_alphabet_source", "stream_completion_doctrine",
    "stream_completion_judgment", "stream_completion_ledger",
    "stream_completion_package", "stream_completion_policy",
    "stream_completion_theorem_source", "validate_stream_completion_result",
]
