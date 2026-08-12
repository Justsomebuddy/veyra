# Dependency inventory

This inventory separates import-time requirements from development tools and
external proof/native systems. Version ranges live in machine-readable files;
this page explains why each dependency exists.

## Python package

| Dependency | Declaration | Required for | Notes |
|---|---|---|---|
| CPython `>=3.11,<3.12` | `pyproject.toml` | portable installed Python APIs | CI selects 3.11.14 on Linux and 3.11.9 on macOS/Windows because those patches are available on the selected runner labels |
| CPython `==3.11.14` | hardened-lane capability | content-bound certificate renewal and complete Linux verification | reviewed certificate identities bind 3.11.14 code-object bytes |
| Python standard library | source imports | `src`, `vam`, and fallback `veyra_sage` | no third-party mandatory runtime package |
| `pip>=26.1.2,<27` | conda/bootstrap profile | installation tooling | exact hosted pin is 26.1.2; the reviewed floor closes archive, self-check/import, and entry-point path handling advisories |
| `setuptools>=83,<84` | build-system | wheel/sdist build | backend is `setuptools.build_meta`; the security-reviewed direct version is 83.0.0 |
| `wheel>=0.45,<0.47` | build-system | wheel build | tested direct version is recorded separately |
| `build>=1.2,<2` | `dev` extra | offline PEP 517 package smoke | invoked as `python -m build --no-isolation` |
| `cryptography>=50,<51` | `signing` extra | Ed25519 replay-receipt signing and public verification | lazily imported; not required for HMAC or other installed APIs; the reviewed floor closes the advisories affecting the older lane |
| `pytest>=9.0.3,<10` | `dev` extra | tests | plugin autoload is disabled in controlled gates; the floor closes the vulnerable tmpdir implementation |
| `ruff>=0.12,<1` | `dev` extra | static lint | target version is Python 3.11 |
| `tqdm>=4.66,<5` | `tools` extra | progress in Lean/hygiene scripts | not imported by the installed runtime API |
| `ipykernel>=6,<7` | `notebooks` extra | notebook kernels | optional |
| `jupyterlab>=4,<5` | `notebooks` extra | interactive notebooks | optional |
| SageMath | external | Sage-native parents/facades | not installable as a normal PyPI dependency; pure-Python fallbacks are separately tested |

Cryptography 50 publishes CPython macOS wheels for arm64, not Intel x86_64.
The signing extra therefore requires a source build with its native prerequisites
on Intel macOS unless a future reviewed wheel becomes available. The base
portable package does not import cryptography and remains independently tested;
base-package CI must not be reported as cross-platform signing evidence.
The hosted Linux Python job installs the exact signing version from binary
wheels and executes the deterministic Ed25519 replay test; macOS/Windows signing
remains outside that evidence.

The direct versions exercised by the maintained CPython 3.11.14 environment are
in `requirements/py311-tested.txt`. The CI bootstrap and its direct transitive
tools are exact in `requirements/ci-py311.txt`; that file installs pip,
setuptools, wheel, build/PEP 517 helpers, Pytest and its direct dependencies,
Ruff, tqdm, and the Windows `colorama` edge before the project is installed
with build isolation and dependency resolution disabled. CI installs the list
itself with `--no-deps`. It is an exact reviewed tool list, not a
hash-locked or platform-byte lock. Build-system ranges and optional extras are
the authoritative install metadata. `environment.yml` mirrors the direct conda
surface but is a solver input, not a complete transitive lock.

## Lean

All 47 sources target `leanprover/lean4:v4.30.0-rc2`. Their non-local imports
(`Init.GrindInstances.Ring.Fin`, `Lean.Elab.Tactic.Omega`, and `Std.Tactic`) are
provided by that Lean distribution; the project does not declare a Lake or
mathlib dependency. `elan` is the supported toolchain selector.

Portable compilation and hardened certificate renewal are distinct. See
`proofs/lean/README.md` and `platform-reproducibility.md`.

## Rust

`vam/native/Cargo.lock` pins `ed25519-dalek 2.2.0`, constrains `base64ct` to
MSRV-compatible `1.7.3` and `zeroize` to MSRV-compatible `1.8.2`, and pins the
resulting transitive graph for the Rust replay-bundle signature verifier. The
crate is configured without RNG
support: signing keys enter only through a borrowed library API and are never
generated, serialized, or logged; trust anchors remain external. VOR5 reuses
the exact closure for bounded threshold verification and caller-selected
rotation epochs; it adds no trusted-time, identity, attestation, or source-
validation dependency. The pinned
signing release declares Rust 1.81 compatibility, below this crate's tested
MSRV 1.83. The direct `base64ct` constraint also prevents a transitive
edition-2024/Rust-1.85 drift through `spki`.
`rust-toolchain.toml` selects Rust 1.95.0 with the minimal profile for
reproduced checks, while `Cargo.toml` declares locked MSRV 1.83. `rustfmt` is
required for the formatting gate.

Install the reproduced Rust lane with
`rustup toolchain install 1.95.0 --profile minimal --component rustfmt`. The
repository toolchain file records the same component set.

## System commands

| Command | Required where |
|---|---|
| `git` | source-checkout hygiene, package provenance snapshot, and contribution workflow |
| GNU Make + Bash | convenience wrapper and complete Linux `make verify` lane only |
| `elan` | whole-source Lean compilation |
| `rustup` | installs/selects reproduced Rust 1.95.0 and exact 1.83.0 for the declared-MSRV compatibility job; the `+toolchain` syntax requires rustup proxies |
| `cargo`, `rustc`, `rustfmt` | native VAM gate through the selected rustup toolchain |
| `sage` | real-Sage smoke/doctest lane |

The security-reviewed portable tool lane uses pip 26.1.2 on CPython 3.11,
while the latest complete Linux lane also records SageMath 10.7 and `elan`
4.2.1. These are environment inputs rather than mandatory PyPI runtime
dependencies. A portable run does not retroactively reproduce the complete
Linux proof lane.

Portable CI uses fixed hosted runner labels and CPython 3.11.9 on macOS and
Windows because setup-python does not provide 3.11.14 there. That matrix checks
the portable package and selected capability-free tests; it does not renew the
3.11.14-bound certificates or claim the complete Linux lane. Labels identify
OS families; GitHub's concrete hosted image revision remains a mutable input
recorded by each workflow run.

Windows users do not need Make or Bash for the portable gate. Every portable
entry point invokes subprocesses as argument arrays rather than shell strings.

## Updating dependencies

1. Change the bounded declaration in `pyproject.toml`, `environment.yml`, or the
   relevant toolchain file.
2. Refresh `requirements/py311-tested.txt` and `requirements/ci-py311.txt` only
   with versions actually tested; keep the latter's direct transitives complete.
3. Run `python scripts/package_smoke.py`, `python scripts/verify_portable.py`,
   and the relevant Lean/Rust/Sage gate.
4. Update this inventory and `CHANGELOG.md`; do not describe a resolver input as
   a hash lock or an unexecuted OS workflow as a pass.
