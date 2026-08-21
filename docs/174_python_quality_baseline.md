# Python quality baseline and bounded packaging hardening

## Status

This document records a measured debt baseline, not a claim that the full
repository is green. The measurements use CPython 3.11 from the exact
`c41fcebb03b56a806ed4e1586167a39fefd1d988` starting point plus this bounded
quality wave.

## Measured local findings

```bash
ruff format --no-cache --check -- .
mypy --config-file pyproject.toml
```

- Ruff format exits `1`: **985 files would be reformatted** and 318 files are
  already formatted.
- Local Mypy 1.19.1 exits `1`: **1612 errors in 396 files**, with 1303 source
  files checked.

Both results are findings. Existing Ruff lint remains a separate gate. The
repository is not mass-formatted because a 985-file mechanical rewrite would
mix unrelated history and content-bound artifacts into an unauditable change.
The Mypy configuration discovers all maintained Python roots (`src`,
`veyra_sage`, `vam`, `scripts`, and `tests`) while excluding build/output,
experimental, generated-notebook and uncommitted-test trees. It enables
namespace-package discovery and error codes. It does not ignore, baseline, or
otherwise suppress the 1612 errors.

Mypy is not declared in the development extras, tested requirements, or hosted
CI lane. Therefore this is a local Mypy 1.19.1 measurement, not a standard
project gate, reproducible environment claim, or version-stable error count.
The configuration makes future discovery explicit without misrepresenting the
current debt as type-checked.

## Bounded hardening in this wave

`scripts/package_smoke.py` validates a source distribution completely before
extracting it. The archive must contain at most 20,000 regular/directory
members and at most 512 MiB of declared uncompressed regular-file data. Every
member must pass the existing relative-path and regular-file/directory checks
and CPython 3.11's standard-library `tarfile.data_filter`. Portable path
identity uses NFC-normalized case-folded POSIX components and rejects dot/empty
components, backslashes, Windows drive/stream colons, trailing dot/space
aliases, duplicate canonical paths, spelling aliases and file/directory
ancestor conflicts. A canonical directory entry may follow files that already
established it as an implicit ancestor; exact duplicates and every file at that
path still fail closed. Extraction begins only after the complete member
sequence and single-root/`pyproject.toml` inventory pass those checks.

Focused synthetic archives cover a normal extraction, member-count overflow,
expanded-size overflow, unsafe member types, normalized duplicate names,
file/parent and child/directory conflicts, case/backslash aliases, and the
invariant that no extraction call or partial output occurs before complete
validation. These archive-boundary regressions are part of the hosted portable
test inventory.

## Explicit boundaries

- No Ruff-format debt was rewritten.
- No Mypy error was hidden or promoted to a required gate.
- Mypy 1.19.1 is not added to project dependencies or CI in this wave.
- Private security-tool findings are not reproduced here.
- No RFC runtime, mathematical statement, proof artifact, registry, public API,
  package payload, or compatibility boundary changes.
- The multi-hour `make verify` is outside this bounded wave.
