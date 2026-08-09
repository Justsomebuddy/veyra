# Veyra curriculum map

## Aim

This layer converts the growing Veyra stack into a school-core curriculum map.  The goal is not only to define objects, but to know what part of the school program is covered, what depends on what, what remains missing, and which theorem cards can be exported to Sage.

## Curriculum primitives

### Curriculum node

A node is a compact concept bucket:

```text
Node = (concept-id, title, domain, grade-band, DEF list, theorem-card IDs, status)
```

Examples: `linear-equations`, `polynomials`, `analysis-seeds`, `geometry-events`.

### Curriculum edge

An edge is a directed learning/dependency relation:

```text
source -> target : relation
```

Examples: arithmetic enables algebra; functions refine into analysis; geometry feeds proof registry.

### Curriculum gap

A compact gap is either a non-covered curriculum node or a covered node with missing theorem specs.  The compact node ledger currently has no gaps.  Deeper school-to-11 work is tracked separately by topic rows in `src/core/registry/curriculum_topics.py` and `docs/concepts/curriculum_core_language_v08.md`.

### Sage export row

A Sage export row is:

```text
(concept-id, domain, theorem-id, sage-hook)
```

This is the bridge from project documentation into executable Sage parent/check objects.

## Current compact coverage snapshot

Implemented in `src/core/registry/curriculum_map.py`:

- 11 curriculum nodes;
- 12 dependency edges;
- 11 covered nodes;
- 0 compact missing nodes;
- 19 Sage export rows from theorem-card registry specs.

Covered domains:

- arithmetic/rational shadows;
- linear equations;
- polynomial algebra;
- combinatorics;
- function transformers;
- continuity/drift/area analysis seeds;
- event/corridor geometry;
- theorem-card registry;
- cyclic trigonometry seeds;
- finite probability laws;
- sample statistics seeds.

## Topic-level map after Core Language v0.8

`src/core/registry/curriculum_topics.py` adds `SchoolTopicCoverage` rows:

```text
TopicRow = (topic, domain, native definition, school shadow, example,
            counterexample, test path, Sage row, status, required primitives)
```

Current topic ledger:

- 15 topic rows;
- 11 covered rows;
- 3 seeded rows needing deeper theorem cards or facades;
- 1 gap row needing a new primitive family.

Remaining non-covered rows are:

- `trigonometry-identities` — seeded angle-composition/identity pack;
- `calculus-depth` — seeded by local linearization, product/chain derivative cards, and integral coherence;
- `statistics-inference` — seeded distribution/sampling/uncertainty certificates;
- `vectors-matrices` — seeded vector/matrix action plus determinant/eigen shadows.

See `docs/concepts/curriculum_core_language_v08.md` for the full native-definition/shadow/example/counterexample table.

## Executable layer

Functions:

- `school_curriculum_nodes()`
- `curriculum_edges()`
- `missing_curriculum_concepts()`
- `domain_coverage()`
- `sage_export_rows()`
- `curriculum_summary()`
- `school_topic_coverage_rows()`
- `school_topic_gap_rows()`

Tests in `tests/registry/test_curriculum_map.py` verify summary counts, cross-domain edges, compact gap detection, domain coverage, Sage export rows, and the Core Language v0.8 topic contract.

## Why this matters

This is the global map of Veyra mathematics. It tells us where Veyra already replaces school apparatus, where it only has seeds, and what must be invented next. It also prevents false completeness claims: deeper gaps are explicit objects in the system even when compact node coverage is complete.

## Next layer

1. promote trig identity pack from `seeded` to `covered`;
2. extend trigonometry identities toward inverse trig/equation normal forms;
3. extend calculus-depth beyond polynomial shadows toward transcendental/limit algebra;
4. expand statistics-inference beyond finite radius checks into concentration/likelihood geometry;
4. define vector/matrix parent objects and determinant/eigen shadows.
