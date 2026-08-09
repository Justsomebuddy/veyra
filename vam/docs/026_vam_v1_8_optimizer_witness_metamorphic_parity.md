# VAM v1.8 — Optimizer witness ledger and metamorphic parity

**Status:** accepted bounded regression evidence  
**Boundary:** not proof-grade optimizer correctness, not global semantic equivalence, not a performance claim.

## Purpose

v1.8 adds two regression surfaces around the conservative optimizer:

1. `vam/src/optimizer_witness.py` builds a deterministic witness ledger for one optimizer run.
2. `tests/vam/test_vam_native_optimizer_metamorphic.py` checks native VAM0/VAMD optimizer behavior under small metamorphic perturbations.

The goal is operational confidence: if a future optimizer change alters the bounded evidence, tests should fail before the change is treated as accepted VAM semantics.

## Witness ledger

`optimizer_witness_ledger(program)` records:

- original instruction rows;
- optimized instruction rows;
- accepted and rejected optimizer rows;
- equivalence-summary rows from the current Python oracle;
- canonical semantic-core reports for original and optimized programs;
- stable SHA-256 JSON digests for each section plus a top-level ledger digest.

The ledger uses:

```text
profile = vam-optimizer-witness-v1
boundary = bounded-witness-ledger
claim = regression-evidence-not-proof
digest_algorithm = sha256-json-v1
```

Allowed statuses are intentionally modest:

- `bounded-regression-match`
- `bounded-regression-blocked`
- `bounded-regression-inconclusive`

These statuses are evidence labels only. They are not theorem labels.

## Native metamorphic harness

The native harness checks that the current `observer-alias-v1` slice remains stable across:

- VAM0 vs decoded VAMD optimizer input producing the same optimized semantic report;
- repeated native runs producing byte-identical JSON output;
- source-line perturbations preserving semantic core while allowing line metadata to differ;
- obstruction cases remaining visible as rejected optimizer rows.

This is still a bounded harness. It does not claim exhaustive coverage of all programs, all optimizer passes, or all future bytecode frames.

## Certificate gate

`vam_reference_v1` now requires:

- `optimizer_witness_ledger()` to produce the bounded witness profile/claim/status/digest;
- the witness implementation and test file to exist;
- this documentation gate to exist;
- the native metamorphic parity test file to exist.

The gate is deliberately presence-plus-smoke evidence. Full proof-grade optimizer semantics remain future work.

## Non-claims

v1.8 does **not** claim:

- formally verified optimizer correctness;
- global semantic equivalence for all VAM programs;
- native speedup;
- VAMD optimized-frame emission;
- compiler verification;
- replacement of Python as the semantic oracle.

## Next pressure

The remaining optimizer/backend work is now clearer:

1. proof-grade optimizer semantics beyond bounded witnesses and corpora;
2. richer compression rules with theorem-level preconditions;
3. VAMD optimized-frame emission only if explicitly specified;
4. performance backends after parity and fallback checks are stronger.
