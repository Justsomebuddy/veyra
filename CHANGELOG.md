# Changelog

## [Unreleased] — Changed
- Enforced the pre-coupling cut on P3-OG maintenance-control receipts
  (issue #80): the public machine boundary now requires the exact freshly
  reconstructed operational initial state before minting a
  `PreCouplingMaintenanceControlReceipt`; coupled or transitioned states are
  rejected as `p3og-maintenance-control-not-pre-coupling`. Authoritative
  pressure/lifecycle replay evidence is unchanged.
- Rotated the released changelog sections (`[4.3.1]` and older) verbatim
  into `docs/reference/changelog-archive.md`, keeping this root file inside
  the repository line-hygiene budget; `[Unreleased]` and future releases
  continue here.
- Recorded the break-locus literature verdict (doc 187): the fixed-relation
  power characterization is classical (Duboc 1986, Prop. 1.7; projection-lemma
  attribution corrected from Cori–Perrin in docs 183/registry); only the
  lattice-parametric layer keeps candidate-novelty standing, checks pending.
- Proved tightness of the break-locus bound (doc 186, `THM-TR2-009`): an
  explicit star construction attains `|B(w)| = r` for every `r` distinct
  primes (machine-verified `r = 1..3`); all 8 pair power-type vectors are
  realized on the exhaustive `a²b²c²` shape; general type-matrix
  realizability stays `OPEN`. Certificate suite total 110.
- Resolved the Principality Conjecture via the Break-Locus Formula (doc 185,
  `THM-TR2-008`): Achievability proved constructively (the root of a power is
  its first block, `THM_TR2_006/007`), so `B(w)` is the minimal antichain of
  the prime floors — agreement 6285/6285; the single-prime slice is PROVED
  and the general conjecture REFUTED by witness `aaccabbbaccaaccbbb`. Suite
  total 109; native end-to-end formalization of the prose assembly stays OPEN.
- Added the TR-2/2 forcing structure (doc 184): projection of a power is a
  power plus the divisor laws (`THM_TR2_002–005`, 53rd Lean source) force the
  prime floors; the Forced-Locus Law was observed and pinned on all 6285
  scanned words; `THM-TR2-001` stayed `CONJECTURE` at this stage. Suite 108.
- Added the TR-2/1 break-locus lane (doc 183): `B(w)` via projection Δ-sets
  with the projection lemma credited and BFS-counterpressured on six full
  lattices; poles classified; `THM-TR2-001` (Principality, `CONJECTURE`)
  registered after seven exhaustive sweeps — 6285 words, zero non-principal,
  pinned post-observation. Suite total 107.
- Added the TR-1 observer-lattice instrumentation (doc 182): commutation
  doctrines as a refinement lattice; node identity as the whole trace-class
  echo with typed refusals and an independent closure validator; edge breaks
  carry verified Ω exhibits; fragility spectra (`aabbcc` breaks exactly on
  the `bc` edge, `abcabc = (abc)²`); the abstract transfer spine is
  `FORMALLY_PROVED` in the 52nd Lean source. Suite total 106.
- Added the DI-2 orbit-partition candidate lane (doc 181): congruences
  licensed from partition structure with every load-bearing step native —
  primality witnessed by structural division residuals (an exact divisor
  blocks with its row), the orbit dichotomy derived from the cut-free
  primitive-root period plus that witness rather than by rotation counting,
  and the congruence itself a reconstruction (`weave(length, full orbits)`
  breath-equals the nonconstant tally; `%` decides nothing). Composed with
  DI-1 over alphabet depth — delta-only step classification, independent
  validator recomputation, anchor-renaming uniformity — the N8 Fermat
  instances are subsumed as one licensed family statement per
  witnessed-prime length (length 3 to depth 4, length 5 to depth 3 in the
  certificate, counts cross-tied to the N8 witnesses). Adversarial controls:
  composite length blocked by the divisor witness; a tally bomb blocked at
  exactly its depth. Five shadow laws `THM_DI2_001`–`005` join the Lean
  inventory as its 51st source; certificate suite total 105. The rule is
  `INTERNAL_RESEARCH_CANDIDATE`: no completed carrier, no unconditional
  universal, no promotion.
- Added the DI-1 doctrinal-induction candidate lane (doc 180): Veyra's first
  native quantifier mechanism. From a base witness, a step schema that
  rewrites the previous derivation (never recomputes), and an adopted
  generator — AFIP's proof-side companion — it licenses ledger-relative
  all-depth proof families with digest-chained receipts; uniformity is the
  anchor-renaming echo of the derivation at two fresh anchors, and the
  certificate ships both adversarial controls (name-peeking step rejected as
  nonuniform; depth bomb blocked at its exact depth). Demo family: `b`
  divides `b·n` via local one-block extension of structural-division
  derivations, licensed to depth 12. Five general shadow laws
  `THM_DI1_001`–`005` join the Lean inventory as its 50th source with real
  `induction` proofs, `THM_DI1_001` deliberately pinning the classical
  shadow. The rule is `INTERNAL_RESEARCH_CANDIDATE`, not an adopted axiom:
  no completed carrier, no unconditional universal, no promotion; the
  P1-D2 countermodels remain binding.
- Added the N8 necklace-congruence lane (doc 179): rotation-orbit rows and
  witnesses in `src/core/necklace_congruence.py` where divisibility is read
  off exact orbit partitions collected through the cut-free `cycle_echo`
  object — prime-length dichotomy, Fermat partition count, and Gauss
  primitive-count divisibility with the Möbius sum as a declared school-shadow
  cross-check; composite length 4 is recorded as a blocked witness with the
  `abab` counterexample. Seven exact finite instance cards
  `THM_N8_001`–`007` join the Lean inventory as its 49th source
  (`VeyraNecklaceCongruence.lean`), and certificate `necklace_congruence_n8`
  joins the executable suite (total 103). Bounded rows only; no general
  theorem, no promotion.
- Completed the claim-discipline documentation: `CONTRIBUTING.md` now
  requires silence-status-map token conformance (bare `ABSENT` deprecated;
  silence-row changes need a gap-audit amendment), forbids `proved` as an
  executable status token, mandates an Amendment-log row for every gap-audit
  edit, and states the shadow-license boundary for host equality/integers/
  ordering in code; the silence-status map is registered in the documentation
  navigation; `docs/reference/proofs.md` states the same PΩ1/PΩ2 combined
  status as the other registry sources; boundary notes were added to docs 02
  (anchor-relative `0_V`; shadow-level phase-congruence wording with the
  native structural-division counterpart), 06 (externally chosen `T_cycle`
  representative versus the orbit-true native object), and 12 (display-only
  canonical cut).
- Reconciled the PΩ1/PΩ2 registry statuses into one truth: the
  per-declaration formal-evidence rows, the Lean inventory rows and scope
  boundary, and the publication-critical summary now all state
  `FORMALLY_PROVED + PUBLICLY_VALIDATED`, matching the present root aliases,
  certificates, and release-bundle entries. The four runtime-generated PΩ1
  UTF-8 bridge declarations are documented as generated, digest-pinned
  non-repository sources in `proofs/lean/README.md`, the formal-evidence
  registry, and `scripts/check_lean_sources.py`; the definitional (`rfl`)
  character of `THM_POMEGA2_007_universal_realization` is stated beside the
  inventory. No mathematical statement changed.
- Added an append-only amendment log with true edit provenance to
  `docs/102_foundational_gap_audit.md` (original 2026-07-15 authorship;
  post-dated 2026-08-14 released-lane edits recorded retroactively per
  P0-O3), plus non-claim rows 7–8 registering scoped negative-existence
  judgments and adoption-conditioned objecthood as doctrine-level additions.
- Added `docs/reference/silence-status-map.md` as the single normative
  correspondence for the typed-silence vocabularies of docs
  149/150/154/155/156/158, resolving the `ABSENT` homonym (evidence-absence
  versus checked exclusion) with pointer notes in each document; added the
  `Rez_D,o` witness-relation homonym disclaimer to doc 158, a host-carried
  computation boundary paragraph to the README and the shadow-layer
  docstrings, the PΩ1 completed-`Nat` import admission to doc 151, and an
  orthogonal-vocabulary note to `THEOREMS.md`.
- Renamed the executable witness status token `proved` to `witnessed` in the
  intrinsic-arithmetic and quantum-tensor lanes and their consumers
  (deduction chain, classical benchmarks, certificates, tests), so no runtime
  summary claims the registry's formal-proof rung. Routed
  `is_cyclic_primitive` through the rotation-invariant primitive root of the
  given presentation, removing the lexicographic canonical cut from the
  decision path; `cyclic_root` remains a documented display shadow.
- Added the non-root `P3OGFormationPressureBinding` consumer requested by issue
  78. Its producer and validator freshly replay the exact P3-OG source,
  formation source, `WITNESSED` first-closure evidence and complete pressure
  report, then bind the shared deterministic selection, selected seed,
  operational entry state and selected candidate result under a separate v1
  digest domain. The selected pressure status is retained even when `REFUTED`;
  lifecycle refutation and every foreign, spliced or drifted premise fail
  closed. The witness has zero promotions and establishes only an exact identity
  relation, not raw/operational representation invariance, a historical
  one-shot selection, full formation, observer role, doctrine admission, typed
  history, HAP, birth token, ablation, same-token efficacy, theorem, source
  truth, physical birth, consciousness or object adoption.
- Closed aggregate-as-local re-entry in exact claim composition with Policy L.
  `LocalClaimReceipt` now admits only canonical leaf contracts with exact
  `LOCAL` quantification and no component-contract identity; aggregate or
  partial aggregate profiles fail at the stable
  `aggregate-contract-local-reentry` boundary before source-root processing.
  Flat N-ary conjunction over local leaves remains permutation-invariant, while
  `(A ∧ B) ∧ C` and `A ∧ (B ∧ C)` cannot be manufactured by relabeling an
  aggregate as a leaf. No recursive flattening or digest ancestry is inferred;
  DTOs, codecs, digest domains, exports, Policy A evidence-occurrence semantics,
  existing pins and P2 production are unchanged. This establishes no source
  truth, agreement, independence, validator trust, authority or promotion.
- Replaced the three production fixed-name Git subprocess call sites in the
  package source copier and repository hygiene checker with one private trusted
  executable boundary. The helper admits only fixed absolute POSIX or Windows
  installation paths, validates the executable and every ancestor, scrubs
  PATH/Git/loader override variables case-insensitively, runs outside the
  repository with a closed stdin and byte capture, and rejects pre-spawn or
  post-attempt identity drift. Exact NUL inventory bytes, global-exclude
  behavior, and ignore status 0/1 semantics remain intact; status greater than
  1 now fails closed. Portable adversarial tests cover both platform policies,
  argv/environment/cwd/timeouts, execution failures, identity drift and both
  consumers. The helper is not a cryptographic binary attestation, atomic
  descriptor execution, Windows ACL verification, repository/index race proof,
  or all-subprocess hardening claim; the two direct Git meta-test findings are
  intentionally unchanged and unsuppressed.
- Fixed exact conjunctions with two distinct established receipts for the same
  semantic contract. Target `component_contract_digests` now records the sorted
  unique semantic contract set, while canonical sources, source/validator
  roots, license bindings, assessments, composition receipts and P2 authority
  bindings retain every distinct receipt occurrence. Producer and validator
  share one private count-logged derivation, so Policy A cannot drift between
  construction and replay. Existing distinct-contract v1/v2 bytes, digests,
  schemas, exports and pins are unchanged; repeated identical receipts remain
  invalid, and semantic deduplication establishes no agreement, independence,
  validator trust, authority upgrade, stronger wording or promotion.
- Replaced exactly four optimization-sensitive VAM result/diagnostic
  assertions. Intrinsic execution now rejects a non-exact rendered `dict`
  before metrics, and frame inspection rejects non-exact `bytes` before the
  decoder, using stable existing codec taxonomy and value-free logs. Impossible
  parser/Core results without diagnostics now close into conservative
  `internal.compiler_bug` / `core.internal.compiler_bug` rows while preserving
  the established no-overclaim boundaries and successful high-level lowering.
  Hostile callbacks and a four-path `python -O` probe are permanently admitted
  to portable CI. Valid VAMI bytes/profile/report digests, legacy VAM0/VAMD,
  Python/Rust parity, valid compilation, exports, pins, certificates, proof
  status and mathematical claims are unchanged. The three inherited Ruff-format
  findings and wider repository Ruff/Mypy/Bandit debt remain out of scope; this
  is not a full `make verify` claim.
- Replaced exactly seven optimization-sensitive core runtime assertions across
  C1 confluence, R13 source verification, provenance digest admission, formal
  process capture and translated C3 cells. Public C1 with both joins absent
  remains total `OPEN` with no cell, while a one-sided partial join is rejected
  earlier as `partial-join-plan`; private complete-cell construction and
  malformed translated joins use stable explicit errors. The R13 verifier remains
  nonthrowing under hostile helpers; provenance rejects non-strings before its
  digest predicate; missing `Popen.stdout` kills and reaps once; and capture
  logs retain only stage, argument count, cap, return code and byte count. The
  target five files are production-B101-free and strict-Mypy-clean while their
  five inherited Ruff-format findings and formal-process B404/B603 findings
  remain explicitly outside this bounded wave. Valid artifacts, digests,
  receipts, output bytes, exports, proof status and claim levels are unchanged.
  Portable hostile-helper coverage allocates an uninitialized exact R13 DTO
  without invoking its pinned Lean-backed producer, keeping the verifier
  regression toolchain-independent without weakening it. The portable process
  test uses a bounded process-group cleanup double, so Windows verifies one
  cleanup call and one reap without changing runtime behavior.
- Replaced the 12 optimization-sensitive certificate producer assertions in
  `certify_observer_genesis` and `certify_productivity` with immediate exact-
  type fail-closed guards. Unexpected subclasses or variants now emit only a
  fixed value-free error reason and raise a stable `RuntimeError` before any
  result field, representation, or callback can be observed, including under
  `python -O`. Valid certificate DTOs, bytes, counts, digests, exports and
  mathematical claim levels are unchanged; this is a runtime invariant fix,
  not new certificate evidence or a repository-wide assertion cleanup.
- Ruff-formatted exactly 21 maintained scripts as one bounded style-only wave:
  nine verifier/build/generator tools and 12 explorer CLIs. Parsed ASTs,
  explorer help stdout/stderr/exit behavior, and regenerated table/notebook
  artifact trees remain exact, including byte-bound manifests. The seven
  already-formatted scripts were left untouched; no script semantics, logging,
  proof status, or generated artifact changed. This does not clear the wider
  repository Ruff/Mypy/Bandit debt and is not a full `make verify` claim.
- Implemented RFC 172 as an additive, non-root
  `src.core.observer_discovery_v3.missing_data` runtime. Exact CSV/JSONL wire
  format, raw bytes, ordered typed semantic masks, projected assignments,
  output payloads, row counts, schemas, policy and permanent nonclaims are
  retained in a separate wrapper. Structural JSON decode is permanently
  `EXTERNAL_BINDING_ONLY`; `NATIVE_POLICY_REPLAY` requires complete fresh
  policy/schema/source replay, including the issue #55 equal-legacy-split
  regression. Existing strict ingestion exports, bytes, digests, errors and
  Phase-II behavior remain unchanged; no imputation, missingness mechanism,
  provenance, statistical validity, theorem, certificate or promotion is
  claimed. Adversarial review additionally hardened whole-policy shallow
  resource gates before copying/UTF-8 work, exact bool/int-aware policy and
  authority comparison, callback-free type admission, digest-free logs and
  detached codec snapshots; fixed v1 export/error/root/canonical-JSON pins
  protect those boundaries. Final adversarial closure adds pre-transcoding
  codec/source record caps, snapshot-boundary row/scalar rechecks, shallow
  top/rule/global-node traversal stops and one combined retained-policy/wrapper
  resource ledger rather than independent component budgets. The ledger counts
  every simultaneous identity, observed string, missing fallback and target
  materialization, closing the final aggregate-text undercharge. Second review
  also applies that ledger to direct structural/codec paths, bounds every codec
  list before nested decoding, performs exact callback-free nonallocating UTF-8
  byte preflight before policy capture, and removes digest values from shared
  canonical/digest exit logs. The shared seed charges the exact retained
  authority spelling, including the external binding's one additional byte.
  Complete-policy preflight also includes the policy container and all five
  actual/generated top fields before detachment, while downgrading recharges
  the completed external result before return. Oversized codec cases use short
  explicit Pytest IDs so Windows never copies megabyte-scale parameter values
  into `PYTEST_CURRENT_TEST`.
- Added an explicit repository-wide Mypy discovery scope for maintained Python
  roots and hardened source-distribution extraction with pre-extraction member
  and expanded-byte ceilings, explicit path/type checks, and the standard
  library `data` filter. Canonical portable identities also reject normalized,
  case/backslash and file/directory hierarchy aliases before any extraction.
  The measured quality baseline remains findings, not a new green gate: Ruff
  format reports 985 files, while the local undeclared Mypy 1.19.1 reports
  1612 errors. The Mypy count is not claimed as version-stable or as dev/CI
  evidence.
  No mass formatting, blanket type suppression, security disclosure, or full
  verification claim is included.
- Accepted RFC 173 as a documentation-only contract for a future non-root
  exact fixed-bin continuous preprocessor. The proposed wrapper binds the
  caller-supplied categorical output schema, ordered passthrough/bin policy,
  canonical decimal lexemes and cut points, exact assignments, split receipts
  and replay-derived `NATIVE_POLICY_REPLAY` authority; structural decode is
  `EXTERNAL_BINDING_ONLY`. Existing strict-v3 schema/ingestion DTOs, bytes,
  digests, two-function exports, errors and Phase-II behavior are unchanged;
  JSON floats, CSV decimal tags, `m:` and `null` still reject. No runtime,
  measurement accuracy, unit semantics, learned binning, continuity, metric,
  statistical validity, source truth, theorem, certificate or promotion is
  claimed; missing-data composition remains separately unimplemented.
- Accepted RFC 172 as a documentation-only contract for a future non-root
  explicit masked missing-data preprocessor. The proposed wrapper binds the
  exact base/projected schemas, ordered policy, raw/semantic-mask/projection
  split receipts and replay-derived `NATIVE_POLICY_REPLAY` authority; structural
  decode is `EXTERNAL_BINDING_ONLY`. Missing categorical cells retain an exact
  caller-declared fallback plus a following `(0,1)` presence bit, while binary
  fields, identities, targets and groups remain required. Existing strict-v3
  schema/ingestion DTOs, bytes, digests, two-function exports, errors and
  Phase-II behavior are unchanged; CSV `m:` and JSON `null` still reject. No
  runtime, imputation correctness, real-world missingness, MCAR/MAR/MNAR, source
  truth, statistical validity, theorem, certificate or promotion is claimed.
- Added the authoritative producer, verifier and strict canonical codec for the
  non-root `LicensedCompositionPresentation` P2 v2 sibling. Every result is
  reconstructed from the raw canonical source family, exact target contract,
  license and unchanged nonpromoting composition receipt. The ordered
  `source-validator-family` now binds each local receipt digest, validator root
  and replay-derived `NATIVE_GOVERNED_REPLAY` or `EXTERNAL_BINDING_ONLY`
  authority class, so detached evidence cannot inherit native authority merely
  by naming the same validator root. The full license, freshly derived
  four-axis assessment, premise, descriptor, request, named-rule
  `PromotionSchemaAudit`, separate fixed-five registry-v2 `SchemaAuditReport`,
  registry and extension-oracle bindings are retained in the public DTO and
  codec. Exact-type callback-free immutable capture closes caller-mutation and
  nested subclass/enum seams before deep replay or equality; 1 MiB text/JSON,
  65,536-node, 128-byte-identifier and depth ceilings, hostile JSON/splice/
  resource tests, and context-local replay-log redaction fail closed. P2-S and
  claim-composition v1 bytes remain exact; schema conformity
  and presentation status establish no truth, coherence, assumption discharge,
  independence, validator trust, ontology, theorem, lifecycle, physical
  instantiation, authentication, chronology, custody or audit-as-truth claim.
- Added the dependency-first, non-root P2 licensed-composition registry-v2
  meta-validator specified by document 171. It is the exact P2-S v1 snapshot
  plus only `composition-licensed-presentation-v2` and its premise projection,
  with fixed `15/18/41/1/5` counts, exact v1 digest/oracle anchors, an
  independently literal-pinned extension oracle and strict nested-type,
  cardinality, identifier, node and text gates before equality. Its only
  possible output row is `PRESENTED / ESTABLISHED / SUPPLIED_PRESENTATION`;
  all assumption and source-validator indices remain visible. That registry-only
  wave exported no premise producer, audit producer, presentation DTO or decoder,
  so schema conformity by itself still cannot create a public presentation or
  establish any permanent nonclaim. The producer contract separately binds native-governed
  versus external-binding replay authority so a validator-root name cannot
  stand in for current execution. P2-S v1 bytes, root exports and rejection
  behavior remain exact.
- Specified the additive, non-root P2 licensed-composition admission v2
  contract. Its only new rule is `composition-licensed-presentation-v2`, with
  the exact `claim-composition-presentation-v2` evidence/index boundary and the
  fixed `PRESENTED / ESTABLISHED / SUPPLIED_PRESENTATION` output. The complete
  v2 registry is the byte-exact v1 snapshot plus one rule and premise
  projection (`15/18/41/1/5`), checked against a separately written extension
  oracle. The producer must preflight bounds, freshly replay raw sources,
  target, license and receipt, and derive its premise, descriptor, request and
  schema-only audit; callers supply no audit or conclusion authority.
  Assumption and source-validator roots remain visible and undischarged. The
  contract inherits composition limits and adds 128-byte identifiers, 1 MiB
  nonpayload text, 65,536 combined nodes and 1 MiB canonical-JSON ceilings.
  P2-S and claim-composition v1 bytes remain unchanged, and no truth, validator
  trust, discharge, independence, universal/existential quantifier upgrade,
  theorem, ontology, lifecycle, physical instantiation, authentication,
  chronology, custody or audit-as-truth claim follows.
  This entry records the docs-only RFC wave; the registry/oracle meta-validator
  and source-backed `LicensedCompositionPresentation` producer remained
  separate dependency-ordered publication waves and are recorded by the two
  newer entries above.
- Added the separately versioned, non-root same-doctrine all-status P1-A
  realization-transport sibling specified by RFC 169. It resolves the current `Blocked` information
  obstruction, admits only freshly reconstructed `STRONG` judgments, specifies
  a four-vertex exact-payload square plus obstruction-path projection, and fixes
  replay, composition, resource, hostile-test and stop conditions. Fresh source
  and target replay rebuilds exact six-payload rows and full endpoint partitions;
  raw fine partitions only refine projected/coarse partitions through explicit
  class maps. Identity/composition rebuild direct receipts, and sibling caps are
  fixed at 256 rows, 262,144 bytes per payload, 8 MiB transported per endpoint,
  32 MiB across six streams, 65,536 combined DTO/decoded nodes and 1 MiB
  nonpayload UTF-8 text. A transient thread-local sibling replay boundary
  replaces the reachable repr/full-root-bearing lower debug records with fixed
  routing metadata before pre-existing target-logger filters run, then removes
  itself without reordering those filters, so authoritative replay cannot
  disclose recurrence, proposition, payload, path, or full-digest bodies
  without changing process-wide record factories. No vertical P1-A cost law is
  claimed.
  Existing P1-A and realization-transport v1 DTOs,
  digests, exports, runtime, status and theorem registries are unchanged;
  cross-doctrine transport remains NO-GO.
- Added a separate non-root strict-v3 categorical ingestion facade that converts
  three caller-declared CSV or JSONL byte payloads into the existing canonical
  `ThreeWayPresentation`. Every row supplies exact stable identity, feature and
  target columns; CSV values use explicit string/integer/boolean tags and JSONL
  preserves native scalar types. Strict UTF-8, byte/record/row/cell and existing
  schema bounds fail closed before canonical construction. The adapter performs
  no schema/type/category inference, missing-value imputation, ID generation,
  automatic split, row recovery, ordinal/continuous interpretation, raw-file
  provenance, custody, statistical claim, theorem, certificate or promotion;
  existing schema/DTO/digest/root exports and Phase-II behavior are unchanged.
- Added a separate, non-root-exported P3-OG raw-cycle first-return pressure lane
  without changing the existing machine-pressure source/report bytes or facade.
  It starts an authority-free linear state at `UNFORMED`, consumes only the
  exact committed seed cycle, records bounded native before/after receipts,
  and stops at the least return after a genuine departure. The lifecycle source
  is fixed by the existing deterministic selected-seed receipt rather than by
  caller choice, and fresh replay validates the full result. A passing endpoint
  binds only to the existing operational `ALIVE` pressure-entry digest. This is
  not a typed history, primitive genealogy, full first-closure judgment, role,
  birth/token, admission, N0/HAP bridge, theorem, certificate, physical claim,
  or promotion. A fixed `(0,1,0)` versus `(0,1,2)` regression now makes the
  raw-representation boundary explicit: the low-level machine has equal
  response/state semantics modulo identity, while lifecycle first-return
  statuses differ. The pressure-entry digest is therefore documented only as
  an identity/replay link, never an operational-representation-invariance claim.
- Made the proof-core canonical JSON boundary strict: Python tuples are now
  rejected at every nesting depth instead of being silently serialized as JSON
  arrays, and all reviewed Core callers explicitly materialize intended arrays
  as lists. Added stable-byte/digest, nested-hostile and whole-`src/core`
  direct-call syntax inventory regressions. The content-bound R9→R13
  manifests, generated R10
  export, source/evidence/theorem artifacts, snapshots, report bindings and R13
  trusted contract were renewed by fresh staged replay; theorem statements,
  proof rules, Lean declarations/object manifests, promotion count and taxonomy
  are unchanged. The independent research-Lean base inventory was then renewed
  for only the changed `VeyraProofElaboration.lean` source row and its derived
  base/proof roots; the research-source root, candidate declarations, claim
  ledger, axiom closures, and toolchain pin are unchanged.
- Integrated eight Lean research files as a separate
  `INTERNAL_RESEARCH_CANDIDATE`: a canonical manifest binds 48 stable
  dependencies, eight candidate sources, 65 declarations/axiom closures, and
  33 literal headline claim boundaries, domain-separated evidence roots, and
  the exact Lean toolchain. Fresh temporary-tree verification, hostile checker
  tests, an explicit `lean-toolchain`, hash-pinned hosted Lean bootstrap, and
  sdist-only packaging replace persistent artifacts; stable theorem statuses and default
  `make verify` are unchanged.
- Hardened P3-OG matched maintenance-control pressure before suffix execution:
  both calibration inputs now require expected active/disabled flags, equal
  coupling responses, equal schema-derived semantic state excluding only the
  control flag and state digest, and exact input/link/digest-bound receipts.
  Accepted precomputed couplings feed the suffix traces without a second
  coupling call; any mismatch refutes with `matched-control-coupling-drift`
  before downstream discrimination. DTO/report bytes, exports, candidate
  status, nonclaims, theorem/notation ledgers, and promotion count are unchanged.
- Added an isolated P3-OG all-candidate machine-pressure research slice with a
  nonce-free canonical selector, bounded retained-residue transitions, native
  maintenance-credit decay, a synthetic pre-coupling maintenance control, and
  fresh exact replay. Exact source/text/integer budgets and terminal removed-
  state guards fail closed. The explicit facade is not re-exported from
  `src.core`; historical blind/one-shot selection, formation/first closure,
  typed post-formation ablation, arithmetic provenance, observer role, N0/HAP
  lift, formal theorem, certificate, object/infinity claim, and promotion remain
  absent or `OPEN`.
- Corrected observer-synthesis v5 represented-task and pruning evidence: the
  misrepresentation-recovery calibration now binds a genuine nonidentity
  represented-state permutation, every same-cost alternative inspected after
  the first winner is counted as evaluated, and only the strictly higher-cost
  suffix is reported as pruned. The independent verifier reconstructs that
  frontier from the task and catalog; affected v5 family/run pins were renewed
  while v1–v4 byte contracts remain unchanged.
- Hardened the observer-worker v5 conditional cgroup harness so an existing
  nondelegated system mount and controller/subtree capability read failures
  return its documented explicit `UNAVAILABLE` report. Invalid limits,
  nonexistent/out-of-mount roots, readback mismatches, and harness faults remain
  fail-closed errors; v1–v4 contracts are unchanged.
- Added a restricted same-doctrine realization-context transport research
  contract: total finite state reindexings preserve exact canonical recurrence
  inputs, both endpoint P1→R16 witnesses are authoritatively replayed, and
  target closure partitions act contravariantly by normalized inverse image.
  Receipts freshly reconstruct full Ready/Blocked evaluation commutation,
  bottom/join preservation, and nonincreasing (optionally exact) cost rows;
  identity/composition helpers do not splice trusted receipt data. Added
  adversarial/property coverage and axiom-free abstract Lean laws. This is no
  cross-doctrine or P1-A transport, category, functor, natural transformation,
  canonical quotient section, exact-cost theorem, Python formal verification,
  theorem promotion, authentication, or ontology claim.
- Added observer synthesis v5 while preserving v1–v4 identities: a separately
  rooted 2,048-row affine parity/reflection grammar; deterministic generated
  hidden-structure, symmetry, misrepresentation, negative-control and synthetic
  held-out calibration; proof-carrying branch-and-bound with canonical lower-
  bound/prune ledgers checked against an independent exhaustive path; and exact
  task/request/result codecs exposing winner roots, catalog-cost observer gap
  and alternatives. Added fail-closed Linux x86-64 closed-tmpfs-root custody
  with parent/child namespace, seccomp and delegated-cgroup readback plus a
  conditional cleanup harness. Added bounded threshold-Ed25519 VOR5 replay with
  external rotation epochs, signed manifests and state-free proof rebuilding,
  plus four axiom-free abstract Lean pruning/transport/exhaustion results.
  These are synthetic finite catalog/task/cost/host-relative results—not
  empirical or causal discovery, statistical generalization, universal
  completeness, workload-limit proof, trusted identity/time/source,
  attestation, Rust verification, theoremhood, or promotion.
- Added observer synthesis v4 without rebinding v1/v2/v3 artifacts: pinned v3
  golden/mutation/metamorphic contracts; a deterministic finite representation
  survey; joint representation/transport/observer/explanation synthesis checked
  semantically against a separate exhaustive reference path over the same
  catalog/primitive semantics; and public positive, negative,
  representation-trap, information-destroying-family, cutoff, and exhaustion
  benchmarks. Added truthful
  Linux worker `baseline`/`isolated`/`strict` profiles with namespace/seccomp
  readback and delegated cgroup-v2 limit, membership, empty-leaf, and cleanup
  custody. The private mount namespace does not hide the host filesystem. Added
  a bounded two-layer Ed25519 VOR4 package and state-free verifier that bind
  manifests, registry roots, optional worker-policy evidence, and exact pipeline
  replay, plus narrow axiom-free Lean results for abstract replay, explicit
  bijections, and finite-list exhaustion. These are finite catalog-relative
  engineering results, not causal or hidden-variable discovery, universal
  representation laws, a sealed sandbox, executable attestation, signer trust,
  source truth, Rust verification, or theorem promotion.
- Accept the platform-native `.exe` suffix when authenticating the fixed
  observer-pipeline worker on Windows, while retaining exact basename matching
  on every platform.
- Added observer synthesis v3 without renewing v1/v2 identities: an append-only
  grammar registry with pinned prefix roots; a typed finite transport DSL whose
  bijection/injection/loss class is derived independently of task-preservation
  evidence; stable-cost-bucket and memoized joint search checked
  against the independent exhaustive engine; an integer observer-gap lab with
  positive/negative controls and explicit transform/observer/explanation/loss
  costs; and an atomic normalize/transport/observer/explanation/aggregate
  pipeline that searches only the declared typed transports under a unified
  transport-plus-observer cost. Transport composition is recursively bounded
  and precharged; selected loss penalties are derived rather than caller-
  asserted. Added payload-typed VOR2 HMAC-SHA256/Ed25519 bundles with domain
  separation, streaming decode, deny-by-default external trust policy, and
  authentication before exact semantic replay while preserving VORP v1.
  Worker v2 reports every physical control separately; a fixed worker-v3 child
  executes the canonical pipeline under verified baseline Linux controls and a
  parent promotes wall/output/process-group custody only after fresh exact
  replay. Strict cgroup/seccomp/namespace custody remains blocked rather than
  emulated. Added an axiom-free abstract Lean bridge for
  canonical acceptance, explicit bijective task transport, and consequences of
  an admitted optimized/reference equality witness. These are finite
  profile-relative engineering results, not general representation laws,
  hidden-variable discovery, speedup, sandbox/remote attestation, signer trust,
  Rust verification, or theorem promotion.
- Pinned the transitive `base64ct` closure inside Rust 1.83, added a parent-side
  close-on-exec FD boundary before the worker-v3 child audit, and made worker-v2
  probes deterministic and truthful on non-Linux platforms after hosted
  portable CI exposed the boundary errors.
- Added observer synthesis v2 without rebinding any legacy receipt: an
  immutable named 1,565-row profile plus a separately rooted 230-row `Parity`
  extension; exhaustive survey of 120 declared shift/permutation encodings;
  deterministic joint transform/observer synthesis with distinct
  `INCOMPLETE`/`EXHAUSTED`; a fixed Linux child worker with verified
  CPU/address-space/core limits, wall timeout and process-group kill/reap; and
  bounded portable external-key HMAC replay that freshly reproduces exact
  evidence bytes. Added an axiom-free abstract Lean research slice for replay
  determinism, bijective task relabeling, and finite-list exhaustion. These are
  profile-relative calibration and shared-key integrity results, not grammar
  completeness, general representation laws, public signatures, sandboxing,
  Rust verification, theorem promotion, or hidden-variable discovery.
  Default worker ceilings allow 10 CPU/30 wall seconds so the same fixed search
  remains bounded without becoming spuriously timing-dependent on contended CI.
- Added an atomic Rust-native observer benchmark-family receipt over the
  unchanged pinned 1,565-row grammar. The identity four-state mixture is found
  by `Crest(Input)` with class saving 2; a two-bit XOR target has exact balanced
  single-bit contingency tables and exhausts the catalog; shifting the mixture
  breaks direct witness reuse but re-synthesis finds `Crest(Tail(Input))` at
  cost `+1`; and a fixed permutation exhausts the catalog. Separate transport
  rows bind the unchanged source-witness truth tables before target
  re-synthesis, and exact replay rejects semantic, marginal, terminal, winner,
  transport, ordering, and cutoff mutations. These are finite grammar-relative
  calibration outcomes, not BM-F009, hidden-variable discovery, general
  impossibility, representation invariance, theoremhood, or promotion.
- Integrated the previously reviewed dependency-free Rust-native shadow of the
  closed R11/R14.1/R14.3b observer-synthesis core under
  `vam_native::observer_synthesis`: typed `Input`/`Tail`/`Crest`/ordered-`Pair`
  observers, byte-exact canonical identities, the pinned 1,565-row grammar,
  finite recurrence semantics, monotone counter budgets, and deterministic
  train-only CEGIS. Python remains the oracle; the weaker in-process native
  trace is domain-separated, diagnostics are opt-in/static/payload-free, and no
  backend dispatch, performance, general synthesis, theorem, or certificate
  claim follows.
- Extended that Rust surface with one deterministic zero-vs-positive quotient
  benchmark and a canonical replayable receipt. The surface `Input` observer
  has three classes/one of two obligations/zero saving; the pinned ordinal-1
  `Crest(Input)` winner has two classes/two obligations/one saving. Receipt
  replay reconstructs the exact catalog, cases, limits, CEGIS run, witness, and
  integer gap, rejects tampering/cutoffs, and records absent wall-clock/process-
  AS enforcement. This is not BM-F009, hidden-variable discovery, holdout,
  signing, theoremhood, performance, or backend promotion.
- Added one canonical Python/Rust identity vector for the shared closed grammar
  and winner. Both implementations independently reproduce the exact catalog
  count/bytes/digest and `Crest(Input)` ordinal/cost/depth/bytes/digest; this is
  differential identity evidence, not whole-receipt or execution equivalence.
- Added a narrow nonpromoting composition-to-P2 seam: a freshly replayed
  `CompositionReceipt` can become an index-free `PremiseArtifact` whose exact
  target, license, assessment, source family, and permanent nonpromotion are
  bound as evidence. No P2 v1 rule consumes the new artifact kind, so the P2
  registry/oracle/certificate remain unchanged with zero promotions. Added a
  canonical detached-local-receipt replay package and bounded independent CLI;
  replay proves neither external validator trust nor source truth, and omitted
  authentication is reported as `NOT_CHECKED`.
- Added an internal Lean model, with no project-declared axioms, of exact finite
  conjunction. It proves
  field-union preservation, permutation invariance, append decomposition, and
  explicit non-upgrade flags for P2 promotion, independence, assumption
  discharge, and universalization. The model is not yet a byte-level Python
  receipt bridge and is intentionally not a public `THM_*`/certificate entry.
- Implemented issue #3 as a separate bounded observer-provenance diagnostic.
  An external scoped-agreement binding remains orthogonal to a typed finite DAG:
  shared decisive source/control ancestry refutes policy-relative independence,
  allowed shared basis does not, and incomplete ancestry remains OPEN. The clone
  consensus fixture therefore preserves `multi_observer_agreement=ESTABLISHED`
  while returning `independent_corroboration=NOT_ESTABLISHED`. This is not
  statistical/causal independence, complete provenance disclosure,
  observer-free truth, objectivity, theoremhood, or P2 promotion.
- Added the issue-18 claim-composition boundary immediately upstream of P2-S.
  Assumption-bearing receipts retain their exact external validator identity;
  governed Phase-III results derive structural evaluation-completion contracts
  without mislabeling capability/attempt roots as assumptions. Bounded
  `EXACT_CONJUNCTION` preserves per-component contracts and exact scope,
  assumptions, observer/doctrine, execution/research lineage, provenance, and
  semantic axes. The `R_A: A -> P(x)` / `R_B: B -> P(y)` control accepts only
  the target retaining `A` and `B`; unconditional, universal, independent,
  adaptive, epistemic/objectivity, and stronger-wording aggregates remain
  `NOT_ESTABLISHED`. A strict source-backed codec exports the complete target,
  license, assessment, and nonpromoting receipt; companion HMAC-SHA256 and
  optional Ed25519 envelopes bind all critical roots without turning
  authentication into truth. Portable CI and installed-wheel smoke now cover
  the package. This adds no P2 rule, discharge theorem, certificate,
  independence, significance, or population claim.
- Raised the security-reviewed Python tool and signing floors to pip 26.1.2,
  setuptools 83.0.0, pytest 9.0.3, and cryptography 50.0.0 across exact
  manifests, package metadata, the conda profile, documentation, and contract
  tests. Hosted Ubuntu now executes the exact optional Ed25519 signing lane.
  This closes the known advisories on the superseded pins; exact lists remain
  reviewed inputs rather than hash/platform-byte locks.
- Updated the exact Python 3.11 tested-environment pin from JupyterLab 4.5.1
  to the compatible 4.5.10 security-patch release; the declared optional
  runtime range remains `jupyterlab>=4,<5`.
- Updated the portable GitHub Actions trust roots from deprecated Node.js 20
  revisions to immutable official Node.js 24 commits: `actions/checkout`
  v7.0.1 and `actions/setup-python` v7.0.0. Least-privilege `contents: read`,
  disabled checkout credential persistence, fixed runner labels, and bounded
  job timeouts remain unchanged.
- Implemented the representational half of `OD-A12` from issue #14: a bounded
  canonical research-line DAG now binds experiment/design/data/outcome roots,
  parents, visible prior outcomes, and adaptation reasons while keeping local
  validity, family recording relative to the declaration, and adaptive
  validity orthogonal. Generic named policies remain unverified and cannot
  license significance or population wording. An exact independent-null
  adaptive-retry witness plus Python/real-Sage binomial cross-check reproduces
  `1-(1-alpha)^m` (about `0.6415` for twenty `alpha=0.05` attempts). This adds
  no theorem/certificate, trusted chronology, disclosure-completeness,
  independence, family-error, anytime-valid, causal, or generalization claim.
- Implemented issue #5 as a sibling Comparative Bridge and Structural
  Separation ledger without changing F5's fixed eight rows. The first exact
  bridge reduces the declared finite G4 existence/effectivity problem to
  matching-family amalgamation for `V ↦ EqRel(V)`; a bounded conflict graph on
  `Q=U/E*` classifies every exact gluing and makes uniqueness equivalent to
  completeness, conditional on existence. Disjoint singletons strictly
  separate existence from uniqueness. An independent Python oracle plus real
  Sage 10.7 `SetPartitions` reproduce all `1275` assignments through `n≤3`
  (`491` gluable, `441` unique), and two digest-bound nonpromoted Lean helpers
  cover pair-coverage uniqueness and the nonunique witness. This adds one
  certificate row (102 total), not a general sheaf/descent/topology theorem,
  novelty, nonexpressibility, or superiority claim.
- Hardened supplied P1→R16 witness validation: evaluation states now receive an
  aggregate 32,768-node/2 MiB precharge before per-row capture, excessive JSON
  nesting fails through the closed realization error boundary, and the portable
  test lane now exercises the full observer-realization behavior on every
  hosted operating system.
- Added the explicit relative P1→R16 realization requested in issue #13. A
  fingerprint-bound external context now declares the finite state/recurrence
  scope, ordered observer costs, structured R11 totalization, and finite join
  completion policy. The checker replays every canonical P1 program on every
  bound input, retains full `Ready`/`Blocked` payloads, derives bottom and joins
  with source-separated provenance, validates the unchanged R16 doctrine, and
  rejects even digest-consistent supplied rows that do not match fresh replay.
  Context-order class representatives are local witnesses only: no canonical
  P1→R16 map, echo embedding, functoriality, quotient transport, ready-only
  image theorem, authentication, Lean proof, novelty, or promotion is claimed.
  Aggregate closure costs and non-UTF-8 carrier text also fail closed before
  canonical encoding; the total source cost is context-bounded, expanded state
  traversal and total replay payload are precharged, and equal-cost generator
  ties follow declared source order. The witness is a deterministic typed value,
  not a standalone portable wire artifact.
- Closed the R16 target-admission ambiguity reported in issue #10. The public
  `observer_descent`, residual-chain, and per-row reduction boundaries now
  require an explicit keyword-only target doctrine, validate its full
  finite-doctrine contract and exact carrier, and admit the target only by
  canonical `(name, responses, cost)` value. Detached exact DTO copies remain valid;
  name-only, extensional-only, reordered, response-drifted, cost-drifted, and
  external targets fail closed. `pullback_observer` remains the explicitly
  ambient low-level operation and is not membership evidence. This is an
  intentional public signature correction; callers must pass
  `target_doctrine=...`, and any stable package release containing it requires
  a major-version migration.
- Completed one bounded, semantics-preserving package-layout wave by moving the
  finite-builder validation and replay implementations beside their existing
  canonical codec, digest, and types modules. The flat runtime/validation paths
  remain physical identity-preserving aliases with legacy pickle, logger,
  reload, root-export, and monkeypatch compatibility. Added static gates for
  Git-custodied Core artifact paths, resolvable relative imports, valid
  path-shaped inline Markdown links, and repository-shaped source citations; a
  concise subject navigation page now complements the unchanged chronological
  documentation paths. Unexpected
  certificate exceptions are regression-tested to propagate and make the CLI
  fail. This deliberately does not add catch-all “unavailable” conversion,
  blanket platform skips, a global import hook, trust-root renewal, weakened
  verification, or bulk source/test/document renames.
- Added a separate strict Phase-III observer-discovery experiment under
  `src.core.observer_discovery_v3` without changing or exporting it from the
  Phase-I/II root APIs: bounded canonical three-way schemas; exact invertible
  representation transports; finite frozen-observer commuting-square
  verification/refutation; a closed `column`/`xor`/`pair` DSL; resource-bounded
  logical-subprocess evaluation; a same-user cooperating-process local ledger;
  per-store capability/test-root uniqueness; claim-first evaluation with a
  precommitted worker-row root; and canonical roots-only `AUDIT_RECEIPT`
  packages authenticated by shared-key HMAC or, with the `signing` extra,
  optional Ed25519. The logical child is not a syscall sandbox, local state has
  no anti-rollback/trusted-time/operator-non-bypass guarantee, key identity and
  trust remain external, and audit receipts are not independently executable
  replay. Finite commuting rows establish neither robustness nor causality,
  explanation, or theoremhood. No certificate, theorem promotion, root export,
  or release-version bump follows.
- Added Phase-II observer-discovery semantics and replication: a deterministic
  claim envelope keeps execution, interpretation, and ontology orthogonal and
  fixes causality, semantic explanation, theoremhood, object formation, P0
  admission, and historical novelty to nonclaims. A separate fixed-winner
  confirmation protocol fully replays the exact upstream `FOUND` report,
  switches to that trusted local replay before test evaluation, rechecks bound
  callable semantics after evaluator callbacks, links the ordered baseline
  family during parent-pinned validation,
  rejects three-way lineage overlap, evaluates only the frozen observer and
  exact named baselines on a third declared categorical test set, requires a
  positive descriptive gap, applies group-aware fixed-family
  global-independence max-stat calibration, and emits result receipts that are
  independently checkable for local self-consistency. The p-value does not
  establish inferential gap superiority.
  This remains in-process, unauthenticated, and not one-shot enforced; it is
  replication evidence, not certification of truth.
- Added an experimental, dependency-free categorical observer-discovery layer
  over the finite R5 grammar: train-only complexity-penalized selection, a
  frozen holdout winner, whole-catalog max-statistic group permutations,
  train-only bootstrap stability, named-baseline gaps, fail-closed terminal
  states, bounded detached pre-validation snapshots, protocol-bound complete
  configuration receipts, recomputed report invariants, occurrence-bounded
  acyclic AST validation, protocol-bound structural grammar/cost replay, a
  train-objective identity with optional trusted-root pinning, and
  domain-separated evidence identities. This is a bounded
  association protocol, not causality, general hidden-variable recovery,
  classical/ML superiority, or a new theorem.
- Replaced the obsolete 300/1000-line split with one reviewable modularity policy: active source and documentation target at most 1000 physical lines, currently necessary exceptions require a path-bound readability justification, stale exceptions fail, and 2000 lines is an absolute maximum. Updated the portable hygiene gate, specialized regression tests, contributor guidance, and active design documentation without rewriting historical release evidence.
- Continued the core package-layout migration by moving finite-builder codec, digest, and type implementations under `src.core.construction.finite_builder`; the former flat paths remain lazy identity-preserving aliases with legacy pickle/logging/class provenance, while internal consumers use the canonical paths. DTO fields, enum values, root exports, codec bytes, digest domains, resource limits, and semantics are unchanged. Portable package metadata now accepts CPython `>=3.11,<3.12`, while typed capability gates preserve exact CPython 3.11.14 and Linux x86_64 requirements for content-bound certificate renewal and hardening. Repository artifact identities remain relative and resolve against a trusted operator-selected or discovered package/source root only at I/O; lexical and existing symlink escapes are rejected. Removed temporary POSIX module shims in favor of lazy real-host adapters; actual external test modules have named capability markers, unavailable complete-lane capabilities fail explicitly, and the reviewed portable allowlist deselects those markers rather than converting failures into skips. Separated dependency extras and exact hosted-tool pins, completed checkout-wheel plus sdist-rebuilt-wheel smoke coverage, pinned reproduced Rust/Lean toolchains, and added immutable-action, fixed-runner-label, bounded Linux/macOS/Windows CI lanes. Reconciled stale planning docs without promoting open research; exact GitHub Actions run `31362980690` now records portable Python, package, and native Rust success for commit `3c44de5045b40ae998b2464483525fc6c6e9cc13` on Linux, macOS, and Windows plus Rust 1.83.0 MSRV on Linux, while the complete Sage/Lean/certificate/hardening lane remains Linux-only.
- Deliberately renewed the content-bound R9→R13 manifest, theorem artifact, and R8 contract chain after the path and lazy-POSIX refactor. The reviewed source-byte changes are limited to physical root resolution, lazy host capability access, and generated binding continuity; theorem statements and trust-boundary semantics are unchanged. Guarded pinned-Lean replay reached `checked` through R13 with all 11 stages returning zero; R13 now binds snapshot `a089eeb5…3867`, report `1d2f69c6…ea68`, theorem artifact `06531f09…8e41`, and contract `a2c8e00f…0a4f` to the renewed R11 `d9831806…c53a` and R12 `54454915…48dc` parents.

## Released history

Released entries `[4.3.1]` and older are archived verbatim in
[docs/reference/changelog-archive.md](docs/reference/changelog-archive.md).
