# 48 — Veyra Sage Proof Graph

**Status:** implemented seed.
**Layer:** Sage-facing proof/check and dependency query facade.
**Goal:** let Sage labs inspect Veyra theorem dependencies and check executable theorem cards as proof objects.

## Why this layer exists

`VeyraSchoolCore` exposes what the school stack contains.
`VeyraProofGraph` exposes why it hangs together:

- theorem → definition dependency edges;
- theorem grouping by Sage-hook domain;
- theorem-card checks against success relations and obstruction catalogs;
- curriculum predecessor/successor queries;
- shortest curriculum paths.

This moves Veyra from a list of claims toward an inspectable proof/check graph.

## Objects

| Object | Meaning |
|---|---|
| `VeyraProofObject` | one theorem spec promoted to a Sage-facing check object |
| `VeyraProofCheck` | result of checking an executable card against a proof object |
| `VeyraProofGraph` | query facade over theorem dependencies and curriculum paths |

## Example

```python
from src.core.registry.depth_packs import binomial_symmetry_card
from veyra_sage.all import VeyraProofGraph

G = VeyraProofGraph()
P = G.proof_object("binomial-symmetry")
P.depends_on("DEF-117")
P.check(binomial_symmetry_card(6, 2)).status
G.curriculum_path("arithmetic-ratios", "statistics")
```

Expected signals:

```text
P.depends_on("DEF-117") == True
check.status == "ready"
path == ("arithmetic-ratios", "combinatorics", "probability", "statistics")
```

## Current scope

The graph is deliberately finite and school-core sized:

- `19` theorem specs;
- theorem-to-definition dependency edges from the registry;
- `12` curriculum edges;
- domain index from Sage hooks such as `geometry.*`, `probability.*`, `statistics.*`.

## Non-collapse rule

A proof object does not become a classical theorem by default.
It checks a Veyra theorem card against declared dependencies, success relations, and obstruction catalogs.

Classical shadows are allowed only as explicit card payloads or `.as_dict()` exports.

## Verification

Executable checks:

- `tests/sage/test_veyra_sage_proofs.py` — summary, domain index, dependency queries, card checks, curriculum paths.
- `tests/sage/test_veyra_sage.py` — certificate suite includes `sage_proof_graph_passed`.
- `scripts/sage_smoke.py` — prints graph summary and arithmetic-to-statistics path.
