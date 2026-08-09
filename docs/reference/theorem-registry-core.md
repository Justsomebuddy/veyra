# Historical core through 1.3.0

Part of the public [Theorem and Definition Registry](../../THEOREMS.md).

## Historical core through 1.3.0

## Definitions

| ID | Name | Location | Dependencies |
|---|---|---|---|
| DEF-001 | Rez | `docs/concepts/primitives.md` | — |
| DEF-002 | Nod | `docs/concepts/primitives.md` | DEF-001 |
| DEF-003 | Tact | `docs/concepts/primitives.md` | DEF-002 |
| DEF-004 | Breath | `docs/concepts/primitives.md` | DEF-002, DEF-003 |
| DEF-005 | Mode | `docs/concepts/primitives.md` | DEF-004 |
| DEF-006 | Echo-equivalence | `docs/concepts/primitives.md` | tests TBD |
| DEF-007 | Stitch | `docs/concepts/primitives.md` | DEF-004 |
| DEF-008 | Veyra addition | `docs/concepts/number_theory.md` | DEF-005, DEF-007 |
| DEF-009 | Veyra multiplication/weave | `docs/concepts/number_theory.md` | DEF-005 |
| DEF-010 | Silent mode | `docs/concepts/number_theory.md` | DEF-005 |
| DEF-011 | First mode | `docs/concepts/number_theory.md` | DEF-003, DEF-005 |
| DEF-012 | Resonance/divisibility | `docs/concepts/number_theory.md` | DEF-005, DEF-007 |
| DEF-013 | Phase congruence | `docs/concepts/number_theory.md` | DEF-012 |

## Axioms

| ID | Name | Location | Status |
|---|---|---|---|
| AX-001 | Residue | `docs/concepts/primitives.md` | seed axiom |
| AX-002 | Directed tether | `docs/concepts/primitives.md` | seed axiom |
| AX-003 | Empty breath | `docs/concepts/primitives.md` | seed axiom |
| AX-004 | Stitch | `docs/concepts/primitives.md` | seed axiom |
| AX-005 | Echo associativity | `docs/concepts/primitives.md` | seed axiom |
| AX-006 | Closure | `docs/concepts/primitives.md` | seed axiom |
| AX-007 | One-tact seed | `docs/concepts/primitives.md` | Core-0 only |

## Lemmas / Theorems

| ID | Name | Statement | Uses | Status |
|---|---|---|---|---|
| LEM-001 | Path-shadow consistency | Core-0 has a graph/path shadow model. | AX-001..AX-006 | sketch |
| THM-001 | Natural shadow | One-nod one-tact modes shadow natural numbers. | AX-007, LEM-001 | conjectured theorem |
| THM-002 | Stitch-addition shadow | `⊕` shadows ordinary addition on `N`. | THM-001 | conjectured theorem |
| THM-003 | Weave-multiplication shadow | `⊗` shadows ordinary multiplication on `N`. | THM-001 | conjectured theorem |

## Conjectures

| ID | Type | Statement | Status |
|---|---|---|---|
| W-001 | weak | One-nod one-tact Veyra arithmetic is isomorphic to `N`. | proof planned |
| S-001 | sharp | One-tact resonance decomposition matches prime factorization. | definitions needed |
| R-001 | risky | Stable natural structures correspond to low-obstruction modes in richer Veyra layers. | speculative |

## Definitions added in 0.2.0

| ID | Name | Location | Dependencies |
|---|---|---|---|
| DEF-014 | Test family | `docs/concepts/echo_tests.md` | DEF-006 |
| DEF-015 | Test-indexed echo-equivalence | `docs/concepts/echo_tests.md` | DEF-014 |
| DEF-016 | Ordered primitive mode | `docs/concepts/mode_enumeration.md`, `src/core/numbers/modes.py` | DEF-005, DEF-015 |

## Lemmas added in 0.2.0

