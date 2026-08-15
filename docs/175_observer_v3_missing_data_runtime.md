# 175 — Observer-v3 Missing-Data Runtime

**Status:** implemented additive runtime; non-root and nonpromoting  
**Contract:** [RFC 172](172_observer_v3_missing_data_policy_rfc.md)  
**Package:** `src.core.observer_discovery_v3.missing_data`

## Public boundary

The package implements an explicit finite missing-marker encoding. A caller
supplies a canonical categorical base schema, one ordered rule per base field,
the complete projected schema, an exact `CSV` or `JSONL` wire format, and the
three original byte payloads. The result is a separate
`MissingnessPresentation`; it never returns an authority-erasing bare
`ThreeWayPresentation`.

`REQUIRED` rejects a missing marker. `EXPLICIT_MASK` is restricted to
categorical fields and retains the declared fallback followed immediately by
the exact integer presence bit `<field>__present_v1`: `0` for missing and `1`
for observed. An observed value equal to the fallback remains distinct from a
missing value. Binary fields, identities, groups and targets are always
required.

The helper `projected_schema_for_missing_policy()` exposes the uniquely required
projection for caller review. `canonical_missing_data_policy()` then verifies
the separately supplied projected schema and binds the exact base/projected
schema digests, ordered typed rules and projection-spec root. Construction
reserves the fixed five-field generated policy overhead before detachment;
retained-policy capture combines the actual five top strings with both schemas
and the rules under the same complete-policy ceiling.

## Replay and codec authority

`missingness_from_csv()`, `missingness_from_jsonl()` and
`replay_missingness_from_sources()` capture exact immutable inputs and replay
all three sources. They are the only constructors of
`NATIVE_POLICY_REPLAY`. Each split receipt binds:

1. `SHA256("veyra.observer-discovery.v3.missing-raw-split.v1" || NUL || raw)`;
2. ordered typed semantic input plus the row-major missing mask;
3. exact projected assignments;
4. the projected canonical payload digest; and
5. the row count.

The top receipt additionally binds the exact wire-format enum, authority class,
policy and schema roots, ordered split receipts, unchanged v1 protocol digest,
boundary and permanent nonclaims.

`missingness_presentation_from_json()` is deliberately structural and accepts
only `EXTERNAL_BINDING_ONLY`. `native_missingness_presentation_from_json()`
requires the policy, both schemas, wire format and all three raw byte payloads;
it reconstructs the native result and compares the complete decoded wrapper.
Likewise, the ordinary JSON encoder accepts only external structure;
`native_missingness_presentation_json()` requires the same complete fresh
source-backed validation before emitting a native-authority wrapper.
Digest equality, a validator name, a structurally decoded value, or an equal
legacy Phase-II projection never upgrades authority.

All authority and policy comparisons use an exact canonical, type-aware graph:
Python's `True == 1` and dataclass equality therefore cannot collapse bool and
integer identities or accept typed category reordering. Encoders first capture
and validate a detached bounded snapshot. The external encoder serializes that
snapshot, while the native encoder serializes the fresh replay result, so a
caller mutation after admission cannot change emitted bytes.

In particular, two all-observed policies with different fallbacks can project
to equal legacy `DiscoverySplit` rows. Their policy/schema/receipt identities
remain different, and the equal legacy value cannot recreate
`NATIVE_POLICY_REPLAY`.

## Bounds and compatibility

Exact byte type, 16 MiB split and 32 KiB physical/logical-record caps precede
decoding; a byte-only CR/LF scan enforces the physical-record cap before any
whole-split UTF-8 conversion. Exact schema/rule types, cardinalities, text
lengths, integer widths and whole-policy node ceilings are checked before
schema, field or category detachment and before UTF-8 encoding. The policy
preflight counts exact UTF-8 bytes directly from built-in string code points,
without allocating encoded copies or invoking callbacks, and later rechecks
the encoded byte totals during detachment. One shared
65,536-node/1 MiB ledger is seeded with the retained policy, both schemas,
expanded projected-schema references and fixed receipt/digest overhead, then
incrementally charges semantic masks, projected assignments and wrapper rows.
The receipt seed charges the exact retained authority value, including the
one-byte-longer `EXTERNAL_BINDING_ONLY` spelling rather than assuming native
authority. `external_binding()` recharges the completed downgraded wrapper
under that external authority before returning it.
Text accounting follows simultaneous retained materializations exactly:
`row_id` three times, the other identities twice, observed feature strings
three times, missing fallback strings twice and targets twice. No component
receives an independent fresh budget: source parsing, direct structural
validation and all codec encode/decode paths apply the same combined
policy-plus-row charge. Structural validation also checks top/rule/global-row
ceilings before nested traversal and rechecks exact row widths and scalar bounds
at the detached snapshot boundary.

The JSON decoder applies exact type and shallow byte/character ceilings before
bytes decoding or string encoding, then rechecks the encoded byte count before
preflight and parsing. Strict UTF-8, duplicate key, tagged scalar, row, field
and projected-cell checks fail closed. Rules, schema fields/categories/targets,
split rows and row values have shallow per-container caps before any nested
decoder comprehension; the three splits also have a 24,576-row global cap.
Lower schema failures are translated into the sibling
`MissingDataProtocolError`; missing-data, shared canonical-schema and shared
digest logs contain fixed event codes and aggregate counts only, never raw
content or digest values.

The v1 compatibility lane fixes the complete public `missing_data.__all__`,
public error shape, policy/projection/split/top receipt roots and one exact
9,085-byte canonical external JSON fixture. These pins are compatibility
evidence only; they do not widen the claim boundary.

The existing ingestion source, private parser, two-function `__all__`, root
exports, DTO bytes/digests/errors and Phase-II behavior are unchanged. The
runtime is included in portable tests and installed-wheel import smoke.

## Nonclaims

The wrapper establishes no real-world absence, fallback correctness,
imputation, MCAR/MAR/MNAR mechanism, source truth/authentication/provenance,
custody, chronology, likelihood, unbiasedness, identifiability, causal or
statistical validity, theorem, certificate, object formation, or claim
promotion. Continuous interpretation and missing×continuous composition remain
out of scope.
