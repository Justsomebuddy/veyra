# Veyra trigonometry, probability, and statistics seeds

## Aim

This layer closes the three largest curriculum gaps from the previous map: trigonometry, probability, and statistics.  The goal is a Veyra-native seed, not a copy of school formulas.

## Trigonometry as cyclic shell theory

A trigonometric angle is rebuilt as a **cyclic phase event**:

```text
Phase(i mod n)
```

The first invariant is not sine/cosine.  It is a cyclic shell echo:

```text
ChordEcho(a,b) = 4·d·(n-d)/n²
```

where `d` is the shortest cyclic distance.  It is exact, rational, periodic, and symmetric.  Classical sine/cosine can later become completion shadows over refined cycles.

Implemented cards:

- `cyclic-period` — advancing by the modulus returns to the same phase;
- `chord-symmetry` — mirror phases have equal chord echo.

## Probability as weighted observer families

A probability space is a finite observer family with nonnegative weights:

```text
Dist = {(name, weight, score)}
```

Probability is a ratio of selected weight to total weight.  Expectation is weighted score balance.

Implemented card:

- `probability-complement` — event and complement probabilities sum to one.

## Statistics as sample echoes

A statistical sample is a finite tuple of ratio echoes.  Mean and variance are exact ratio shadows.  The first theorem card is not a normal approximation; it is the balancing law of the mean:

```text
Σ(x_i - mean) = 0
```

Implemented card:

- `mean-balance` — deviations from sample mean sum to zero.

## Executable layer

Implemented in `src/core/numbers/cyclic_probability_stats.py`:

- `CyclicPhase`, `phase_advance()`, `phase_distance()`, `cyclic_chord_echo()`;
- `phase_period_card()`, `chord_symmetry_card()`;
- `WeightedOutcome`, `FiniteDistribution`, `probability_of()`, `expectation()`;
- `probability_complement_card()`;
- `SampleEcho`, `sample_mean()`, `sample_variance()`, `mean_balance_card()`.

Tests in `tests/numbers/test_cyclic_probability_stats.py` verify phase period/distance/chord symmetry, exact event/complement probability, expectation, mean, variance, and mean balance.

## Registry and curriculum effect

The theorem registry now includes four new specs:

1. `cyclic-period`
2. `chord-symmetry`
3. `probability-complement`
4. `mean-balance`

The curriculum map now reports:

- 11 curriculum nodes;
- 11 covered nodes;
- 0 missing nodes;
- 19 Sage export rows after depth packs.

## Caveat

This does not mean the full school program is complete.  It means the largest missing domains now have executable Veyra seeds.  Full replacement still needs depth: trigonometric identities, probability laws, distributions, inference, combinatorics, and exam-grade theorem packs.

## Next layer

Build depth packs:

1. trig identities from cyclic chord algebra;
2. combinatorics as finite observer counting;
3. probability union/independence cards;
4. statistics distribution and inference cards;
5. Sage export adapter for curriculum rows.
