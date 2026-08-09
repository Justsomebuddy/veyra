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

`veyra_sage.all.__all__` is the only supported public import surface for the Sage lab.  The exact symbol ledger lives in `docs/reference/veyra_sage_api.md` and is checked by `tests/sage/test_veyra_sage_api_index.py`.

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

## Core package layout

The core engine is grouped by subject rather than by file-name prefix. A
package exists for each area that has its own vocabulary and its own failure
modes: `certificates/` for executable certificate entry points, `observer/` for
observer-indexed semantics, `construction/` for bounded constructions,
`prime_power/` and `padic/` for the carrier families, `confluence/` and
`transport/` for the transport contracts, `registry/` for theorem, notation,
curriculum and promotion registries, `formal/` for Lean export catalogues,
`kernel/`, `language/`, `geometry/`, `numbers/`, `shadows/`, `quantum/`,
`ontology/`, and `surprise/` for the corresponding layers. A package that grows
its own internal vocabulary is split again, as `observer/network/` and
`padic/completion/` are; `tests/` mirrors the same grouping.

### Modules that stay flat

Some modules remain directly under `src/core/` because their location is itself
part of a hand-reviewed digest, and moving them would invalidate that digest
without changing any behaviour.

The Merkle source closures enumerated by the R10, R11, R12.5 and R13 bridges
are the largest group: `records_digest` hashes each file's relative path
together with its content, so a rename is indistinguishable from an edit. The
theorem-contract handlers form a second group, because their digests bind
`__module__`, `__qualname__` and CPython bytecode; editing so much as an error
message there renews a pinned constant. The `prime_power_unbounded_*` cluster
forms a third, since its exact path list is asserted as a review closure by the
P3-N6 tests.

Relocating any of these is a deliberate semantic and artifact review, never a
mechanical digest recompute.

### Legacy import compatibility

A relocated module keeps its former import path. `src/core/_legacy.py` installs
a meta-path finder driven by `src/core/legacy_modules.json`, so the old name
resolves to the module object at the canonical location: both names yield the
same object, the alias is registered in `sys.modules`, and the parent package
attribute is set. Existing `unittest.mock.patch` targets and subprocess import
snippets therefore keep addressing the same object. Modules migrated before the
alias layer existed carry their own explicit legacy `__module__` provenance for
pickling and log routing, which the alias layer does not disturb.

New code imports the canonical path. The alias layer can be retired once no
consumer outside `src/core/` refers to a former name.

Further layout changes follow the same bounded process: move one coherent
cluster, retain explicit compatibility imports, verify old and new object
identity, update the known consumers, and run focused semantic and hygiene
checks before starting the next cluster.

## Maintenance checklist

When changing `veyra_sage/` public surface:

- update `veyra_sage/all.py`;
- update `docs/reference/veyra_sage_api.md`;
- run `PYTHONPATH=. python3 -m pytest -q tests/sage/test_veyra_sage_api_index.py`;
- if the change is conceptual, update `THEOREMS.md` and `NOTATION.md`;
- follow `CONTRIBUTING.md` and update `CHANGELOG.md` plus relevant public documentation when behavior or meaning changes.
