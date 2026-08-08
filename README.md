# Veyra

Veyra is a new attempt to rethink mathematics and explore new approaches to
number theory. It is research software for studying mathematics through finite
distinctions, observable residues, recurrence, and transport between observer
contexts. The project combines executable Python semantics, Lean artifacts,
finite counterexample searches, proof ledgers, and an experimental abstract
machine.

> **Research status:** Veyra is not a finished foundation of mathematics.
> Executable certificates are evidence about exact finite contracts; they are
> not automatically general theorems, ontological proofs, or claims about
> physical reality.

The project release line is **4.3.1**. The installable Python package is
**`veyra-core` 2.99.0**.

## Central idea

Veyra begins with distinctions and the stable residues they leave, rather than
assuming sets, points, equality, or metric space as primitives. Its initial
vocabulary is:

- **rez** — an act of distinction;
- **nod** — a stable residue or boundary left by a rez;
- **tact** — a registered transition between nods;
- **breath** — a directed finite tether of tacts;
- **mode** — a closed breath, interpreted as recurrence returning to its
  boundary.

Arithmetic first appears through conservative finite shadows of closed modes.
These shadows provide a consistency anchor; they do not establish that all
mathematics reduces to Veyra.

## Public status

### Released, bounded results

The public registry currently includes:

- finite observer-indexed echo relations and obstruction-aware semantics;
- exact finite translation, refinement, and declared-confluence contracts;
- bounded productive processes and explicitly ledger-relative all-depth
  families;
- a concrete prime-power compatible-family carrier with canonical finite-stage
  operations, relative to its stated doctrine and proof ledger;
- finite prime-power reduction and transport networks;
- checked Lean artifacts for exact statements listed in `proofs/lean/`;
- finite abstract-machine parsing, execution, and conservative optimization
  experiments.

The authoritative classification is in [`THEOREMS.md`](THEOREMS.md). Notation
is registered in [`NOTATION.md`](NOTATION.md), and release history is recorded
in [`CHANGELOG.md`](CHANGELOG.md).

### Research candidates and open questions

The following remain open or candidate-level unless a registry entry says
otherwise:

- observer genesis beyond an explicitly supplied finite history;
- universal translation or refinement between arbitrary observers;
- unrestricted confluence or Church–Rosser results;
- a general passage from finite productivity to an all-depth family;
- completed infinity independent of a stated construction principle;
- generic, categorical, or topological completion;
- absolute objecthood, observer-independent identity, physical realization, or
  metaphysical necessity;
- field structure or equivalence with an external p-adic library;
- adoption of the candidate modal kernel as an authoritative foundation.

The foundational gap audit in
[`docs/102_foundational_gap_audit.md`](docs/102_foundational_gap_audit.md) is the
non-claim baseline. The
[`six closure principles`](docs/154_six_closure_principles.md) separate
ontological, semantic, constructive, and provenance obligations without
silently promoting one into another.

## Verification status

An immutable 77-certificate snapshot completed the comprehensive verification
pipeline and source-continuity check. Work added after that snapshot has focused
test and proof checks, but the complete current tree has not yet completed a new
comprehensive verification run. The changelog and registry preserve this
boundary; no later focused result should be read as a replacement for the
snapshot-wide result.

## Repository map

| Path | Purpose |
|---|---|
| `src/core/` | executable semantics, certificates, and bounded constructions |
| `proofs/lean/` | exact Lean sources and proof notes |
| `docs/` | research compendium and status boundaries |
| `tests/` | unit, adversarial, and certificate tests |
| `vam/` | Veyra Abstract Machine experiments |
| `experimental/omegaa/` | isolated unfinished Omega-A checker research; not installed or verified by default |
| `veyra_sage/` | Sage-facing finite facades and notebook helpers |
| `scripts/` | certificate and reproducibility entry points |
| `THEOREMS.md` | definitions, propositions, proof artifacts, and statuses |
| `NOTATION.md` | notation registry |

Start with:

1. [`docs/00_manifesto.md`](docs/00_manifesto.md)
2. [`docs/01_primitives.md`](docs/01_primitives.md)
3. [`docs/04_discovery_report.md`](docs/04_discovery_report.md)
4. [`docs/67_proof_discipline.md`](docs/67_proof_discipline.md)
5. [`docs/102_foundational_gap_audit.md`](docs/102_foundational_gap_audit.md)

## Installation

### Python environment

Requirements:

- Python 3.11 or newer;
- `make` for the provided command shortcuts;
- optional external components listed below for the broader proof and native
  checks.

```bash
git clone https://github.com/Justsomebuddy/veyra.git veyra
cd veyra
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Conda users can instead create the maintained environment:

```bash
conda env create -f environment.yml
conda activate veyra-core
python -m pip install -e .
```

### Optional proof and native components

- Lean: `leanprover/lean4:v4.30.0-rc2` through `elan`;
- Rust: a stable `cargo`/`rustc` installation for native VAM checks;
- SageMath for Sage-specific interactive use.

The exact Lean commands for published artifacts are listed in
[`proofs/lean/README.md`](proofs/lean/README.md).

## Testing and reproducibility

Show available commands:

```bash
make help
```

Run a focused Python-only onboarding check:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  python -m pytest -q tests/test_axiom_kernel.py tests/test_approx_resonance.py
```

Run the active test suite:

```bash
make test
```

Run executable certificates:

```bash
make cert
```

Run the complete project pipeline only after the optional prerequisites are
available. It can be substantially longer than the focused checks:

```bash
make verify
```

Regenerate published tables or notebook artifacts with:

```bash
make tables
make notebooks
```

Generated output is deterministic for the checked inputs, but machine-level
timings are not treated as mathematical evidence. Proof artifacts bind exact
source bytes, statements, and declared assumptions where their documentation
says so.

## How to read claims

Veyra uses several evidence levels that must not be collapsed:

- **definition** — introduces a term or structure;
- **executable certificate** — a bounded computation over an exact contract;
- **checked proof artifact** — a theorem checked from the stated source and
  assumptions;
- **relative result** — valid only under a named doctrine, ledger, observer, or
  finite scope;
- **candidate** — proposed but not adopted as a theorem or foundation rule;
- **open** — not established by the current project.

Passing tests does not promote a candidate. A statement changes status only
through an explicit registry entry with its dependencies and non-claims.

## Experimental Omega-A

[`experimental/omegaa/`](experimental/omegaa/) preserves unfinished kernel
research outside stable Core. Its prerequisites and prototypes are available
for inspection, but KCS is unfinished and KEC has unresolved findings. It has
no complete checker, soundness theorem, authority rule, registry admission,
production API, or release. Default installation and `make verify` exclude it.

The conceptual boundary is documented in
[`docs/156_omegaa_semantic_authority_ladder.md`](docs/156_omegaa_semantic_authority_ladder.md).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for setup, claim discipline, test
expectations, and review requirements. Please use
[`SECURITY.md`](SECURITY.md) for vulnerability reports and
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) for community expectations.

## Citation

Citation metadata is provided in [`CITATION.cff`](CITATION.cff). Cite the exact
release or commit used, because proof ledgers and certificate boundaries evolve.

## License

Veyra is distributed under the [MIT License](LICENSE).
