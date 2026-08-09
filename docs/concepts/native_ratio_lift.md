# Native Ratio Lift

**Registry:** raw ratio operation `DEF-377`; native cross-scale addition `DEF-378`.

## 1. Purpose

Earlier ratio operations proved school fractions through canonical length shadows.

Core 2.1 adds raw/native ratio operations that preserve Veyra structure before reduction.

## 2. Raw cross-scale addition

For ratios `N₁/S₁` and `N₂/S₂`:

`raw_add = (N₁·S₂ ⊞ N₂·S₁) / (S₁ ⋉ S₂)`

where `·S` repeats both balance poles by the scale length and `⋉` length-weaves scale modes.

The canonical rational shadow may reduce later, but raw addition keeps the common scale.

Example:

`1/2 + 1/3` becomes raw `5/6`, not immediately reduced by external fraction arithmetic.

## 3. Raw multiplication

Balance multiplication distributes polarity:

- positive pole: `A⁺B⁺ ⊞ A⁻B⁻`;
- negative pole: `A⁺B⁻ ⊞ A⁻B⁺`.

Scale modes compose by length-weave.

## 4. Certification lift

The ratio certificate is now Level 1:

- it uses native raw cross-scaling;
- it checks the raw numerator/scale structure;
- then it checks the classical shadow.

## 5. Remaining work

The scale product is still an external length-weave. Future work should define internal scale objects and echo-compatible scale multiplication.
