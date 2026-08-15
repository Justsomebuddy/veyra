#!/usr/bin/env python3
"""Run practical Veyra scale-memory logarithm recovery demos."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import _project_bootstrap  # noqa: F401
from src.core.ratio import ratio_from_ints
from src.core.scale_memory_log import finite_field_log_fixture, recover_transition_depth, scale_memory_obstruction_card

logger = logging.getLogger("veyra.scale_memory_log_demo")


def stage(index: int, total: int, message: str) -> None:
    """Print visible progress stage."""
    logger.debug("stage entry index=%d total=%d message=%s", index, total, message)
    print(f"[{index}/{total}] {message}")
    logger.debug("stage exit")


def main() -> int:
    """Run exact, residual, cyclic, and obstruction recovery demos."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    logger.debug("main entry")
    stage(1, 5, "Recovering exact scale-memory depth 2^n=32")
    exact = recover_transition_depth("doubling-exact", ratio_from_ints(2), ratio_from_ints(32), 10)

    stage(2, 5, "Recovering residual scale-memory depth near 20")
    residual = recover_transition_depth(
        "doubling-residual", ratio_from_ints(2), ratio_from_ints(20), 6, ratio_from_ints(4)
    )

    stage(3, 5, "Unwrapping finite cyclic shadow 5^n mod 97 = 83")
    cyclic = finite_field_log_fixture()

    stage(4, 5, "Checking collapsed-generator obstruction")
    obstruction = scale_memory_obstruction_card()

    stage(5, 5, "Building JSON recovery summary")
    payload = {
        "exact": exact.as_dict(),
        "residual": residual.as_dict(),
        "cyclic": cyclic.as_dict(),
        "obstruction": obstruction.as_dict(),
    }
    print(json.dumps(payload, sort_keys=True))
    ok = (
        exact.status == "exact"
        and residual.status == "approximate"
        and cyclic.status == "exact"
        and obstruction.status == "blocked"
    )
    print(f"[done] errors={0 if ok else 1}")
    logger.debug("main exit ok=%s", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
