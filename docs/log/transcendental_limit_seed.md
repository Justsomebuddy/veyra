# Veyra transcendental/limit algebra seed

**Date:** 2026-06-06
**Status:** executable finite seed, not full transcendental analysis

## Aim

This layer starts the roadmap step beyond polynomial shadows.  It does not introduce real analytic functions as primitive objects.  Instead, it records a finite Veyra-native acceptance surface for transcendental-looking school shadows:

```text
formal finite series + derivative-shift cards + explicit tail envelope
```

## Executable objects

Implemented in `src/core/shadows/transcendental_limit.py`:

- `FormalSeriesShadow` — named finite coefficient row with truncation obstruction;
- `LimitEnvelope` — rational center/radius envelope for a truncated shadow;
- `exp_series(order)` — finite formal `exp(x)` coefficients through `order`;
- `log1p_series(order)` — finite formal `log(1+x)` coefficients through `order`;
- `exp_derivative_card(order)` — checks `D E_n = E_{n-1}` exactly;
- `log1p_derivative_card(order)` — checks `D L_n = 1 - x + x² - ...` through finite order;
- `alternating_log1p_envelope(order, point)` — alternating next-term envelope for `0 < x <= 1`;
- `alternating_tail_bound_card(order, point)`;
- `transcendental_limit_checklist()`.

All arithmetic stays in exact ratio shadows.

## Canonical witness

At `order=4` and `x=1/2`:

| Row | Exact shadow |
|---|---|
| `exp_series(4)` | `1, 1, 1/2, 1/6, 1/24` |
| `log1p_series(4)(1/2)` center | `77/192` |
| next alternating term radius | `1/160` |

The certificate is intentionally finite: it proves the derivative shifts and a bounded tail envelope, not equality to a completed real `exp` or `log` object.

## Certificate

`src/core/certificates/transcendental.py` adds `transcendental_limit` to the executable certificate suite.
Essence/Core now records 18 executable layers.

## Limits

This seed does not claim:

- full convergence theory;
- real-number construction beyond existing completion intervals;
- symbolic transcendental simplification;
- trig/exponential equation solving;
- arbitrary analytic continuation.

The first reusable convergence layer is now `docs/log/convergence_algebra_seed.md`; stronger real-analysis claims still require separate definitions, counterexamples, and proof/export discipline.

## Verification

Targeted tests:

```bash
PYTHONPATH=. python3 -m pytest -q tests/shadows/test_transcendental_limit.py tests/shadows/test_certify.py tests/kernel/test_essence_core.py
```

Full verification remains:

```bash
the complete verification suite
```
