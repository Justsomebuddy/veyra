# Active registry from DEF-177

Part of the public [Theorem and Definition Registry](../../THEOREMS.md).

## DEF-177 — Cycle echo
A full rotation-orbit object for a closed mode, used instead of choosing one lexicographic cyclic representative.

## DEF-178 — Primitive count row
A length-indexed comparison of ordered primitive words, cyclic primitive echoes, and collapse count.

## DEF-179 — Primitive phase profile
A cyclic resonance profile enriched with part/whole primitive status, cycle echoes, exponent, offsets, and obstruction.

## DEF-180 — Spectrum/compression comparison row
A candidate row carrying resonance-spectrum rank and compression-score rank side by side.

## DEF-181 — Aura mark
A structured left/right/distance/tact context mark before legacy string rendering.

## DEF-182 — Tact aura echo
A first-class context echo object for a tact, made of structured aura marks.

## DEF-183 — Native resonance-number certificate
The executable certificate that checks cycle-echo primitive counts and spectrum/compression comparison.

## DEF-184 — Edit drift resonance
A cyclic resonance profile allowing insert/delete/substitution drift measured by edit distance.

## DEF-185 — Compression tree
A recursive positive-saving explanation tree whose internal nodes choose resonating parts.

## DEF-186 — Polynomial factor hit
A Veyra ratio root together with its linear factor, quotient, and zero residual.

## DEF-187 — Cost strategy comparison
A side-by-side weighted resonance comparison under uniform, manual, and aura-derived mismatch costs.
## DEF-188 — Compression algebra certificate
The executable certificate for edit drift, compression trees, polynomial factor hits, and cost strategy comparison.

## DEF-189 — Rule coverage cell
A proof-discipline row counting ready/blocked/unknown proof steps and non-empty source spans by rule name.

## DEF-190 — Semantic domain coverage row
An explicit arithmetic, geometry, or logic shadow row with source expression, status, and visible semantic keys.

## DEF-191 — Primitive model note
A consistency note tying one Veyra primitive family to an intended model, executable witness, and model-noted status.

## DEF-192 — Stable formal export row
A theorem-card export candidate emitted only when dependencies are present and Sage hook is non-pending.

## DEF-193 — Proof discipline certificate
The executable certificate for rule/span coverage, semantic-domain coverage, model notes, and stable export gating.

## DEF-194 — Veyra surprise witness
A mode whose surface observer gives no useful compression while a declared hidden observer gives a positive-saving explanation; S1 additionally compares such witnesses against declared classical baseline signatures.

## DEF-195 — Observer-gap score
The hidden-observer saving minus the nonnegative surface-observer saving for the same mode; in S1 a positive gap may separate a structured row from a baseline-matched control row.

## DEF-196 — Edit-lift surprise
A Veyra surprise witness where exact-cycle compression is the surface observer and edit-drift resonance is the hidden observer.

## DEF-197 — Sage public API row
A documented public `veyra_sage.all.__all__` symbol with domain, kind, owner module, and boundary status.

