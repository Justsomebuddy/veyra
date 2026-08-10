# Veyra package boundary

**Date:** 2026-06-05
**Decision:** `veyra_sage/` is a research laboratory first and a future Sage extension second.

## Boundary decision

The current project has two deliberately different layers:

| Layer | Path | Stability | Purpose |
|---|---|---|---|
| Core engine | `src/core/` | experimental but tested | native Veyra objects, theorem cards, language kernel, certificates |
| Sage lab facade | `veyra_sage/` | public research-lab API | Sage-style parents, wrappers, notebooks, refutations, and certificate smoke |
| Future package extension | not split yet | deferred | installable Sage extension after API churn slows |

`veyra_sage.all.__all__` is the only supported public import surface for the Sage lab.  The exact symbol ledger lives in `docs/reference/veyra_sage_api.md` and is checked by `tests/test_veyra_sage_api_index.py`.

## What is stable now

Stable enough for notebooks, examples, and tests:

- `VeyraSchoolCore`, theorem specs, curriculum nodes, export rows;
- proof graph/check wrappers;
- notebook builders and generated artifact summaries;
- modes, balances, ratios, and polynomial parent/element wrappers;
- language, essence, and proof-discipline lab summaries;
- refutation and refutation-search notebooks;
- `sage_certificate_suite()` as the executable health contract.

## What is intentionally unstable

The following are still research objects and should not be promised as package-level compatibility:

- internal dataclass field order outside documented wrappers;
- lower-level module imports not re-exported through `veyra_sage.all`;
- exact notebook cell counts except where certificates pin them;
- experimental native primitives before theorem cards and counterexample pressure exist;
- generated artifact paths beyond `notebooks/generated/` and manifest semantics.

## Promotion rule for a future Sage extension

A symbol can move from research-lab API to package-stable API only when it has all of:

1. documentation entry in `docs/reference/veyra_sage_api.md`;
2. at least one direct pytest or doctest;
3. certificate coverage or an explicit reason why certification is not meaningful;
4. no pending theorem-card dependencies;
5. a negative/counterexample story for claims that can fail;
6. import through `veyra_sage.all`.

## Current packaging posture

Do not split a separate Sage extension yet.  Keep one repository while the mathematical language and theorem-card registry are changing quickly.  The next packaging checkpoint should happen only after:

- Core Language semantics and proof discipline survive another major sprint;
- school-topic gap rows stop changing weekly;
- public API additions become mostly additive;
- generated notebooks are consumed outside this repository.

## Core package layout migration

The core engine is being reorganized in small compatibility-preserving slices
instead of one repository-wide move.  The first canonical construction package
is:

```text
src/core/construction/
└── finite_builder/
    ├── codec.py
    ├── digest.py
    └── types.py
```

Internal P1-B and scoped-formation consumers import these canonical modules.
The former flat modules, `src.core.finite_builder_codec`,
`src.core.finite_builder_digest`, and `src.core.finite_builder_types`, remain
lazy compatibility aliases: importing a legacy path installs its alias through
the ordinary import machinery, and old and new imports then resolve to the same
module object with a valid parent-package attribute. Functions, the codec
exception, loggers, dataclasses, and enums retain their legacy module provenance
for pickling, instrumentation, and log routing. Root exports, DTO fields, and
enum values remain unchanged. This preserves existing imports while giving new
code a cognitively local package boundary. The move changes no codec bytes,
digest domains, resource limits, or finite-construction semantics.

Further layout changes must follow the same bounded process: move one coherent
cluster, retain explicit compatibility imports, verify old/new object identity,
update only known consumers, and run focused semantic and hygiene checks before
starting another cluster.

## Maintenance checklist

When changing `veyra_sage/` public surface:

- update `veyra_sage/all.py`;
- update `docs/reference/veyra_sage_api.md`;
- run `PYTHONPATH=. python3 -m pytest -q tests/test_veyra_sage_api_index.py`;
- if the change is conceptual, update `THEOREMS.md` and `NOTATION.md`;
- follow `CONTRIBUTING.md` and update `CHANGELOG.md` plus relevant public documentation when behavior or meaning changes.
