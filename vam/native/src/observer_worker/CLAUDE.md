# Native Observer Worker Module

## Purpose

This module owns versioned native observer-worker execution, physical-control
readback, bounded supervision, and autonomous replay. Earlier v1–v4 contracts
remain frozen; v5 adds Linux x86-64 closed-rootfs and delegated-cgroup custody.

## V5 cgroup harness boundary

- `PASSED` requires creation of a fresh leaf plus exact control, membership,
  abnormal-exit cleanup, and removal readback.
- `UNAVAILABLE` is reserved for valid host capability/delegation failures:
  the system cgroup mount is not a delegation, required controller state cannot
  be read/enabled, or the kernel/delegation refuses leaf/control operations.
- Invalid limits, nonexistent or out-of-mount roots, non-directory paths,
  malformed ownership claims, mismatched readback, and harness program failures
  remain fail-closed errors.

## Logging

Every changed function emits project diagnostic entry/exit or rejection events.
Events describe state transitions without paths, PIDs, payloads, or secrets.

## Version

Observer worker v5 hardening revision 1.
