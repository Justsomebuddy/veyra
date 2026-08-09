# Veyra

Research software for rebuilding mathematics from finite distinctions instead
of sets, points, equality, or metric space. It studies observable residues,
recurrence, and transport between observer contexts through executable Python
semantics, Lean artifacts, finite counterexample searches, proof ledgers, and
an experimental abstract machine.

> **Not a finished foundation of mathematics.** Executable certificates are
> evidence about exact finite contracts. They are not general theorems,
> ontological proofs, or claims about physical reality.

Release line **4.3.1**. Package **`veyra-core` 2.99.0**. MIT licensed.

## Install

Requires **CPython 3.11 or newer** and `make`.

```bash
git clone https://github.com/Justsomebuddy/veyra.git veyra
cd veyra
python3.11 -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Conda: `conda env create -f environment.yml && conda activate veyra-core`.

Nix provides reproducible shells for the same layers:

```bash
nix develop          # Python checks plus cargo and its matching rustc
nix develop .#full   # additionally exposes elan for pinned Lean checks
nix develop .#sage   # additionally exposes SageMath
nix flake check      # platform-independent CI gate
```

Optional, per check: Lean `leanprover/lean4:v4.30.0-rc2` via `elan`, a stable
`cargo`/`rustc` for the native VAM, SageMath for Sage sessions. Lean commands
are in [`proofs/lean/README.md`](proofs/lean/README.md).

## Run

```bash
make help    # list commands
make test    # pytest suite
make cert    # executable certificates
make verify  # everything, needs the optional prerequisites
```

## How to read claims

Evidence levels are not interchangeable:

| Level | Meaning |
|---|---|
| definition | introduces a term or structure |
| executable certificate | a bounded computation over an exact contract |
| checked proof artifact | a theorem checked from stated source and assumptions |
| relative result | holds only under a named doctrine, ledger, observer, or finite scope |
| candidate | proposed, not adopted |
| open | not established |

Passing tests does not promote a candidate; only an explicit registry entry
does, carrying its dependencies and non-claims.

## Vocabulary

- **rez** — an act of distinction;
- **nod** — a stable residue or boundary left by a rez;
- **tact** — a registered transition between nods;
- **breath** — a directed finite tether of tacts;
- **mode** — a closed breath, recurrence returning to its boundary.

Arithmetic appears as conservative finite shadows of closed modes. That is a
consistency anchor, not a reduction of mathematics to Veyra.

## Status

An immutable 77-certificate snapshot passed the comprehensive verification
pipeline and source-continuity check. Later work has passed focused test and
proof checks only; the current tree has **not** completed a new comprehensive
run. No focused result replaces the snapshot-wide one.

[`experimental/omegaa/`](experimental/omegaa/) holds unfinished kernel research
outside stable Core: no complete checker, soundness theorem, authority rule,
registry admission, or release. Excluded from installation and `make verify`.

## Where to look

| | |
|---|---|
| [`THEOREMS.md`](THEOREMS.md) | authoritative statement classification |
| [`NOTATION.md`](NOTATION.md) | notation registry |
| [`CHANGELOG.md`](CHANGELOG.md) | release history |
| [`docs/concepts/foundational_gap_audit.md`](docs/concepts/foundational_gap_audit.md) | the non-claim baseline: what is open |
| [`docs/index.md`](docs/index.md) | documentation entry point |
| [`AGENTS.md`](AGENTS.md) | repository map, commands, pinned artifacts |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | contribution policy |
| [`CITATION.cff`](CITATION.cff) | cite the exact release or commit; ledgers evolve |
