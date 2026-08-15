# 173 — Exact Fixed-Bin Continuous Preprocessing V1 RFC

**Date:** 2026-08-15  
**Status:** accepted documentation contract; runtime not implemented  
**Issue:** [#57](https://github.com/Justsomebuddy/veyra/issues/57)  
**Future package:** `src.core.observer_discovery_v3.continuous_data`

## Problem

Strict-v3 ingestion accepts finite categorical string/integer/boolean domains and deliberately performs no continuous interpretation. Floating-point parsing, data-derived binning, normalization, or quantile fitting must not be introduced behind the existing categorical API.

This RFC freezes one optional, separately versioned exact-decimal binning boundary. It is independent of the missing-data RFC and does not request implementation in the existing ingestion package.

## Compatibility boundary

The existing `src.core.observer_discovery_v3` schema, ingestion APIs, DTOs, canonical bytes, digests, exports, limits, errors, and Phase-II behavior remain exact. JSON numeric floats and CSV decimal tags remain invalid to v1. Current ingestion `__all__` remains exactly its two CSV/JSONL builders and the pinned schema/train/validation/test/protocol fixture digests remain `d42e8500d9ebc85082c79a98adc1a1f8d73ab7cffb8724e31311e78f596fcb2e`, `7aa79b6bef37899967e46b68aec6651de256901ee9ecc51bbd4a26084457097a`, `38137753a110489085db6e805348a44f234e3fe868309f21d43a94c69859ab49`, `bb36865915e69edd987a7126bfb914679cdc2c8e0bf7b5817c94ce8a37e05b8d`, and `c2bf2795f7b5008622242582f25227c59abc7415a8ae30a9f75f1995b3d6b0d1`.

Any future implementation must live only in non-root sibling `src.core.observer_discovery_v3.continuous_data`, use policy schema `veyra.observer-discovery.v3.continuous-policy.v1` and wrapper schema `veyra.observer-discovery.v3.continuous-presentation.v1`, and return a separate `ContinuousBinnedPresentation`, never a bare v1 presentation that hides how exact-decimal observations became categories. It must not edit, widen, or refactor the existing ingestion parser or exports.

## Proposed v1 policy and output schema

The policy binds one existing canonical output `RepresentationSchema` and exactly one ordered rule per schema field:

1. `PASSTHROUGH_CATEGORICAL` — current CSV/JSON categorical scalar grammar applies and the output field is unchanged.
2. `EXACT_DECIMAL_BINS` — the source column carries canonical exact decimals; the output field must be `categorical`, and its exact typed categories are the caller-declared bin labels in exact order with `len(labels) = len(cutpoints) + 1`.

Field names and order are exactly those of the bound output schema. No schema, field, label, cut point, scale, center, variance, or range is learned from any split. Targets, identities, and groups remain categorical and cannot use `EXACT_DECIMAL_BINS`.

The literal canonical decimal grammar uses exact whole-lexeme matching:

```regex
\A(?:0|-?(?:0\.[0-9]*[1-9]|[1-9][0-9]*(?:\.[0-9]*[1-9])?))\Z
```

It permits `-0.5`, `0`, `7`, and `12.25`; it rejects exponent notation, leading plus, negative zero, redundant leading zero, `.5`, `1.`, and trailing fractional zero such as `1.0`. Cut points use the same canonical strings. Semantics are exact coefficient/decimal-scale rationals, never Python/JSON/binary floats.

JSONL exact-decimal cells are JSON strings such as `"12.25"` in policy-declared `EXACT_DECIMAL_BINS` columns, with no `d:` prefix. CSV uses `d:<canonical-decimal>`. The policy prevents these values from being interpreted as categorical strings. Passthrough columns retain current exact scalar encoding. CSV `m:` and JSON `null` remain errors.

For strictly increasing cut points `c1...cn`, intervals are `(-∞, c1)`, `[c1, c2)`, ..., `[cn, +∞)`; equality at a cut point enters the upper bin. Infinities are conceptual boundaries only and are never input or encoded values. The output category for each interval is the corresponding exact typed category already present in the bound schema.

## Receipt and replay authority

The authority class is exactly `NATIVE_POLICY_REPLAY` or `EXTERNAL_BINDING_ONLY`. `NATIVE_POLICY_REPLAY` is derived only after fresh replay of the exact policy, bound output schema, and all three original raw payloads. A validator name, digest, structurally decoded wrapper, or equal v1 presentation root never confers native authority.

Each split receipt separately binds this ordered tuple:

1. domain-separated raw-byte digest;
2. ordered canonical exact-decimal semantic-observation digest;
3. exact bin-assignment digest;
4. projected output payload digest; and
5. row count.

The top receipt binds version, authority, output schema digest, policy digest, ordered train/validation/test receipts, exact v1 protocol digest, and boundary/nonclaim digest. Equal projected v1 roots may coexist with unequal raw/policy receipts. Raw digests establish supplied-byte identity only, never source origin, truth, authentication, or provenance.

The bounded structural decoder may create only an `EXTERNAL_BINDING_ONLY` value and grants no native authority. The source-backed replay API accepts the policy, bound schema, and exact train/validation/test bytes, reconstructs everything from scratch, and is the sole native verifier. Digest-only acceptance is forbidden. Callers cannot supply or upgrade authority.

Digest domains are exactly `veyra.observer-discovery.v3.continuous-policy-root.v1`, `veyra.observer-discovery.v3.continuous-raw-split.v1`, `veyra.observer-discovery.v3.continuous-semantic-observations.v1`, `veyra.observer-discovery.v3.continuous-bin-assignment.v1`, `veyra.observer-discovery.v3.continuous-split-receipt.v1`, `veyra.observer-discovery.v3.continuous-receipt.v1`, and `veyra.observer-discovery.v3.continuous-nonclaims.v1`.

## Bounds and validation order

Raw exact type and 16 MiB split/32 KiB physical-record caps, exact one-rule-per-field cardinality, and aggregate policy caps of 16384 nodes and 1 MiB nonpayload UTF-8 precede decoding. Parsing then incrementally charges logical records, decimal lexemes, semantic observations, assignments, nodes, and text. Decimal byte, digit, and scale caps are checked before integer construction; the bounded coefficient is then constructed and immediately required to have `bit_length <= 256` before any cross-multiplication, comparison, or assignment. Complete output schema/field/cell budgets are precharged before canonical construction.

Fixed caps are: at most 32 fields, at most 127 cut points/128 labels per exact-decimal field, at most 128 UTF-8 bytes per decimal lexeme, at most 256 coefficient bits, scale at most 18, and all existing 16 MiB split, 32 KiB record, 8192-row, 262144-cell, identity, text, categorical, and lineage limits. Combined source, policy, observations, assignments, receipt, and wrapper material is capped at 65536 nodes and 1 MiB nonpayload UTF-8/canonical JSON. Exceeding any cap rejects rather than clips or rounds. Logs contain only fixed reason codes, safe type names, and aggregate counts.

## Required evidence for a later implementation

- exact v1 byte/digest/export/error pins and root nonexport;
- boundary assignment at every cut point and exact CSV/JSONL semantic parity;
- mixed passthrough/exact-decimal order, typed category labels, negative values, and fractional exactness without float conversion;
- noncanonical decimal, unordered/duplicate/excessive cut points, label mismatch, overflow, missing-value, target/identity, splice, mutation, callback/TOCTOU, authority-confusion, decoder, replay, and resource pressure;
- package and Linux/macOS/Windows portable coverage;
- independent contract and implementation reviews.

## Non-claims and stops

This policy establishes only exact finite categorization relative to caller-declared rational cut points and labels. It does not establish that a phenomenon is continuous, measurement accuracy, units/dimensions, metric preservation, proximity, monotonic response, rounding/quantization adequacy, optimal or sufficient bins, calibration, normalization, distributional fit, population validity, target secrecy, statistical leakage freedom beyond existing ID disjointness, source truth/authentication/provenance, custody, chronology, causal/statistical validity, theorem, certificate, object formation, or claim promotion.

Stop and redesign if implementation requires changing old ingestion source/`__all__`, schema/version/boundary/digest bytes, errors, Phase-II behavior, or the old private parser; fitting any parameter from any split; binary float canonical semantics; missingness; numeric targets; omitted raw/semantic/policy authority; or treating detached/equal-root evidence as native replay.

## Publication scope

This issue and its RFC document are documentation-only. Any executable sibling is a later independently reviewed issue/PR. Missing values and missing×continuous composition remain rejected and belong only to separate independently reversible RFC work.