| ID | Name | Statement | Uses | Status |
|---|---|---|---|---|
| LEM-002 | Echo relation law | `≈_T` is reflexive, symmetric, and transitive in the external shadow model. | DEF-014, DEF-015 | stated |
| LEM-003 | Test refinement law | If `T ⊆ U`, then `x ≈_U y` implies `x ≈_T y`. | DEF-014, DEF-015 | stated |

## Definitions added in 0.3.0

| ID | Name | Location | Dependencies |
|---|---|---|---|
| DEF-017 | Substitution weave | `docs/concepts/weave_and_n_shadow.md`, `src/core/numbers/modes.py` | DEF-005, DEF-007 |
| DEF-018 | Length-weave | `docs/concepts/weave_and_n_shadow.md`, `src/core/numbers/modes.py` | DEF-017 |
| DEF-019 | Natural shadow map | `docs/concepts/weave_and_n_shadow.md`, `proofs/latex/veyra-core.tex` | DEF-011 |

## Status update 0.3.0

| ID | Previous | Current | Evidence |
|---|---|---|---|
| W-001 | proof planned | proved in external shadow draft | `docs/concepts/weave_and_n_shadow.md`, `proofs/latex/veyra-core.tex`, `tests/numbers/test_modes.py` |
| THM-001 | conjectured theorem | theorem in external shadow model | `proofs/latex/veyra-core.tex` |
| THM-002 | conjectured theorem | theorem in external shadow model | `proofs/latex/veyra-core.tex` |
| THM-003 | conjectured theorem | theorem for length-weave in external shadow model | `proofs/latex/veyra-core.tex` |

## Definitions added in 0.4.0

| ID | Name | Location | Dependencies |
|---|---|---|---|
| DEF-020 | Schema compatibility | `docs/concepts/multitact_counterexamples.md`, `src/core/numbers/counterexamples.py` | DEF-014, DEF-015, DEF-017 |

## Counterexamples added in 0.4.0

| ID | Claim refuted | Witness | Location | Status |
|---|---|---|---|---|
| CE-001 | Length echo is full identity | `ab ≈_{T_len} aa` but split by `T_bag` | `docs/concepts/multitact_counterexamples.md` | verified by tests |
| CE-002 | Bag echo is full identity | `ab ≈_{T_bag} ba` but split by `T_word` | `docs/concepts/multitact_counterexamples.md` | verified by tests |
| CE-003 | Cyclic and ordered identity coincide | `ab ≈_{T_cycle} ba` but split by `T_word` | `docs/concepts/multitact_counterexamples.md` | documented |
| CE-004 | Stitch is absolutely commutative | `a⊙b=ab`, `b⊙a=ba`, split by `T_word` | `docs/concepts/multitact_counterexamples.md` | verified by tests |
| CE-005 | Symbol-sensitive weave respects length echo | `ab≈_{T_len}aa`, but `σ(ab)=xyy`, `σ(aa)=xx` | `docs/concepts/multitact_counterexamples.md` | verified by tests |

## Definitions added in 0.5.0

| ID | Name | Location | Dependencies |
|---|---|---|---|
| DEF-021 | Unary schema compatibility | `docs/concepts/schema_compatibility.md`, `src/core/kernel/compatibility.py` | DEF-014, DEF-015 |
| DEF-022 | Binary schema compatibility | `docs/concepts/schema_compatibility.md`, `src/core/kernel/compatibility.py` | DEF-014, DEF-015 |
| DEF-023 | Numeric-prime mode | `docs/concepts/prime_variants.md`, `src/core/numbers/primes.py` | THM-001 |
| DEF-024 | Ordered primitive rhythm | `docs/concepts/prime_variants.md`, `src/core/numbers/primes.py` | DEF-016 |
| DEF-025 | Cyclic primitive rhythm | `docs/concepts/prime_variants.md`, `src/core/numbers/primes.py` | DEF-014, DEF-016 |
| DEF-026 | Resonance-prime mode | `docs/concepts/prime_variants.md`, `src/core/numbers/primes.py` | DEF-012 |

## Propositions added in 0.5.0

