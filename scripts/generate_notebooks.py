#!/usr/bin/env python3
"""Generate real Veyra Sage notebook artifacts with progress."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from veyra_sage.all import current_notebook_artifacts, notebook_artifact_summary, write_current_notebook_artifacts  # noqa: E402

logger = logging.getLogger("veyra.generate_notebooks")


def stage(index: int, total: int, message: str) -> None:
    """Print visible progress stage."""
    logger.debug("stage entry index=%d total=%d message=%s", index, total, message)
    print(f"[{index}/{total}] {message}")
    logger.debug("stage exit")


def progress(done: int, total: int, start: float, label: str) -> None:
    """Print one-line progress with counters, ETA, elapsed, and speed."""
    logger.debug("progress entry done=%d total=%d label=%s", done, total, label)
    elapsed = max(time.perf_counter() - start, 0.001)
    speed = done / elapsed
    remaining = total - done
    eta = remaining / speed if speed else 0.0
    print(f"\r{label}: Processed {done}/{total} | Remaining {remaining} | ETA {eta:.1f}s | Elapsed {elapsed:.1f}s | Speed {speed:.1f}/s", end="")
    logger.debug("progress exit speed=%f", speed)


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="notebooks/generated", help="directory for generated .ipynb/.md artifacts")
    parser.add_argument("--no-markdown", action="store_true", help="write .ipynb only")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    logger.debug("main entry args=%r", args)
    started = time.perf_counter()
    try:
        stage(1, 4, "Building current notebook inventory")
        artifacts = current_notebook_artifacts()
        summary = notebook_artifact_summary(artifacts)
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))

        stage(2, 4, f"Writing artifacts to {args.output_dir}")
        write_start = time.perf_counter()

        def callback(done, total, artifact):
            progress(done, total, write_start, f"Writing {artifact.family}/{artifact.name}")

        manifest = write_current_notebook_artifacts(args.output_dir, include_markdown=not args.no_markdown, progress=callback)
        print()

        stage(3, 4, "Verifying generated ipynb JSON")
        output = Path(args.output_dir)
        ipynb_files = sorted(output.glob("**/*.ipynb"))
        errors = 0
        verify_start = time.perf_counter()
        for index, path in enumerate(ipynb_files, 1):
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("nbformat") != 4 or "cells" not in data:
                errors += 1
            progress(index, len(ipynb_files), verify_start, f"Verifying {path.name}")
        print()

        stage(4, 4, "Done")
        elapsed = time.perf_counter() - started
        md_files = sorted(output.glob("**/*.md"))
        print(f"manifest={output / 'manifest.json'}")
        print(f"[done] notebooks={manifest['notebooks']} ipynb={len(ipynb_files)} markdown={len(md_files)} errors={errors} elapsed={elapsed:.2f}s")
        logger.debug("main exit errors=%d elapsed=%f", errors, elapsed)
        return 0 if errors == 0 and len(ipynb_files) == manifest["notebooks"] else 1
    except Exception as exc:
        logger.exception("main error: %s", exc)
        print(f"[done] notebooks=0 ipynb=0 markdown=0 errors=1 error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
