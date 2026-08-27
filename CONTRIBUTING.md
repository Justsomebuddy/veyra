# Contributing to Veyra

Thank you for helping improve Veyra. Contributions to code, proofs,
documentation, counterexamples, and reproducibility are welcome.

## Before starting

1. Read `README.md` and `docs/102_foundational_gap_audit.md`.
2. Search existing issues and pull requests before proposing overlapping work.
3. Open a design issue before a large semantic, proof, or public API change.
4. Keep every claim within the exact observer, doctrine, ledger, and finite or
   all-depth scope that supports it.

Security-sensitive reports must follow `SECURITY.md`, not a public issue.

## Public repository workflow

This repository is the canonical public project. Treat every tracked file,
commit message, issue, pull request, and test artifact as immediately public.

Before committing:

1. Synchronize with `main` and inspect `git status`, the staged path list, and
   the complete staged diff.
2. Stage only the explicit paths intended for the change; avoid broad staging
   that can silently include unrelated or newly generated files.
3. Confirm that no credentials, personal data, private paths, local workflow
   files, generated caches, raw dumps, or unpublished research entered the
   change.
4. Keep one logical change per commit and use a descriptive Conventional
   Commit subject. Do not publish WIP or unrelated cleanup in the same commit.
5. Update code, tests, public documentation, `CHANGELOG.md`, theorem status,
   notation, and evidence registries together whenever the change affects them.
6. Run the narrowest relevant checks plus repository hygiene, and state exactly
   what passed, failed, or was not run. Never convert test coverage into a
   stronger mathematical claim.

Before pushing:

- re-read the final commit rather than only the working-tree diff;
- require a clean worktree and verify the intended branch and exact destination
  `https://github.com/Justsomebuddy/veyra`;
- use a normal fast-forward push; do not use `--force`, `--mirror`, `--all`, or
  routine history rewriting;
- use a pull request for substantial semantic, proof, API, dependency, or
  repository-policy changes;
- stop immediately if sensitive data was committed. A follow-up deletion does
  not remove it from history; use the private reporting path in `SECURITY.md`.

History rewriting is reserved for coordinated incident response and requires
an explicit public-impact review, backups, and post-rewrite clone validation.

## Development setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --no-deps -r requirements/ci-py311.txt
python -m pip install --no-build-isolation --no-deps -e .
```

On Windows PowerShell, create and activate the environment with:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --no-deps -r requirements/ci-py311.txt
python -m pip install --no-build-isolation --no-deps -e .
```

Use a CPython 3.11 patch release for the portable surface; the complete
hardened lane still requires CPython 3.11.14. The shell-neutral onboarding gate is
`python scripts/verify_portable.py`; see
`docs/reference/platform-reproducibility.md` for platform limitations.

Run the onboarding checks:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  python -m pytest -q tests/test_axiom_kernel.py tests/test_approx_resonance.py
python -m ruff check src tests
```

Some proof and native checks additionally require the pinned Lean version,
Rust, or SageMath. See `README.md`, `proofs/lean/README.md`, and the platform
reproducibility contract.

## Contribution standards

### Claims and proofs

- Label additions as definitions, bounded certificates, checked proof
  artifacts, relative results, candidates, or open questions.
- Do not infer a general theorem from finite test coverage.
- State assumptions, dependencies, failure modes, and non-claims next to the
  result.
- Add adversarial cases or counterexamples when a boundary can be tested.
- Update `THEOREMS.md` and `NOTATION.md` whenever a public statement or symbol
  changes.
- Use silence/status tokens exactly as fixed in
  `docs/reference/silence-status-map.md`; the bare token `ABSENT` is
  deprecated in new text, and adding, renaming, or re-partitioning any
  silence row requires a `docs/102_foundational_gap_audit.md` amendment in
  the same change.
- Never use `proved` as an executable/runtime status token; reserve it for
  the registry's formal rungs and use `witnessed`/`refuted`/`blocked` for
  bounded executable checks.
- Any edit to `docs/102_foundational_gap_audit.md` must append a row to its
  append-only Amendment log in the same change.
- Keep proof-source and digest bindings exact where an existing contract
  requires them.

### Code

- Prefer small, deterministic functions with explicit error paths.
- Preserve resource limits and fail-closed validation.
- Host `==`, integers, and ordering may carry mathematical content only in
  declared shadow modules under the `docs/06_echo_tests.md` §3 license;
  native decision paths must be observer-indexed or orbit/rotation-invariant,
  and display-only canonicalizations must be labeled as such.
- Add tests for normal, boundary, malformed, and hostile inputs.
- Do not commit caches, generated binaries, credentials, or local paths.
- Keep active source and documentation files at or below the project's
  1000-line target and split modules when that improves cohesion and review.
  A file may exceed 1000 lines only through an explicit path-bound hygiene
  exception explaining why a split would reduce readability; no file may
  exceed the absolute 2000-line maximum. Remove the exception when the file
  returns to 1000 lines or fewer.

### Documentation

- Write for readers without access to unpublished context.
- Use repository-relative paths.
- Separate established results from proposals and future work.
- Update `CHANGELOG.md` for user-visible behavior or public mathematical
  status changes.

## Testing

Run the narrowest relevant checks while developing. Before requesting review,
run at least:

```bash
python -m ruff check <changed-python-paths>
python -m pytest -q <relevant-test-paths>
git diff --check
```

If all optional prerequisites are installed and the change affects shared
semantics, run:

```bash
make verify
```

State exactly which checks ran, their results, and which checks did not run.

## Pull requests

A pull request should include:

- a concise problem statement;
- the chosen solution and alternatives considered;
- mathematical scope, assumptions, and non-claims;
- tests and proof checks performed;
- documentation and registry changes;
- compatibility or migration notes when relevant.

Keep unrelated refactors separate. Review may request a smaller proof surface,
additional counterexamples, or narrower wording before acceptance.

By contributing, you agree that your contribution is licensed under the MIT
License in `LICENSE` and that you will follow `CODE_OF_CONDUCT.md`.
