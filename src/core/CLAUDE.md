# Core module memory

Version: **0.1.0**. Scope: the stable Python engine and its executable
certificate surfaces.

## Contracts

- Certificate helpers must validate producer result variants before consuming
  fields. Maintained certificate invariants use callback-free exact-type guards,
  fixed value-free error logs, and stable runtime exceptions that survive
  optimized Python.
- Certificate hardening must preserve valid DTOs, bytes, counts, digests,
  exports, proof status, and mathematical claim levels.
- Public failures must not format, inspect, or log hostile values. Secrets, raw
  inputs, environment data, and full sensitive digests never belong in logs.
- Maintained handwritten files target at most 1,000 lines and never exceed the
  2,000-line hard maximum.

## Session Notes (2026-08-15)

- The first bounded assertion-hardening wave replaces exactly four
  observer-genesis and eight productivity certificate result assertions with
  immediate exact-type guards. All 12 positions reject uninitialized hostile
  subclasses before callbacks, and representative failures remain stable under
  `python -O`; other production assertions remain separate future work.
