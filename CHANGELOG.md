# Changelog

## [Unreleased] — Changed
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
## [4.3.1] 2026-08-09 — Publication-ready public root
- Consolidated a portable clean-history tree for the dedicated `Justsomebuddy/veyra` repository with public controls, reproducible gates, corrected cache-ignore probes, and an explicit cautious commit/push/documentation policy; removed private paths, credentials, local automation metadata, generated artifacts, and retired cryptographic research; reconciled theorem/Lean evidence, notation, links, and status language without promotion; restored Omega-A only as an isolated experiment outside the stable package/default verification, with unfinished checker, soundness, and authority boundaries explicit.
## [4.3.0] 2026-08-08 — P3-N3/N4 local realization and scoped equality
- Released exact N1→PΩ2 realization and all-projection scoped carrier equality with 25 attacks, 48 aliases, bundle `13`, registry target `100`, focused `22/22`, direct L1, root `1836/1836`, zero promotions, and isolated strict GO.
- Serialized registry-100 and renewed isolated Lean axiom checks remain background evidence; no current full verify, generic completion, topology, absolute identity, N5 adoption, physical/metaphysical or foundation-independent infinity follows. The strict-reviewed ΩG philosophy separates relative, generic, and absolute completion (`GO 0/0/0/0`); the public closure framework keeps representation, interpretation, soundness, adoption, and typed infinity distinct without promotion. Unreleased ΩG1 remains only a two-instance non-generalization audit. Versions root/docs `4.2→4.3`, package/src `2.98→2.99`, core `2.37→2.38`, tests `3.46→3.47`.
## [4.2.0] 2026-08-07 — P3-N2 prime-power reduction observer network
- Released arithmetic-derived finite P3-T reductions, strict integer-family separators, and symbolic thin `Natᵒᵖ` identity/composition/comparison/observer-square/path coherence; focused `39/39`, public `1/1`, direct L1, isolated Lean SHA `77f5a989…10cf`, ledger `37/54`, oracle `2c4cad69…1e9`, attacks `23/23`, two refutations, one typed OPEN boundary, 56 aliases, root `1788/1788`, registry `99`, and zero promotions pass. Documentation separated six typed contracts and corrected stale C2/C3/C4/PΩ/N2 wording without promotion. No current full verify, N0/N3/N4/N5 instance, C2.3, inverse/generic network, or absolute objectivity follows. Versions root/docs `4.1→4.2`, package/src `2.97→2.98`, core `2.36→2.37`, tests `3.45→3.46`.
## [4.1.0] 2026-08-07 — P3-C2.2 exact finite generated transport coherence
- Released exact finite total setoid transport with `2` local commuting squares, `72` generated global fillers, semantic work `13307`, isolated Lean `3/3` at `4804c563…e395`, and a `23`-row/`41`-edge ledger at oracle `b634ea8c…e6cb`; cofinal boundary reconciliation is derived from C2.2. Focused `35/35`, public `1/1`, direct L1, 17 attacks, 57 collision-safe aliases, root `1732/1732`, registry `98`, static/LOC, zero promotions, and final review GO pass. NatOp is separate symbolic reduction algebra, not N2; no higher C2.3, Church–Rosser, path equality, absolute identity, objecthood, or current full verify. Versions root/docs `4.0→4.1`, package/src `2.96→2.97`, core `2.35→2.36`, tests `3.44→3.45`.
## [4.0.0] 2026-08-07 — P3-A1b exact prime-power productive bridge
- Released one closed `G_z(n)=z mod p^(n+1)`: THM001/002 totality/determinism, THM003 process coherence independent of N1, and THM004 exact all-depth commutation with direct `F_z`; isolated Lean `6/6`/`7/7` with pinned main/pressure sources, 27-row/53-edge ledger/oracle, and a total/coherent offset pressure refutation. Focused `49/49`, public `1/1`, direct L1, 56 collision-safe aliases, root `1675/1675`, registry `97`, static/LOC, zero promotions, and final review GO pass. No arbitrary productive conversion, choice/DC/coinduction/König, carrier/PΩ realization, physical/foundation-independent infinity, or current full verify. Versions root/docs `3.99→4.0`, package/src `2.95→2.96`, core `2.34→2.35`, tests `3.43→3.44`.
## [3.99.0] 2026-08-07 — P3-T finite compositional observer network
- Released one exact five-node/seven-edge P1-bound network with 112 copied raw A2 rows, nonvacuous typed maps, five identities, exact partial pullback composition, arbitrary finite simple positive paths, seven associativity rows, two semantic triangles, one true two-map translation isomorphism, strict separators, and bounded strict-cycle rejection. Focused `45/45`, public `1/1`, direct L1 (`attacks=18`, `promotions=0`), 53 collision-safe aliases, registry `96`, static/LOC, and final review GO `0/0/0/0` pass. Prime-power N2, universal observer/refinement order, ontic identity/objectivity, promotion, and current full verify remain open/unclaimed. Versions root/docs `3.98→3.99`, package/src `2.94→2.95`, core `2.33→2.34`, tests `3.42→3.43`.
## [3.98.0] 2026-08-07 — P3-N1 direct integer residue family
- Released exact A1 `F_z(n)=z mod p^(n+1)` with three pinned Lean theorems for total coordinates, all reductions, and compatible-family construction; the 20-row/32-edge ledger closes at `propext` and has oracle `3a9970d7…d1f`. Focused `30/30`, direct L1, 33 collision-safe root aliases, registry `95`, Ruff/pycompile/diff/LOC pass. This is not a productive `G_z`, `G_z→F_z` bridge, completed carrier/PΩ2 use, local realization, promotion, absolute infinity/objecthood, or current full verify. Versions root/docs `3.97→3.98`, package/src `2.93→2.94`, core `2.32→2.33`, tests `3.41→3.42`.
## [3.97.0] 2026-08-07 — PΩ2 exact prime-power completion
- Released `ZpVeyra(p)` as the literal dependent subtype of compatible prime-power Fin residues, with canonical reductions, a constructed stage-ring witness, 17 exact Lean obligations, and an isolated p-specific theorem-017 application.
- The 45-row ledger exposes used proof irrelevance, exact theorem/import edges, and closure `Quot.sound`/`propext`; source/package/run/judgment bind the canonical operations and concrete instance. Focused `46/46`, direct L1, isolated Lean `(0,0,0,0)`, collision-safe root API, registry `94`, static/LOC, and strict review GO pass. No categorical/mathlib/topological/generic/productive-to-family/physical/metaphysical/foundation-independent completion or current full-verify claim. Versions root/docs `3.96→3.97`, package/src `2.92→2.93`, core `2.31→2.32`, tests `3.40→3.41`.
## [3.96.0] 2026-08-07 — P3-C1 strict-ranked generated-path confluence
- Released exact finite ranked continuation systems, source-derived reachable peaks, pure relation-path local cells, structural no-axiom `THM_P3C1_001_ranked_local_to_generated_confluence`, six bounded carry-normalization QA systems, ten counterpressure rows, hostile-safe bounded revalidation, collision-safe aliases, and level-1 registry certificate `93`.
- Focused `20/20`, direct L1, Ruff/compile/public/LOC, and definitive review GO `0/0/0/0` pass. This is joinability only relative to one strict-ranked finite system: no C1/C3 transport provenance, transport coherence, unique normal form, Church–Rosser, unbounded confluence, objecthood, completed infinity, promotion, or current full verify claim. Versions root/docs `3.95→3.96`, package/src `2.91→2.92`, core `2.30→2.31`, tests `3.39→3.40`.
## [3.95.0] 2026-08-07 — P1-E4 finite historical observer actualization
- Released one finite history-relative HAP token from raw P1-B+E1 with strict parent-derived Past/Future, first lineage birth, target-sealed anti-circular strict-past closure, three mandatory counterfactual classes, same-lineage/token/scope efficacy, separated core/token/history/judgment digests, hostile-safe bounded validation, collision-safe `E4*`/`e4_*` aliases, and L1 certificate.
- Focused `37/37`, direct L1, registry `92`, static/LOC, definitive external GO `0/0/0/0`. No physical/preformal/consciousness/absolute/observer-independent actualization, promotion, or current full verify claim. Versions root/docs `3.94→3.95`, package/src `2.90→2.91`, core `2.29→2.30`, tests `3.38→3.39`.
## [3.94.0] 2026-08-07 — P1-C4 finite Scoped Formation Principle
- Released one finite `FiniteScopedObjectPresentation` relative only to exact SFP/doctrine/scope after raw P1-B/G4/C2/A2/C3 replay, response-derived ternary G4, nonempty support/persistence, declared finite confluence, and genuine direct/translated refinement survival; failures resolve `REFUTED > OPEN`.
- Focused `28/28`, combined `69/69`, direct L1, registry `91`, collision-safe `C4*`/`c4_*` root API, static/LOC, definitive external review GO `0/0/0/0`. No absolute/history/physical/infinity/object-necessity/global-confluence/promotion/current-full-verify claim. Versions root/docs `3.93→3.94`, package/src `2.89→2.90`, core `2.28→2.29`, tests `3.37→3.38`.
## [3.93.0] 2026-08-07 — P2-S status/promotion schema meta-validator
- Released an exact nonpromoting meta-calculus over 15 typed judgment domains and 17 rules, with 40 named premise projections plus one index projection, a fixed five-schema allowlist, 12 rejected adjacent-cast attacks, collision-safe root exports, and level-1 certificate `status_promotion_p2s` at registry `90`.
- Focused `20/20`, literal oracle `2cbe0f2f1f1025696b947c73e32196f230e7748c77c030543d2292a34585875a`, static/LOC/public/registry checks, and definitive review GO `0/0/0/0` pass. The release reports `promotions=0` and `ontology_claims=0`: no ontology theorem, new axiom, object, infinity, retroactive reclassification, codebase-wide completeness, or current full `make verify` is claimed. Versions root/docs `3.92→3.93`, package/src `2.88→2.89`, core `2.27→2.28`, tests `3.36→3.37`.
## [3.92.0] 2026-08-07 — PΩ1 exact ledger-relative Stream(A) completion
- Released completed `Stream(A)` only relative to exact doctrine/ledger: focused `37/37`, direct L1, isolated Lean `15/15`, pinned compiler, ledger `36/46`/`Quot.sound`, generator closure, shared four-phase cap, registry `89`, static/LOC, review GO. No physical/metaphysical/foundation-independent infinity, D1/D3 promotion, generic completion/inverse limits, PΩ2, C4, or current full verify. Versions root/docs `3.91→3.92`, package/src `2.87→2.88`, core `2.26→2.27`, tests `3.35→3.36`.
## [3.91.0] 2026-08-07 — P1-C3 — Compact: one finite typed translated cell, unchanged C1, focused `31/31`, combined `124/124`, registry `88`, review GO; no reverse/universal refinement, C2 coverage, C4/object, Church–Rosser, infinity/completion, promotion/current full verify. Versions root/docs `3.90→3.91`, package/src `2.86→2.87`, core `2.25→2.26`, tests `3.34→3.35`.
## [3.90.0] 2026-08-07 — P1-D3 — Compact: one ledger-relative periodic family, supplied/oracle assumed, five one-law countermodels, focused `34/34`, registry `87`, Lean `11`/`4766c6…4a70b`, review GO; no carrier/universal/separation/history/generic-AFIP/PΩ/promotion/current full verify, and unavailable session `22892` remains unclaimed. Versions root/docs `3.89→3.90`, package/src `2.85→2.86`, core `2.24→2.25`, tests `3.33→3.34`.
## [3.89.0] 2026-08-07 — P1-C2 declared finite confluence aggregation
- Released exact nonempty local-fork and separately declared arbitrary same-endpoint history catalogs (including cycle-versus-identity), atomic hard-cap-first preflight, complete ordered coverage, separate finite statuses, hostile-safe fresh revalidation, root exports, and level-1 `confluence_aggregate_p1c2`; focused `22/22`, direct certificate, registry `86`, Ruff/pycompile/diff/LOC, and review GO `0/0/0` pass. No generated-path universe, termination, Church–Rosser, C3/C4, object formation, infinity, promotion, or current-tree full `make verify` is claimed; immutable I1-77 remains separate.
## [3.88.0] 2026-08-07 — P1-D2 finite-to-universal counterpressure
- Released five exact inference audits with disjoint outcomes: two evidence insufficiencies and three countermodels (two pinned-Lean foundation-bound, one structural target chooser), policy-threaded resource refusal, fresh revalidation, collision-safe root enum aliases and facade exports, and level-1 `productivity_counterpressure_p1d2` certificate.
- Focused `39/39`, exact ordered rows `5/5`, insufficiency `2/2`, countermodels `3/3`, Lean `2/2`, chooser `1/1`, promotions `0`, registry `85`, pinned Lean `v4.30.0-rc2` rc0/no `sorry`/`admit` at `32ebbb…fcec`, Ruff/compile/LOC, and implementation review GO `0/0/0` pass. No generator nonexistence, D3/all-depth family, completed carrier, historical target independence, PΩ, or current-tree full `make verify` is claimed; immutable I1-77 remains separate.
## [3.87.0] 2026-08-07 — Provisional P1-A2 finite observer relations
- Added exact doctrine/source/scope-bound ordered Cartesian replay, independent preservation/reflection/domain laws, deterministic equivalence/refinement/coarsening/open classification, raw P1-A triangle replay, proposal-conflict/loss separation, typed preflight refusal, fresh result revalidation, and level-1 `observer_relations_p1a2` certificate; indexed doc 151 as a synthesis/status map only.
- Focused `23/23`, direct certificate, registry `84`, Ruff/pycompile/diff/LOC, `certify.py` 300, pinned `certify_types.py`, root gate `fail=0`, and independent code review pass. Runtime crossed-partition incomparability is deferred under unary R11 although the classifier truth table is tested; A2.3/A2.4, C2/C3/C4, off-scope/universal order, invertibility, object formation, and promotion remain OPEN/NOT_ESTABLISHED; immutable I1-77 is separate and no full current-tree `make verify` is claimed.
## [3.86.0] 2026-08-07 — Provisional P1-E1 doctrine-relative observer genesis
- Added strict primitive AST/native mode replay, a Mode-only exact 24-row adapter, fresh bounded reachability, path-relevant recurrence, scoped discrimination/persistence/exact-index residue efficacy, explicit OEP admission, typed preflight refusal, fresh result revalidation, and a level-1 `observer_genesis_p1e1` certificate.
- Focused `28/28`, direct certificate, Ruff, pycompile, diff, LOC, registry `83`, `certify.py` 300, unchanged `certify_types.py`, and final review GO `0/0/0` pass. The old aggregate is retired with no claimed outcome; immutable I1-77 is separate. E2/R11 realization, E3 self-observation, E4 chronology/physical provenance, consciousness, physical instantiation, target independence, and promotion remain OPEN/NOT_ESTABLISHED.
## [3.85.0] 2026-08-07 — Provisional P1-D1 pointwise productivity
- Added one closed nonempty periodic structurally guarded generator with policy-independent program/generator identity, O(n) one-demanded fresh prefixes, coherent restriction identity/composition, typed preallocation `RESOURCE_LIMIT`, bounded returned-result revalidation, and a level-1 `productivity_p1d1` certificate.
- Focused `30/30`, direct certificate, Ruff, pycompile, diff, LOC, D1-gate registry `82`, `certify.py` 300, unchanged `certify_types.py` SHA `0de598…b258`, and independent review GO `0/0/0` pass. Old aggregate is pending/nonrepresentative; immutable I1-77 is separate. D2/D3/all-depth/PΩ remain OPEN; all-depth evidence/provenance OPEN and carrier/target independence NOT_ESTABLISHED.
## [3.84.0] 2026-08-07 — Provisional P1-C1 exact direct-echo fork
- Added generic doctrine-bound finite diagram/path/fork sources, distinct bound branches and joins, full monotone alignment, fresh persistence/response replay, a derived transport 2-cell, deterministic commitments, swap pressure, and a level-1 `confluence_p1c1` certificate.
- Focused `29/29`, direct certificate, Ruff, pycompile, diff, LOC, C1-gate registry `81`, max production/test `266/291`, C1-gate `certify.py` exactly 300, unchanged `certify_types.py`, and independent review GO `0/0/0` pass. Old live aggregate is pending/nonrepresentative; immutable I1-77 is separately green. This establishes only one exact direct-echo fork: C2 aggregation, C3 translation/G4, C4 scoped formation, global/Church–Rosser, productivity/infinity/PΩ, and promotion remain OPEN.
## [3.83.0] 2026-08-07 — Provisional P1-B formal finite generability
- Added exact seed/program/doctrine membership, closed target-free `SeedRef`/`PulseStep` replay/composition, fresh output identities, deterministic commitments, artifact/judgment revalidation, and replay-before-target `GENERABLE`/`TARGET_MISMATCH` with a provisional level-1 certificate.
- Focused `19/19`, direct certificate, Ruff, pycompile, diff, LOC, and independent review GO `0/0/0` pass; the older aggregate is pending/nonrepresentative. Only formal finite generability is claimed: genesis/chronology/target independence/scoped object/confluence/productivity/all-depth/PΩ/promotion remain open.
## [3.82.0] 2026-08-07 — Provisional P1-A observer morphisms
- Added exact membership/immutability-bound structural R11 response projection, comparison-domain factorization, separate strong coverage, structural loss/status, and identity/composition laws with a provisional level-1 certificate. Focused `19/19`, direct certificate, Ruff, pycompile, diff, and ≤300 LOC pass; aggregate certification is pending and static target is 79.
- No chronology, construction, scoped object, confluence, productivity, all-depth/PΩ, theorem/R8/layer/Sage/taxonomy/novelty claim. P1-B next targets target-free closed seed/pulse replay and formal generability only.
## [3.81.0] 2026-08-06 — Bounded positive ontology P0
- Added an executable provisional P0 nucleus: exact `p0-v1` SHA-256-bound crest/tail doctrine, hostile-safe closed-observer snapshots, typed support/silence, replay-derived facets, path-relative persistence, fixed declared-family extension, finite coherence pressure, and five explicitly separated infinity levels.
- Post-review focused P0 tests pass `27/27`, the direct level-1 certificate passes, the static suite count is 78, and independent re-review finds no blocker/high/medium after alien-path, unrelated-atlas, tuple-sentinel, and hostile-G4 repairs. No full P0 `make verify` was run; immutable I1-77 is separate. Constructibility stays OPEN and scoped-object is only OPEN/REFUTED, with no ontic-existence, general-refinement, metaphysical-proof, R8/layer/Sage/taxonomy/novelty claim.
## [3.80.0] 2026-08-06 — Bounded observer infinity and residue towers
- Added exact finite prefix observers, prime-power residue windows, first obstructions, and bounded coherent residue addition/multiplication; registered `observer_infinity_i1` as continuation certificate 77.
- Added digest-bound `THM_I1_001..004`: stream recovery/uniqueness/conflict from an explicitly supplied all-depth prefix family and one-link modular-addition refinement. Initial review found and triggered repair of Lean/Python alignment, hostile logging, pre-encoding bounds, and exact theorem-set gates; post-fix `19/19` and pinned Lean pass. Independent re-review reports no blocker/high/medium at `7be8b425c0cefb243706d71d4774fa886df5ddb75c611cf6e2fb848930a75975`; aggregate/full immutable verification remains open.
- This is a completion-motivated inverse-system experiment, not a constructed p-adic inverse limit/carrier or a new infinity/cardinal/transfinite/topology/field/novelty/layer/Sage/R8 claim.
## [3.79.1–3.79.2] 2026-08-06 — R14.3b trusted CEGIS snapshot repairs — Restored one-argument ordinary-fit dispatch, then closed field/container/grammar snapshot-copy TOCTOU with hook-safe exact local snapshots, exact-default/fresh-brand verification, and invalid-before-evaluation mapping; unrelated runtime faults propagate, focused `115/115` passes, and the serial gate remains open.
## [3.79.0] 2026-08-06 — Final four fixed X8 cards
- Added closed A004–A006 sampled-continuity/drift/midpoint-area cards and fixed C002 mod-12 chord mirror; rebound A001–A006 and C001–C002 to new full-file hashes.
- Appended the exact final four rows and explicit wrapper/root APIs; X8 is 19 completed / 0 prep-ready across six files with the same certificate.
- No general analysis/trigonometry claim; B001/G4 and continuation/frozen counts 76/75 remain unchanged.
## [3.78.0] 2026-08-06 — Four-card fixed geometry X8 wave
- Added closed G002–G005 SSS/SAS/line-shell/relabel fixtures to the shared geometry Lean artifact and rebound G001–G005 to one full-file SHA-256.
- Appended four catalog rows and explicit public accessors; X8 is 15 completed / 4 prep-ready across six files with the same certificate.
- Scope remains fixed arithmetic only; no general SSS/SAS/intersection/transformation theorem, and B001/G4/76/75 remain unchanged.
## [3.77.0] 2026-08-06 — Fixed variance-shift numerators and X8 evaluator split
- Added `THM_S002_variance_shift_1_3_5_plus_10`: direct numerator equality and both values `8` only for `(1,3,5)`/`(11,13,15)`; rebound S001/S002 to the shared full-file digest.
- Moved internal row evaluation/prep lookup into `formal_export_evaluator.py` while preserving public row identity, 13-key order, live checker monkeypatching, and fail-closed captured-byte continuity.
- X8 is 11 completed / 8 prep-ready across six files; continuation suite 76 and frozen gate 75 remain separate.
## [3.76.0] 2026-08-06 — Fixed binomial-symmetry computation
- Added recursive finite `choose` and `THM_B001_binomial_symmetry_6_2`, bound to the full combinatorics-file SHA-256.
- X8 is now 10 completed / 9 prep-ready across six files; the continuation suite stays 76 and the original frozen gate stays 75.
- Scope is only `choose 6 2 = choose 6 4 = 15`, not general binomial symmetry or combinatorics.
## [3.75.0] 2026-08-06 — Canonical four-outcome independence count product
- Added `THM_P003_probability_independence_counts` to the shared probability artifact and rebound P001/P002/P003 to its new whole-file digest.
- X8 is now 9 completed / 10 prep-ready across five files; the continuation suite stays 76 and the original frozen gate stays 75.
- Scope is only `Ω={00,01,10,11}`, `A={10,11}`, `B={01,11}` and `1*4=2*2`, not general independence, probability, or measure theory.
## [3.74.0] 2026-08-06 — Finite observer-patch exact gluing
- Added exact-type finite patches/partition sections, generated `E*`, exact gluing iff no local contradiction, and the AB/BC/CA singleton-overlap obstruction; three full-file-SHA-bound Lean theorems use captured compilation plus reread continuity. Adversarial tests and `observer_patch_atlas_g4` bring the continuation suite to 76 while 36 layers, 93 Sage exports, 41/280 notebooks/cells, `2/4/25/5`, all general geometry/R8 boundaries, and the original frozen 75-certificate gate remain unchanged.
## [3.73.0] 2026-08-06 — Canonical four-outcome union count
- Added `THM_P002_probability_union_counts` to the shared probability artifact and rebound P001/P002 to its new whole-file digest.
- X8 is now 8 completed / 11 prep-ready across five files; certificates remain 75.
- Scope is only `A={10,11}`, `B={01,11}` and `3+1=2+2`, not general probability, inclusion-exclusion, or measure theory.
## [3.72.0] 2026-08-06 — Fixed-sample X8 mean balance
- Added pinned Lean `THM_S001_mean_balance_1_3_5` for only the canonical sample `(1,3,5)`.
- Split X8 bindings/checks, reject digest mismatch before Lean, compile only trusted captures in isolation with continuity, preserve legacy API, and reject comment/missing/wrong/swap attacks.
- Updated X8 from 6/13 to 7/12 across five unique checked Lean files without changing the 75-certificate suite or claiming general statistics.
- Kept the original frozen snapshot's serial K0 and isolated Sage gates open.
## [3.71.1] 2026-08-06 — Roadmap closure hardening
- Made Q11 tensor labels injective and added a guarded compile gate for four exact Lean theorem IDs.
- Derived optimizer candidate/observer provenance from validated definitions instead of trusting caller offsets or observer inputs.
- Replaced quantified text substitution with bounded structural exact-kind specialization and matching Python/Rust limits.
- Corrected R16 to partial/conditional descent language and synchronized 75 certificate / 93 Sage-export / 36-layer metadata.
- Kept the new VAM surfaces isolated and open/blocked: no opcode/runtime wiring, whole-optimizer proof, native-performance, VAMD emission, or promotion claim.
- Serial K0 and the isolated Sage certificate-suite summary remain release gates until immutable-tree evidence exists.
- Corrected the stale contiguous-nine F5 regression expectation after retired `BM-F008`; the active F001–F007/F009 ledger is 8/8 derived.
## [3.71.0] 2026-08-04 — Bounded roadmap closure and R16 reduction
- Added `THM-S7-001` with a five-row degree-factor/topological-order separation and certificate.
- Added exact finite tensor/Born/full-unitarity semantics, bounded Lean closure, and a second certificate; suite target is 75.
- Added VAM visible-use/open-theorem, symbolic quantifier, standalone Rust parity, and blocked VAMD policy surfaces; no certificate or native wiring because every status remains open/blocked.
- Reduced finite R16 to best-lower partition abstraction and CBC to full-path annotation, added a five-state descent-totality counterexample, and rejected novelty/R8 promotion.
- Release verification remains serial; xdist is excluded from integrity-sensitive release evidence.
## [3.70.0] 2026-08-04 — Bounded R12–R16 closure and active-surface cleanup
- Added the bounded R12 effects/VAM bridge, exact-premise R13 observer theorem, R14 synthesis pipeline, and finite R16 descent/path-invariant research surfaces with their documented non-promotion boundaries.
- Added the corresponding Python/Rust/Lean, Sage, certificate, fixture, and regression surfaces recorded in the module logs for versions 3.46–3.69.
- Consolidated the active R12–R16 surface around its published observer, proof, and finite-calculus contracts.
- Removed unrelated experimental dependencies from active imports, certificates, benchmarks, documentation, and roadmap.
## [3.40.0] 2026-07-15 — R11 native observer/echo proof core v2
- Added certificate `observer_core_r11`, closed `veyra.observer-core.v2` syntax/partial semantics, and replayable `veyra.observer-proof.v2`: branded non-scalar recurrence/mark/pair responses, bounded embedded-R7/artifact replay, exact tail/silence obstruction, one-way R7 equality+readiness→echo, unequal-pulse crest non-collapse, and exact used-support `observer-core-semantics`, `observer-core-codec`, `crest-pulse-law`.
- Added `THM-R11-001..006` and separate bridge `veyra.lean.r11.observer-echo-tcb.v1`: 34 source/export inputs, nine Lean stages/eight reviewed intermediate oleans, and unchanged runtime closure 2,365 files / 522,231,408 bytes (`990d68abe5bda161659d2a28ad9ba70f8739fdc30fb3655e3258df6bbc2f761a`).
- Frozen evidence: artifact `2bcf57b5dda6b92569328da5de0b5477058dcde08f57a986ced8882b1f5c6c95`, R10 `445bffcf753f29ae20b0e92799561c2e1c047ab4993ef9ac5b22921fc03d8264`, snapshot `0f68fbfa0696f4c2e47c30042eafce7245da92310a9bc267700198ce44c0acc0`, binding `ebacad7ae4334e1e2eb693e015d7417df266400ae18783cb1daa21218f649f30`.
- Boundary/evidence: certificate does not renew R8 or promote a layer (`1/4/25/5`, `proof_complete=False`); Python parser/codec/hash/bridge remain reviewed TCB, the non-self-bound manual manifest root is pinned here as `fb0f280af681a583c757a021f6503bc0ad1186ac5b76399619f82a83d9926c45`, and OS/runtime privilege boundaries remain outside. All hardening waves close stateful-map, ancestor-remap, hostile-container, GC-mutable manifest/object/snapshot roots, noncanonical-support, and pre-continuity call-order findings: immutable snapshot-name rows are validated before R10/filesystem/Lean work, and corruption yields zero R10 calls. Focused observer/bridge `80/80`, manifest `34/34`, and guarded Lean `9/9` pass. Final `make verify` exited 0 with pytest `1315/1315` at 100%, certificates `67/67`, Sage smoke `errors=0`, doctest `attempted=41`/`failed=0`, and clean hygiene; independent final review found no blocker/high/medium.
## [3.39.0] 2026-07-14 — R10 proof-grade Core elaboration
- Added `veyra.proof-surface.v1`: captured closed recurrence source, typed spans, resource bounds, capture-safe named-binder lowering into every R7 rule/native law, exact claim checking, and a composite source/AST/R7/R9 artifact.
- Added constructor-derived six-category support and Lean `THM-R10-001..005`: generic R7/image semantic equivalence and checked-proof soundness plus exact elaborated proof/support checks.
- Hardened trust with 37 reviewed sources, nine reviewed deterministic intermediate oleans in fresh per-run/stage directories, and a traced 2,365-file Lean userspace closure guarded across source/object/runtime reads; exact directory shape plus 25 absent module/loader-shadow paths block stale, hardlink, path-remap, and resolver injection.
- Boundary: closed recurrence surface only; Python parser/resolver remain TCB, support is not proved minimal, legacy theorem language is finite-obligation only, R9 remains fixed-image only, taxonomy stays `1/4/25/5` with `proof_complete=False`; R11 observer/echo proof semantics is next.
- Frozen bridge evidence: ten-stage snapshot `b91c2840...35f04bb`; binding `445bffcf...03d8264`; bridge `18/18`, attacks `9/9`, Rust `12/12`, full verify `1235/1235` + `66/66`, Sage/doctest/hygiene, and final reviews pass.
## [3.38.0] 2026-07-14 — R9 exact intrinsic native-image transport
- Added exact `Recurrence ≃ IntrinsicModeImage`, `THM-R9-001..008`, refutations, and a 16-source/eight-stage pinned bridge; no arbitrary strict/word/cyclic/weighted/approx/profile claim, taxonomy remains `1/4/25/5`, and final R9 gates passed (`65/65`).
## [3.37.0] 2026-07-14 — R8 fail-closed theorem promotion contracts
- Replaced theorem-name membership with an immutable trusted handler manifest binding exact layer identity, theorem/artifact closure, semantic carrier, Lean bridge, providers, and boundary.
- Readiness now accepts only fully resolved contracts; duplicate/reused proofs, singleton theorem transplantation, registry-key swaps, and malformed/stale handlers block.
- Cached checked bridge reports are independently rehashed against the reviewed TCB, generated export, pinned toolchain, binding, diagnostics, and boundary; poisoned cache evidence blocks.
- Taxonomy stayed honestly `1 theorem-derived / 4 witness-only / 25 shadow / 5 meta`; at the R8 checkpoint the three carriers remained unbridged and cyclic resonance remained shadow.
- Verification: focused `67/67`, Rust `12/12`, four Lean gates, full `make verify` (`64/64`, Sage, doctest `41/41`, hygiene), diff check, and clean independent re-review.
## [3.36.0] 2026-07-14 — R7 proof-carrying Core
- Added typed proof replay, general Lean checker soundness, immutable TCB/source binding, `THM-R7-001..004`, and the sole theorem-derived `intrinsic-resonance` nucleus.
- Readiness is `1/4/25/5`; review hardening plus targeted `71/71`, Rust `12/12`, full `make verify` (`63/63`, Sage, doctest `41/41`, hygiene), diff check, and independent review pass.
## [3.34.0] 2026-07-14 — Foundational semantic closure R1–R6
- Core/native/VAM parity, single-root witness receipts, structural arithmetic/Lean bridges, and protocol-bound synthesis close R1–R5 without proving 25 shadows.
- R6 is one scoped class-member result—not global superiority or a generated corpus; full `make verify` passed (`62/62`, Sage, doctest `41/41`, hygiene).
## [3.29.0] 2026-07-10 — VAM optimizer single-pass timing fix — Compact: one-pass definition snapshots and refreshed 512-block local artifact; no speed/native claim.
## [3.28.0] 2026-07-10 — VAM battle benchmark harness — Compact: added bounded local timing artifact; no speedup/native-performance claim.
## [3.27.0] 2026-07-10 — VAM v2.7 obstruction-boundary rejection law — Compact: sixth local law plus rejected `OBSTRUCT` witness; no optimizer/VAMD/speed claim.
## [3.26.0] 2026-07-10 — VAM v2.6 compress-idempotent rejection law — Compact: fifth local law plus rejected witness; no optimizer/VAMD/speed claim.
## [3.25.0] 2026-07-10 — VAM v2.5 modular cert/proof split — Compact: split optimizer proof catalog and VAM optimizer certificate gate under 300 LOC; refactor evidence only.
## [3.24.0] 2026-07-10 — VAM v2.4 optimizer pre/post witnesses — Compact: added executable witness rows/docs/tests; near-cap split closed by v2.5.
## [3.23.0] 2026-07-10 — VAM v2.3 dead-shadow local law
- Added fourth checked optimizer local law: `dead-shadow` unused lookup/drop preservation in `proofs/lean/VeyraOptimizer.lean`.
- `vam_reference_v1` now gates four Lean local laws plus v2.0-v2.3 docs/tests; all passes remain obligation-backed.
- Boundary: no whole-pass/whole-optimizer correctness, optimized VAMD emission, or speed claim.
## [3.22.0] 2026-07-10 — VAM v2.2 compress-alias local law
- Added third checked optimizer local law: same source/observer `compress-alias` lookup preservation in `proofs/lean/VeyraOptimizer.lean`.
- `vam_reference_v1` now gates three Lean local laws plus v2.0-v2.2 docs/tests; `dead-shadow` remains obligation-only, and all passes remain obligation-backed.
- Boundary: no whole-pass/whole-optimizer correctness, optimized VAMD emission, or speed claim.
## [3.21.0] 2026-07-10 — VAM v2.1 compress-idempotent local law
- Added second checked optimizer local law: same-observer `compress-idempotent` rewrite idempotence in `proofs/lean/VeyraOptimizer.lean`.
- `vam_reference_v1` now gates two Lean local laws plus v2.0/v2.1 docs/tests; `compress-alias` and `dead-shadow` remain obligation-only, and all passes remain obligation-backed.
- Boundary: no whole-pass/whole-optimizer correctness, optimized VAMD emission, or speed claim.
## [3.20.0] 2026-07-10 — VAM v2.0 optimizer proof bridge — Compact: added observer-alias Lean local law gate; optimizer passes remained obligation-backed.
## [3.19.0] 2026-07-10 — VAM v1.9 optimizer proof-obligation ledger
- Added bounded optimizer obligation rows for observer-alias, compress-alias, compress-idempotent, and dead-shadow, embedded into the optimizer witness ledger with coverage/digest checks.
- `vam_reference_v1` now gates the v1.9 obligation ledger and docs/tests; boundary remains obligation-map evidence only, not proof-grade correctness or speed.
## [3.18.0] 2026-07-10 — VAM v1.8 optimizer witness and metamorphic parity
- Added deterministic optimizer witness ledgers with bounded digests for original/optimized rows, optimizer rows, equivalence summaries, and semantic-core reports.
- Added native optimizer metamorphic tests for VAM0/VAMD report parity, byte-stable output, line-insensitive semantic cores, and rejected obstruction visibility.
- `vam_reference_v1` now gates the witness ledger and metamorphic harness; boundary remains bounded regression evidence only, not proof-grade correctness or speed.
## [3.17.0] 2026-07-09 — VAM v1.7 optimized VAM0 emission
- Added native `--emit-optimized-vam0` to write optimized VAM0 frame artifacts for VAM0 input plus exact `observer-alias-v1`.
- Added native encoder and tests that decode the emitted frame and compare optimized IR/semantic report against the Python oracle.
- Boundary: VAMD optimized-frame emission, speed/performance backend, proof-grade optimizer, GPU/FPGA, and proof-assistant claims remain blocked.
## [3.16.0] 2026-07-09 — VAM v1.6 VAMD optimizer policy and generated parity
- Native optimizer now accepts decoded VAM0/VAMD semantic report inputs with `input_magic` and `decoded-ir-report-only` boundary fields.
- Added bounded generated VAM0/VAMD optimizer parity corpus against the Python oracle for rows, optimized IR, and semantic reports.
- Boundary: no optimized frame emission, speed/performance backend, proof-grade optimizer, GPU/FPGA, or proof-assistant claim.
## [3.15.0] 2026-07-09 — VAM v1.5 native optimizer extension parity
- Extended Rust native optimizer parity beyond observer alias to duplicate `COMPRESS`, same-observer `compress-idempotent`, and obstruction-safe dead-shadow pruning, split into `<300 LOC` submodules.
- Added required Python-oracle integration tests for safe/rejected optimizer cases and documented v1.5 boundaries in `vam/docs/023`.
- Boundary at v1.5: fixture-scoped parity only; proof-grade correctness, optimized-frame emission, speed/performance backend, GPU/FPGA, and proof-assistant claims remained blocked; v1.6 narrows VAMD optimizer policy to decoded report-only input.
## [3.14.0] 2026-07-09 — VAM v1.4 native optimizer parity slice
- Added bounded Rust `--optimize observer-alias-v1` for VAM0, expanded VAMD malformed-boundary tests, expanded VAM0/VAMD parity fixtures, and speed-neutral `vam/benchmarks/semantic_parity.py`.
- Boundary: this is first-slice optimizer parity only; full native optimizer, proof-grade equivalence, speed/performance backend, GPU/FPGA, and proof-assistant claims remain blocked.
- Verification: targeted native optimizer/boundary/parity tests, cargo tests, Ruff, harness smoke/full runs, and root `make verify`.
## [3.13.0] 2026-07-09 — VAM v1.3 native VAMD execution parity
- Added `vam0-inspect` VAM0/VAMD magic autodetect, VAMD report magic, JSON writer split, and dense CLI report parity tests against the Python canonical oracle.
- Boundary: this is fixture-scoped parity only; native optimizer, speed/performance backend, GPU/FPGA, and proof-assistant claims remain blocked.
- Verification: targeted native tests, Rust cargo tests, Ruff, and independent review passed; full `make verify` passed (`62/62`, Sage smoke, doctest `41/41`, hygiene).
## [3.12.0] 2026-07-08 — VAM v1.2 dense bytecode slice
- Added VAMD dense bytecode: Python encoder/decoder, Rust parser scaffold, dense boundary tests, `docs/020`, isolated HL-1 observer/process lowering, and `vam_reference_v1` coverage.
- Boundary: VAMD is compact representation/parity work only; native CLI execution, native optimizer, speed/performance backend, and proof-assistant claims remain future work.
- Verification: targeted v1.2 tests, Rust cargo tests, and full `make verify` passed (`62/62` certificates, Sage smoke ok, doctest `41/41`, hygiene clean).
## [3.11.0] 2026-07-08 — VAM v1.1 taxonomy and opcode groundwork
- Added stable VAM error taxonomy rows, metadata-only dense opcode table, finite transport-only proof-object rows, docs `017`-`019`, and `vam_reference_v1` coverage.
- Boundary: dense bytecode encoder/runtime integration, native optimizer implementation, performance backends, and proof-assistant semantics remain future work.
- Verification: targeted VAM slice and full `make verify` passed (`62/62` certificates, Sage smoke ok, doctest `41/41`, hygiene clean).
## [3.10.0] 2026-07-08 — VAM v1.0 finite semantics and boundary hardening
- Added finite theorem-case carriers, shell/conjunction carrier labels, expanded obstruction/malformed-frame fixtures, native CLI boundary tests, and conservative `compress-idempotent` normalization.
- `vam_reference_v1` now gates finite theorem cases, shell transported/blocked carriers, and expanded fixture coverage; no proof-assistant, speed, dense opcode, or native optimizer claim.
## [3.9.0] 2026-07-08 — VAM v0.9 golden parity tightening
- Added VAM golden fixtures, native Rust unit tests, fixture-wide Rust/Python report parity, report-fingerprint equivalence checks, obligation transport-only gate, docs `015`, and certificate coverage.
- Boundary: parity remains fixture-scoped; dense opcodes, optimizer-native parity, GPU/FPGA, speed, and proof-assistant claims remain gated pending broader fixtures and contracts.
## [3.8.0] 2026-07-08 — VAM v0.8 execution-contract slice
- Added canonical VAM reports, finite shell lowering, obligation IR, high-level echo seed, optimizer equivalence summaries, Rust execution report slice, tests, and docs `014`.
- Boundary: Rust is parity-only, shell/obligation/high-level rows are not proof assistants, and optimizer equivalence is execution evidence only; full `make verify` passed (`62/62` certificates, Sage smoke ok, doctest `41/41`, hygiene clean).
## [3.7.0] 2026-07-08 — VAM diagnostics, theorem carriers, and native scaffold
- Added `vam/src/diagnostics.py`, `vam/src/theorem.py`, Rust `vam/native/` scaffold, tests, and VAM docs `012`-`013`.
- `vam_reference_v1` now covers diagnostics/theorem carriers/native scaffold; full `make verify` passed (`62/62` certificates).
## [3.6.0] 2026-07-08 — Parallel review protocol
- Compact: added bounded parallel-review guidance, linked docs/TODO/memory/VAM, and passed full `make verify` (`62/62`).
## [3.5.0] 2026-07-08 — VAM coordination safety pass
- Compact: integrated the multi-review VAM safety/docs pass (`007`-`011`) and passed full `make verify` (`62/62`).
## [3.4.0] 2026-07-08 — VAM Core Language lowering
- Compact: added finite Core -> VAM compiler, trace/boundary shadows, and `vam_reference_v1` coverage; `make verify` passed (`62/62`).
## [3.3.0] 2026-07-08 — VAM conservative optimizer
- Compact: added duplicate observer aliasing and dead shadow pruning with obstruction-preserving reject rows; `make verify` passed (`62/62`).
## [3.2.0] 2026-07-08 — VAM0 binary frame
- Added `vam.src.bytecode`: deterministic `VAM0` binary frame with magic/version/size/CRC32 header and compact instruction payload.
- Extended VAM tests and `vam_reference_v1` certificate to cover `.vmasm -> IR -> VAM0 -> IR -> execute`.
- Boundary: binary envelope only; dense opcode tables, optimizer, compiler, and native backend remain future work; full `make verify` passed (`62/62`).
## [3.1.0] 2026-07-08 — VAM reference interpreter v0.2
- Added importable VAM reference layer: `.vmasm` parser/disassembler, instruction/object/state representation, deterministic interpreter, and obstruction-preserving execution.
- Added VAM tests and `src.core.certify_vam` bridge; global certificate suite now includes `vam_reference_v1`.
- Boundary: text IR/interpreter only; binary `VAM0`, optimizer, Core compiler, and native backend remain future work.
- Verification: full `make verify` passed (`62/62` certificates, Sage smoke, doctest, hygiene).
## [3.0.0] 2026-07-08 — VAM abstract machine scaffold
- Created `vam/` for the Veyra Abstract Machine track.
- Added roadmap, VAM Spec v0.1, `.vmasm` text bytecode draft, module memory/logs, placeholder backend folders, and a minimal echo example.
- Boundary: scaffold/spec only; no native-speed, compiler-completeness, GPU/FPGA, or proof-assistant claim.
## [2.99.0] 2026-07-08 — Veyra magic audit M1
- Added `src/core/veyra_magic.py` and `veyra_magic_m1`: bounded audit identifies observer synthesis as the strongest current Veyra-specific magic candidate.
- Added `docs/119_veyra_magic_m1.md`, tests, API/TODO/registry/memory updates, and explicit no-superiority/no-speedup boundary.
- Verification: full `make verify` passed (`61/61` certificates, Sage smoke ok, doctest `41/41`, hygiene clean).
## [2.98.0] 2026-07-08 — Surprise de Bruijn trail S6
- Added `src/core/surprise_debruijn.py` and `surprise_debruijn_s6`: two binary de Bruijn cycles match every cyclic window count of width `1..3`, but differ under trail-adjacency/order-4 graph observer.
- Updated surprise docs, TODO, API, theorem/notation registries, and memory with explicit no-universal-impossibility boundary.
- Verification: full `make verify` passed (`60/60` certificates, Sage smoke ok, doctest `41/41`, hygiene clean).
## [2.97.0] 2026-07-08 — Quantum circuit compression Q9
- Added `src/core/quantum_circuit_compression.py` and `quantum_circuit_compression_q9`: exact finite peephole reductions, global-phase normalization, and observer-preserving reductions.
- Extended Q3 baseline coverage to 16 rows / 10 families with `Q9-CIRCUIT-COMPRESS` under a classical compiler-peephole baseline.
- Added `docs/118_quantum_circuit_compression_q9.md`, TODO/API/registry/memory updates, and explicit no-compiler-optimality/no-advantage boundary.
- Verification: full `make verify` passed (`59/59` certificates, Sage smoke ok, doctest `41/41`, hygiene clean).
## [2.96.0] 2026-07-08 — Quantum QFT period shadows Q8
- Added `src/core/quantum_qft_period.py` and `quantum_qft_period_q8`: exact finite `QFT_4` period-to-frequency rows for periods `1/2/4`, offset echo, and false-period obstruction.
- Extended Q3 baseline coverage to 15 rows / 9 families with `Q8-QFT-PERIOD` under classical Fourier-analysis baseline.
- Added `docs/117_quantum_qft_period_q8.md`, TODO/API/registry/memory updates, and explicit no-Shor-scale/no-advantage boundary.
- Verification: targeted Q8/baseline/certificate tests and full `make verify` passed (`57/57` certificates, Sage smoke ok, doctest `41/41`, hygiene clean).
## [2.95.0] 2026-07-08 — Surprise S3/S5 search, XOR, and k-wise ledger
- Added `src/core/surprise_search.py` and `surprise_search_s3`: exhaustive binary words length `4..8` search plus XOR and k-wise parity hidden-correlation rows.
- Result: `496` scanned words, `32` expanded-observer-profile collisions, `0` robust expanded-baseline-blind splits, `1` pairwise-blind split, and `1` 3-wise-blind parity split.
- Updated TODO/docs/API/registries/memory with explicit boundaries: triple/global parity is a classical high-order observer, not an impossibility theorem.
- Verification: full `make verify` passed after S5/Q9 (`59/59` certificates, Sage smoke ok, doctest `41/41`, hygiene clean).
## [2.94.0] 2026-07-07 — Observer-gap surprise separation S1
## [2.94.1] 2026-07-07 — Surprise S1 certificate regression fix
- Fixed `surprise_separation_s1` to certify the expanded baseline-pressure ledger (`expanded_families`, `audit_rows`, `caught_by_expanded`) and the 5-item checklist.
- Strengthened tests so the S1 certificate pass flag is asserted after counterexample-pressure expansion.
- Verification: targeted surprise/certificate tests passed; CPU profiling snapshot recorded for process/optimization review.
- Added `src/core/surprise_separation.py`: first finite baseline-blind pair (`aabaabb` vs `abbaaab`) plus expanded baseline audit rows; the stronger block-frequency, higher-lag, and cyclic-spectral baselines catch the toy pair.
- Added `surprise_separation_s1` certificate, tests, TODO roadmap, and Math Master docs/registry updates with an explicit no-universal-classical-impossibility boundary and counterexample pressure.
- Verification: targeted surprise/cert tests and full `make verify` passed (`55/55` certificates, Sage smoke ok, doctest `41/41`, hygiene clean).
## [2.93.0] 2026-07-07 — Quantum error obstruction Q7
- Added `src/core/quantum_error_obstructions.py` and `quantum_error_obstruction_q7`: six named finite debugging rows for phase break, interference loss, leakage, non-unitarity, syndrome ambiguity, and branch distinguishability.
- Extended Q3 baseline coverage to 14 rows / 8 families with `Q7-ERROR-OBS`, preserving zero stronger claims and zero overclaims.
- Added `docs/116_quantum_error_obstruction_q7.md`, updated Math Master registries/TODO/API docs, and kept Q-Veyra finite/debug-only.
- Verification: targeted Q7/baseline/certificate tests, Lean `VeyraAlgebra.lean`, and full `make verify` passed (`pytest` green, certificates `54/54`, Sage smoke ok, doctest `41/41`, hygiene clean).
## [2.92.2] 2026-07-07 — Probability complement formal export A3
- Added `proofs/lean/VeyraProbability.lean` with checked Lean artifact `THM_P001_probability_complement_counts` for `probability-complement`.
- Extended `formal_export_completion_x8` to 6 completed candidates and 13 remaining prep-ready candidates while preserving finite-card-only probability boundaries.
- Updated formal proof docs, API/proof notes, theorem/notation registries, TODO, and memory under the Math Master gate.
- Verification: targeted Lean/formal-export tests passed and full `make verify` passed (`pytest` green, certificates `55/55`, Sage smoke ok, doctest `41/41`, hygiene clean).
## [2.92.1] 2026-07-07 — Linear equation formal export A2
- Added Lean artifact `THM_A003_linear_equation_unique_solution` for the `linear-equation-solution` theorem-card candidate in `proofs/lean/VeyraAlgebra.lean`.
- Extended `formal_export_completion_x8` to 5 completed candidates and 14 remaining prep-ready candidates while preserving finite-card-only algebra boundaries.
- Updated formal proof docs, theorem/notation registries, TODO, and memory under the Math Master gate.
- Verification: targeted Lean/formal-export tests passed and full `make verify` passed (`pytest` green, certificates `54/54`, Sage smoke ok, doctest `41/41`, hygiene clean).
## [2.92.0] 2026-07-07 — Quantum gate identity Q6 and algebra Lean rows
- Added `src/core/quantum_gate_identities.py`: 11 finite exact/global-phase gate identity rows plus 3 compiler baseline rows.
- Added `quantum_gate_identity_q6` certificate and expanded `quantum_baseline_q3` to 13 rows / 7 families with zero stronger claims.
- Added `proofs/lean/VeyraAlgebra.lean` and promoted `polynomial-identity` plus `polynomial-evaluation` to checked X8 Lean artifacts.
- Documented Q6 and updated X8 counts to 4 completed / 15 prep-ready candidates while preserving no-overclaim boundaries.
- Verification: full `make verify` passed (`pytest` green, certificates `53/53`, Sage smoke ok, doctest `41/41`, hygiene clean).
## [2.91.1] 2026-07-07 — Algebra formal export pack A1
- Added `proofs/lean/VeyraAlgebra.lean`: checked Lean artifacts for `polynomial-identity` (`THM_A001_polynomial_identity_coeffs`) and `polynomial-evaluation` (`THM_A002_polynomial_eval_at_3`).
- Extended `formal_export_completion_x8` to 4 completed candidates and 15 remaining prep-ready candidates while preserving finite-card-only algebra boundaries.
- Updated formal proof docs, API/proof notes, theorem/notation registries, TODO, and memory under the Math Master gate.
- Verification: targeted Lean/formal-export tests and certificate suite passed (`53/53`) and full `make verify` passed (`pytest` green, Sage smoke ok, doctest `41/41`, hygiene clean).
## [2.91.0] 2026-07-07 — Quantum QEC echo Q5
- Added `src/core/quantum_qec_echo.py`: finite observer-indexed QEC branch rows, observer-family rows, syndrome/logical split echoes, and ambiguity rows.
- Added `quantum_qec_echo_q5` certificate and tests requiring 14 branches, 4 observer families, 8 corrected single-error rows, 6 double-error obstructions, 4 split rows, 6 ambiguity rows, and zero overclaims.
- Expanded `quantum_baseline_q3` to 12 current quantum baseline rows covering Q1/Q2/Q4/Q5 while preserving zero stronger claims.
- Documented Q5 in `docs/114_quantum_qec_echo_q5.md` and marked the QEC observer-indexed echo TODO complete.
- Verification: full `make verify` passed (`pytest` green, certificates `52/52`, Sage smoke ok, doctest `41/41`, hygiene clean).
## [2.90.2] 2026-07-07 — Formal export style hygiene
- Wrapped long formal-export X8 boundary/import/certificate lines without semantic changes.
- Compacted older `src/core/MODULE_LOG.md` tail entries so module documentation stays below the 300 LOC limit.
- Verification: targeted `tests/test_formal_export_completion.py tests/test_certify.py` passed (`5/5`); whitespace diff check clean.
## [2.90.1] 2026-07-07 — Formal export geometry completion
- Added checked Lean artifact `THM_G001_pythagorean_3_4_5` in `proofs/lean/VeyraGeometry.lean`; extended `formal_export_completion_x8` to 2 completed and 17 prep-ready candidates; marked the finite-only geometry/algebra TODO complete without claiming full geometry formalization. Full `make verify` passed (`pytest` green, certificates `51/51`, Sage smoke ok, doctest `41/41`, hygiene clean).
