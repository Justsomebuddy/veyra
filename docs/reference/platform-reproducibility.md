# Platform and reproducibility contract

## Supported surfaces

Veyra has two deliberately different support levels.

| Surface | Linux | macOS | Windows |
|---|---|---|---|
| installable portable Python subset and finite semantics | supported on CPython 3.11; verified locally and in hosted CI on 3.11.14 | verified in hosted CI on CPython 3.11.9 | verified in hosted CI on CPython 3.11.9 |
| wheel/sdist build and isolated wheel import | verified locally and in hosted CI | verified in hosted CI | verified in hosted CI |
| VAM Rust crate | verified locally and in hosted CI with pinned Rust | verified in hosted CI with pinned Rust | verified in hosted CI with pinned Rust |
| compiling all 43 Lean sources with `elan` | supported when the pinned toolchain is installed | expected where `elan` supplies the pinned toolchain | expected where `elan` supplies the pinned toolchain |
| content-bound certificate renewal and guarded Lean execution | Linux x86_64 only | unsupported | unsupported |
| R14 process/resource hardening | Linux/POSIX contract only | unsupported | unsupported |
| Sage-native facade | supported when SageMath provides the hardened CPython 3.11.14 lane | dependent on a compatible SageMath distribution | dependent on a compatible SageMath distribution |

Portable imports never install fake `fcntl`, `pwd`, or `resource` modules.
Platform-specific operations are lazy and guarded by typed capability checks;
missing `inotify`, file locks, process limits, a pinned Lean runtime, real Sage,
or native Rust fail explicitly instead of being emulated or converted into a
pass. `tests/conftest.py` classifies actual Lean, Rust, and worker-hardening test
modules; prerequisite sentinels cover the real lock, Sage, and selected-toolchain
probes. The portable runner uses a reviewed allowlist and explicitly deselects
all capability markers as defense in depth rather than dynamically skipping
failures. The unfiltered complete lane still runs every test.

