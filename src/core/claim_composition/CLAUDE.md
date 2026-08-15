# Claim Composition Module Memory

## Purpose

`src.core.claim_composition` constructs and freshly replays bounded local claim
contracts, canonical source families, exact finite conjunction licenses,
four-axis assessments, nonpromoted receipts, public exports, authentication,
detached replay packages and the index-free v1 P2 premise.

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

Module contract `1.0.1` (issue #71 Policy A semantic component set).

## Session Notes (2026-08-15)

- Same-contract/distinct-receipt construction now deduplicates only target
  semantic component identity. Permanent v1/property/P2 regressions retain two
  exact evidence occurrences, external-only authority and false stronger flags.
- Focused and broader claim-composition/P2 verification passed `22/22` and
  `116/116`; package metadata passed `30/30`, the exact v1/v2 pin passed, and
  strict target Mypy, Bandit, Ruff lint, compile, hygiene, privacy and boundary
  gates are green. Full `make verify` was intentionally not run.
