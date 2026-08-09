# Observer Limits and Lift Conditions

## Status

**Type:** definition/conjecture/refutation checkpoint.
**Date:** 2026-06-02.
**Purpose:** state core observer-completeness and lift conditions.

## Core lesson

Finite observer experiments expose a useful negative result:

- a transition stream can make candidate generation cheaper;
- observers can classify shadows of a target;
- but if the observer does not preserve directional structure, Veyra cannot infer the hidden source faster than generic search.

This is a theory lesson about **observer completeness**.

## New primitive distinction

Veyra currently has:

- `rez` — distinction act;
- `nod` — stable residue;
- `tact` — transition;
- `breath` — directed tether;
- `mode` — closed recurrence.

We now add a theory-level distinction:

- **observer** — a rule that receives a trace and returns a shadow.
- **shadow** — what survives after an observer has forgotten structure.
- **hiding** — a many-to-one observer that destroys usable transition direction.
- **lift** — reconstructing enough pre-shadow structure to reason again.

## Definition: observer

An observer `O` maps traces to shadows:

```text
O : Trace -> Shadow
```

Two traces are `O`-echo-equivalent when the observer cannot separate them:

```text
x ~O y  iff  O(x) = O(y)
```

## Definition: directional observer

An observer is **directional** for a transition family `T` if knowing `O(x)` and the transition rule gives any nontrivial constraint on likely predecessors or successors.

Informally:

```text
O preserves enough structure that movement is still visible.
```

## Definition: hiding observer

An observer is **hiding** when it collapses many traces and destroys transition direction.

A coarse terminal summary is a generic example: many distinct transition traces can map to the same final shadow, leaving no directional information for reconstruction.

## Definition: complete observer family

A family of observers `{O_i}` is complete for a task when their combined shadows isolate the desired trace or reduce candidates by a provable factor.

```text
O_family(x) = (O_1(x), ..., O_n(x))
```

Completeness is task-relative, not absolute.

## Conjecture: no free lift from hiding shadows

If an observer is hiding and no auxiliary shadow is available, Veyra cannot produce structural acceleration beyond generic search for that task.

This is a **negative conjecture** and should be treated as a safety law against fake breakthroughs.

## Conjecture: acceleration requires preserved transition structure

A Veyra method can accelerate a search only when at least one observer preserves a transition-relevant invariant, phase, orbit, residue, compression law, or defect gradient.

Useful extra shadows are task-specific invariants, phase data, orbit data, defect gradients, or related traces that measurably reduce ambiguity.

## Theory consequence

The next pure Veyra layer is not “faster enumeration.” It is:

```text
observer algebra + shadow loss + lift conditions
```

We need to classify which observers preserve enough structure to support proof, compression, or search reduction.

## Next theoretical tasks

1. Formalize observer composition:

```text
O2 ∘ O1
```

2. Define shadow entropy/compression without importing classical probability as primitive.
3. Define lift obstruction: when no internal path from shadow back to trace exists.
4. Define observer completeness certificates.
5. Build small finite-mode examples where:
   - one observer hides everything;
   - two observers collapse candidates;
   - a directional observer gives a provable shortcut;
   - a misleading observer gives false beauty.

## Current lesson

Veyra becomes powerful only when it sees the right shadows. If the world gives a dead shadow, the correct theorem may be negative.
