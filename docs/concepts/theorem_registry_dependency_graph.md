# Veyra theorem registry and dependency graph

## Aim

Theorem cards are useful only if they know what they depend on.  This layer adds a registry: every executable theorem card receives an ID, a claim, definition dependencies, success relations, known obstructions, and a Sage hook name.

## Registry primitives

### Theorem spec

A theorem spec is the non-executed contract:

```text
Spec = (id, title, claim, DEF-dependencies, success-relations, obstruction-catalog, sage-hook)
```

It is the bridge between documentation, code, proof checks, and Sage lab integration.

### Dependency edge

A dependency edge is a directed relation:

```text
TheoremID -> DEF-xxx
```

This lets us ask what a theorem needs before treating a card as meaningful.

### Registry check

A registry check combines a produced theorem card with its spec:

```text
Check(Spec, Card, KnownDEFs) -> ready | blocked
```

A card is `ready` only when all dependencies exist and the card relation is one of the spec's success relations.

### Obstruction catalog

Each spec lists allowed obstruction names.  This is important: failure is not noise.  It becomes structured mathematical data.

## Current geometry registry

Implemented specs:

1. `pythagorean-separation`
2. `sss-triangle`
3. `sas-triangle`
4. `line-shell-intersection`
5. `plane-relabel-composition`

Each has dependency edges into DEF-076..DEF-090 and a Sage hook placeholder like `geometry.pythagorean`.

## Executable layer

Implemented in `src/core/registry/theorem_registry.py`:

- `TheoremSpec` — registry contract.
- `RegistryCheck` — card validation result.
- `RegistrySummary` — registry health summary.
- `geometry_theorem_specs()` — built-in geometry theorem specs.
- `dependency_edges()` — graph edge emitter.
- `missing_dependencies()` — definition coverage check.
- `check_card()` — card/spec/dependency validator.
- `registry_summary()` — total edges and Sage hook readiness.

Tests in `tests/registry/test_theorem_registry.py` verify registry summary, dependency edges, ready Pythagorean card, missing-dependency blocking, card obstruction blocking, and tangent line-shell card readiness.

## School-program impact

This is the first layer where Veyra begins to replace not just concepts, but the **curriculum dependency graph**:

- definitions know which theorem cards consume them;
- theorem cards know their obstructions;
- failed cases become teachable counterexample paths;
- Sage can later call theorem hooks as executable proof/check objects.

## Next layer

Build the same registry discipline for algebra and analysis cards:

1. equation cards;
2. polynomial identity cards;
3. continuity/change/area cards;
4. cross-domain dependency map from arithmetic to geometry to analysis;
5. export registry summaries to Sage.
