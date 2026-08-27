# Proof Notes

## Current formal status

The early F/X bridges remain checked alongside the later R7–R13 proof spine.
The presence of a Lean source distinguishes a formal declaration from prose, but
does not by itself make the surrounding family a public release. Executable
certificates are validation evidence unless tied to a checked formal kernel and
an explicit non-claim boundary.

## Checked bridges

- Formal bridge entry point: `src/core/formal_bridge.py`.
- Lean files include `proofs/lean/VeyraEcho.lean`, theorem-card files, R7–R13 files, and `VeyraOptimizer.lean`.

## Experimental research candidate

`experimental/research_lean/` is separate from the stable 53-source inventory.
Its manifest binds eight sources, 65 declarations (33 headlines), imports,
digests, exact Lean `4.30.0-rc2` commit, and every printed axiom closure.
`make research-lean` verifies a fresh temporary snapshot. It does not promote
stable IDs: THM-001–003 remain conjectures, number theory remains classical
local `Nat`/`Int`, and the shadow result covers only unary `Recurrence`.
- `VeyraObserverSynthesisReplay.lean` is an `INTERNAL_RESEARCH_CANDIDATE`
  abstract slice: it proves functional replay determinism/sound acceptance,
  pointwise target preservation under an explicitly supplied bijective
  relabeling, and the exact list-relative meaning of finite-catalog exhaustion.
  It does not formalize the Rust implementation, canonical bytes or hashes,
  CEGIS/catalog completeness, resource custody, or any concrete benchmark row.
- `VeyraObserverSynthesisV3.lean` is an `INTERNAL_RESEARCH_CANDIDATE`
  abstract bridge for canonical rebuild acceptance, task transport through an
  explicitly supplied bijection, and consequences of an explicit equality
  witness between optimized and reference search. It does not formalize Rust,
  cryptography, process custody, concrete profiles, benchmark outcomes, or
  catalog completeness.
- `VeyraObserverSynthesisV4.lean` is an axiom-free
  `INTERNAL_RESEARCH_CANDIDATE` for exact abstract codec/replay laws,
  explicit-bijection task transport, and the list-relative meaning of finite
  exhaustion. It does not formalize the Rust codec, signatures, operating-
  system isolation, source/toolchain manifests, a concrete grammar, or a
  universal search result.
- `VeyraObserverSynthesisV5.lean` is an axiom-free
  `INTERNAL_RESEARCH_CANDIDATE` for caller-supplied admissible pruning,
  finite branch-and-bound coverage, explicitly admitted transport
  preservation, and exact list-relative exhaustion. It does not prove the
  concrete Rust lower bound/ledger, VOR5 framing or signatures, Linux custody,
  a concrete catalog complete, or any universal discovery result.
- `VeyraRealizationTransport.lean` is an axiom-free
  `INTERNAL_RESEARCH_CANDIDATE` for abstract relation inverse-image identity,
  composition, indiscrete-bottom and common-refinement preservation, plus
  composition of an explicitly hypothesized cost-nonincreasing action. It does
  not formalize Python, R11/R16 correspondence, authoritative replay, receipts,
  concrete contexts, P1-A, or cross-doctrine transport.
- `THM-F001`: for every observer `o` and object `x`, `echo(o,x,x)`.
- `THM-F002`: `(n * k + 1) % n = 1 % n`, the product-plus-one arithmetic shadow now used by finite native Mode-length Euclid rows.
- `THM-F003`: finite prime-period Fermat phase row over native Mode/Breath length observers; Python certificate only.
- `THM-R12-001..009`: Python-aligned 2047/2048/4096/128-bounded R12 lowering-image recurrence decode/injectivity, R11 primitive/observer/observation/echo preservation, obstruction-prefix transport, and exact tail/silence blockage; universal helper lemmas are not correspondence evidence, and arbitrary raw-IR equivalence/VAMI parsing/receipt authentication do not follow.
- `THM-R13-001..005`: guarded source acceptance/sound unit-weave semantics, exact R9 image, and readiness-conditioned R12 echo under explicit observer/recurrence/outcome bounds; tail/silence and crest rows discharge public R12 wrappers. Only this bounded `THM-R13-003` drives promotion.
- VAM optimizer bridge: `VeyraOptimizer.lean` checks only observer-alias lookup preservation, same-observer compress-idempotent local rewrite idempotence, visible-use observer preservation, different-observer compress-idempotent rejection, obstruction-boundary compress-idempotent rejection, same source/observer compress-alias lookup preservation, and dead-shadow unused-lookup/drop preservation; v2.4-v2.9 pre/post witnesses connect these laws to executable examples, not to a whole-pass or whole-optimizer proof.
- Finite quantum tensor bridge: `VeyraQuantumTensor.lean` proves natural-weight
  Born normalization, arbitrary finite-factor tensor normalization, and exact
  reversible norm-map closure under tensor product/composition. It is not a
  source/object-bound bridge to Python `Q(sqrt(2))[i]`, Hilbert spaces, or a
  physical apparatus.
