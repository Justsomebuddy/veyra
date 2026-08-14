#!/bin/bash
set -euo pipefail
export PATH="$HOME/.elan/bin:$PATH"
cd "$(dirname "$0")/.."
python3 scripts/check_research_lean.py