## DEF-198 — Veyra package boundary
The decision ledger separating current research-lab API, core engine, and deferred package-stable Sage extension.
## DEF-199 — School topic coverage row
A post-Core-Language-v0.8 row containing native definition, school shadow, example, counterexample, test path, Sage row, status, and required primitives.
## DEF-200 — School topic gap row
A school topic coverage row whose status is not `covered`, marking seeded or missing primitives needed before school-to-11 replacement can be claimed.
## DEF-201 — Local linearization
A first-order polynomial observer shadow at an anchor, carrying value, slope, tangent polynomial, and obstruction state.
## DEF-202 — Calculus product-rule card
A theorem card checking that the derivative of a product polynomial equals `f'g + fg'` in ratio-polynomial shadows.
## DEF-203 — Calculus chain-rule card
A theorem card checking that the derivative of a polynomial composition equals `(f'∘g)g'` in ratio-polynomial shadows.
## DEF-204 — Integral coherence certificate
An exact antiderivative interval certificate for a ratio-polynomial shadow.
## DEF-205 — Calculus-depth certificate
The executable certificate joining local linearization, product rule, chain rule, and integral coherence into the first calculus-depth seed.
## DEF-206 — Vector mode
A finite nonempty tuple of ratio-mode coordinates used as a school-vector shadow.
## DEF-207 — Matrix transformer
A nonempty rectangular tuple of ratio rows acting on vector modes by exact row dots.
## DEF-208 — Determinant product card
An executable 2x2 theorem card checking `det(AB)=det(A)det(B)` under ratio shadows.
## DEF-209 — Eigen-shadow card
An executable card checking whether `Av` equals `λv`, with zero-vector obstruction.
## DEF-210 — Linear algebra seed certificate
The executable certificate for matrix action, determinant, trace, product, and eigen candidate shadows.
## DEF-211 — Distribution family shadow
A named finite distribution-family row with exact ratio-valued parameters.
## DEF-212 — Mean interval estimate
A finite sample-mean interval row with explicit radius, bounds, sample count, and status.
## DEF-213 — Statistics mean hypothesis card
An executable finite theorem card accepting or rejecting a null mean under explicit tolerance.
## DEF-214 — Statistics inference certificate
The executable certificate joining distribution parameters, interval estimates, hypothesis cards, and uncertainty seed.
## DEF-215 — Trigonometry identity vector
A rational cosine/sine phase shadow represented by existing ratio modes.
## DEF-216 — Unit identity gap
The exact ratio shadow `cos²+sin²-1` used to test rational unit phases.
## DEF-217 — Sum-angle identity card
An executable theorem card checking rational phase composition by sum-angle formulas.
## DEF-218 — Double-angle identity card
An executable theorem card checking phase self-composition against double-angle formulas.
## DEF-219 — Inverse phase identity card
An executable theorem card checking that a phase plus its inverse gives `(1,0)`.
## DEF-220 — Trigonometry identities certificate
The executable certificate joining rational unit phase, Pythagorean, sum-angle, double-angle, and inverse cards.
## DEF-221 — Trigonometry Sage lab facade
A `veyra_sage` research-lab facade exposing rational phase rows and trigonometry identity theorem cards as JSON/notebook-ready rows.
## DEF-222 — Linear algebra Sage lab facade
A `veyra_sage` research-lab facade exposing matrix action rows and determinant/eigen seed cards.
## DEF-223 — Statistics inference Sage lab facade
A `veyra_sage` research-lab facade exposing finite distribution, interval, hypothesis, and uncertainty rows.
## DEF-224 — Sage seed-facade export bundle
The public API, certificate, and generated-notebook bundle that exports trigonometry, linear algebra, and statistics seed facades without claiming package-stable Sage-extension semantics.
## DEF-225 — Formal series shadow
A finite named coefficient row representing a transcendental-looking expression with explicit truncation obstruction.
## DEF-226 — Exponential derivative-shift card
A finite theorem card checking that the derivative of the order-`n` formal exponential shadow equals the order-`n-1` shadow.
## DEF-227 — Log1p derivative-shift card
A finite theorem card checking that the derivative of the order-`n` formal `log(1+x)` shadow equals the alternating geometric shadow through degree `n-1`.
## DEF-228 — Limit envelope
A rational center/radius row that bounds a truncated expression under an explicit finite observer.
## DEF-229 — Alternating tail envelope card
A finite theorem card certifying that a `log(1+x)` alternating next-term radius bounds the unexpanded tail for the declared point range.
## DEF-230–234 — Convergence algebra seed bundle
`CauchyTailCert` (finite tail diameter under tolerance), `MajorantBound` (observed value under bound), `NestedIntervalCert` (nested width-shrink row), `RadiusGuard` (series point inside declared radius), and `ConvergenceCard` (finite theorem cards for those guarded claims).
## DEF-235–238 — Phase equation normal-form bundle
`PhaseBasis` is the bounded rational phase dictionary, `PhaseCoordinateRow` resolves `cos/sin = r`, `PhasePairRow` resolves `(cos,sin)=(a,b)`, and `InversePhaseObstructionCard` records `unit-gap`/`basis-gap` rather than claiming full inverse trigonometry.
## DEF-239–242 — Statistics concentration/likelihood bundle
`ConcBound` records Chebyshev-style rational bounds and Hoeffding exponent guards, `BernLike` records exact Bernoulli likelihood rows, `LikeRatioCard` compares finite likelihood shadows, and `DecisionErr` names TP/TN/FP/FN threshold outcomes.
## DEF-243–246 — Semantic shadow certificate bundle
`SemanticShadowKey` names required observer keys for a declared external domain, `SemanticDomainRow` now carries required/missing keys and a blocked counterexample status, `SemanticShadowCertificate` is the `declared-shadow` row status, and `DomainCertCount` is the proof-discipline count of accepted declared-domain rows.
## DEF-247–323 / THM-R3/R4/R6 — Native/formal/synthesis bundle
`DEF-319–323` cover connected receipts, witness/shadow classification, intrinsic division, protocol-bound observers, and scoped synthesis evidence. `THM-R3-001–002`, `THM-R4-001–007`, and `THM-R6-001–002` remain scoped as documented in `docs/121`–`122`.
## DEF-324–328 / THM-R7-001–004 — R7 proof-carrying Core
Typed de Bruijn syntax, substitution, independent inference, canonical graph replay, and byte/toolchain binding prove supported-checker soundness and `∀r:Recurrence, resonates r r`. This is not cyclic/phase resonance; see `docs/123_proof_carrying_core_r7.md`.
## DEF-329–330 / PROP-R8-001 — Trusted theorem promotion
`DEF-329` is the immutable anchored layer/theorem/carrier/bridge contract; `DEF-330` is independently rehashed promotion evidence. `PROP-R8-001` states that no layer is `theorem-derived` without its exact trusted contract; this is an executable integrity proposition, not a new mathematical theorem.
## DEF-331–334 / THM-R9-001–008 — Exact intrinsic native-image transport
`DEF-331–334` define the fixed-anchor unary `IntrinsicMode` image, total stack-safe encode/partial exact decode, structural law/refutation rows, and 16-source/8-file checked bridge. Lean proves evaluator readiness, image round trips/injectivity, stitch/weave, resonance equivalence, and R7 reflexivity transport; the R8 contract now requires this carrier/bridge while still promoting only `THM-R7-004`. No generic `Mode`, word/cyclic, weighted, approximate, or profile claim; see `docs/125_intrinsic_mode_transport_r9.md`.
## DEF-335–339 / THM-R10-001–005 — Source-replayed proof elaboration
`DEF-335–339` define the closed recurrence proof surface, captured-source/de Bruijn elaborator, composite R7/R9 artifact, constructor-derived support, and 37-source/10-stage bridge with reviewed intermediate objects and traced userspace continuity. Lean proves generic R7/image semantics and checked-proof soundness, then the exact proof/support match. Parser/resolver remain Python TCB; support is not proved minimal; see `docs/126_proof_grade_core_elaboration_r10.md`.
## DEF-340–347 / THM-R11-001–006 — Native observer/echo proof core
`DEF-340–347` define `veyra.observer-core.v2`, typed input/tail/crest/pair ASTs, branded recurrence/mark/pair responses, ordered native obstructions, three-way echo outcomes, conservative R7 embedding, explicit-origin artifacts, and the 34-input/9-stage R10-bound bridge. Lean proves ready-echo characterization/reflexivity, one-way equality lifting, exact tail/silence obstruction, two-sided domain blockage, and crest non-collapse. Echo does not imply equality; no callable synthesis or layer promotion occurs, so taxonomy remains `1/4/25/5` and `proof_complete=False`; see `docs/127_native_observer_echo_core_r11.md`.
## DEF-367–369 — S7 seeded separation corpus bundle
`CorpusPairRow` records a baseline-blind separated pair or a baseline-caught negative-control pair from the seeded 640-word corpus, `CorpusObstructionRow` records a split-free corpus slice, and `CorpusSummaryRow` binds exact counts and the corpus digest. Finite separation against the three named S1 baselines only; no universal classical-impossibility claim.
## DEF-370–372 — Q10 quantum surprise bundle
`QSurpriseWitnessRow` records a limited-menu observer gap detecting Bell-state hidden correlation without full tomography, `QSurpriseObstructionRow` records a provably blind basis menu, and `QSurpriseBaselineRow` keeps the product-factor, full-tomography (declared stronger reference), and classical-correlation honesty baselines. Correlation detection only; no quantum-advantage, nonclassicality, or tomography-replacement claim.
## DEF-373–375 — R15 benchmark evidence bundle
`BenchmarkEvidenceSpec` declares per-benchmark evidence requirements, `BenchmarkEvidenceRow` records assumptions, carrier strength, proof-length class, TCB/search/runtime cost, and observer information loss with the enforced scoped-`stronger` restatement, and `BenchmarkEvidenceObstructionRow` blocks incomplete or unscoped rows. Ledger/definition rows only; never a superiority claim over classical mathematics.
## DEF-379–385 — R12.1 shadow-effect and observation-brand bundle
`CarrierId`, atomic `BridgeCapability`, derived `BridgeDirection`, disjoint `EvidenceClass`/`EvidenceScope`, `BridgeClaim`, and observer-bound `BrandedObservation` distinguish general kernel/formal evidence from finite obligations, executable witnesses, and VAM `CERT`. The fixed registry classifies R9 exact-image equivalence, R11 one-way preservation and crest quotient, and finite legacy Core→VAM preservation. Definitions/audit only: no new theorem, Lean bridge, certificate, promotion, or taxonomy change; see `docs/133_shadow_effect_system_r12.md`.
## DEF-386–403 — R12.2–R12.3 intrinsic VAM IR and finite replay transport — `IntrinsicAnchorIR`, `IntrinsicTactIR`, exact-image `IntrinsicRecurrenceIR`, closed responses/obstructions/outcomes, `IntrinsicLoweringLane`, `IntrinsicLoweringReceipt`, and `TransportedIntrinsicIR` form an immutable sidecar plus four replay-bound preservation lanes. R7/R9 sources and R11 observation/echo computations are replayed; receipts bind finite executable evidence, provenance, ordered sources, observer/kind/payload and IR with no raw-outcome or legacy `CERT` promotion. No byte codec/runtime, Lean, certificate, R8 promotion, theorem, or legacy VAM change; see docs 134–135.
## DEF-404–409 / THM-R12-001–009 — R12.4–R12.5 intrinsic execution and formal preservation — `VAMI` v1 supplies bounded 13-tag raw-IR framing and independent Python/Rust structural parity; the R11-continuous, 28-source/10-stage/9-object Lean bridge proves recurrence decode/injectivity, primitive/observer/observation/echo transport, obstruction prefixing, and tail/silence blockage only under explicit Python-aligned 2047/2048/4096/128 resource predicates. Universal helper lemmas are not correspondence evidence. Capability is only `preserves` with `formal-bridge/general` evidence: CRC/receipts are unauthenticated, arbitrary raw-IR reflection/equivalence, certificate/Sage/R8 promotion/taxonomy/legacy changes do not follow; see docs 136–137.
## DEF-410–413 / THM-R13-001–005 — Promoted intrinsic observer-echo nucleus — The exact doc139 artifacts/report connect R7 soundness, the R9 image, R11 readiness, and R12 lowering only when `observerBounded`, `r11RecurrenceBounded`, and `echoOutcomeBounded` hold; fixed tail/crest rows discharge public R12 wrappers. The second exact R8 contract promotes only this bounded `intrinsic-observer-echo`; broad `echo` remains witness-only and `proof_complete=False`.
## DEF-414–424 — R16 observer-descent and crest-braid bundle
Finite observer doctrines, extensional distinction/refinement, admitted joins, pullback, greatest descent, relational residual, synergy, chain-balance witness, tact profile, minimal crest, and finite crest braid. The executable descent/chain boundaries now require the declared target doctrine and exact canonical `q in O_Y`; the ambient pullback helper alone supplies no membership evidence. `DEF-425` refinement-atlas completion remains conjectural; see docs 141–142.
## THM-R16-001–003 — Residual partition, disjointness, and zero-synergy chain rule
For finite doctrines where the target is exactly admitted and every named direct/staged descent exists, the rows give two disjoint decompositions of the same distinction debt. The abstract predicate spine is Lean-checked; Python target admission and internal-join validation do not prove descent totality, and the concrete bridge is not R8 proof/promotion evidence.
## DEF-426–430 / THM-S7-001 — Bounded topological observer gap
`FiniteDAG`, the S7 degree-factor signature, its declared factor class, exact topological-order count, and the five-row isolated-extension family define a finite separation. `THM-S7-001` states only that the two named eight-vertex incidence DAGs, after adjoining `t=0..4` labelled isolates, have equal declared baseline signatures and unequal linear-extension counts. Exact subset-DP and certificate `observer_gap_topology_s7` check the rows; no all-DAG, minimality, discovery, or superiority claim follows. See doc 143.
## DEF-431–436 / THM-Q11-001–004 — Finite tensor/Born/unitarity bundle
`tensor_modes`, `tensor_gates`, exact Born weights, adjoint, full two-sided unitarity witnesses, and guarded unitary application extend the finite `Q(sqrt(2))[i]` carrier. In `VeyraQuantumTensor.lean`, `THM-Q11-001` is finite Born normalization, `THM-Q11-002` is arbitrary finite-factor tensor normalization, `THM-Q11-003` is exact-unitary closure under tensor product, and `THM-Q11-004` is closure under composition. Lean's natural-weight carrier is not proved equivalent to the Python amplitude carrier. No Hilbert-space, apparatus, simulator, or quantum-advantage claim follows. See doc 144.
## DEF-437–445 — VAM bounded completion/obstruction bundle
Visible-use guard rows, an always-open whole-optimizer theorem skeleton, symbolic `DECLARE_FORALL`, capture-safe total specialization, bounded native parity status, and explicit optimized-VAMD emission policy close the ambiguous roadmap families with executable statuses. They are definitions and obligation ledgers, not a whole-optimizer theorem, proof-producing quantifier semantics, native proof-grade parity, emitted VAMD frame, or performance backend. See doc 145.
## DEF-446 — R16 best-lower reduction audit and partiality boundary
`best_lower_approximation` independently computes a unique greatest admitted lower relation when it exists; `z4_reduction_audit` checks `16/16` target-doctrine-bound descents and `64/64` composition precision gaps. A five-state source counterexample with its raw partition admitted by a separate valid target doctrine proves that finite bottom plus internal joins does not make descent total. R16.6 is closed by rejection of novelty promotion, not by a non-reduction theorem. See doc 146.
## X8 `THM_S001/S002`, `THM_P002/P003`, `THM_B001` — Fixed arithmetic cards
Lean checks only the declared `(1,3,5)` mean, two fixed variance numerators, canonical four-outcome union/independence counts, and `choose 6 2 = choose 6 4 = 15`; no general statistics/probability/measure/combinatorics theorem. See doc 109.
## X8 `THM_G002`–`G005`, `THM_A004`–`A006`, `THM_C002` — Final fixed geometry/analysis/cyclic cards
Lean checks only the declared coordinate, five-sample double-map, three square-drift, midpoint-sum, and mod-12 chord fixtures; no general geometry/continuity/derivative/integration/analysis/trigonometry theorem. See doc 109.
## DEF-447–453 / THM-G4-001–003 — Finite observer-patch exact gluing
Finite patches carry partition-valued local sections; `E*` is the equivalence closure of their union, and an obstruction is an `E*` equality locally distinguished inside a patch. Lean `THM_G4_001_exact_gluing_exists_iff_no_local_contradiction` proves the exact existence criterion, `THM_G4_002_triangle_singleton_overlaps_pass` proves the three pairwise checks, and `THM_G4_003_triangle_exact_gluing_impossible` proves the AB/BC/CA obstruction. Full bytes are SHA-256-bound before captured compilation and reread afterward. No manifold, sheaf, field, general topology, or R8 promotion claim; see doc 147.
## DEF-454–461 / THM-I1-001–004 — Observer infinity and prime-power residue towers
Exact finite prefix/residue windows report first restriction obstructions; Lean proves stream recovery/uniqueness/conflict from an explicitly supplied all-depth coherent prefix family and a one-link modular-addition refinement law. This is a completion-motivated inverse-system pattern in Veyra observer language: I1 constructs neither the Lean family nor a p-adic inverse-limit carrier, and no new infinity/cardinal/transfinite/topology/field/novelty/R8 claim follows. See doc 148.
## DEF-462–468 — P1-A2 exact finite observer-relation bundle
`ObserverRelationScope`, complete ordered pair replay, independent preservation/reflection/domain laws, exact-scope classification, translation triangles, and structural loss are executable definitions with a level-1 certificate, not theorems. Runtime crossed-partition incomparability is deferred under unary R11 although the classifier truth table is tested; no off-scope/universal order, invertibility, identity, formation, or promotion follows. See docs 150–151.
## DEF-469–482 / THM-D2-001–005 — P1-D2 finite-to-universal counterpressure
`productivity_counterpressure*` distinguishes exactly two evidence-insufficiency judgments from three countermodels. Pinned Lean `VeyraProductivityCounterpressure.lean` proves finite descent rows/no infinite natural strict descent and shrinking-tail local/nesting/diagonal laws at SHA `32ebbb960c6a3091402f3dcddf6753c5cf451a7c98357b68ff08fd13e390fcec`; the structural chooser reads its target. These rows refute only five exact implications and prove no generator nonexistence, D3 family, completed carrier, or historical target independence.
## DEF-483–496 — P1-C2 declared finite confluence aggregation — Exact nonempty local-fork and separately declared arbitrary same-endpoint history catalogs, including cycle-versus-identity, replay to complete ordered coverage and separate finite statuses. This is executable level-1 evidence, not a theorem; no generated-path universe, termination, Church–Rosser, object formation, infinity, or promotion follows.
## DEF-497–515 / THM-D3-001–011 — P1-D3 periodic all-depth family
`all_depth_family*` replays the raw D1 periodic source and captured Lean bytes to introduce one extensional compatible prefix family as `FORMALLY_DERIVED` relative to its exact ledger. Supplied/oracle families remain `ASSUMED`; five countermodels refute one law each without proving family nonexistence. The eleven no-axiom Lean theorems at SHA `4766c63f1d398eff41d490218acbaa56a396ce61ec06a14fe85b1814cc64a70b` cover periodic coordinates/membership/compatibility, equality laws, restriction identity/composition/congruence, coordinatewise family equivalence, and constructor determinism. No completed carrier, universal realization, observer separation, historical independence, generic AFIP, or PΩ follows.
## DEF-516 — P1-C3 finite typed translated cell — Exact byte-and-kind bridge plus raw strong P1-A/complete A2 replay yields one asymmetric every-occurrence translated cell; no reverse/universal refinement, C2 coverage, C4/object, Church–Rosser, infinity/completion, or promotion follows, and no theorem is registered.
## DEF-517–531 / THM-POMEGA1-001–015 — Exact ledger-relative Stream(A) completion
`stream_completion*` binds finite prefixes, compatible families, `Stream(A)=Nat→A`, restrictions, diagonal realization, joint separation, exact generator/toolchain and a 36-row/46-edge ledger closing at `Quot.sound`. Eleven SCP plus four generated UTF-8 bridge theorems establish one completed carrier only relative to that doctrine/ledger; no physical/metaphysical/foundation-independent infinity, D1/D3 promotion, generic completion/inverse limit, PΩ2, C4, or promotion follows.
## DEF-532–539 — P2-S meta-calculus — Exact 15-domain/17-rule/40+1-projection/five-schema/12-cast literal-oracle validation only; `NOT_CLAIMED`, zero promotions/ontology, and no theorem/axiom/object/infinity/completeness.
## DEF-540–552 — P1-C4 finite Scoped Formation Principle
`scoped_formation*` replays raw P1-B/G4/C2/A2/C3 and creates one `FiniteScopedObjectPresentation` only when all exact finite components establish, including nonempty support/persistence and genuine direct/translated refinement survival. Ternary response-derived G4 knowledge and `REFUTED > OPEN` remain visible. Level-1 evidence (`28/28`, combined `69/69`, registry `91`) is not a theorem and implies no absolute/history/physical/infinity/object-necessity/global-confluence/promotion claim.
## DEF-553–566 — P1-E4 finite Historical Actualization Principle
`observer_actualization*` derives strict Past/Future only from parent edges, binds first lineage birth and target-sealed anti-circular strict-past assumptions, replays raw P1-B+E1 plus three counterfactual classes and same-token/lineage/scope efficacy, and separates core/token/history/judgment digests. Level-1 evidence (`37/37`, registry `92`, validation passed) establishes one token only relative to one finite supplied history; it is no theorem and proves no physical/preformal/consciousness/absolute/observer-independent actualization or promotion.
## THM-P3C1-001 — Strict-ranked local-to-generated confluence
`THM_P3C1_001_ranked_local_to_generated_confluence` proves by structural strong induction that complete local joinability in one finite relation whose every edge strictly lowers `ρ` makes every same-start generated finite path pair joinable. The pinned Lean theorem has no axioms; Python binds the exact system/source/roots/ranks/generated peaks and pure relation paths. It proves no transport coherence, C1/C3 provenance, unique normal form, Church–Rosser, unbounded confluence, objecthood, infinity, or promotion.
## DEF-567–583 / THM-POMEGA2-001–017 — Exact prime-power completion
`VeyraPadicCompletion.lean` defines `ZpVeyra(p)` as the literal dependent subtype of all compatible `Fin (p^(n+1))` residue families. It constructs canonical stage zero/one/negation/addition/multiplication and their reduction/ring laws, then proves modulus/reduction laws, realization, coordinate agreement, joint separation, relative uniqueness, nonvacuity, coordinatewise commutative-ring closure, and the exact PPCP bundle. `THM_POMEGA2_017_ppcp_introduction` takes only the prime witness and instantiates `veyraCanonicalStageRingLaws`; an isolated p-specific source applies it. The 45-row ledger closes at `Quot.sound`, `propext`. This establishes one carrier only relative to that exact doctrine/ledger, not a categorical inverse limit, mathlib equivalence, topology/field, generic completion, productive-to-family rule, physical infinity, or foundation-independent actuality. See doc 152.
## DEF-584–585 / THM-P3N1-001–003 — Direct integer residue family — `VeyraPadicFamilyIntroduction.lean` defines `F_z(n)=z mod p^(n+1)` and proves total coordinates, all reductions, and one compatible family under the exact 20/32 ledger; no process bridge, carrier, promotion, or absolute infinity follows.
## DEF-586–612 — Finite compositional observer network — `observer_network*` replays one exact five-node/seven-edge P1-bound network with identities, pullback composition, finite paths, associativity, triangles, one two-map isomorphism, separators, and strict-cycle rejection; no N2, universal order, ontic identity, or promotion follows.
## DEF-613–635 / THM-P3A1B-001–004 — Exact prime-power productive bridge
`VeyraPrimePowerProductiveBridge.lean` proves totality and determinism of the single closed `G_z(n)=z mod p^(n+1)`, derives process coherence independently of N1, then proves exact all-depth commutation with direct `F_z`. Its 27-row/53-edge ledger and total/coherent offset counterpressure add no arbitrary productive conversion, choice/DC/coinduction/König route, carrier realization, promotion, or unrestricted infinity.
## DEF-636–657 / THM-P3C2-001–003 — Exact finite generated transport coherence
`VeyraTransportCoherence.lean` derives global commuting fillers from strict rank, total setoid maps, and complete local squares; separate `NatOp` identity/composition theorems are only symbolic reduction algebra. `CofinalBoundaryReconciliation` is a C2.2 consequence, not a 3-cell. No higher C2.3, N2 bridge, path equality, Church–Rosser, absolute identity, objecthood, or promotion follows.
## DEF-658–682 / THM-P3N2-001–007 — Prime-power reduction observer network
`prime_power_reduction_network*` binds exact arithmetic-derived finite reduction maps and strict integer-family separators to a captured symbolic thin `Natᵒᵖ` theory. `VeyraPrimePowerReductionNetwork.lean` proves reduction identity and composition, comparison-proof witness independence, equality of all canonical same-endpoint finite paths, the compatible-family observer square, and the two separator equations. The 37-row/54-edge ledger closes at `Classical.choice`, `propext`, and `Quot.sound`. No completion judgment, final PPCP theorem, C2 premise, inverse translation, generic observer network, ontic/objective identity, or promotion follows.
## DEF-683–704 / THM-P3N3-001–002 / THM-P3N4-001 — Exact local realization and scoped equality
N3 realizes the exact N1 family in the exact PΩ2 carrier and proves every coordinate. N4 consumes an independently sourced all-depth premise plus PΩ2 joint separation and derives only ledger-relative scoped carrier equality. The Lean sources, public aliases, focused functional/adversarial/formal/public tests, and the release-bundle certificate are present in this publication; status is **FORMALLY_PROVED + PUBLICLY_VALIDATED**. This does not establish generic completion, topology, absolute identity, N5 adoption, or physical/foundation-independent infinity.
## DEF-705–709 — Relative P1→R16 observer realization
`RealizationContext` binds one external finite state-to-recurrence scope plus
explicit totalization, cost, and join-closure policies; structured replay rows
retain exact R11 `Ready|Blocked` payloads; normalized partitions and
minimum-generator provenance derive one bounded R16 bottom/join completion;
the ordered first representative records only a context-local section; and the
terminal witness is accepted only after authoritative full R11 replay and exact
R16 reconstruction. This is level-1 executable evidence, not a canonical map,
echo embedding, functor, natural transformation, quotient transport, ready-only
image theorem, Lean result, authentication, or promotion. See doc 161.
## DEF-710–716 — Comparative bridge and finite G4 quotient-conflict classification
The separate structural ledger assigns only `KNOWN_ANALOGUE`,
`CANDIDATE_BRIDGE`, `REDUCED`, or `OPEN` to bridges and only
`CANDIDATE_SEPARATION`, `STRICTLY_SEPARATED`, or `OPEN` to explicit predicate
separations. `CB-G4-001` reduces one declared finite G4 exact-gluing existence
problem to matching-family amalgamation for the set-valued presheaf
`V ↦ EqRel(V)`. Conditional on existence, `Q=U/E*` carries the conflict graph;
exact gluings correspond to conflict-independent partitions of `Q`, and
uniqueness is equivalent to completeness. `SEP-G4-001` separates existence
from uniqueness by disjoint singletons. This is executable/finite and uses two
digest-bound nonpromoted Lean helpers; no new registered theorem card, general
sheaf/descent/topology result, novelty, nonexpressibility, or superiority follows.
See doc 162.
## THM-P3N6W-001–004 — Prime-power uniform late distinction — internal research candidate
`VeyraPrimePowerInformation.lean` constructively packages, for each requested `k`, the zero/`p^(k+1)` carrier pair agreeing through `k` and separating at `k+1`. The four Lean declarations are checked formal source results, but this publication contains no release-bundle certificate or public export for the family. Status is **INTERNAL_RESEARCH_CANDIDATE**, not a released registry theorem. It establishes neither ΩN completed indexing, `InformationUnbounded`, cardinality nor uncountability.
