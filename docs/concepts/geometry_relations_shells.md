# Veyra geometry relations, shells, and relabels

## Aim

The previous geometry layer created events and tremor corridors.  This layer adds relation certificates: when two corridors are the same kind of corridor, when an event belongs to a constant-separation shell, when two corridors share a drift direction, and when a coordinate shadow is merely relabeled.

## Relation primitives

### Corridor congruence

Two corridors are congruent when their separation echoes match:

```text
Corr(A,B) ≅ Corr(C,D)  iff  Sep²(A,B)=Sep²(C,D)
```

This avoids primitive human length.  Length is a completion lift; squared separation is the exact finite certificate.

### Triangle signature

A triangle event family is described by sorted side echoes plus turn orientation:

```text
Sig△(A,B,C) = sort(Sep²(AB), Sep²(BC), Sep²(CA)) + Turn(A,B,C)
```

Mirrors may be accepted by dropping the turn-preservation observer.

### Constant-separation shell

A circle is rebuilt as a shell around a center event:

```text
Shell(C,r²) = { E | Sep²(C,E)=r² }
```

Membership is `inside`, `on`, or `outside` by exact comparison.

### Parallel drift

Two plane corridors are parallel when their direction displacement determinant is zero.  This is not a line axiom; it is a no-turn relation between drift echoes.

### Plane relabel

A transform is an affine relabeling of event shadows:

```text
E' = M·E + b
```

Some relabels preserve separation echoes, others scale them.  The distinction is executable, not assumed.

## School-program coverage

| School concept | Veyra abstraction | Status |
|---|---|---|
| equal segments | corridor congruence | exact |
| SSS triangle congruence | triangle side signature | exact |
| mirror/reflection caveat | optional turn preservation | exact |
| circle | constant-separation shell | exact |
| inside/on/outside circle | shell comparison | exact |
| parallel lines | zero-turn drift relation | exact |
| translation/rotation/scaling | plane relabel operators | executable |

## Executable layer

Implemented in `src/core/geometry/relations.py`:

- `corridor_congruence()` compares corridor separation echoes.
- `triangle_signature()` and `triangle_congruence()` compare triangle event families.
- `circle_shell()` classifies shell membership.
- `parallel_corridors_2d()` checks zero-turn drift.
- `PlaneRelabel` plus `translation_relabel()`, `quarter_turn_relabel()`, and `scale_relabel()` execute event relabels.

Tests in `tests/geometry/test_geometry_relations.py` verify congruent corridors, shell membership, triangle congruence with mirror obstruction, parallel certificates, translations, quarter-turns, and scaling of separation.

## New Veyra viewpoint

Classical school geometry treats shape equality as visual sameness.  Veyra treats it as equality of observer certificates: separation echoes, turn echoes, and relabel behavior.  A circle is not a drawn curve; it is a shell of equal separation.  A transformation is not motion in space; it is a disciplined relabeling of event shadows.

## Next layer

Build theorem cards and proof seeds for:

1. triangle congruence variants;
2. Pythagorean relation as separation decomposition;
3. line/circle intersection as corridor-shell solving;
4. coordinate transforms as a group-like transformer family;
5. geometry completion for irrational lengths.
