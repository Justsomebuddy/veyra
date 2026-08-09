# Compression Score

## 1. Why compression?

A resonance spectrum can list many candidate rhythms for a whole mode. But not every resonance explains the structure equally well.

A good explanation should be:

- short enough to compress the whole;
- accurate enough to require few defects;
- not overly dependent on arbitrary phase offset;
- reproducible by a clear expansion rule.

## 2. First Core-1.0 score

**DEF-037 — Explanation cost.**

For a spectrum entry `e` with candidate part `p`, best defect count `δ`, and best phase offset `r`, define:

`cost(e) = len(p) + defect_weight·δ + phase_weight·phase_penalty(r)`

where:

- `phase_penalty(r)=0` if `r=0`, otherwise `1`;
- default `defect_weight=2`;
- default `phase_weight=0.25`.

**DEF-038 — Compression saving.**

`save(e) = len(whole) - cost(e)`.

Positive saving means the candidate is shorter/cheaper than spelling the whole directly.

**DEF-039 — Compression ratio.**

`ratio(e) = save(e) / len(whole)`.

## 3. Ranking

Compression ranking sorts resonating candidates by:

1. higher saving;
2. lower defect count;
3. shorter candidate length;
4. lower phase offset;
5. lexical tie-breaker.

## 4. Example

Let:

`whole = abac`

Candidate `ab` with one defect:

- `len(part)=2`
- `δ=1`
- `phase offset=0`
- `cost = 2 + 2·1 + 0 = 4`
- `save = 4 - 4 = 0`

So `ab` explains the whole as a near-rhythm but does not compress it under default defect cost.

If defects are cheap (`defect_weight=1`):

- `cost = 3`
- `save = 1`

Then `ab` becomes a useful compressed explanation.

## 5. Interpretation

Compression score is not truth. It is an exploration heuristic:

> A structure may be understood by the rhythms that explain it with minimal description cost.

This connects Veyra to:

- Kolmogorov-style compression intuition;
- motif discovery;
- noisy periodic signals;
- scientific model selection.

## 6. Next direction

Current score is crude. Future variants should add:

- weighted tact-specific defect costs;
- edit-distance insertion/deletion drift;
- probabilistic likelihood;
- multi-part explanations;
- hierarchical compression trees.
