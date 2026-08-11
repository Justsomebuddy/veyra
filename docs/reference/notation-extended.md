# Extended Notation Registry

Part of the public [Notation Registry](../../NOTATION.md).

## Transformer, completion, geometry, and finite-statistics notation

The following table groups the stable notation introduced by `DEF-059` through
`DEF-115`. Every symbol remains tied to its public registry definition.

| Symbol | Meaning | Registry |
|---|---|---|
| `F,G`; `F∘G`; `F⁻¹`; `Fix(F)`; `Γ_O(F)` | mode transformers, composition, affine lift, fixed residues, and observer graph shadow | DEF-059–063 |
| `Q^n`; `F^n`; `root_n(Q)`; `log_B(Q)` | repeated ratio weave, transformer iterate, root attempt, and transition-count lift | DEF-064–067 |
| `I_n`; `J ⊑ I`; `width(I)`; `Tail_ε(x→L)`; `no-jump` | refinement interval, width, finite-tail certificate, and continuity seed | DEF-068–071 |
| `Tremor(a,r,n)`; `Echo_ε(F,a,r,n)`; `DQ⁺`; `DQ±`; `Area_N` | sampled perturbation, no-jump certificate, drift quotients, and finite area braid | DEF-072–075 |
| `E`; `Corr`; `Sep²`; `Turn`; `Area△` | event, corridor, squared separation, orientation, and triangle area echoes | DEF-076–080 |
| `≅`; `Sig△`; `Shell`; `Par`; `E'=M·E+b` | corridor congruence, triangle signature, shell, parallel drift, and plane relabeling | DEF-081–085 |
| `Card(φ)`; `Dot`; `Pyth`; `Corr∩Shell`; `Relabel₂∘Relabel₁` | finite geometry theorem-card forms | DEF-086–090 |
| `Spec(T)`; `T→DEF-k`; `Check`; `Ω_T`; `SageHook(T)` | theorem specification, dependency, validation, obstruction, and executable hook | DEF-091–095 |
| `Card(Ax+B=Cx+D)`; `Card(P≡Q)`; `Card(Echo_ε)`; `Card(DQ_h stable)`; `Card(Area additivity)` | bounded algebra and analysis theorem cards | DEF-096–100 |
| `Node_C`; `C_i→C_j`; `Gap(C)`; `Cover(D)`; `SageRow(C,T)` | curriculum nodes, dependencies, gaps, coverage, and export rows | DEF-101–105 |
| `Phase(i mod n)`; `ChordEcho`; `P(E)`; `E[X]`; `mean`; `var`; `Σ(x_i-mean)=0` | finite trigonometric, probability, and statistics shadows | DEF-106–115 |

## Depth-pack/Sage-export notation

| Symbol | Meaning | Status |
|---|---|---|
| `n!_V` | factorial count echo | DEF-116 |
| `C_V(n,k)` | binomial count echo | DEF-116 |
| `C_V(n,k)=C_V(n,n-k)` | binomial symmetry card; `THM_B001` covers only `C_V(6,2)=C_V(6,4)=15` | DEF-117 / `THM_B001_binomial_symmetry_6_2` |
| `P(A∪B)` | probability union card; `THM_P002` covers only the canonical four-outcome count fixture | DEF-118 / `THM_P002_probability_union_counts` |
| `A ⟂ B` | finite independence card; `THM_P003` covers only the canonical four-outcome count product | DEF-119 / `THM_P003_probability_independence_counts` |
| `Var(S+c)=Var(S)` | variance-shift card; `THM_S002` covers only numerator equality/values `8` for `(1,3,5)` and `(11,13,15)` | DEF-120 / `THM_S002_variance_shift_1_3_5_plus_10` |
| `G002..G005`; `A004..A006`; `C002` | closed geometry wave; fixed five-point double map, three square drifts, midpoint sums; fixed mod-12 chord mirror | `THM_G002..G005` / `THM_A004_sampled_continuity_double_0_five_points` / `THM_A005_square_symmetric_drift_3_steps_1_2_3` / `THM_A006_identity_midpoint_area_4_4_8` / `THM_C002_chord_symmetry_12_0_3_9` |
| `SageExportRow` | registry/curriculum export row | DEF-121 |

