# Repository map

Mechanical reference for coding agents: where things live, how to run them, and
which parts bite. Policy — commit rules, scope discipline, what to run before
committing — is in [`CONTRIBUTING.md`](CONTRIBUTING.md) under **For agents**.
Read that first.

## Top level

| Path | Purpose |
|---|---|
| `src/core/` | executable semantics, certificates, bounded constructions |
| `proofs/lean/` | exact Lean sources and proof notes |
| `docs/` | `concepts/` explanation, `reference/` registries, `log/` sprint reports, `tutorials/` introductions, `releases/` archived history |
| `tests/` | unit, adversarial, and certificate tests, grouped like `src/core` |
| `vam/` | Veyra Abstract Machine experiments |
| `veyra_sage/` | Sage-facing finite facades and notebook helpers |
| `scripts/` | certificate and artifact generation entry points |
| `experimental/omegaa/` | isolated unfinished research; not installed or verified |
| `THEOREMS.md` | statement classification and status |
| `NOTATION.md` | notation registry |

Before changing anything semantic, read `docs/concepts/manifesto.md`,
`docs/concepts/primitives.md`, `docs/concepts/discovery_report.md`,
`docs/log/proof_discipline.md`, and `docs/concepts/foundational_gap_audit.md`, in that
order. [`docs/concepts/package_boundary.md`](docs/concepts/package_boundary.md) states the
`src/core` ↔ `veyra_sage` boundary and the layout-migration process.

## Layout

`src/core/` is grouped by subject: `certificates/`, `observer/`,
`construction/`, `prime_power/`, `confluence/`, `padic/`, `registry/`,
`shadows/`, `transport/`, `numbers/`, `quantum/`, `formal/`, `ontology/`,
`surprise/`, `geometry/`, `kernel/`, `language/`. Most modules still sitting
flat at `src/core/` are the digest-pinned ones described under *Pinned
artifacts*, and those must stay where they are. The `observer_synthesis_v2*`
cluster is the exception: it is flat because its worker and subprocess import
protocol has not yet been migrated, and it is bound by no proof closure. The
smaller synthesis v1 surface lives in `observer/synthesis.py`.

Former flat import paths still resolve. `src/core/_legacy.py` maps each of them
to its canonical module through `src/core/legacy_modules.json` and returns the
same module object, so old imports and `patch()` targets keep working. Write new
code against the canonical path.

`tests/` mirrors those groups and adds `tests/vam/`, `tests/sage/`,
`tests/proof/` for the pinned TCB cluster, and `tests/meta/` for checks on the
repository itself. A helper module shared by one group lives in that group's
directory; `tests/fixtures/` holds data and subprocess entry points used across
groups.

## Environment

The project needs **CPython 3.11 or newer**. Proof-handler contracts bind the
source text that defines each handler, so the pinned digests reproduce on any
supported interpreter; `make test` and `make cert` check the floor and say so
plainly. Lean `leanprover/lean4:v4.30.0-rc2` via `elan`, `cargo`/`rustc`, and
SageMath are needed only for their corresponding checks.

The R10 runtime guard needs Linux `inotify`. Elsewhere the module still imports
and `inotify_supported()` reports `False`; guarded Lean runs then fail closed
with `r10-runtime-watch-platform-unsupported` rather than running unwatched.

## Commands

```bash
make help        # list commands
make test        # pytest suite
make cert        # executable certificate suite
make sage-smoke  # Sage facade smoke checks
make hygiene     # cache-ignore hygiene
make verify      # test + cert + sage + hygiene
make tables      # regenerate processed table artifacts
make notebooks   # regenerate Sage-lab notebook artifacts
```

Select an interpreter with `PYTHON=python3.11 make <target>`. Generated output
under `data/processed/`, `data/tmp/`, and `notebooks/generated/` is
deterministic for the checked inputs and untracked; machine timings are not
mathematical evidence.

## Conventions

**Paths.** Resolve every repository artifact through
[`src/core/paths.py`](src/core/paths.py) — `PROJECT_ROOT`, `LEAN_DIR`,
`TMP_DIR`. Never resolve against the process working directory, and never
hardcode a `parents[N]` depth: the depth is wrong the moment the module moves,
and it fails silently. Repository-relative *strings* hashed into proof ledgers
are identities rather than locations, so they stay relative and are not derived
from these values.

