# Veyra geometry from tremor corridors

## Aim

This layer begins geometry without taking Euclidean point/line/plane as primitive.  A point is an **event**: an anchored observation package.  A segment is a **tremor corridor**: the bounded path of allowed interpolation between two events.  Classical coordinates are only shadows used for executable checking.

## Primitive stack

### Event point

An event point is a tuple of ratio shadows with a label:

```text
E = <q1, q2, ..., qn>
```

It is not metaphysically a dot.  It is the stable address of an observation.

### Tremor corridor

A corridor between events `A` and `B` is the bounded interpolation family:

```text
Corr(A,B) = { A + t(B-A) | 0 ≤ t ≤ 1 }
```

The parameter `t` is a ratio-mode shadow, so containment can be certified exactly for rational events.

### Separation echo

Distance is not primitive.  The first invariant is squared separation:

```text
Sep²(A,B) = Σ(B_i-A_i)^2
```

Square root length belongs to the completion layer when needed.

### Turn echo

For plane events, orientation is the sign of a two-corridor determinant:

```text
Turn(A,B,C) = sign((B-A)×(C-A))
```

This gives left/right/flat without importing angle as primitive.

### Area echo

Triangle area is half the absolute turn determinant.  Area is therefore a turn accumulation shadow, consistent with the previous area-braid layer.

## School-program coverage

| School concept | Veyra abstraction | Status |
|---|---|---|
| point | anchored event | executable |
| segment | tremor corridor | executable |
| midpoint | corridor half-event | exact |
| distance | squared separation + completion length | executable seed |
| collinearity | flat turn / corridor containment | exact rational certificate |
| triangle area | turn determinant / 2 | exact rational certificate |
| coordinate geometry | event-shadow notation | secondary representation |

## Executable layer

Implemented in `src/core/geometry/__init__.py`:

- `EventPoint` — anchored event.
- `TremorCorridor` — bounded interpolation corridor.
- `event_shadow()` — exact rational coordinate shadow.
- `squared_separation()` — distance invariant before square-root completion.
- `corridor_midpoint()` and `corridor_interpolate()` — corridor events.
- `corridor_contains()` and `corridor_parameter()` — containment certificates.
- `turn_2d()` — left/right/flat orientation certificate.
- `triangle_area()` — exact area shadow.

Tests in `tests/geometry/test_geometry.py` verify midpoint, `3-4-5` squared separation, interpolation containment, parameter recovery, turn orientation, triangle area, and degenerate flat cases.

## New Veyra viewpoint

Human geometry starts with idealized shapes.  Veyra geometry starts with stable observation events and asks what corridor relations remain invariant under allowed observers.  Shapes are not primitive sets of points; they are **families of corridors and turn echoes**.

## Next layer

Build school geometry theorem seeds:

1. corridor congruence by separation echo;
2. triangle congruence by separation triples and turn orientation;
3. parallelism as equal drift/turn obstruction;
4. circle as constant separation shell;
5. coordinate transforms as event-family relabelings.
