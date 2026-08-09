# Additions 1.4.0–2.2.0

Part of the public [Theorem and Definition Registry](../../THEOREMS.md).

## Additions 1.4.0–2.2.0

## Processed artifacts extended in 1.4.0
| Artifact | Generator | Contents | Status |
|---|---|---|---|
| `data/processed/weighted_resonance_ab_len4.csv` | `scripts/generate_tables.py` | weighted-defect resonance rows for part `ab` | generated |
## Definitions added in 1.5.0
| ID | Name | Location | Dependencies |
|---|---|---|---|
| DEF-044 | Tact aura | `docs/concepts/tact_similarity.md`, `src/core/numbers/tact_similarity.py` | DEF-003, DEF-005 |
| DEF-045 | Aura similarity | `docs/concepts/tact_similarity.md`, `src/core/numbers/tact_similarity.py` | DEF-044 |
| DEF-046 | Aura-derived defect cost | `docs/concepts/tact_similarity.md`, `src/core/numbers/tact_similarity.py` | DEF-041, DEF-045 |
## Propositions added in 1.5.0
| ID | Name | Statement | Uses | Status |
|---|---|---|---|---|
| PROP-016 | Context twins become cheap defects | In cyclic context `abac`, `b` and `c` have identical radius-1 auras, so `κ_A(b,c)=κ_A(c,b)=0.25` under default floor. | DEF-044..DEF-046 | verified by tests |
## Processed artifacts extended in 1.5.0
| Artifact | Generator | Contents | Status |
|---|---|---|---|
| `data/processed/tact_aura_costs_abac.csv` | `scripts/generate_tables.py` | derived tact aura similarities and costs | generated |
## Definitions added in 1.6.0
| ID | Name | Location | Dependencies |
|---|---|---|---|
| DEF-047 | Balance mode | `docs/concepts/balance_modes.md`, `src/core/shadows/balance.py` | DEF-005 |
| DEF-048 | Opposite balance | `docs/concepts/balance_modes.md`, `src/core/shadows/balance.py` | DEF-047 |
| DEF-049 | Ratio mode | `docs/concepts/ratio_modes.md`, `src/core/shadows/ratio.py` | DEF-047 |
| DEF-050 | Canonical ratio shadow | `docs/concepts/ratio_modes.md`, `src/core/shadows/ratio.py` | DEF-049, THM-001 |
## Propositions added in 1.6.0
| ID | Name | Statement | Uses | Status |
|---|---|---|---|---|
| PROP-017 | Balance recovers signed length arithmetic | Under `len±`, balance stitch and opposite recover integer addition and negation. | DEF-047, DEF-048 | verified by tests |
| PROP-018 | Ratio recovers rational arithmetic shadow | Under `shadow(Q)`, ratio addition/subtraction/multiplication/inverse recover rational arithmetic where defined. | DEF-049, DEF-050 | verified by tests |
## Definitions added in 1.7.0
| ID | Name | Location | Dependencies |
|---|---|---|---|
| DEF-051 | Length dominance | `docs/concepts/order_magnitude.md`, `src/core/shadows/order.py` | DEF-047 |
| DEF-052 | Balance magnitude | `docs/concepts/order_magnitude.md`, `src/core/shadows/order.py` | DEF-047, DEF-051 |
| DEF-053 | Ratio dominance | `docs/concepts/order_magnitude.md`, `src/core/shadows/order.py` | DEF-049, DEF-050 |
| DEF-054 | Ratio interval | `docs/concepts/order_magnitude.md`, `src/core/shadows/order.py` | DEF-053 |
## Propositions added in 1.7.0
| ID | Name | Statement | Uses | Status |
|---|---|---|---|---|
| PROP-019 | Dominance recovers school inequalities | Balance and ratio comparisons recover integer/rational order in the one-tact length shadow. | DEF-051, DEF-053 | verified by tests |
| PROP-020 | Ratio intervals recover interval membership | Closed/open ratio interval checks recover rational interval membership under `shadow`. | DEF-054 | verified by tests |
## Definitions added in 1.8.0
| ID | Name | Location | Dependencies |
|---|---|---|---|
| DEF-055 | Linear ratio form | `docs/concepts/linear_equations.md`, `src/core/shadows/equation.py` | DEF-049 |
| DEF-056 | Linear constraint | `docs/concepts/linear_equations.md`, `src/core/shadows/equation.py` | DEF-055 |
| DEF-057 | Equation obstruction | `docs/concepts/linear_equations.md`, `src/core/shadows/equation.py` | DEF-056 |
## Propositions added in 1.8.0
| ID | Name | Statement | Uses | Status |
|---|---|---|---|---|
| PROP-021 | Linear constraints recover school equations | In the one-tact rational shadow, solving `A·x+B=C·x+D` recovers ordinary linear equation solutions and obstructions. | DEF-055..DEF-057 | verified by tests |
## Definitions added in 1.9.0
| ID | Name | Location | Dependencies |
|---|---|---|---|
| DEF-058 | Polynomial ratio form | `docs/concepts/polynomial_forms.md`, `src/core/shadows/polynomial.py` | DEF-049, DEF-055 |
## Propositions added in 1.9.0
| ID | Name | Statement | Uses | Status |
|---|---|---|---|---|
| PROP-022 | Polynomial operations recover school algebra shadows | Addition, convolution multiplication, evaluation, and formal derivative match ordinary rational polynomial arithmetic in the length shadow. | DEF-058 | verified by tests |
## Definitions added in 2.0.0
| ID | Name | Location | Dependencies |
|---|---|---|---|
| DEF-376 | Full realization certificate | `docs/concepts/full_realization_contract.md`, `src/core/certify.py` | DEF-015, DEF-030, DEF-046, DEF-047, DEF-049, DEF-053, DEF-056, DEF-058 |
## Certification added in 2.0.0
| Certificate | Method | Status |
|---|---|---|
| echo | `≈_T` observer-indexed echo | pass |
| cyclic_resonance | `▹_cyc` phase resonance | pass |
| aura_weighted | `κ_A` aura-derived weighted resonance | pass |
| balance/ratio/order/equation/polynomial | Veyra school-core shadows | pass |
## Definitions added in 2.1.0
| ID | Name | Location | Dependencies |
|---|---|---|---|
| DEF-377 | Raw ratio operation | `docs/concepts/native_ratio_lift.md`, `src/core/shadows/ratio.py` | DEF-047, DEF-049 |
| DEF-378 | Native cross-scale addition | `docs/concepts/native_ratio_lift.md`, `src/core/shadows/ratio.py` | DEF-377 |
## Certification updated in 2.1.0
| Certificate | Previous | Current |
|---|---|---|
| ratio | Level 0 canonical shadow addition | Level 1 raw cross-scale addition plus shadow check |
## Certification added in 2.2.0
| Certificate | Method | Status |
|---|---|---|
| sage_mode_parent | `VeyraModes` preserves cyclic and weighted resonance methods | pass |
| sage_balance_parent | `VeyraBalances` preserves balance stitch/opposition behavior with explicit shadows | pass |
| sage_ratio_parent | `VeyraRatios` preserves raw/canonical ratio behavior with explicit shadows | pass |
| sage_polynomial_parent | `VeyraPolynomials` preserves polynomial operations with explicit coefficient/value shadows | pass |
