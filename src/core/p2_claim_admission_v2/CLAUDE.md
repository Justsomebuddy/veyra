# P2 Claim Admission v2

## Scope

This non-root sibling publishes the additive registry/oracle and the separate
source-backed producer for the named P2 rule
`composition-licensed-presentation-v2`. It preserves P2-S v1 and
`claim_composition` v1 objects, digests, registries, literal oracle, premise,
exports, and root facade exactly. `LicensedCompositionPresentation` is a typed
licensed presentation only; it is not truth, theorem, ontology or promotion of
the unchanged v1 receipt.

## Published registry contract

- Version: `p2-r17-claim-admission-v2`.
- Registry: `p2-s-promotion-registry-v2`, exact counts `15/18/41/1/5` and
  digest `ba6020151518faf5eb2fa2eb22943af4c7d0abd88b393b1388f848e63dbc3eb4`.
- The v2 snapshot is exactly the immutable v1 snapshot plus one rule; the v1
  registry digest remains
  `375f1654807b462c3a9ebd9a112a75ee28fc96a4029cf767acae1fd591a60e9d`.
- Premise: `composition` / `claim-composition-presentation-v2`.
- Output only: `PRESENTED / ESTABLISHED / SUPPLIED_PRESENTATION`.
- Visible indices, in order: `contract`, `claims`, `scope`, `assumptions`,
  `doctrine`, `source-validators`, `composition`; no new index projection.
- Evidence order: `target-contract`, `claim-set`, `scope-set`,
  `assumption-set`, `doctrine-set`, `source-validator-family`,
  `source-family`, `composition-license`, `composition-assessment`,
  `nonpromotion`.
- The producer interprets `source-validator-family` as the ordered
  `(local receipt digest, validator root, authority class)` family, where the
  authority class distinguishes fresh native-governed replay from external
  binding-only replay even when validator roots and v1 receipts coincide.
- The extension oracle validates schema shape, the exact additive snapshot,
  semantic pins, cardinalities, literal digests, and the v1 prefix. It is
  meta-validation only and cannot by itself construct or promote a presentation.

## Producer contract

- `build_licensed_composition_presentation(...)` and its validators accept only
  the raw canonical sources, exact target contract, license, unchanged receipt
  and bounded judgment identifier; the caller cannot supply a descriptor,
  request, audit, conclusion, policy, status or provenance.
- Fresh replay retains the exact target, license, four-axis assessment, receipt,
  premise, descriptor, request, registry/oracle pair, named-rule
  `PromotionSchemaAudit` and separate fixed-five registry-v2
  `SchemaAuditReport` in the public DTO and strict codec.
- Each source retains an ordered `(local receipt digest, validator root,
  authority class)` binding. Authority is derived from the fresh replay path:
  `NATIVE_GOVERNED_REPLAY` only for a native governed result, otherwise
  `EXTERNAL_BINDING_ONLY`, regardless of validator-root spelling.
- The verifier and decoder rebuild the complete result from raw authority and
  require exact equality. The canonical decoder rejects duplicate/unknown/
  trailing/noncanonical JSON, hostile scalars/containers, stale roots and
  cross-object splices.
- Raw authority and candidate values are copied through a callback-free exact
  DTO/enum whitelist under the node/depth/text budgets before replay or
  equality. Every result retains that private snapshot, never caller-owned DTO
  identity, closing both callback and concurrent `object.__setattr__` seams.
- Sibling limits are 2..64 sources, 128 UTF-8 bytes per identifier, 1 MiB
  aggregate nonpayload text, 65,536 combined structural nodes, depth 128 and
  1 MiB canonical JSON, in addition to all composition-v1 limits.
- `protected_replay_logs()` uses a context-local first-position filter guarded
  by one `RLock` and exactly restores lower logger filters after success/error;
  unrelated threads are not redacted.

## Permanent boundary

The registry claims no source truth, validator trust, logical consistency or
coherence, assumption discharge or unconditionalization, independence or
corroboration, adaptive/family/statistical/population validity, universal or
existential upgrade, objectivity or observer independence, theorem,
certificate or formal proof, ontology, object/history/lifecycle, empirical or
physical instantiation, authentication/custody/chronology, or audit-as-truth.
The unchanged v1 receipt promotion bit remains false.

## Files

- `registry.py`: additive full snapshot, semantic pins, literal extension
  oracle, and v1-preservation checks.
- `replay.py`: authoritative composition replay, ordered authority bindings,
  exact premise/descriptor/request and named-rule schema audit.
- `schema_audit.py`: dedicated literal five-target registry-v2 audit and exact
  reconstructing validator; it does not reuse the v1-only audit builder.
- `public.py`: full public DTO producer and source-backed exact validator.
- `codec.py`: full-field canonical JSON encoder and rebuild-only decoder.
- `types.py`: immutable public DTO and exact authority enum/binding.
- `validation.py` / `resource_validation.py`: callback-free immutable DTO/enum
  capture plus exact identifier, structural and text resource gates before
  replay/equality.
- `log_boundary.py`: context-local replay-log redaction and exact restoration.
- `errors.py`: fixed package exception and bounded rejection helper.
- `__init__.py`: explicit non-root registry, producer, validator, audit and codec
  public surface.
