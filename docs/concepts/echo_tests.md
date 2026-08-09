# Echo-Equivalence as Test-Indexed Identity

## 1. Problem

Core-0 removed primitive equality. But mathematics still needs a disciplined way to say when two constructions count as the same.

Veyra answer:

> Identity is always relative to an admitted family of tests.

So the real relation is not `x ≈ y`, but:

`x ≈_T y`

where `T` is a test family.

## 2. Test family

A **test family** `T` is a finite or specified collection of observers.

Each observer `t ∈ T` maps a construction to an observable response:

`t : construction -> response`

Two constructions echo under `T` when every observer in `T` returns the same response.

## 3. Definition

**DEF-014 — Test family.** A test family is a collection of observers admitted for a given layer of Veyra.

**DEF-015 — Test-indexed echo-equivalence.**

`x ≈_T y` iff for every observer `t ∈ T`, `t(x) = t(y)` in the external shadow language.

Important: the `=` here is outside Veyra. It belongs to the human-shadow model used to test the seed.

## 4. Immediate properties

If every observer has ordinary equality in its response type, then `≈_T` is an equivalence relation:

1. Reflexive: `x ≈_T x`.
2. Symmetric: if `x ≈_T y`, then `y ≈_T x`.
3. Transitive: if `x ≈_T y` and `y ≈_T z`, then `x ≈_T z`.

Status: theorem in the external model, not an internal metaphysical claim.

## 5. Refinement

If `T ⊆ U`, then `U` is a finer test family than `T`.

Finer tests can split echoes:

`x ≈_U y  =>  x ≈_T y`

but not conversely.

This captures a key Veyra principle:

> identity can become more detailed when the universe admits stronger tests.

## 6. First test families for modes

Modes are currently represented externally as finite tact words.

Let `w` be a word over tact alphabet `A`.

### Length test `T_len`

Observer:

`len(w)` = number of tacts.

Under `T_len`, `αβ ≈ βα ≈ αα` because all have length 2.

### Parikh test `T_bag`

Observer:

`bag(w)` = count of each tact kind.

Under `T_bag`, `αβ ≈ βα`, but `αβ` is not echo-equivalent to `αα`.

### Ordered word test `T_word`

Observer:

`word(w)` = exact tact sequence.

Under `T_word`, `αβ` and `βα` are distinct.

### Cyclic test `T_cycle`

Observer:

`cycle(w)` = canonical rotation class of a closed mode.

Under `T_cycle`, `αβ ≈ βα`, because a closed recurrence has no privileged starting cut.

## 7. Consequence for number theory

In one-tact Core-0, `T_len`, `T_bag`, `T_word`, and `T_cycle` collapse to the same observations. That is why ordinary natural numbers appear stable.

In multi-tact layers, they diverge. This divergence is where new mathematics begins.

## 8. Open question

Should a Veyra theorem always specify its test family?

Current rule: yes. Any theorem involving echo-equivalence must declare `T` explicitly or be marked incomplete.
