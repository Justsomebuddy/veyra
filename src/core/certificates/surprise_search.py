"""Certificate for bounded observer-gap surprise search rows."""
from __future__ import annotations
import logging
from ..certify_types import Certificate
from ..surprise.search import surprise_search_checklist, surprise_search_summary

logger = logging.getLogger(__name__)

def certify_surprise_search_s3() -> Certificate:
    """Certify the finite expanded-baseline surprise search ledger."""
    logger.debug("certify_surprise_search_s3 entry")
    summary = surprise_search_summary()
    expected = {
        "search_rows": 1,
        "scanned_words": 496,
        "signature_groups": 464,
        "colliding_signature_groups": 32,
        "split_signature_groups": 0,
        "robust_pairs": 0,
        "hidden_correlation_rows": 1,
        "pairwise_blind_hidden_splits": 1,
        "overclaims": 0,
    }
    passed = summary == expected and len(surprise_search_checklist()) == 6
    detail = f"words={summary['scanned_words']} collisions={summary['colliding_signature_groups']} robust={summary['robust_pairs']} xor={summary['pairwise_blind_hidden_splits']}"
    result = Certificate("surprise_search_s3", "finite expanded-baseline and XOR hidden-correlation observer-gap ledger", passed, detail, 1)
    logger.debug("certify_surprise_search_s3 exit result=%r", result)
    return result
