# Mode Enumeration Experiments

## Purpose

The first computational experiment is intentionally tiny:

- enumerate closed mode shadows as finite tact words;
- group them by test families;
- detect simple resonance/power structure;
- compare one-tact and two-tact behavior.

## External representation

A mode shadow is represented as a finite word over an alphabet of tact symbols.

Examples with alphabet `{α, β}`:

- silent mode: `ε`
- one-tact modes: `α`, `β`
- two-tact modes: `αα`, `αβ`, `βα`, `ββ`

This is only a shadow model. Internally, a mode is a closed breath.

## Resonance in the ordered word test

A mode `a` resonates inside mode `b` under ordered testing when `b` is an exact repetition of `a`:

`b = a^k`

Examples:

- `α ▹ αααα`
- `αβ ▹ αβαβ`
- `αβ` does not ordered-resonate inside `βαβα`, unless cyclic tests are admitted.

## Prime-like / primitive modes

A non-silent mode is **ordered-primitive** if it is not a repetition of a shorter non-silent word.

Examples:

- `α` is primitive.
- `αα` is not primitive: `α^2`.
- `αβ` is primitive under ordered word testing.
- `αβαβ` is not primitive: `(αβ)^2`.

## First insight

Ordinary primes are not the first generalization in multi-tact mode theory. The immediate generalization is **primitive word / indecomposable recurrence**.

This suggests two tracks:

1. one-tact arithmetic recovers prime numbers;
2. multi-tact arithmetic studies primitive rhythms, conjugacy classes, and resonance obstructions.

## Experiment command

```bash
python3 scripts/enumerate_modes.py --alphabet ab --max-len 4 --test ordered
python3 scripts/enumerate_modes.py --alphabet ab --max-len 4 --test cycle
```