## Sage school-core facade notation
| Symbol | Meaning | Status |
|---|---|---|
| `VeyraSchoolCore()` | Sage-facing facade over theorem/curriculum registries | DEF-124 |
| `Spec_S(T)` | wrapped theorem spec with dependencies and Sage hook | DEF-122 |
| `Node_S(C)` | wrapped curriculum concept with coverage status | DEF-123 |
| `ExportRow_S.as_dict()` | JSON-ready theorem/curriculum bridge row | DEF-125 |

## Sage proof graph notation
| Symbol | Meaning | Status |
|---|---|---|
| `Proof_S(T)` | theorem spec promoted to a checkable proof object | DEF-126 |
| `Check_S(T,card)` | proof-check result for an executable theorem card | DEF-127 |
| `Dep(T)` | definition dependencies of theorem `T` | DEF-128 |
| `Use(D)` | theorem IDs that depend on definition `D` | DEF-128 |
| `Path(C₀,C₁)` | shortest curriculum path between concept nodes | DEF-128 |

## Sage notebook export notation
| Symbol | Meaning | Status |
|---|---|---|
| `Cell_MD(s)` | markdown notebook cell | DEF-129 |
| `Cell_PY(s)` | executable Python/Sage code cell | DEF-129 |
| `Notebook_V` | generated Veyra lab notebook artifact | DEF-130 |
| `Notebook_V → md/ipynb` | markdown or nbformat rendering | DEF-130 |

## Sage domain notebook notation
| Symbol | Meaning | Status |
|---|---|---|
| `Dom_V` | available Sage-hook theorem domains | DEF-131 |
| `Spec_N(d)` | notebook descriptor for domain `d` | DEF-131 |
| `Notebook_V(d)` | generated domain theorem notebook | DEF-132 |
| `{Notebook_V(d)}` | all generated domain notebooks | DEF-132 |
## Sage executable card notation
| Symbol | Meaning | Status |
|---|---|---|
| `Ex(T)` | executable theorem-card example for theorem `T` | DEF-133 |
| `Run(Ex(T))` | proof check produced by running example `T` | DEF-133 |
| `Σ_card` | executable card coverage summary | DEF-134 |
| `Notebook_card(d)` | domain notebook that runs theorem-card examples | DEF-135 |

