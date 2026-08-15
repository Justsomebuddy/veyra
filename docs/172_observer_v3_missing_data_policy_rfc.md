# 172 — Explicit Masked Missing-Data Preprocessing V1 RFC

**Date:** 2026-08-15  
**Status:** accepted contract; additive runtime implemented in document 175  
**Issue:** [#55](https://github.com/Justsomebuddy/veyra/issues/55)  
**Future package:** `src.core.observer_discovery_v3.missing_data`

## Problem

Strict-v3 categorical CSV/JSONL ingestion deliberately rejects every missing value. Missingness must not be smuggled in as an ordinary category, silently dropped, or imputed by an adapter that still returns an indistinguishable v1 `ThreeWayPresentation`.

This RFC freezes one optional, separately versioned missingness-encoding boundary. It does not request implementation in the existing ingestion package.

## Compatibility boundary

The existing `src.core.observer_discovery_v3` schema, ingestion APIs, DTOs, canonical bytes, digests, exports, limits, errors, and Phase-II behavior remain exact. Existing CSV `m:` cells and JSON `null` remain invalid. In particular, current ingestion `__all__` remains exactly its two CSV/JSONL builders and the pinned schema/train/validation/test/protocol fixture digests remain `d42e8500d9ebc85082c79a98adc1a1f8d73ab7cffb8724e31311e78f596fcb2e`, `7aa79b6bef37899967e46b68aec6651de256901ee9ecc51bbd4a26084457097a`, `38137753a110489085db6e805348a44f234e3fe868309f21d43a94c69859ab49`, `bb36865915e69edd987a7126bfb914679cdc2c8e0bf7b5817c94ce8a37e05b8d`, and `c2bf2795f7b5008622242582f25227c59abc7415a8ae30a9f75f1995b3d6b0d1`.

Any future implementation must live only in non-root sibling `src.core.observer_discovery_v3.missing_data`, use policy schema `veyra.observer-discovery.v3.missing-policy.v1` and wrapper schema `veyra.observer-discovery.v3.missing-presentation.v1`, and return a separate `MissingnessPresentation`, never a bare v1 presentation that erases policy authority. It must not edit, widen, or refactor the existing ingestion parser or exports.

## Proposed v1 policy and projection

The policy binds the canonical base `schema_digest`, a complete caller-supplied projected `RepresentationSchema`, and exactly one ordered rule for every base feature. First compute `projection_spec_root = H("veyra.observer-discovery.v3.missing-projection-spec-root.v1", base schema digest, ordered modes, exact fallbacks, exact derived names)`. This root explicitly excludes the projected schema ID and digest:

1. `REQUIRED` — the projected field is byte-identical to the base field and missing input rejects.
2. `EXPLICIT_MASK` — permitted only for a base `categorical` field. The projected schema contains the byte-identical base field followed immediately by a derived binary field named `<base-name>__present_v1`, with exact integer categories `(0, 1)`. Presence is `1 = PRESENT` and `0 = MISSING`.

A missing cell uses one caller-declared fallback whose exact type and value already belong to the base categorical domain and sets presence to `0`. An observed cell, including an observed value equal to the fallback, sets presence to `1`; therefore missing and observed fallback are distinct. Exact `binary` fields are always `REQUIRED` in v1. The projected schema must match this expansion exactly, have a different schema ID fixed as `missing-v1:<64-lowercase-hex projection_spec_root>`, and remain within all v1 schema bounds. Only after that validation is the final policy root computed over the base schema digest, projection-spec root, projected schema digest, and ordered rules; no digest depends on itself. Derived-name UTF-8 overflow or collision with any input, derived, identity, target, or reserved name rejects.

No row, identity, target, or group field may be missing. No row is dropped, repaired, reordered, deduplicated, or synthesized. An all-observed input is allowed, but its wrapper/policy authority remains distinct.

Wire syntax is explicit and otherwise unchanged:

- CSV feature cell: exact `m:` only under `EXPLICIT_MASK`;
- JSONL feature value: exact `null` only under `EXPLICIT_MASK`.

## Receipt and replay authority

The authority class is exactly `NATIVE_POLICY_REPLAY` or `EXTERNAL_BINDING_ONLY`. `NATIVE_POLICY_REPLAY` is derived only after fresh replay of the exact policy, base/projected schemas, and all three original raw payloads. A validator name, digest, structurally decoded wrapper, or equal v1 presentation root never confers native authority.

Each split receipt separately binds this ordered tuple:

1. domain-separated raw-byte digest;
2. ordered semantic-input plus row-major missing-mask digest;
3. exact projection/assignment digest;
4. projected output payload digest; and
5. row count.

The top receipt binds version, authority, base and projected schema digests, policy digest, ordered train/validation/test receipts, exact v1 protocol digest, and boundary/nonclaim digest. Equal projected v1 roots may coexist with unequal raw/policy receipts. Raw digests establish supplied-byte identity only, never source origin, truth, authentication, or provenance.

The bounded structural decoder may create only an `EXTERNAL_BINDING_ONLY` value and grants no native authority. The source-backed replay API accepts the policy, both schemas, and exact train/validation/test bytes, reconstructs everything from scratch, and is the sole native verifier. Digest-only acceptance is forbidden. Callers cannot supply or upgrade authority.

Digest domains are exactly `veyra.observer-discovery.v3.missing-projection-spec-root.v1`, `veyra.observer-discovery.v3.missing-policy-root.v1`, `veyra.observer-discovery.v3.missing-raw-split.v1`, `veyra.observer-discovery.v3.missing-semantic-mask.v1`, `veyra.observer-discovery.v3.missing-projection.v1`, `veyra.observer-discovery.v3.missing-split-receipt.v1`, `veyra.observer-discovery.v3.missing-receipt.v1`, and `veyra.observer-discovery.v3.missing-nonclaims.v1`.

## Bounds and validation order

Raw exact type and 16 MiB split/32 KiB physical-record caps, policy cardinality, and aggregate policy caps of 16384 nodes and 1 MiB nonpayload UTF-8 precede decoding. Parsing then incrementally charges logical records, decoded scalars, masks, nodes, and text. The complete projected schema/field/cell budget is precharged before canonical construction.

The projected output remains within the existing 32-field, 8192-row-per-split, 262144-cell, scalar/text/integer and lineage limits. Combined source, policy, mask, receipt, and projected-wrapper material is capped at 65536 nodes and 1 MiB nonpayload UTF-8/canonical JSON. Exceeding any cap rejects rather than truncates. Logs contain only fixed reason codes, safe type names, and aggregate counts.

## Runtime realization

The additive implementation is documented by
[`175_observer_v3_missing_data_runtime.md`](175_observer_v3_missing_data_runtime.md).
It lives only in the named non-root sibling, retains the complete policy and
receipt beside the projected presentation, binds the exact wire-format enum,
and uses `SHA256(domain_utf8 || NUL || exact_bytes)` for each raw split. The
structural decoder accepts only `EXTERNAL_BINDING_ONLY`; native authority is
available only through complete fresh source-backed replay.

## Required implementation evidence

- exact v1 byte/digest/export/error pins and root nonexport;
- CSV/JSONL semantic parity and split-order preservation;
- required-versus-masked cases, observed fallback versus missing fallback, and all-observed policy-bound replay;
- missing identity/target and binary-mask rejection;
- fallback/category, projected schema, derived-name, duplicate-key, type, resource, splice, mutation, callback/TOCTOU, authority-confusion, decoder, and replay pressure;
- package and Linux/macOS/Windows portable coverage;
- independent contract and implementation reviews.

## Non-claims and stops

This policy establishes only an explicit finite encoding of caller-declared missing markers. It does not establish that a marker denotes real-world absence, that a fallback is correct, or any MCAR/MAR/MNAR mechanism. It establishes no imputed observation, sampling validity, likelihood, unbiasedness, identifiability, target secrecy, statistical leakage freedom beyond existing ID disjointness, source truth/authentication/provenance, custody, chronology, causal/statistical validity, theorem, certificate, object formation, or claim promotion.

Stop and redesign if implementation requires changing old ingestion source/`__all__`, schema/version/boundary/digest bytes, errors, Phase-II behavior, or the old private parser; accepting unmarked sentinels; missing identities/targets; masking binary fields; learning fallbacks; dropping rows; erasing mask/raw/policy bindings; or treating detached/equal-root evidence as native replay.

## Publication scope

The original issue and RFC publication were documentation-only. The executable
sibling is a later independently reviewed implementation and does not widen the
old ingestion package. Continuous numeric interpretation and missing×continuous
composition remain explicitly out of scope and belong to separate independently
reversible work.