- R16 reduction audit is executable Python evidence, not a new formal theorem:
  it identifies best-lower approximation and composition precision loss, while
  a five-state regression blocks unconditional descent totality.
- X7 prep ledger: `formal_export_prep.py`; X8 captures digest-bound bytes and completes all 19 candidates across 6 files with 0 remaining. Newest scope is only four closed A004–A006/C002 fixtures.
- Finite G4 atlas bridge: `VeyraObserverPatchAtlas.lean` proves exact global
  equivalence gluing iff generated closure creates no local contradiction, all
  three singleton overlaps in the AB/BC/CA triangle pass, and exact global
  gluing is nevertheless impossible. The certificate rejects whole-file digest
  mismatch before Lean, compiles exact captured bytes, and rereads continuity.
  Two additional digest-bound helpers prove a pair-coverage sufficient condition
  for extensional uniqueness and a disjoint-singleton nonuniqueness witness.
  They are not registered theorem cards, and the executable quotient-partition
  classification is not claimed Lean-proved. This is not a manifold, general
  sheaf/descent, field, general-topology, novelty, or R8 theorem.
- I1 coherent-tower bridge: `VeyraCoherentTowers.lean` recovers and uniquely
  determines a stream from an explicitly supplied all-depth coherent family,
  blocks a global stream under one restriction conflict, and proves modular
  addition preserves one refinement link. Finite Python windows do not
  construct the Lean hypothesis or a p-adic inverse-limit carrier; no new
  infinity, cardinal/transfinite object, topology, field, novelty, or R8 result
  follows.
- P1-D2 counterpressure bridge: `VeyraProductivityCounterpressure.lean` pins five
  exact theorem IDs at SHA `32ebbb…fcec`; it supplies finite descent rows, no
  infinite natural strict descent, and shrinking-tail laws. Two separate finite
  evidence rows require no Lean. These three countermodels do not prove that a
  generator is nonexistent or construct D3/all-depth/PΩ.
- P1-D3 family bridge: `VeyraAllDepthFamily.lean` pins eleven no-axiom theorem
  IDs at SHA `4766c6…4a70b`; it constructs the exact periodic prefix family,
  proves coordinate membership/compatibility, equality/restriction laws, and
  constructor determinism. Python replays raw D1 provenance and the captured
  source. This establishes one family only relative to its ledger, not a
  completed carrier, universal realization, observer separation, historical
  independence, generic AFIP, or PΩ.
- P1-C2 has no new Lean theorem: its level-1 Python certificate replays one exact
  nonempty local catalog and one separately declared finite same-endpoint history
  catalog, including cycle-versus-identity. It is not generated-path completeness,
  termination, Church–Rosser, object formation, infinity, or promotion.
- P1-C3 has no new Lean theorem: its level-1 Python certificate establishes one
  exact finite typed translated cell only. Direct C1 is unchanged; reverse or
  universal refinement, C2 coverage, C4/object formation, Church–Rosser,
  infinity/completion, and promotion remain unproved.
- PΩ1's isolated `VeyraStreamCompletion.lean` source binds eleven SCP theorems;
  deterministic UTF-8 generation adds four exact bridge theorems. The pinned
  `15/15` result and `Quot.sound` closure establish `Stream(A)` only relative to
  its exact doctrine/ledger, not generic or physical/metaphysical infinity.
- PΩ2's `VeyraPadicCompletion.lean` binds the literal dependent compatible-
  family subtype, canonical Fin ring witness, and exact
  `THM_POMEGA2_001..017`. The p-specific source imports the compiled
  generic object and applies theorem 017 to `pomega2PrimeWitness`; final closure
  is `Quot.sound`, `propext`. The result is only relative to its 45-row ledger,
  not generic/categorical/topological/physical/foundation-independent completion.
  Both PΩ families are `FORMALLY_PROVED + PUBLICLY_VALIDATED`: root aliases,
  certificates, and release-bundle entries are present (see `THEOREMS.md` and
  the formal-evidence registry); the four generated PΩ1 bridge theorems are
  digest-pinned generator output, not repository sources.
- P1-C4 has no new Lean or mathematical theorem. Its level-1 certificate replays
  raw P1-B/G4/C2/A2/C3 to establish one finite scope-relative presentation with
  genuine direct/translated refinement survival; no absolute/history/physical/
  infinity/object-necessity/global-confluence/promotion claim follows.
