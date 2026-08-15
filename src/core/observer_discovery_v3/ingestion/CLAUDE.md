# Strict v3 Categorical Ingestion

## Contract

- `categorical_three_way_from_csv(...)` and
  `categorical_three_way_from_jsonl(...)` accept one explicit v3 schema and
  three separately named, exact `bytes` payloads.
- The facade returns the existing `ThreeWayPresentation`; canonical schema,
  presentation and three-way validators remain authoritative.
- CSV uses exact headers and `s:`/`i:`/`b:true|b:false` scalar tags. JSONL uses
  exact native string/integer/boolean scalars and rejects duplicate keys.
- Each split is capped at 16 MiB and every physical/logical record at 32 KiB.
  Strict UTF-8, no BOM/NUL, fixed rows/keys, and all existing schema bounds are
  fail-closed.
- Public exports live only in this subpackage. Do not add root/schema exports.

## Nonclaims

No schema/type/category inference, generated identity, imputation, automatic
split, row recovery, missing/ordinal/continuous interpretation, byte/path
provenance, custody, leakage proof beyond canonical ID disjointness,
statistical claim, theorem, certificate, promotion, or Phase-II behavior follows.

## Logging

Log only fixed reason/detail codes, safe type names, and aggregate sizes/counts.
Never log payloads, identities, feature names, or scalar values.

## Session Notes (2026-08-14)

- Added the first bounded byte-only categorical ingestion adapter as a separate,
  independently reversible package with hostile parsing/resource regressions.

## Future sibling boundary (RFC 172)

- Missing-data preprocessing remains absent from this package. RFC 172 freezes
  only a later non-root `missing_data` design with a separate wrapper and
  source-backed replay authority. Do not widen these parsers or exports.
- CSV `m:` and JSON `null` continue to reject. Continuous and combined policies
  are separate future contracts.

## Session Notes (2026-08-15)

- Published the docs-only masked-missingness RFC without changing runtime,
  package exports, categorical pins, errors, or Phase-II behavior.
