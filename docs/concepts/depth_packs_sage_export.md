# Veyra depth packs and Sage export adapter

## Aim

The previous layer gave trigonometry, probability, and statistics executable seeds.  This layer adds first depth packs and a Sage-facing export adapter.

## Combinatorics depth

Combinatorics is a finite observer-count layer:

```text
n!      = ordered arrangement count echo
C(n,k)  = unordered choice count echo
```

Implemented card:

- `binomial-symmetry` — `C(n,k)=C(n,n-k)`.

This gives probability a finite counting foundation instead of treating weights as isolated data.

## Probability depth

Implemented cards:

- `probability-union` — `P(A∪B)=P(A)+P(B)-P(A∩B)`;
- `probability-independence` — `P(A∩B)=P(A)P(B)` classification.

The cards operate on finite weighted observer distributions, so every value remains exact.

## Statistics depth

Implemented card:

- `variance-shift` — variance is invariant under constant sample shifts.

This begins the route from sample echoes to inference-ready statistics.

## Sage export adapter

Implemented rows:

```text
SageExportRow(row_type, name, domain, hook, payload)
```

Functions:

- `theorem_sage_export_rows()` — converts theorem specs to Sage-facing rows;
- `curriculum_sage_export_rows()` — wraps curriculum export tuples.

These rows are intentionally JSON-ready and stable enough for later `veyra_sage` integration.

## Registry/curriculum update

The theorem registry now has 19 specs:

- 5 geometry;
- 6 algebra/analysis;
- 4 trig/prob/stat seeds;
- 4 depth-pack cards.

The curriculum map now has:

- 11 nodes;
- 11 covered;
- 0 missing;
- 19 Sage export rows.

## Executable layer

Implemented in `src/core/registry/depth_packs.py`:

- `factorial_echo()`;
- `choose_echo()`;
- `binomial_symmetry_card()`;
- `probability_union_card()`;
- `independence_card()`;
- `variance_shift_card()`;
- `theorem_sage_export_rows()`;
- `curriculum_sage_export_rows()`.

Tests in `tests/registry/test_depth_packs.py` verify combinatorics counts, probability union, independence, variance shift, and Sage export rows.

## Next layer

Wire this into `veyra_sage`:

1. Sage parent/object for theorem specs;
2. Sage parent/object for curriculum nodes;
3. export/import smoke tests;
4. a `VeyraSchoolCore` facade for all school replacement cards.
