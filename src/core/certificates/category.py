"""Category-like translation certificate hooks for Veyra."""

from __future__ import annotations

import logging

from ..shadows.category_like import category_closure_rows, category_invariant_rows, category_like_checklist, category_like_summary, category_universal_shadow_rows
from ..certify_types import Certificate

logger = logging.getLogger(__name__)


def certify_category_like_translation() -> Certificate:
    """Certify Sprint X3 finite category-like translation layer."""
    logger.debug("certify_category_like_translation entry")
    summary = category_like_summary()
    closures = category_closure_rows()
    invariants = category_invariant_rows()
    universal = category_universal_shadow_rows()
    passed = summary == {"objects": 4, "morphisms": 4, "closed": 4, "invariants": 2, "broken": 1, "universal": 3, "blocked": 1, "checklist": 4} and all(row.status == "closed" for row in closures) and [row.status for row in invariants] == ["invariant", "broken"] and [row.status for row in universal] == ["exact", "exact", "blocked"] and len(category_like_checklist()) == 4
    result = Certificate("category_like_translation_x3", "finite object/morphism/invariant/universal-shadow translation", passed, f"objects={summary['objects']} universal={summary['universal']} blocked={summary['blocked']}", 1)
    logger.debug("certify_category_like_translation exit result=%r", result)
    return result
