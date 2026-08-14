"""Fixed resource and wire-format constants for categorical ingestion."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

HARD_MAX_SPLIT_BYTES = 16 * 1024 * 1024
HARD_MAX_RECORD_BYTES = 32 * 1024

IDENTITY_COLUMNS = ("row_id", "source_id", "content_id", "group_id")
TARGET_COLUMN = "target"
RESERVED_COLUMNS = frozenset((*IDENTITY_COLUMNS, TARGET_COLUMN))
