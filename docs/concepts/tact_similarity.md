# Tact Aura Similarity

## 1. Problem

Weighted resonance in Core 1.3 accepted an external cost map `κ(expected,actual)`.

That was useful, but still too human: the system had to be told that `b→c` is cheap.

Core 1.5 derives a first cost map from the mode itself.

## 2. Definition: tact aura

For a context collection `C` of closed modes, the radius-`r` aura of a tact `x` is:

`A_r(x | C) = { L_i:y, R_i:z }`

where `y` appears `i` steps to the left of an occurrence of `x`, and `z` appears `i` steps to the right, using cyclic indexing.

The aura does not say what `x` is. It says how `x` is held by surrounding breath.

## 3. Similarity

Aura similarity is the Jaccard overlap:

`sim_A(x,y) = |A(x) ∩ A(y)| / |A(x) ∪ A(y)|`

Exact same tact still has cost zero. Distinct tacts with identical auras are not identical; they are context-twins.

## 4. Derived cost

For distinct tacts:

`κ_A(x,y) = clamp(1 - sim_A(x,y), min_mismatch, max_mismatch)`

Default: `min_mismatch=0.25`, `max_mismatch=1.0`.

The floor prevents distinct tacts from collapsing into zero-cost identity.

## 5. Example: `abac`

In the cyclic mode `abac`:

- `b` has aura `{L1:a, R1:a}`;
- `c` has aura `{L1:a, R1:a}`;
- therefore `sim_A(b,c)=1` and `κ_A(b,c)=0.25`.

So `ab` can weighted-resonate in `abac` without a hand-written `b>c:0.25` rule.

## 6. Caveat

`cyclic_tact_aura_echoes()` now promotes aura to structured `AuraMark` / `TactAuraEcho` objects; legacy string marks are only text shadows for tables and old tests.
