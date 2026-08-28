# Missing-Data Runtime Memory

## Contract

- Version: RFC 172 / `veyra.observer-discovery.v3.missing-policy.v1`.
- Additive non-root sibling; never edit or import the strict ingestion parser.
- `NATIVE_POLICY_REPLAY` comes only from complete fresh policy, schema, format
  and three-source replay. Structural decode is `EXTERNAL_BINDING_ONLY`.
- Raw split identity is exactly `SHA256(domain_utf8 || NUL || exact_bytes)`.
- Preserve exact bool/int/string scalar identity in every domain comparison and
  digest. Never infer, learn or omit a fallback, row, identity, group or target.
- Preflight exact type/cardinality/text/integer/node bounds across the complete
  policy graph before detachment or UTF-8 encoding; never log content/digests.
- Include the policy container and all five actual/generated top fields in that
  aggregate; constructors reserve fixed generated digest/root overhead before
  any capture.
- Serialize only a validated detached snapshot (external) or fresh replay
  result (native); never reuse the mutable caller graph after validation.
- Seed one shared wrapper ledger with retained policy/schema/receipt overhead;
  parsing, masks, projection, direct structural validation and codecs never
  reset the 65,536-node/1 MiB ceilings.
- Seed the exact retained receipt authority; external binding is one UTF-8 byte
  longer than native replay and must never inherit the native text charge;
  recharge the completed downgraded result before returning it.
- Count simultaneous text exactly: row ID ×3, other identities ×2, observed
  strings ×3, missing fallback strings ×2 and target ×2.
- Apply byte/character caps before codec transcoding and physical-record caps
  before whole-source UTF-8 decoding; recheck row/scalar bounds while copying.
- Oversized test payloads require explicit short ASCII Pytest IDs; never allow
  their representations into Windows `PYTEST_CURRENT_TEST`.
- Count exact built-in-string UTF-8 bytes without allocating an encoded copy
  before any policy detachment; shallow-cap every codec list before nested
  decoders and keep all shared canonical/digest exit logs value-free.
- Issue #55 regression is permanent: equal legacy `DiscoverySplit` rows cannot
  recover missing-policy authority.

## Layout

- `types.py` / `errors.py`: fixed DTO, enum and closed failure surfaces.
- `resources.py`: callback-free exact capture and precharge.
- `policy.py`: schema/rule expansion and digest validation.
- `parsing.py`: independent bounded CSV/JSONL grammar.
- `digest.py`: typed canonical commitments and exact raw hash.
- `runtime.py`: native replay, receipts and structural validation.
- `codec.py`: bounded canonical JSON and native/external decode separation.

## Verification

Run the three `test_observer_discovery_v3_missing_data*.py` files together with
the old ingestion, representation and Phase-II compatibility suites. Preserve
portable/package metadata and root/export/digest/error pins.
