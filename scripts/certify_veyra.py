#!/usr/bin/env python3
"""Run executable Veyra workability certificates with progress."""

from __future__ import annotations

import json
import logging
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import _project_bootstrap  # noqa: F401
from src.core.certify import certificate_suite, certificate_summary  # noqa: E402

logger = logging.getLogger("veyra.certify")


def stage(index: int, total: int, message: str) -> None:
    """Print visible progress stage."""
    logger.debug("stage entry index=%d total=%d message=%s", index, total, message)
    print(f"[{index}/{total}] {message}")
    logger.debug("stage exit")


def main() -> int:
    """CLI entrypoint."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    logger.debug("main entry")
    try:
        stage(1, 3, "Running certificate suite")
        certs = certificate_suite()
        for cert in certs:
            status = "PASS" if cert.passed else "SKIP" if not cert.available else "FAIL"
            print(f"{status} {cert.name} level={cert.level} method={cert.method} detail={cert.detail}")

        stage(2, 3, "Building summary")
        summary = certificate_summary(certs)
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))

        stage(3, 3, "Done")
        unavailable = tuple(
            cert.name for cert in certs if not cert.passed and not cert.available
        )
        failed = tuple(
            cert.name for cert in certs if not cert.passed and cert.available
        )
        if unavailable:
            print(f"[note] {len(unavailable)} certificates need an absent toolchain: "
                  f"{', '.join(unavailable)}")
        ok = not failed
        print(f"[done] certificates={summary['total']} passed={summary['passed']} "
              f"failed={len(failed)} unavailable={len(unavailable)}")
        logger.debug("main exit ok=%s", ok)
        return 0 if ok else 1
    except Exception as exc:
        logger.exception("main error: %s", exc)
        print(f"[done] certificates=0 passed=0 errors=1 error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
