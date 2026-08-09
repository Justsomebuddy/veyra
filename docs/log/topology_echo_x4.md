# X4 — Topology from deformation-invariant echoes

**Date:** 2026-07-07  
**Status:** Sprint X4 closed as a finite topology-echo layer.  
**Implementation:** `src/core/geometry/topology_echo.py`, `src/core/certificates/topology.py`, `veyra_sage/topology_echo.py`.  
**Certificate:** `topology_echo_x4`.

## Claim boundary

X4 does **not** claim full topology. It adds executable finite tests for topology-like echoes over Veyra corridor and shell shadows:

- shape data are finite nodes plus undirected corridor echoes;
- deformation tests are relabels, corridor subdivisions, collapses, or tears;
- accepted claims are exactly invariant rows under the declared deformation;
- failed claims are kept as explicit obstruction cards.

This keeps topology language inside the same bounded Math Master discipline as the earlier theorem cards: every claim has a row, a certificate, and a test.

## Core rows

| Row | Meaning |
|---|---|
| `EchoShape` | finite corridor/shell shadow with nodes, corridors, kind, component count, boundary count, and cycle rank |
| `DeformationEchoRow` | before/after invariant comparison for one finite deformation |
| `TopologyObstructionCard` | blocked deformation that changes a declared topology-like echo |

Supported invariants:

| Invariant | Computation |
|---|---|
| `components` | finite connected-component count |
| `boundary` | number of degree-one boundary nodes |
| `cycle-rank` | `edges - nodes + components` |

## Positive deformation echoes

| Example | Deformation | Invariant rows |
|---|---|---|
| `corridor -> corridor_drift` | subdivide corridor `A-B` by inserted node `X` | `components=1`, `boundary=2` stay invariant |
| `shell -> shell_relabel` | relabel `A,B,C` to `X,Y,Z` | `cycle-rank=1`, `boundary=0` stay invariant |

These are deliberately small fixtures. The point is not graphical richness; the point is that deformation-invariant claims are executable and regressible.

## Obstruction cards

| Card | Deformation | Broken invariant | Obstruction |
|---|---|---|---|
| `corridor-tear` | drop corridor `B-C` | `components: 1 -> 2` | `component-split` |
| `shell-collapse` | collapse `C -> A` | `cycle-rank: 1 -> 0` | `cycle-collapse` |

The obstruction cards prevent accidental overclaiming: if a deformation changes the finite invariant, the row is blocked rather than silently accepted.

## Sage surface

`VeyraTopologyLab` exposes JSON-ready rows:

- `shape_rows()` — all default corridor/shell shapes with invariant counts;
- `invariant_rows()` — positive deformation-invariant rows;
- `obstruction_rows()` — blocked non-invariant deformations;
- `checklist()` and `summary()` — Sprint X4 acceptance surface;
- `build_topology_echo_notebook()` — generated global notebook.

The generated artifact is tracked as `notebooks/generated/global/topology_echo.*`. Current generated notebook inventory after X4 is `40` notebooks and `275` cells.

## Verification

```bash
PYTHONPATH=. python3 -m pytest -q tests/geometry/test_topology_echo.py tests/sage/test_veyra_sage_topology_echo.py tests/shadows/test_certify.py tests/sage/test_veyra_sage.py
the complete verification suite
```

Expected contract:

- `topology_echo_x4` passes;
- `topology_echo_summary()` reports `shapes=4`, `invariant_hits=4`, `blocked=2`;
- `topology_echo_lab_summary()` reports the same rows through the Sage facade;
- global generated notebook artifacts report `40` notebooks / `275` cells.