- P1-E4 has no new Lean or mathematical theorem. Its level-1 certificate checks one finite supplied history: raw P1-B+E1, strict parent-derived cuts, first lineage birth, target seal, three counterfactuals, and same-token efficacy. Physical/preformal/consciousness/absolute/observer-independent actualization remains unproved.
- P3-C1's `VeyraGeneratedConfluence.lean` binds the no-axiom
  `THM_P3C1_001_ranked_local_to_generated_confluence`: strict rank decrease
  plus complete generated local joinability implies joinability of every pair
  of generated finite paths in that relation. It does not prove transport
  coherence, C1/C3 provenance, unique normal forms, Church–Rosser, or infinity.
- P3-T has no new Lean theorem. Its level-1 certificate freshly replays one exact finite P1-bound network with identities, partial pullback composition, a genuine two-map isomorphism, strict separators, triangles, and bounded strict-cycle rejection; this proves no prime-power N2, universal observer order, ontic identity, or promotion.
- P3-A1b pins `VeyraPrimePowerProductiveBridge.lean` (`f0382dee…0382e`) and
  pressure source (`bb21c6a1…f1b5`): THM001/002 give exact closed-program
  totality/determinism, THM003 proves process coherence independently of N1,
  and THM004 commutes with direct `F_z` at every depth. The offset pressure
  source is total/coherent but refuted; no generic selector or infinity follows.
- P3-C2 pins `VeyraTransportCoherence.lean` (`4804c563…e395`): THM001
  structurally derives exact finite global transport fillers from complete local
  commuting squares; THM002/003 are separate symbolic `NatOp` reduction laws.
  Isolated replay covers all three declarations; the latter are not an N2 bridge. Derived cofinal
  boundary reconciliation is C2.2, while a genuine higher C2.3 stays open.
- P3-N2 pins `VeyraPrimePowerReductionNetwork.lean` (`77f5a989…10cf`) and
  rechecks the exact PΩ2 reduction-source and N1-family source closures. Seven
  theorem rows prove reduction identity/composition, comparison-witness
  independence, every same-endpoint thin `Natᵒᵖ` path equal, the family observer
  square, and the two separator equations. Its 37-row/54-edge ledger oracle is
  `2c4cad69…1e9`; neither the completed-carrier judgment, PPCP final theorem,
  C2 status, inverse translation, generic network, nor objectivity is a premise.
- P3-N3/N4 pin `VeyraPadicLocalRealization.lean` (`db273191…d2da`) and
  `VeyraPadicAllDepthEquality.lean` (`3d59ef92…27a`): N3 realizes the exact
  N1 family in the exact PΩ2 carrier; N4 uses a source-bound all-depth premise
  and PΩ2 joint separation for scoped carrier equality. Their proof unions are
  `31/45`, `34/49`, and `108/155`; no generic completion or absolute identity.
  Both families are `FORMALLY_PROVED + PUBLICLY_VALIDATED` because their named
  Lean declarations, public aliases, certificates, and release-bundle entries
  are present.
- P3-N0, P3-N6, and P3-N6-W are `INTERNAL_RESEARCH_CANDIDATE`. Their Lean
  declarations may be cited as formal evidence for the displayed conditional or
  constructive statement, but no public family-level theorem follows.

## P3-N6 public interface boundary

The public N6 interface consists only of the declarations in
`VeyraPrimePowerUnbounded.lean`:

1. `veyraPowerCarrier hp k`, the compatible family generated by `p^k`;
2. `P3N6RawEquality hp x y`, literal equality on that candidate carrier;
3. `THM_P3N6_001..005`, covering finite-prefix agreement, next-depth
   distinction, natural-power carrier injection, and the exact equality adapter.

This interface is a research candidate. It does not export N6-W, a completed
unbounded-depth observer, cardinal infinitude, or an automatic passage from
finite-depth witnesses to a completed all-depth object. N6-W remains a separate
candidate in `VeyraPrimePowerInformation.lean`.
- P2-S has no new mathematical or Lean theorem. Its level-1 certificate checks
  a versioned meta-schema: 15 domains, 17 exact rules, 40 named premise
  projections plus one index projection, five fixed allowlisted DTO schemas,
  and 12 rejected bare casts against independent literal oracle
  `2cbe0f2f1f1025696b947c73e32196f230e7748c77c030543d2292a34585875a`.
  The result is schema conformity only, with `promotions=0` and
  `ontology_claims=0`; it is not proof of any listed rule conclusion and does
  not retroactively certify P1/PΩ artifacts.

## Proof priorities

1. Keep `THM-F001` and `THM-F002` as tiny external bridge sanity checks; do not describe `THM-F003` as formalized until exported.
2. Move from proof of echo reflexivity to a theorem involving actual Veyra syntax objects.
3. Do not generalize any of the 19 fixed X8 cards; no prep-ready rows remain.
4. Add native runtime semantics before claiming broad internal Veyra proof power.
5. Replay the R12.5 source/object/toolchain-bound report before R12.6 certificate/Sage exposure; never treat `preserves` as reflection or equivalence.
6. Extend I1 to profinite/all-modulus towers only after the prime-power finite-window and all-depth-hypothesis boundary survives review.