The workflow in `.github/workflows/portable.yml` is the executable OS matrix.
[GitHub Actions run `31362980690`](https://github.com/Justsomebuddy/veyra/actions/runs/31362980690)
passed all seven jobs for exact commit
`3c44de5045b40ae998b2464483525fc6c6e9cc13`: portable Python and native Rust
on Linux, macOS, and Windows, plus the exact Rust 1.83.0 MSRV lane on Linux.
This verifies only the portable/package/native surfaces named in the table; it
does not extend the Linux-only Sage, Lean, certificate-renewal, or process
hardening claims.

## Python version and capabilities

The portable installed surface supports **CPython `>=3.11,<3.12`**. The
content-bound certificate and complete hardened Linux surfaces additionally
require **CPython 3.11.14 exactly**. Some executable certificate identities bind
reviewed CPython code-object bytes, and CPython does not promise those bytes to
remain identical across patch releases. Capability checks therefore keep a
portable import from implying that certificate renewal is available.

Accepting Python 3.12+ would still be misleading and is rejected in package
metadata. A future multi-minor release must first replace or version the
identity contract and renew its evidence.

The installable library has no mandatory third-party Python runtime dependency.
Optional dependency groups are:

- `dev`: build, Pytest, and Ruff;
- `tools`: `tqdm` for repository verification scripts;
- `signing`: optional `cryptography` backend for Ed25519 replay receipts;
- `notebooks`: Jupyter kernel and lab tooling.

`requirements/py311-tested.txt` pins the direct versions exercised by the
maintained Python 3.11.14 lane. `requirements/ci-py311.txt` pins the CI tools
and their direct Python dependencies, including the build backend bootstrap;
neither file is a hash-locked or platform-byte lock. `environment.yml` is the
equivalent conda solver input with bounded direct requirements; conda may
resolve different compatible transitive builds on different platforms.

## Reproducing an installation

POSIX shells:

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --no-deps -r requirements/ci-py311.txt
python -m pip install --no-build-isolation --no-deps -e .
python scripts/verify_portable.py
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --no-deps -r requirements/ci-py311.txt
python -m pip install --no-build-isolation --no-deps -e .
python scripts/verify_portable.py
```

The portable runner avoids Bash, GNU `find`, and GNU Make. `make` remains a
convenience wrapper for the complete Linux source-checkout lane.

Repository artifacts use normalized relative POSIX identities in reports and
resolve against the discovered package/source root only at I/O. An absolute
`VEYRA_PROJECT_ROOT` override is trusted operator input and is accepted only
when it is absolute and contains the expected `pyproject.toml` and `src/core`
layout; that layout check is not repository authentication. Escapes, absolute
or non-normalized logical identities, backslash-specific identities, and
existing symlink escapes are rejected, so changing the caller's CWD cannot
silently retarget proofs or temporary output.

## Distribution contents

The wheel contains the importable `src`, `veyra_sage`, and `vam` packages plus
the VAM example used by the public certification path. The source distribution
also carries public docs, Lean sources, scripts, tests, notebooks, and the Rust
crate. `python scripts/package_smoke.py` builds both formats offline with the
installed build tools, inspects their required payload, installs the
checkout-built wheel into one isolated target, rebuilds a second wheel from the
source distribution, installs it into another isolated target, and imports only
from those targets.

The wheel supports the portable finite API subset; it is not a self-contained
certificate-renewal bundle. Certificate functions that audit repository paths
such as `tests/`, `proofs/lean/`, or `vam/native/` require an unpacked source
distribution or source checkout and can legitimately return a non-passing
boundary from a wheel-only install. Package smoke therefore checks imports and packaged VAM
resources, not a source-checkout certificate pass.

Archive bytes are not claimed to be bit-for-bit identical across arbitrary
setuptools, wheel, filesystem, or compression versions. Reproduce semantics
from an exact commit with the recorded direct tool versions; compare unpacked
content when auditing source distributions.

## External toolchains

- Lean source compilation uses `leanprover/lean4:v4.30.0-rc2` via `elan`.
- The native crate records Rust `1.95.0` in `rust-toolchain.toml`; its declared
  MSRV is `1.83`, a compatibility contract distinct from the reproduced release
  compiler.
- SageMath is external to PyPI packaging. `make sage-required` invokes the smoke
  suite through `sage -python` and rejects fallback-only execution.

The complete Linux `make verify` lane requires all three toolchains. The
portable lane intentionally excludes content-bound certificate renewal,
Sage-native checks, and Linux process hardening rather than reporting them as
cross-platform passes.

The current security-reviewed portable Python tool lane records pip 26.1.2,
setuptools 83.0.0, and pytest 9.0.3. The latest complete Linux proof lane also
records CPython 3.11.14, SageMath 10.7, `elan` 4.2.1, Lean 4.30.0-rc2, and
Rust 1.95.0. These tool versions do not convert the direct Python constraint
file into a transitive or cross-platform bit-for-bit lock, and portable runs do
not retroactively reproduce the complete proof lane.

The optional signing lane uses cryptography 50.0.0. Its CPython macOS wheel is
arm64-only; Intel macOS requires a separately verified source build with native
prerequisites. Ordinary portable-package success does not establish that
optional signing capability on every host architecture.
The hosted Ubuntu lane separately installs the exact binary signing dependency
and runs the canonical Ed25519 replay test; this is Linux evidence only.

The hosted workflow pins action commits, fixed runner labels, job timeouts, the
exact Python tool list, Rust 1.95.0, and exact Rust 1.83.0 for declared-MSRV
compatibility. Linux uses CPython 3.11.14; macOS and Windows use the newest
setup-python patch available on all selected images, 3.11.9. The exact hosted
run cited above supplies the current cross-platform evidence. Runner labels
select OS families, not immutable image revisions; the concrete hosted image
revision remains mutable workflow-run evidence, so later runs must be evaluated
independently rather than inheriting this result.

The action layer uses immutable official Node.js 24 revisions:
`actions/checkout` v7.0.1 at
`3d3c42e5aac5ba805825da76410c181273ba90b1` and `actions/setup-python`
v7.0.0 at `5fda3b95a4ea91299a34e894583c3862153e4b97`. Version comments are
descriptive only; the full commit identifiers are the executable trust roots.
This replaces the deprecated Node.js 20 action runtime without broadening
workflow permissions or enabling persisted checkout credentials.

The final diff-integrity stage checks unstaged changes, the staged index, and
the current commit object. On a clean commit-bound run, the commit-object check
remains non-vacuous even though both working-tree diffs are empty.
