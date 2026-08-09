# Contributing to Veyra

Contributions to code, proofs, documentation, counterexamples, and
reproducibility are welcome. This file is the policy;
[`AGENTS.md`](AGENTS.md) is the mechanical reference for layout, commands, and
pinned artifacts. Security-sensitive reports follow
[`SECURITY.md`](SECURITY.md) rather than a public issue, and community
expectations are in [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## Shared ground rules

These bind humans and agents alike.

### Claims and proofs

Label every addition as a definition, a bounded certificate, a checked proof
artifact, a relative result, a candidate, or an open question, and state its
assumptions, dependencies, failure modes, and non-claims alongside it. A
general theorem never follows from finite test coverage. Where a boundary can
be tested, add the adversarial case or counterexample that tests it. When a
public statement or symbol changes, `THEOREMS.md` and `NOTATION.md` change with
it.

Proof-source and digest bindings stay exact. Renewing a pinned digest is a
review of the underlying diff, not a recompute — see *Pinned artifacts* in
`AGENTS.md` for which files are bound and why.

### Code

Prefer small deterministic functions with explicit error paths, fail-closed
validation, and preserved resource limits. Cover the normal, boundary,
malformed, and hostile cases.

Decompose by meaning. A module owns one coherent concept, vocabulary, and public
responsibility; split it only when the extracted part has an independent
purpose and remains understandable on its own. File length is not a constraint:
a structured module of two or three thousand lines can be the clearest shape.
Conversely, splitting one concept into `_types`, `_validation`, `_runtime`, and
`_preflight` fragments that cannot stand alone makes navigation and review
harder without creating real module boundaries.

Resolve repository artifacts through `src/core/paths.py`, never against the
process working directory and never through a hardcoded `parents[N]` depth,
which is wrong the moment a module moves and fails silently when it does. A
test follows the same rule and must pass when `pytest` is invoked from any
directory. Commits carry no caches, generated binaries, credentials, or local
paths.

### Documentation

Write for a reader with no access to the conversation that produced the change.
A document states what is true of the repository, not what happened during a
session: no change narration, no counts or file totals that rot on the next
edit, no before-and-after framing. Prefer structured prose to long bullet
lists — a list is for genuinely enumerable things, not for sentences that lost
their verbs. Separate established results from proposals and future work, and
update `CHANGELOG.md` when user-visible behaviour or public mathematical status
changes.

### Public repository

Every tracked file, commit message, issue, pull request, and test artifact is
immediately public. Before committing, confirm that no credentials, personal
data, private paths, local workflow files, generated caches, raw dumps, or
unpublished research entered the change. If sensitive data was committed, stop:
a follow-up deletion does not remove it from history, so use the private path
in `SECURITY.md`. History rewriting is reserved for coordinated incident
response and requires an explicit public-impact review, backups, and
post-rewrite clone validation.

## For humans

Read `README.md` and `docs/concepts/foundational_gap_audit.md` first, search
existing issues and pull requests before proposing overlapping work, and open a
design issue before a large semantic, proof, or public API change.

Set up with:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Run the narrowest relevant checks while developing. Before requesting review,
run `ruff check` over the changed paths, `pytest -q` over the relevant tests,
and `git diff --check`; if all optional prerequisites are installed and the
change affects shared semantics, run `make verify`. State exactly which checks
ran, what they returned, and which did not run.

A pull request carries a concise problem statement, the chosen solution and the
alternatives considered, the mathematical scope with its assumptions and
non-claims, the tests and proof checks performed, the documentation and
registry changes, and any migration notes. Keep unrelated refactors separate;
review may ask for a smaller proof surface, more counterexamples, or narrower
wording.

## For agents

Everything above applies. In addition:

### Commits

Do not add `Co-Authored-By`, `Generated with`, or any other attribution trailer
to a commit message or pull request body.

One logical change per commit, with a descriptive Conventional Commit subject —
no WIP, no unrelated cleanup riding along. Stage explicit paths; `git add -A`
and `git add .` sweep in generated files. Re-read the finished commit rather
than the working-tree diff, require a clean worktree, verify the branch, and
push fast-forward only. Never `--force`, `--mirror`, `--all`, or routine
history rewriting.

### Scope

Keep it simple by default: choose the smallest change that solves the stated
problem, prefer editing an existing module to adding one, and prefer adding one
small module to introducing a layer.

Touch only what the task requires. Opportunistic reformatting, renaming, import
reordering, and drive-by refactors inflate the review surface and, in this
repository, can invalidate a pinned digest. Do not relocate or reformat
anything listed under *Pinned artifacts* in `AGENTS.md` unless the task is to
renew that digest. If the task is ambiguous in a way that changes the outcome,
ask before building.

### Verification

Run the full local gate and report its actual output:

```bash
make verify
```

If part of it cannot run — missing Lean, Rust, Sage, or a non-3.11 interpreter —
name what was skipped. A partial run is never a pass, and test coverage never
becomes a stronger mathematical claim.

State what changed, what was verified and how, and what remains unverified. If
a pinned digest changed, name the constant, the file, and the reason: the
renewal is only as good as the human review of the diff underneath it.

---

By contributing, you agree that your contribution is licensed under the MIT
License in `LICENSE`.
