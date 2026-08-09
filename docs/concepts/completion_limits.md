# Completion, Refinement, and Limits

## Purpose

The power/root layer exposed a gap: `sqrt(2)` is not meaningless, but it cannot live inside the current rational ratio shadow as an exact ratio mode.

Veyra therefore needs **completion**: a way to represent a missing object by a stable refinement trace.

## Completion shadow

**DEF-068 — Completion shadow.**

A completion shadow is a nested family of rational observer bounds:

```text
I0 ⊇ I1 ⊇ I2 ⊇ ...
```

where each interval is a sharper shadow of a not-yet-internal object.

The object is not inserted by faith. It is approached by certified refinement.

## Refinement

**DEF-069 — Refinement.**

An interval `J` refines interval `I` when:

```text
I.lower ≤ J.lower ≤ J.upper ≤ I.upper
```

Refinement is the first Veyra replacement for “getting closer.”

## Width observer

The width of a completion interval is:

```text
width(I)=upper(I)-lower(I)
```

A completion trace becomes useful when width can be made smaller than a declared tolerance observer.

## Square-root refinement

For positive ratio `Q`, `sqrt(Q)` can be represented by bisection intervals:

```text
low^2 ≤ Q < high^2
```

Example:

```text
sqrt(2)
```

is not a rational ratio, but it has a refinement trace with shrinking width.

## Limit certificate

**DEF-070 — Tail limit certificate.**

A finite tail certificate says a sampled trace remains within tolerance `ε` of a candidate shadow:

```text
for all x in tail: distance(x,candidate) ≤ ε
```

This is not a full infinite proof. It is an executable school-analysis seed.

## Continuity seed

**DEF-071 — No-jump condition.**

A transformer is continuous under a refinement observer when refining the input does not cause an uncontrolled output jump.

This is only a seed. Full continuity requires quantified refinement families.

## School concepts recovered

| School concept | Veyra view |
|---|---|
| irrational number | completion shadow |
| approximation | finite refinement interval |
| error bound | width observer |
| limit | stable tail/refinement certificate |
| convergence | shrinkable nested shadows |
| continuity | no observer jump under refinement |

## Executable layer

Implemented in:

- `src/core/shadows/completion.py`
- `tests/shadows/test_completion.py`

Current coverage:

- nested square-root refinement;
- `sqrt(2)` interval certificate;
- exact-root interval containment;
- tail limit certificates;
- tail-jump obstruction.

## Next theory step

Completion gives the doorway to analysis:

1. continuity certificates for transformers;
2. derivative as local transition ratio;
3. integral as accumulated residue;
4. real-number-like completed ratio shadows.
