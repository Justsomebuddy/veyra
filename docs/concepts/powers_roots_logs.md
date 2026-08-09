# Powers, Roots, and Logarithms as Veyra Lifts

## Purpose

After functions, school mathematics introduces powers, roots, and logarithms. Veyra treats these not as separate magic operations, but as transformer iteration and lift attempts.

## Power

**DEF-064 — Power weave.**

For a ratio mode `Q` and integer `n`, `Q^n` is repeated multiplicative weave in the ratio shadow layer:

```text
Q^0 = 1
Q^(n+1) = Q^n · Q
Q^(-n) = (Q^-1)^n
```

This recovers school integer powers.

## Transformer iteration

**DEF-065 — Transformer iterate.**

For a transformer `F`, the `n`-fold iterate is:

```text
F^0 = id
F^(n+1) = F ∘ F^n
```

This is the function-level origin of repeated process, dynamics, and discrete time.

## Root

**DEF-066 — Root lift.**

A root is an inverse lift of a power weave:

```text
find R such that R^n ⇔ Q
```

If no ratio shadow root exists, the lift reports an obstruction instead of pretending the result lives in the current layer.

Example obstruction:

```text
sqrt(2) -> irrational-shadow
```

This says the current rational mode layer is incomplete for that lift.

## Logarithm

**DEF-067 — Transition-count lift.**

A logarithm is a count-lift:

```text
find n such that B^n ⇔ Q
```

In the current finite executable layer this is a bounded search over integer transition counts. A continuous logarithm will require a completed scale/limit layer.

## School concepts recovered

| School concept | Veyra view |
|---|---|
| integer power | repeated ratio weave |
| negative power | inverse then repeated weave |
| root | inverse lift of power |
| irrational root | obstruction to rational shadow layer |
| logarithm | transition-count lift |
| iteration | repeated transformer composition |

## Executable layer

Implemented in:

- `src/core/shadows/power.py`
- `tests/shadows/test_power.py`

Current coverage:

- positive, zero, and negative powers;
- exact rational nth-root lift;
- irrational-root obstruction;
- bounded discrete log shadow;
- affine transformer iteration.

## Scale-memory upgrade

`docs/log/scale_memory_log.md` upgrades `DEF-067` into practical recovery certificates: exact transition-depth recovery, residual logs, cyclic unwraps, and explicit obstructions.

## Next theory step

This layer still exposes the next missing school bridge: **completion**.

Roots like `sqrt(2)` and continuous logs do not fail because they are meaningless. They fail because the rational ratio layer is incomplete.

Next Veyra layer:

```text
completion / refinement / limit
```

This is the entrance to analysis.