| ID | Name | Statement | Uses | Status |
|---|---|---|---|---|
| PROP-001 | Factor-through criterion | Unary `W` respects `(T_in,T_out)` iff output echo-key factors through input echo-key. | DEF-021 | stated |
| PROP-002 | Prime split | Numeric-prime and primitive-rhythm are independent axes in multi-tact settings. | DEF-023..DEF-026 | witnessed by `ab` and one-tact powers |

## Definitions added in 0.6.0

| ID | Name | Location | Dependencies |
|---|---|---|---|
| DEF-027 | Cyclic representative | `docs/concepts/cyclic_weave.md`, `src/core/numbers/weave.py` | DEF-014, DEF-015 |
| DEF-028 | Cyclic weave | `docs/concepts/cyclic_weave.md`, `src/core/numbers/weave.py` | DEF-017, DEF-027 |

## Propositions added in 0.6.0

| ID | Name | Statement | Uses | Status |
|---|---|---|---|---|
| PROP-003 | Ordered weave cycle compatibility | Fixed-symbol ordered substitution respects `(T_cycle,T_cycle)`. | DEF-017, DEF-021 | verified finite tests |
| PROP-004 | Ordered weave word incompatibility | Fixed-symbol ordered substitution generally does not respect `(T_cycle,T_word)`. | DEF-017, CE-003 | verified finite tests |
| PROP-005 | Cyclic weave word compatibility | `cyc_weave_σ` respects `(T_cycle,T_word)` by canonicalization. | DEF-027, DEF-028 | verified finite tests |

## Definitions added in 0.7.0

| ID | Name | Location | Dependencies |
|---|---|---|---|
| DEF-029 | Phase offset | `docs/concepts/phase_resonance.md`, `src/core/numbers/resonance.py` | DEF-005, DEF-012 |
| DEF-030 | Cyclic resonance | `docs/concepts/phase_resonance.md`, `src/core/numbers/resonance.py` | DEF-029 |
| DEF-031 | Resonance obstruction | `docs/concepts/phase_resonance.md`, `src/core/numbers/resonance.py` | DEF-030 |

## Propositions added in 0.7.0

| ID | Name | Statement | Uses | Status |
|---|---|---|---|---|
| PROP-006 | Cyclic resonance extends ordered resonance | If `part` ordered-resonates in `whole`, then `part ▹_cyc whole`. | DEF-012, DEF-030 | verified finite tests |
| PROP-007 | Phase-shift witness | `ab` does not ordered-resonate in `baba`, but `ab ▹_cyc baba` with offsets `1,3`. | DEF-029, DEF-030 | verified by tests |

## Definitions added in 0.8.0

| ID | Name | Location | Dependencies |
|---|---|---|---|
| DEF-032 | Defect | `docs/concepts/approximate_resonance.md`, `src/core/numbers/approx_resonance.py` | DEF-005 |
| DEF-033 | Defect count | `docs/concepts/approximate_resonance.md`, `src/core/numbers/approx_resonance.py` | DEF-032 |
| DEF-034 | Approximate cyclic resonance | `docs/concepts/approximate_resonance.md`, `src/core/numbers/approx_resonance.py` | DEF-030, DEF-033 |

## Propositions added in 0.8.0

| ID | Name | Statement | Uses | Status |
|---|---|---|---|---|
| PROP-008 | Exact implies approximate | If `part ▹_cyc whole`, then `part ▹_{cyc,≤d} whole` for any `d≥0`. | DEF-030, DEF-034 | verified by tests |
| PROP-009 | One-defect witness | `ab ▹_{cyc,≤1} abac` but not `ab ▹_cyc abac`. | DEF-034 | verified by tests |

## Definitions added in 0.9.0

| ID | Name | Location | Dependencies |
|---|---|---|---|
| DEF-035 | Resonance spectrum | `docs/concepts/resonance_spectrum.md`, `src/core/numbers/spectrum.py` | DEF-034 |
| DEF-036 | Spectrum rank | `docs/concepts/resonance_spectrum.md`, `src/core/numbers/spectrum.py` | DEF-035 |

## Propositions added in 0.9.0