**Tests.** A test addresses repository files the same way library code does,
through `src.core.paths`. Tests that must not import the package — those that
build a synthetic package to isolate a module under audit — locate the root by
walking up to `pyproject.toml`, and `tests/conftest.py` offers `repo_root`,
`lean_dir`, and `tmp_artifacts` fixtures for the same purpose. A test must pass
when `pytest` is invoked from any directory; nothing may depend on the caller's
working directory. Cover the normal, boundary, malformed, and hostile cases,
and keep each test's failure message specific enough to name what broke.

**Module boundaries.** Decompose by meaning. A module owns one coherent concept,
vocabulary, and public responsibility. Split it only when a part has an
independent purpose and can be understood as a complete module of its own.
File length is not an architectural constraint: a well-structured module may
legitimately span several thousand lines. Names ending in `_types`,
`_validation`, `_runtime`, or `_preflight` are a warning sign when those files
cannot stand on their own; merge such fragments when they are merely phases of
one concept and are not digest-pinned.

**Public surface.** `veyra_sage.all.__all__` is the only supported public import
surface. Its ledger is
[`docs/reference/veyra_sage_api.md`](docs/reference/veyra_sage_api.md), checked
by `tests/sage/test_veyra_sage_api_index.py`.

**Documentation.** Write for a reader with no access to the conversation that
produced the change. Documents state what is true of the repository, not what
happened during a session: no change narration, no counts that will rot, no
before-and-after. File names carry no chronology — git history and
`CHANGELOG.md` already do. Durable explanation goes in `docs/concepts/`,
registries in `docs/reference/`, dated sprint reports in `docs/log/`, and
practical introductions in `docs/tutorials/`. `docs/index.md` is a short
hand-written entry point, not an exhaustive file catalog: keep it selective,
point readers to stable concepts and registries, and give every documentation
directory at least one link so nothing becomes unreachable. `tests/meta/`
fails on a broken markdown link and on any documentation reference to a path
that does not exist; it does not check that the index is complete.

**Environment-gated tests.** Mark anything reaching the Lean toolchain with
`pytest.mark.requires_lean` and anything needing Linux-only kernel interfaces
with `pytest.mark.requires_linux`. `tests/conftest.py` skips them when the
environment cannot provide them, so an absent toolchain reads as absent rather
than as a broken proof.

## Pinned artifacts — do not move or reformat

Parts of `src/core` are bound by hand-reviewed digests, so renaming,
relocating, or reformatting them breaks the proof ledger even when the change is
semantically neutral.

The **Merkle source closures** are enumerated by `observer_core_bridge.py`,
`proof_elaboration_bridge.py`, `intrinsic_observer_echo_formal_bridge_core.py`,
`intrinsic_vam_formal_bridge_core.py`, and `intrinsic_mode_bridge.py`.
`records_digest` in `proof_elaboration_toolchain.py` hashes each file's relative
path together with its content, so a move alone invalidates the digest. Expected
values live in the `*_manifest.py` modules and are declared an externally
reviewed manual trust root.

**Handler source and module identity** are bound by
`layer_theorem_contract_executable.py`, which digests `__module__`,
`__qualname__`, and the defining source text of the handler functions pinned in
`layer_theorem_contract_handlers.py`. Editing a handler — including a comment
inside one — renews `R13_TRUSTED_EXECUTABLE_DIGEST` and, because the contract
object carries that value, `R13_TRUSTED_CONTRACT_DIGEST` with it.

A **path review closure** in the P3-N6 tests asserts the exact
`src/core/prime_power_unbounded_*.py` path list, and those same tests load
`padic.completion.core` and `padic.family_introduction.core` by dotted string
into a synthetic package. That import bypasses `_legacy.py`, so those two
modules are pinned by path: merging either package into a single module breaks
the closure even though every ordinary import still resolves. Separately,
`src/core/certificates/vam.py` decides certificate capability from `.exists()`
checks against `vam/` and `tests/vam/` paths, so moving those files silently
downgrades the certificate instead of failing.

A per-file digest is a plain sha256 of the file bytes and can be recomputed. The
aggregate `binding_digest` values additionally bind the Lean artifact and
toolchain identity, so renewing them needs Linux with the pinned toolchain.
Either way the renewal is a review of the underlying diff, never a recompute.