## Sage refutation notebook notation
| Symbol | Meaning | Status |
|---|---|---|
| `Ref(T)` | intentional failing theorem-card example | DEF-136 |
| `Mut(T)` | deliberately corrupted theorem-card boundary test | DEF-137 |
| `Run(Ref(T))` | blocked proof check for a bad card | DEF-136 |
| `Σ_ref` | refutation coverage summary | DEF-136 |
| `Notebook_ref(d)` | domain notebook that asserts blocked checks | DEF-138 |
## Sage refutation search notation
| Symbol | Meaning | Status |
|---|---|---|
| `Cand(p)` | parameterized theorem-card candidate | DEF-139 |
| `Hit(p)` | blocked candidate with obstruction evidence | DEF-140 |
| `Search(d)` | finite refutation search over domain `d` | DEF-141 |
| `Σ_search` | tried/blocked/domain search summary | DEF-141 |
| `Notebook_search(d)` | domain notebook that runs the search | DEF-141 |
## Core Language, native resonance, and translation notation
| Symbol | Meaning | Status |
|---|---|---|
| `expr/Kind/Infer/NF/Shadow` | compact Core Language parse/type/inference/normal/shadow stack | DEF-142–149 |
| `Traceᵖ(src)` / `Σᵖ` | source-spanned proof trace and summary | DEF-157–158 |
| `Caseᶠ`, `Σᶠ`, `Coverageᶠ` | mutation/fuzz/coverage language pressure | DEF-159–174 |
| `[w]_cyc` / `Orb_cyc(w)` | internal cycle echo / full rotation orbit | DEF-177 |
| `Prim_ord(n)`, `Prim_cyc(n)` | ordered primitive count and cyclic primitive echo count | DEF-178 |
| `PhasePrim(p,W)` | phase resonance enriched by primitive/exponent facts | DEF-179 |
| `Rank_spec`, `Rank_comp` | spectrum rank and compression rank comparison | DEF-180 |
| `AuraEcho(x)` | structured tact aura echo before string shadow | DEF-181 |
| `EditRes(p,W,e)` | cyclic edit-drift resonance profile | DEF-184 |
| `Treeκ(W)` | hierarchical compression tree | DEF-185 |
| `RootHit(P,r)` | native polynomial factor/root hit | DEF-186 |
| `CostCmp` | uniform/manual/aura cost comparison | DEF-187 |
| `RuleCov/DomainCov/ModelNote/ExportStable` | proof-discipline coverage, shadow, model, and stable-export rows | DEF-189–193 |
| `API_S/Boundary_V/TopicRow/Gap_school/Lin_a(P)/CalcCard/Trig_V/Trig_S/Mat_V/LA_S/Eig_V/InferStat/Stat_S/Series_T/Env_T/Cauchy_T/Major_T/Nest_T/Radius_T/PhaseEq_T/InvPhase_T/Conc_T/BernLike_T/DecisionErr_T` | Sage public API, curriculum rows, seed facades, finite transcendental envelopes, convergence/phase guards, and statistics concentration/likelihood/error rows | DEF-197–242 |
| `Surp(W)` / `BlindSig(W)` / `SepS1` / `AuditS2` / `SearchS3` / `XorS4` / `KWiseS5` / `DbS6` / `MagicM1` | observer-gap surprise witness, baseline signature, separation/audit/search/correlation rows | DEF-194–196 / DEF-311–314 |
| `Gap_surprise` | hidden saving minus surface saving | DEF-195 |
| `SemShadow_X1` / `ReqKeys(D)` / `Counter_D` / `DomainCert(D)` | seven-domain semantic-shadow certificate bundle: required keys, blocked counterexample, and declared-shadow acceptance | DEF-243–246 |
| `Div_cyc(P,W)` / `PrimeObs(W)` / `RankFactor(W,P)` | X2 native number-theory rows: cycle lift divisibility, resonance-prime obstruction, and spectrum/compression/factor comparison | DEF-247–250 |
| `Obj_V`, `Mor_V`, `Inv_V`, `UnivShadow_V` | X3 finite object, morphism, invariant, and bounded universal-shadow rows | DEF-251–254 |
| `0ᴵ_V`, `1ᴵ_V`, `⊕ᴵ`, `⊗ᴵ`, `÷ᴵ`; `Receipt(src)`, `AxClosure`; `ObsTerm(G)`, `Fit_T`, `Hold_H`; `B_prop ⊊ B_parity` | anchored intrinsic zero/one, stitch/weave/division; single-root replayable witness graph and derived axioms; protocol-bound train-only fit and payload-disjoint fixed-winner holdout; executable scoped proper-marginal/parity class inclusion | DEF-319–323 / THM-R3-001–002 / THM-R4-001–007 / THM-R6-001–002 |
| `Γ;Δ ⊢ p:P`; `#P`; `Bind_R7`; `Contract_R8(L)` / `Verified_R8(L)` | typed R7 judgment/artifact/binding; exact promotion contract and independently rehashed evidence | DEF-324–330 / THM-R7-001–004 / PROP-R8-001 |
| `Enc₉` / `Dec₉`; `Modeᴵ`; `≃ᴵ₉`; `Src₁₀`; `AST₁₀`; `Supp₁₀`; `Bind_R10` | R9 fixed image codec/equivalence; R10 source/AST, used-support, and 37-source/10-stage source/object/runtime-continuity binding | DEF-331–339 / THM-R9-001–008 / THM-R10-001–005 |
| `Obs₁₁ ::= input \| tail(Obs₁₁) \| crest(Obs₁₁) \| pair(Obs₁₁,Obs₁₁)`; `Ready/Blocked`; `Echo/Mismatch/DomainBlocked`; `Bind_R11` | closed typed observer AST, branded partial responses/ordered obstructions, three-way echo result, and 34-input/9-stage R10-bound artifact; echo is not equality | DEF-340–347 / THM-R11-001–006 |
| `Cap(B)` / `Dir(B)`; `EvClass/EvScope`; `Brand_O(v)` | R12 atomic bridge capabilities and derived direction; disjoint evidence origin/scope; observer/source/kind/payload-bound R11 observation | DEF-379–385 |
| `Anchorᴵᴿ`; `Tactᴵᴿ`; `Recᴵᴿ`; `Readyᴵᴿ/Blockedᴵᴿ`; `Echoᴵᴿ/Mismatchᴵᴿ/DomainBlockedᴵᴿ`; `Lower₁₂·₃`; `Receipt₁₂·₃`; `VAMI₁(x)` / `Run_VAMI(x)`; `Bind_R12·5` | R12.2 exact-image sidecar, R12.3 finite replay, R12.4 raw-IR framing/runtime, and R12.5 valid-image Lean preservation; no receipt authority or promotion evidence | DEF-386–409 / THM-R12-001–009 |
| `Δ(p)`; `F♯q`; `D_F(q)`; `R_F(q)`; `S_{F,G}(q)`; `Cr_O(x,y)`; `CB_O(γ)` | R16 distinction relation, ambient pullback, target-doctrine-bound greatest admitted descent (`q in O_Y`), typed residual, compositional synergy, minimal crest, and ordered crest braid | DEF-414–425 / THM-R16-001–003 |
| `Sig_deg(G)`; `LE(G)` | S7 declared degree-factor signature and exact labelled topological-order count | DEF-426–430 / THM-S7-001 |
| `⊗Q`; `Born(ψ)`; `U†`; `Unitary(U)` | exact finite tensor, Born-weight ledger, adjoint, and two-sided matrix witness | DEF-431–436 / THM-Q11-001–004 |
| `DECLARE_FORALL`; `Spec∀`; `OptSkel`; `EmitVAMD?` | open VAM quantified schema/specialization, optimizer obligation skeleton, and fail-closed emission policy | DEF-437–445 |
| `BestLower_A(c)`; `ReductionR16`; `BalMean(1,3,5)` | best admitted lower relation/R16 audit; fixed `(1,3,5)` mean balance | DEF-446 / `THM_S001_mean_balance_1_3_5` |
| `P_i`; `E_i`; `E*`; `Obs_G4` | finite observer patch, local partition echo, generated equivalence closure, and within-patch contradiction set | DEF-447–453 / THM-G4-001–003 |
| `Π_n`; `ρ_m^n`; `Stream(Π)`; `R_{p,k}`; `π_k`; `Obs_I1` | all-depth prefix views/restriction/recovered stream; finite prime-power residue shadows/projection/obstruction | DEF-454–461 / THM-I1-001–004 |
| `x ~_O y`; `O_f ≼_S O_c`; `Class_S(f,c)`; `Tri_τ`; `Loss_S` | finite observer echo relation, preservation order, exact-scope classifier, response triangle, and structural-loss status | DEF-462–468 |
| `CP_D2`; `Insuff_D2`; `CModel_D2`; `X_n={k∈N | n≤k}` | five-inference counterpressure catalog, disjoint insufficiency/countermodel outcomes, and shrinking natural tails | DEF-469–482 / THM-D2-001–005 |
| `Hist_C2`; `Cat_C2`; `Conf_C2` | declared path/identity history, exact finite requirement catalog, and separate local/global finite confluence statuses | DEF-483–496 |
| `F_D3[n]`; `ρ_m^n`; `≈family`; `AFIP_D3`; `Ledger_D3` | periodic all-depth coordinate, prefix restriction, coordinatewise family equivalence, ledger-relative introduction, and exact assumption closure | DEF-497–515 / THM-D3-001–011 |
| `Bridge_C3`; `τ_C3`; `Cell_C3` | exact byte-and-kind P0/P1-A bridge, asymmetric every-occurrence response translation, and one finite typed translated cell | DEF-516 |
| `Prefix_A(n)`; `Fam_A`; `Stream(A)`; `ρ_n`; `diag`; `SCP(A)`; `Ledger_Ω1` | finite prefixes, compatible all-depth families, stream carrier, restriction/diagonal realization, exact completion rule, and assumption ledger | DEF-517–531 / THM-POMEGA1-001–015 |
| `J=(kind,status,provenance,indices)`; `Reg_P2S`; `PremProj_r,p`; `IndexProj_k,i`; `Audit_P2S`; `Cast_P2S` | typed claim descriptor, fixed status/rule registry, named premise/index projections, five-schema meta-audit, and adjacent-cast rejection matrix | DEF-532–539 |
| `SFP(D,S)`; `Present_S`; `G4_S`; `Survive_R` | exact finite scoped-formation rule/presentation, response-derived ternary gluing, and genuine direct/translated refinement survival | DEF-540–552 |
| `Past_H(b)`; `Future_H(b)`; `HAP(H,b,M,S,D)`; `Token_H(b)` | strict parent-derived causal cuts, finite history-relative actualization, and separated birth/token/history/judgment identity | DEF-553–566 |
| `M_n=p^(n+1)`; `ZMod(M_n)`; `ρ_m^n`; `ZpVeyra(p)`; `PPCP_p`; `Ledger_Ω2` | prime-power stages, canonical remainder reductions, literal compatible-family subtype, exact completion bundle, and exposed foundation ledger | DEF-567–583 / THM-POMEGA2-001–017 |
| `realize(F_z)`; `rho_n(x)`; `x≈_{p,D}y` | exact N1-family realization, all projections, and scoped carrier equality relative to N1/PΩ2/N3/N4 ledgers | DEF-683–704 / THM-P3N3-001–002 / THM-P3N4-001 |
| `OAP`; `TTRP`; `(s_ab,t_ab)`; `SCAP`; `PSP`; `AAP`; `RCPΩ`; `completed-carrier-in(P.digest)`; `CompletedInfinity(P,J)` | docs-154 umbrella contracts and schematic typed source/response transport; exact relative carrier identity; stronger unbounded-depth completed indexing (not cardinal infinitude); no acceptance of task-local P3-TG notation or automatic promotion | docs 154 / ΩG design |
| `W_p(k)`; `VeyraPrimePowerLateWitness(hp,k)` | canonical zero/`p^(k+1)` pair agreeing through `k` and separating at `k+1`; constructive Lean-metalanguage witness only | THM-P3N6W-001–004 |
## P2-S status/promotion notation
| Form | Meaning | Strength |
|---|---|---|
| `J=(kind,status,provenance,indices)` | a typed claim descriptor whose status and provenance must be admitted by its exact kind domain | definition only |
| `EXECUTABLE_REPLAY` / `FORMALLY_DERIVED` | distinct positive provenance classes; execution is never silently cast into formal derivation | no promotion |
| `Reg_P2S` | literal-oracle-bound registry of 15 kind domains, 17 rules, 40 premise projections, and one index projection | closed metadata |
| `x →_R y`; `x →*_R y`; `TLGC(R,ρ)` | one continuation, its finite reflexive-transitive path, and strict-rank local-to-generated confluence relative to exact system `R` | THM-P3C1-001 |
| `PremProj_r,p(J)` | the allowlisted projection of named premise `p` for rule `r`, preserving the exact validated artifact | meta-operation |
| `IndexProj_k,i(J)` | the sole allowlisted existential hiding of named index `i`, retaining the declared remaining bindings | meta-operation |
| `Audit_P2S(J)=SCHEMA_CONFORMANT` | the request conforms to a declared rule/schema under its explicit assumption DAG | not ontological establishment |
| `Cast_P2S(a,b)=REJECTED` | an adjacent status/provenance cast has no matching rule | obstruction only |
| `ontology(Audit_P2S)=NOT_CLAIMED` | schema validation does not establish an object, theorem, axiom, or infinity | permanent boundary |
