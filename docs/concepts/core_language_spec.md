# Veyra Core Language v0.1

**Status:** executable seed.
**Implementation:** `src/core/language/__init__.py`.
**Tests:** `tests/language/test_core_language.py`.

## Why this layer exists

The previous Veyra core had working mathematical objects, but the language
itself was still implicit. This document locks the first operational surface:
what can be written, what kind it has, how it is assembled, how equality is
replaced, how inference reports obstruction, and how external school math is
viewed as a shadow rather than as primitive truth.

## The nine kernel pieces

| # | Missing piece | v0.1 artifact |
|---|---|---|
| 1 | Formal grammar | atom/call DSL parsed by `parse_veyra()` |
| 2 | Object types | `VeyraKind` |
| 3 | Assembly rules | `expr_kind()` |
| 4 | Replacement for equality | `echo(left,right,observer)` |
| 5 | Logic of inference | `infer_veyra()` → `ready/blocked/unknown` |
| 6 | Normal form | `normalize_veyra()` + `normal_text()` |
| 7 | Semantics | `semantic_shadow(term, domain)` |
| 8 | Minimal interpreter | `interpret_veyra()` |
| 9 | School translation | `school_translation_table()` |

## Grammar

Veyra v0.1 uses a deliberately tiny grammar:

```text
expr  := atom | call
atom  := head ':' label
call  := head '(' expr (',' expr)* ')'
head  := letters / digits / '_' / '-'
```

Examples:

```text
nod:a
rez:cut
nod(rez:cut)
tact(nod:a,nod:b)
breath(tact(nod:a,nod:b))
mode(breath(tact(nod:a,nod:b),tact(nod:b,nod:a)))
echo(mode(...),mode(...),observer:length)
```

## Types and assembly

Core kinds are:

`rez`, `nod`, `tact`, `breath`, `mode`, `trace`, `weight`, `relation`,
`observer`, `obstruction`, `value`.

Important assembly rules:

- `nod(rez:x)` creates a residue from a distinction.
- `tact(nod:a,nod:b)` creates a smallest directed transition.
- `breath(tact(...), ...)` creates a finite transfer chain.
- `mode(breath(...))` creates a closed-mode shadow.
- `echo(left,right,observer:o)` creates a relation, not an identity claim.
- bad assemblies are blocked, not silently coerced.

## Echo instead of equality

Traditional equality asks whether two expressions are identical. Veyra asks:

> do two traces become indistinguishable under a declared observer?

Built-in observers:

| Observer | Meaning |
|---|---|
| `kind` | compare type/kind only |
| `label` | compare atom label |
| `length` | compare finite length shadow |
| `trace` | compare full normal trace |
| `boundary` | compare visible first/last boundary |

Thus two modes can echo by `length` while being blocked by `trace`. This is the
first explicit split between equality and observer-relative sameness.

## Inference states

`infer_veyra()` returns:

- `ready` — expression is valid or relation resonates under observer;
- `blocked` — type assembly or echo check failed;
- `unknown` — syntax/type is valid, but observer semantics is not available.

This gives Veyra its first proof/refutation/unknown triad.

## Semantic shadows

`semantic_shadow(term, domain)` projects a Veyra expression into an explicitly
declared external domain:

- `arithmetic` adds length shadows;
- `geometry` adds boundary shadows;
- `logic` adds inference status and obstruction;
- `generic` keeps only kind and normal trace.

The key rule: external school math is a **shadow**, not the foundation.

## Translation table

`school_translation_table()` provides nine first bridges: object, equality,
number, point, segment, proof, counterexample, normal form, and model.

## Current proof of workability

The layer is not philosophical prose only. It is executable:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/language/test_core_language.py tests/shadows/test_certify.py
```

Current verification: targeted `10 passed`; full suite `222 passed`; doctest 41/41; smoke ok; line hygiene 0 files >300.
