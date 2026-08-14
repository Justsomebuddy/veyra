#!/bin/bash
set -euo pipefail
export PATH="$HOME/.elan/bin:$PATH"
cd "$(dirname "$0")/.."
# Gate: the 48-file pinned tree still compiles warning-free.
python3 scripts/check_lean_sources.py --jobs 8 2>&1 | tail -3
