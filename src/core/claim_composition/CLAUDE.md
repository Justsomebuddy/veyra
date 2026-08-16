# Claim Composition Module Memory

## Purpose

`src.core.claim_composition` constructs and freshly replays bounded local claim
contracts, canonical source families, exact finite conjunction licenses,
four-axis assessments, nonpromoted receipts, public exports, authentication,
detached replay packages and the index-free v1 P2 premise.

## Policy L local-source admission

- `LocalClaimReceipt` admits only canonical leaf contracts with exact
  `LOCAL` quantifier and an empty `component_contract_digests` tuple.
- `_is_local_source_contract()` is the sole local-profile gate. Aggregate
  re-entry fails with `aggregate-contract-local-reentry` before source-root or
  validity processing; logs contain only entry/exit and the fixed reason.
- Exact conjunction remains one flat N-ary operation over admitted local
  leaves. Aggregate outputs cannot be relabeled as leaves; no digest ancestry,
  recursive flattening or recomposition authority is inferred.

## Policy A semantic-component contract

- `ClaimContract.component_contract_digests` on an exact conjunction is the
  sorted unique set of source semantic contract digests.
- Canonical sources remain occurrence-based and ordered by exact local receipt
  digest. Distinct receipts for the same contract remain distinct sources;
  an exactly repeated receipt is rejected.
- License source bindings, assessment/receipt source families and downstream
  P2 receipt/validator/authority bindings retain every distinct occurrence.
- `_component_contract_digests()` is the sole producer/validator derivation.
  Its entry/exit logs disclose counts only, never contract or receipt roots.

## Compatibility and nonclaims

- Do not change `_canonical_roots`, canonical source ordering, local receipt,
  license, assessment or composition-receipt schemas/codecs/domains, public
  exports, root exports or P2 production for this policy.
- Existing distinct-contract v1/v2 bytes and digest pins must remain exact.
- Multiple receipts establish only `MULTIPLE_LOCAL_RECEIPTS`; they do not
  establish source truth, agreement, independent corroboration, independence,
  validator trust, native authority, assumption discharge, stronger wording,
  theorem status or P2 promotion.

## Version

Module contract `1.0.2` (issue #76 Policy L local-source admission).

## Session Notes (2026-08-16)

- Policy L closes aggregate-as-local re-entry at the canonical local-receipt
  constructor. Flat A∧B∧C remains canonical; both nested bracketings fail at
  the same named boundary. DTOs, codecs, digest domains, exports, Policy A
  evidence occurrence semantics and P2 production remain unchanged.

## Session Notes (2026-08-15)

- Same-contract/distinct-receipt construction now deduplicates only target
  semantic component identity. Permanent v1/property/P2 regressions retain two
  exact evidence occurrences, external-only authority and false stronger flags.
- Focused and broader claim-composition/P2 verification passed `22/22` and
  `116/116`; package metadata passed `30/30`, the exact v1/v2 pin passed, and
  strict target Mypy, Bandit, Ruff lint, compile, hygiene, privacy and boundary
  gates are green. Full `make verify` was intentionally not run.
