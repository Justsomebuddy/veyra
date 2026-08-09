# Finite tensor, Born, and unitarity semantics

**Status:** checked finite semantic layer  
**Implementation:** `src/core/quantum/tensor_semantics.py`  
**Formal artifact:** `proofs/lean/VeyraQuantumTensor.lean`  
**Tests:** `tests/quantum/test_quantum_tensor_semantics.py`, `tests/quantum/test_quantum_tensor_formal.py`
**Certificate:** `quantum_tensor_q11`

## Scope

This layer closes three prerequisites for using quantum vocabulary in the
finite Q-Veyra branch:

1. tensor products accept any finite number of state or gate factors;
2. Born weights are defined exactly as squared amplitude norms;
3. unitarity is checked over the complete finite matrix, on both sides.

The executable scalar carrier is the existing
`Q(sqrt(2))[i]` representation `QAmp`. No floating-point comparison or
tolerance enters these checks.

## Executable definitions

For modes

\[
  |\psi_j\rangle=\sum_{x_j}a_{j,x_j}|x_j\rangle,
\]

`tensor_modes((psi_1, ..., psi_n))` constructs

\[
  \bigotimes_{j=1}^n|\psi_j\rangle
  =\sum_{x_1,\ldots,x_n}\left(\prod_j a_{j,x_j}\right)
   |x_1\otimes\cdots\otimes x_n\rangle.
\]

The empty product is the one-dimensional scalar mode. Nonempty tensor factors
must use nonempty basis labels without the reserved `⊗` separator, making the
human-readable product labels injective. `tensor_gates` uses the same empty
product convention for Kronecker products of square matrices.

For a finite mode, `born_distribution` returns the exact ledger

\[
  p_x=|a_x|^2=a_x^*a_x,
\]

and `born_total` returns `sum_x p_x`. `is_normalized` requires exact equality
with one. These are exact weights; callers must not reinterpret an
unnormalized vector as a probability distribution.

For a square gate `U`, `unitarity_witness` constructs the conjugate transpose
and checks every entry of

\[
  U^\dagger U=I \quad\text{and}\quad UU^\dagger=I.
\]

This is a full finite matrix check rather than sampling selected seed states.
`apply_unitary` fails closed unless that witness succeeds and then checks exact
norm preservation after application.

## Formal theorem scope

`VeyraQuantumTensor.lean` deliberately uses a smaller theorem carrier than the
Python implementation:

- a `FiniteBornState` is a list of natural probability numerators with a
  positive common scale;
- `THM_Q11_001_born_rule_normalized` proves that the finite outcome weights sum to the
  declared scale;
- `TensorBorn` represents an arbitrarily long finite factor chain;
- `THM_Q11_002_tensor_born_normalized` proves exact normalization of that chain;
- `ExactUnitary` packages a forward map, a two-sided inverse, and exact norm
  preservation;
- `THM_Q11_003_tensor_unitary` and `THM_Q11_004_compose_unitary` prove closure
  under tensor product and composition.

The Lean theorem does **not** claim equivalence between natural-weight states
and the full executable `Q(sqrt(2))[i]` carrier. Python matrix identities and
Lean structural closure are separate, explicitly bounded evidence layers.

## Validation and failure behavior

The Python API rejects:

- empty or dimension-mismatched modes;
- duplicate, empty, or reserved-`⊗` tensor-factor basis labels;
- non-square or empty gate matrices;
- incompatible bases for inner products;
- gate/state dimension mismatches;
- application of a matrix without a complete unitarity witness.

Tests cover empty and three-factor tensors, exact Hadamard Born weights,
two-factor Born multiplicativity, one- and two-qubit unitary gates, an
eight-dimensional tensor gate, norm preservation, ambiguous-label rejection,
exact theorem-ID presence, pinned Lean compilation, and other rejection paths.

## Claim boundary

This artifact establishes only **finite executable semantics** and the exact
Lean theorem scope described above. It is not:

- an analytic infinite-dimensional Hilbert-space development;
- a noise, calibration, or hardware model;
- a certified general-purpose quantum simulator;
- evidence for quantum advantage;
- evidence about a physical quantum apparatus.

Any future apparatus, performance, or advantage statement requires a separate
model, external evidence, baselines, and certification.
