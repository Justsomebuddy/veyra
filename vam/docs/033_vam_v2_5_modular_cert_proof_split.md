# VAM v2.5 — Modular certificate/proof split

**Status:** accepted structural refactor for VAM optimizer certification and proof-catalog organization  
**Boundary:** module organization and maintainability only; no new whole-pass proof, whole-optimizer correctness, VAMD optimized emission, native speed, or proof-assistant claim.

## Purpose

v2.5 closes the v2.4 pressure point: the VAM certificate bridge and optimizer proof bridge were at the project file-size boundary. Instead of adding more gates to already-dense modules, the optimizer-specific responsibilities are split into focused helpers.

## New module boundaries

- `src/core/certify_vam.py` remains the high-level `vam_reference_v1` certificate suite runner.
- `src/core/certify_vam_optimizer.py` owns the optimizer proof-bridge and pre/post witness gates used by `vam_reference_v1`.
- `vam/src/optimizer_proofs.py` remains the public proof-row and Lean-check API.
- `vam/src/optimizer_proof_catalog.py` owns the checked local-law catalog and required Lean-symbol binding checks.

## Preserved semantics

The split is intentionally behavior-preserving:

- seven checked local laws remain required;
- v2.4 executable pre/post witness rows remain required;
- all optimizer passes remain obligation-backed;
- the certificate detail string still reports proof-bridge and pre/post witness state;
- module-size tests now keep the split from regressing back into monoliths.

## Verification pressure

The acceptance checks are:

1. `certify_vam_optimizer_gate()` reports a checked proof bridge and accepted pre/post witnesses;
2. the catalog binds all required Lean theorem symbols from `proofs/lean/VeyraOptimizer.lean`;
3. the original accepted split kept `src/core/certify_vam.py`, `src/core/certify_vam_optimizer.py`, `vam/src/optimizer_proofs.py`, and `vam/src/optimizer_proof_catalog.py` under 300 LOC; current maintenance applies the repository's 1000-line target and justified-exception ceiling;
4. targeted optimizer/cert tests and full project verification pass.

## Non-claims

v2.5 does **not** add optimizer power. It is a structural step that makes future work safer: richer compression laws, more executable witnesses, and a later whole-optimizer theorem skeleton can be added without turning certificate/proof modules into unreadable monoliths.
