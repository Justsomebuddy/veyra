# P2 Claim Admission v2

## Scope

This non-root sibling currently publishes only the additive, meta-only registry
and literal extension oracle for the named P2 rule
`composition-licensed-presentation-v2`. It preserves P2-S v1 and
`claim_composition` v1 objects, digests, registries, literal oracle, premise,
exports, and root facade exactly.

The authoritative presentation producer, verifier, strict decoder, public DTO,
replay boundary, and enriched premise are a separate pending publication wave.
They are not exported by this registry-only package revision.

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
- The later producer must interpret `source-validator-family` as the ordered
  `(local receipt digest, validator root, authority class)` family, where the
  authority class distinguishes fresh native-governed replay from external
  binding-only replay even when validator roots and v1 receipts coincide.
- The extension oracle validates schema shape, the exact additive snapshot,
  semantic pins, cardinalities, literal digests, and the v1 prefix. It is
  meta-validation only and cannot construct or promote a presentation.

## Permanent boundary

The registry claims no source truth, validator trust, logical consistency or
coherence, assumption discharge or unconditionalization, independence or
corroboration, adaptive/family/statistical/population validity, universal or
existential upgrade, objectivity or observer independence, theorem,
certificate or formal proof, ontology, object/history/lifecycle, empirical or
physical instantiation, authentication/custody/chronology, or audit-as-truth.
The unchanged v1 receipt promotion bit remains false.

## Current files

- `registry.py`: additive full snapshot, semantic pins, literal extension
  oracle, and v1-preservation checks.
- `errors.py`: fixed package exception and bounded rejection helper.
- `resource_validation.py`: dependency-light exact digest, 128-byte identifier,
  structural, and text resource validation shared with the pending producer
  wave.
- `__init__.py`: registry-only public surface; no producer-facing APIs.
