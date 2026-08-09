# Veyra geometry theorem cards

## Aim

This layer turns the event/corridor geometry into executable theorem cards.  A theorem card is a small certificate: it names the claim, states whether the relation is proven under the current observer, records obstruction if blocked, and keeps exact evidence.

## Cards implemented

### Pythagorean separation

For an apex event `A` and leg events `B,C`:

```text
Dot(A→B, A→C)=0  =>  Sep²(B,C)=Sep²(A,B)+Sep²(A,C)
```

The card refuses non-right apexes instead of pretending the theorem applies.

### SSS triangle card

`SSS△` reuses triangle signatures: sorted side echoes plus optional turn orientation.  With turn preservation enabled, mirrored triangles are obstructed as `turn-mismatch`.

### SAS triangle card

The SAS analogue compares two side echoes and the included dot echo:

```text
Sep²(A,B), Sep²(A,C), Dot(A→B,A→C)
```

This avoids importing angle magnitude; the angle is represented by the dot observer.

### Corridor-shell intersection

A corridor against a constant-separation shell becomes a quadratic in the corridor parameter:

```text
Sep²(C, A+t(B-A)) = r²
```

Exact rational parameters are returned.  Irrational parameters are labeled `completion-needed`, linking back to the completion layer.

### Plane relabel composition

Affine relabels compose as expected:

```text
Outer(Inner(E)) = (Outer∘Inner)(E)
```

The card checks the equality on an event shadow.  This is the seed of a transform-family algebra.

## Executable layer

Implemented in `src/core/geometry/theorems.py`:

- `TheoremCard` and `IntersectionCard`.
- `dot_echo()` and `dot_vectors()`.
- `pythagorean_card()`.
- `sss_card()` and `sas_card()`.
- `line_shell_intersections()`.
- `identity_relabel()`, `compose_relabels()`, `relabel_composition_card()`.

Tests in `tests/geometry/test_geometry_theorems.py` verify right and blocked Pythagorean cards, SSS/SAS congruence, two/tangent/no line-shell intersections, identity relabeling, and relabel composition.

## School-program coverage

| School concept | Veyra card | Status |
|---|---|---|
| Pythagorean theorem | separation decomposition card | exact |
| SSS congruence | triangle signature card | exact |
| SAS congruence | side-dot card | exact |
| line-circle intersection | corridor-shell quadratic card | exact rational / completion-needed |
| identity transform | identity relabel | exact |
| composition of transforms | relabel composition card | exact sample certificate |

## New Veyra viewpoint

The theorem is not a detached human sentence.  It is a living certificate that knows its observer assumptions and its failure mode.  This is the bridge from “new notation” to a replacement mathematics: every school theorem becomes a testable Veyra card.

## Next layer

Build a theorem-card registry and proof dependency graph:

1. cards know which definitions they depend on;
2. cards can emit counterexample searches;
3. cards can be promoted from sample certificate to theorem schema;
4. cards can be exposed to the Sage lab as proof/check objects.
