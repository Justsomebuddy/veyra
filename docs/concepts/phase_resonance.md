# Phase Resonance

## 1. Why exact repetition is not enough

The first resonance relation was ordered repetition:

`part ▹ whole` iff `whole = part^k` as a linear word.

This is too cut-sensitive for closed modes. A closed recurrence has no privileged first tact.

Example:

- `part = ab`
- `whole = baba`

Ordered repetition says `ab` does not resonate inside `baba`, because `baba != (ab)^2`.

But as a closed recurrence, `baba` is only a rotated presentation of `abab`. So `ab` should resonate inside it with phase shift.

## 2. Definition

**DEF-029 — Phase offset.**

A phase offset of `part` inside `whole` is a rotation index `r` such that rotating `whole` by `r` yields an exact repetition of `part`.

So `ab` resonates inside `baba` with offset `1`:

`rotate(baba,1) = abab = (ab)^2`.

**DEF-030 — Cyclic resonance.**

`part ▹_cyc whole` iff:

1. `part` is non-silent;
2. `len(whole)` is a multiple of `len(part)`;
3. some rotation of `whole` is `part^k`.

## 3. Difference from ordered resonance

| part | whole | ordered | cyclic/phase |
|---|---|---:|---:|
| `ab` | `abab` | yes | yes |
| `ab` | `baba` | no | yes |
| `ab` | `abba` | no | no |
| `aba` | `baaba` | no | no, length obstruction |

## 4. Phase obstruction

If no phase offset exists, the failure can have two causes:

1. **length obstruction** — `len(whole)` is not divisible by `len(part)`;
2. **pattern obstruction** — length fits, but no rotation tiles.

This gives the first primitive obstruction taxonomy for Veyra resonance.

## 5. Scientific intuition

Many physical systems do not require literal alignment. They require phase-compatible closure.

Veyra phase resonance says:

> A rhythm can be present inside a closed structure even when the observer's cut is shifted.

This begins to separate intrinsic recurrence from coordinate/cut artifact.

## 6. Next target

The next resonance relation should allow bounded defects or phase drift:

- approximate resonance,
- resonance with one obstruction,
- resonance spectrum over all candidate parts,
- minimal edit/rotation obstruction.
