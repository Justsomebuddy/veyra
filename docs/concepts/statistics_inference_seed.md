# Statistics inference seed

**Status:** executable seed, not full mathematical statistics.
**Implemented:** `src/core/shadows/statistics_inference.py`, `src/core/certificates/statistics.py`.

## Native intent

The `statistics-inference` school row now has explicit distribution, interval, hypothesis, and uncertainty shadows.  The seed builds on existing `SampleEcho`, sample mean, and ratio arithmetic instead of importing probability measure theory as a primitive.

## Executable objects

- `DistributionFamily(name, parameters, status)` — named finite family with exact ratio parameters.
- `bernoulli_family(successes, trials)` — Bernoulli/binomial one-parameter shadow with `p` and `p(1-p)`.
- `IntervalEstimate(center, lower, upper, radius, samples, status)` — sample-statistic interval row.
- `mean_interval(sample, radius)` — exact interval around sample mean.
- `hypothesis_mean_card(sample, null_mean, tolerance)` — finite accept/reject theorem card.
- `standard_error_shadow(variance, samples)` — variance-per-sample uncertainty seed before square-root completion.

## Certificate

`statistics_inference` checks:

1. mean interval center and containment;
2. Bernoulli parameter shadows;
3. accepted and rejected mean-hypothesis cards;
4. variance-per-sample uncertainty;
5. the four-item seed checklist.

## What is still not claimed

- no asymptotic theorem;
- no continuous likelihood geometry, Bayesian update, or regression layer;
- no confidence-level calibration beyond explicit finite radius;
- no Sage facade yet for distribution families.

## Tests

- `tests/shadows/test_statistics_inference.py`
- `tests/shadows/test_certify.py`
- `tests/registry/test_curriculum_map.py`
