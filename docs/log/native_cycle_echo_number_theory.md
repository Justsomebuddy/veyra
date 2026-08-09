# Native Cycle-Echo Number Theory

**Date:** 2026-06-03
**Status:** Sprint A executable layer.
**Implementation:** `src/core/numbers/native_number.py`, `src/core/numbers/tact_similarity.py`.
**Certificate:** `native_resonance_number` in `src/core/certify.py`.

## What changed

The old cyclic layer used a lexicographically least rotation as a convenient display word.  That was useful, but not native enough: a closed mode should not secretly choose one human cut.

This layer introduces `CycleEcho`, an internal object whose value is the full rotation orbit:

```python
cycle_echo(Mode.from_word("baba")).words == ("abab", "baba")
```

The sorted `words` view is only a deterministic external display; equality of `CycleEcho` is orbit equality.

## Sprint A closures

| TODO item | New object/function |
|---|---|
| ordered vs cyclic primitive counts | `primitive_count_table()` |
| replace lexicographic representative | `CycleEcho`, `cycle_echo()`, `cyclic_weave_echo()` |
| phase resonance vs cyclic primitive profiles | `primitive_phase_profile()` |
| spectrum ranking strategies | `compare_spectrum_compression()` |
| compression score vs spectrum rank | `SpectrumCompressionRow` |
| tact aura as internal echo object | `AuraMark`, `TactAuraEcho`, `cyclic_tact_aura_echoes()` |

## Primitive count example

For alphabet `{a,b}`:

| Length | Ordered primitive words | Cyclic primitive echoes | Collapse |
|---:|---:|---:|---:|
| 1 | 2 | 2 | 0 |
| 2 | 2 | 1 | 1 |
| 3 | 6 | 2 | 4 |

Interpretation: ordered words count cut presentations; cyclic echoes count closed recurrence classes.

## Phase + primitive profile

For `part=ab`, `whole=baba`:

- `part` is primitive;
- `whole` is not primitive;
- exponent is `2`;
- cyclic resonance is true;
- phase offsets are `(1,3)`.

So Veyra can now say: a primitive rhythm explains a non-primitive closed whole up to phase, instead of merely saying “ordered equality failed”.

## Spectrum vs compression

`compare_spectrum_compression()` keeps two orders side by side:

- resonance spectrum rank: best phase/defect fit;
- compression rank: best explanation saving.

These are not identical notions.  A candidate may fit early in the spectrum but compress poorly if defects or phase are expensive.

## Aura echo promotion

`cyclic_tact_aura_echoes()` creates structured context marks:

```python
AuraMark(side="L", distance=1, tact="a")
```

Legacy string marks like `L1:a` are now text shadows, not the native object.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/numbers/test_native_resonance_number.py tests/numbers/test_tact_similarity.py tests/shadows/test_certify.py
python3 scripts/certify_veyra.py
```

Verified on 2026-06-03: full tests `295/295`, doctest `41/41`, Sage smoke ok, certificates `19/19`, line hygiene `0` files over 300.

Expected signals:

- `native_resonance_number` passes;
- certificate suite total increases to `18`;
- Essence/Core layer count increases to `11`.

## Next

Sprint A remains the base cycle-echo layer. Sprint X2 now extends it with `docs/log/native_number_theory_x2.md`: cycle divisibility rows, resonance-prime obstruction rows, and factor-lift rank comparisons.
