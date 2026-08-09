"""Certificate for the seeded larger observer-gap separation corpus."""
from __future__ import annotations
import logging
from ..certify_types import Certificate
from ..surprise.corpus import surprise_corpus_checklist, surprise_corpus_summary

logger = logging.getLogger(__name__)

def certify_surprise_corpus_s7() -> Certificate:
    """Certify the seeded S7 corpus with blind/caught/obstruction rows."""
    logger.debug("certify_surprise_corpus_s7 entry")
    summary = surprise_corpus_summary()
    passed = (
        summary.seed == 20260708
        and summary.corpus_words == 640
        and summary.signature_groups == 479
        and summary.colliding_groups == 120
        and summary.positive_gap_words == 110
        and summary.blind_pairs_found == 7
        and summary.blind_rows == 7
        and summary.caught_rows == 8
        and summary.obstruction_rows == 5
        and summary.status == "classified"
        and len(summary.digest) == 64
        and len(surprise_corpus_checklist()) == 6
    )
    detail = f"words={summary.corpus_words} blind={summary.blind_rows} caught={summary.caught_rows} obstructions={summary.obstruction_rows}"
    result = Certificate("surprise_corpus_s7", "seeded larger baseline-blind/caught separation corpus", passed, detail, 1)
    logger.debug("certify_surprise_corpus_s7 exit result=%r", result)
    return result
