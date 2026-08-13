#!/usr/bin/env python3
"""Print the pytest marker expression matching this host's capabilities.

``make test`` uses this expression to deselect capability-marked test files
(see tests/conftest.py) whose lane is unavailable on the current host, so the
public suite runs green on portable macOS/Windows hosts and still runs the
complete lane when Lean, Rust, SageMath, and Linux hardening are present.
"""

from __future__ import annotations

from src.platform_capabilities import Capability, capability_status

LANE_CHECKS = (
    (Capability.POSIX_FILE_LOCKS, "requires_posix_file_locks"),
    (Capability.LINUX_HARDENING, "requires_linux_hardening"),
    (Capability.LEAN_TOOLCHAIN_CANDIDATE, "requires_lean_candidate"),
    (Capability.LEAN_TOOLCHAIN_CANDIDATE, "requires_pinned_lean"),
    (Capability.SAGE_RUNTIME, "requires_real_sage"),
    (Capability.RUST_1_95, "requires_native_rust"),
)


def main() -> None:
    """Emit the deselection expression, or nothing on a complete lane."""
    missing = [
        marker
        for capability, marker in LANE_CHECKS
        if not capability_status(capability).available
    ]
    expression = " and ".join(f"not {marker}" for marker in missing)
    if expression:
        print(expression)


if __name__ == "__main__":
    main()
