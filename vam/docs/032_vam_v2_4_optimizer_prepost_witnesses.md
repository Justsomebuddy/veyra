# VAM v2.4 — Optimizer pre/postcondition witnesses

**Status:** accepted executable witness evidence for `vam/src/optimizer_prepost.py` and `tests/vam/test_vam_optimizer_prepost.py`  
**Boundary:** executable pre/post witness evidence only; not a whole-pass proof, not whole-optimizer correctness, not global semantic equivalence, not speed/native performance, not VAMD emission.

## Purpose

v2.4 introduced the executable witness layer; v2.9 now connects the seven checked local laws to concrete optimizer examples through executable pre/postcondition witnesses. The witness layer is deliberately small: each row records a local law name, a concrete before/after optimizer shape, the expected precondition, and the expected postcondition that should be observed by the local example.

This is a bridge between proof artifacts and executable regression evidence. It does not upgrade the optimizer into a theorem-proved pass. It shows that the checked local laws are represented by concrete examples that can be run and inspected.

## Artifacts

- Module: `vam/src/optimizer_prepost.py`
- Test: `tests/vam/test_vam_optimizer_prepost.py`
- Boundary field: `optimizer-prepost-witness`
- Claim field: `executable-prepost-witness-not-proof`

The rows stay deterministic and reviewable, using compact instruction lists rather than broad generated corpora.

## Local laws covered

The current witness set covers exactly the seven currently checked local laws:

1. `observer-alias` — local observer lookup preservation.
2. `compress-alias` — same source/observer `COMPRESS` lookup preservation.
3. `compress-idempotent` — same-observer compression idempotence.
4. `compress-idempotent` — visible-use observer preservation.
5. `compress-idempotent` — different-observer rejection.
6. `compress-idempotent` — obstruction-boundary rejection.
7. `dead-shadow` — unused lookup/drop preservation.

Each witness names the connected checked local law and keeps pass-level optimizer behavior separate from the local-law evidence.

## Suggested witness row contract

A compact row can be enough:

```text
law = observer-alias | compress-alias | compress-idempotent | dead-shadow
boundary = optimizer-prepost-witness
claim = executable-prepost-witness-not-proof
precondition = checked local example precondition
postcondition = checked local example postcondition
before_digest = digest/canonical report for the concrete input
optimized_digest = digest/canonical report for the concrete optimized form
status = witness-ready
```

The Python dataclass is `OptimizerPrePostWitness`; the boundary and claim strings stay stable for certificate/export integration.

## How this relates to earlier evidence

- v1.8 witness/metamorphic parity gave bounded regression evidence.
- v1.9 proof-obligation rows named the optimizer obligations.
- v2.0-v2.3 checked four local laws in Lean; v2.6-v2.7 add two rejection laws; v2.9 adds visible-use observer preservation.
- v2.4-v2.9 connect those seven checked local laws to concrete executable examples.

The relationship is evidential, not proof-compositional. The witness rows can justify that local-law examples are executable and synchronized with optimizer examples, but they do not compose into whole-pass correctness.

## Certificate/export pressure

The integration gate requires:

- all seven local-law names to appear in the pre/post witness summary;
- every row to use `boundary = optimizer-prepost-witness`;
- every row to use `claim = executable-prepost-witness-not-proof`;
- the witness module and test file to exist;
- no row to claim global semantic equivalence, native speed, optimized VAMD emission, or whole-optimizer proof.

Because `src/core/certify_vam.py` is near the project file-size cap, the next certification work should split VAM certificate/proof helpers before adding more large gates.

## Non-claims

v2.4 does **not** claim:

- proof of any whole optimizer pass;
- proof of the whole optimizer;
- global semantic equivalence;
- optimized VAMD frame emission;
- native speedup, GPU readiness, or VAMD/native performance;
- replacement of the Python semantic oracle;
- a theorem skeleton for the whole optimizer.

## Next pressure

1. v2.5 completed the near-cap certificate/proof module split before adding more gates;
2. add richer compression laws only as local checked laws plus executable examples;
3. keep witness rows small enough to review by hand;
4. only after enough local laws and witnesses exist, draft an explicit whole-optimizer theorem skeleton with all missing assumptions named.