| ID | Name | Statement | Uses | Status |
|---|---|---|---|---|
| PROP-010 | Exact-first ranking | Exact resonances rank before bounded-defect resonances with positive defect count. | DEF-035, DEF-036 | verified by tests |
| PROP-011 | Spectrum contains bounded witness | `Spec_1(abac,{ab,cc})` ranks `ab` as bounded-defect resonance. | DEF-035 | verified by tests |

## Definitions added in 1.0.0

| ID | Name | Location | Dependencies |
|---|---|---|---|
| DEF-037 | Explanation cost | `docs/concepts/compression_score.md`, `src/core/numbers/compression.py` | DEF-035, DEF-036 |
| DEF-038 | Compression saving | `docs/concepts/compression_score.md`, `src/core/numbers/compression.py` | DEF-037 |
| DEF-039 | Compression ratio | `docs/concepts/compression_score.md`, `src/core/numbers/compression.py` | DEF-038 |

## Propositions added in 1.0.0

| ID | Name | Statement | Uses | Status |
|---|---|---|---|---|
| PROP-012 | Exact repetition compresses | `ab` compresses `ababab` with saving `4` under default weights. | DEF-037..DEF-039 | verified by tests |
| PROP-013 | Defect cost controls explanation | `ab` explaining `abac` has saving `0` at `w_def=2`, saving `1` at `w_def=1`. | DEF-037..DEF-039 | verified by tests |

## Definitions added in 1.1.0

| ID | Name | Location | Dependencies |
|---|---|---|---|
| DEF-040 | Processed table artifact | `docs/concepts/processed_tables.md`, `src/core/registry/tables.py` | DEF-035, DEF-037 |

## Reproducible artifacts added in 1.1.0

| Artifact | Generator | Contents | Status |
|---|---|---|---|
| `data/processed/spectrum_abac.csv` | `scripts/generate_tables.py` | resonance spectrum rows | generated |
| `data/processed/compression_abac.csv` | `scripts/generate_tables.py` | compression score rows | generated |
| `data/processed/prime_variants_len4.csv` | `scripts/generate_tables.py` | prime variant profiles | generated |
| `data/processed/counterexamples_len4.json` | `scripts/generate_tables.py` | finite counterexample witnesses | generated |
| `data/processed/manifest.json` | `scripts/generate_tables.py` | run parameters and artifact metadata | generated |

## Processed artifacts extended in 1.2.0

| Artifact | Generator | Contents | Status |
|---|---|---|---|
| `data/processed/phase_resonance_ab_len4.csv` | `scripts/generate_tables.py` | ordered/cyclic resonance rows for part `ab` | generated |
| `data/processed/approx_resonance_ab_len4.csv` | `scripts/generate_tables.py` | bounded-defect resonance rows for part `ab` | generated |
| `data/processed/cyclic_weave_len4.csv` | `scripts/generate_tables.py` | ordered vs cyclic weave outputs | generated |

## Definitions added in 1.3.0

| ID | Name | Location | Dependencies |
|---|---|---|---|
| DEF-041 | Weighted defect cost map | `docs/concepts/weighted_defects.md`, `src/core/numbers/weighted_resonance.py` | DEF-032 |
| DEF-042 | Weighted defect | `docs/concepts/weighted_defects.md`, `src/core/numbers/weighted_resonance.py` | DEF-041 |
| DEF-043 | Weighted approximate cyclic resonance | `docs/concepts/weighted_defects.md`, `src/core/numbers/weighted_resonance.py` | DEF-034, DEF-041 |

## Propositions added in 1.3.0

| ID | Name | Statement | Uses | Status |
|---|---|---|---|---|
| PROP-014 | Cheap defect witness | With `κ(b,c)=0.25`, `ab ▹_{cyc,κ≤0.5} abac`. | DEF-041..DEF-043 | verified by tests |
| PROP-015 | Default cost rejection | With empty cost map and budget `0.5`, `ab` does not weighted-resonate in `abac`. | DEF-041..DEF-043 | verified by tests |
