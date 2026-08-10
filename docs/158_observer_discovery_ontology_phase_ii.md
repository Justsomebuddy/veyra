# 158 — Observer Discovery Ontology, Phase II

**Status:** philosophical and candidate design note.  
**Claim class:** definitions, engineering boundaries, and bounded experimental
proposals only.  
**Theorem status:** no theorem is stated or proved here.  
**Depends on:** P0 positive ontology, P1 constructive observer doctrine, P2
philosophical kernel, M1 observer synthesis, R5 bounded synthesis, and the R14
trusted-calculus boundary.

## 1. Purpose and present tension

**[Repository status]** M1 describes the current research candidate as finding
an observer under which an object becomes simple, explanatory, or blocked.
R5 makes part of that idea executable by searching a finite typed grammar,
selecting on training cases, locking the winner, and evaluating it on a
payload-disjoint holdout.

**[Repository status]** P0 and P2 do not treat an arbitrary supplied value as an
observer-independent object. They distinguish representation, observation,
witnessed support, coherent presentation, and scoped object formation. They
also treat observerhood as a doctrine-relative role rather than as an arbitrary
callable.

**[Repository status]** R5 accepts typed Python evaluators whose executable
identity is bound into the protocol. Such evaluators are useful research
shadows, but their successful execution does not establish ontic observerhood.
R14 draws a stricter trust boundary around canonical R11 observer syntax and
explicitly refuses to treat the permissive R5 surface as the trusted observer
calculus.

**[Philosophical diagnosis]** The phrase “the object becomes simple” therefore
compresses several distinct judgments. The current executable result is more
precisely a low-cost observer program satisfying a finite task on declared
presentations. It is not yet an intrinsic simplicity result, an explanation, an
object-formation judgment, or a discovery of hidden substance.

**[Candidate Phase-II thesis]** Certified observer discovery should be defined
as a doctrine-scoped epistemic event: a predeclared observer calculus yields a
replayable distinction or explanation that survives locked validation and
named counterpressure. The discovery concerns a relation among presentations
under a doctrine. It does not reveal what an observer-independent object is.

**[Candidate naming rule]** Until a final-set receipt has been independently
replayed and its provenance authenticated, public interfaces should prefer
“bounded association witness” or “audited evidence receipt.” The stronger
phrase “certified discovery” is a roadmap term, not a status silently granted
by the current `FOUND` token or by an unkeyed digest.

## 2. Ontological and epistemic chain

**[Candidate schema]** Phase II uses the following chain:

```text
source or phenomenon s                         optional and possibly external
  -- encoding under schema Sigma --> representation e
  -- admitted denotation ----------> presentation p = [e]_Sigma
  -- coupling with observer o ------> typed response, silence, or obstruction
  -- replay and validation ---------> discovery witness W
  -- separate P1/SFP obligations ---> scoped object formation, if supplied
```

**[Philosophical boundary]** The discovery engine ends at the witness. It does
not turn a file, table, graph, trace, or successful response into a scoped
object. Object formation remains a separate constructive judgment requiring
its own doctrine, provenance, persistence, coherence, confluence, refinement,
and formation evidence.

**[Philosophical boundary]** The source may be unavailable or may not possess a
canonical observer-independent description. Phase II therefore reports what
was established about the admitted presentation, not what the source “really
is.”

## 3. Exact Phase-II definitions

### 3.1 Representation

**[Definition OD-D01]** A **representation** is a finite record

```text
e = (schema, canonical_payload, provenance, representation_scope).
```

The schema declares types, ordering rules, units, missing-value treatment,
canonicalization, and any known information loss. The payload is the exact
finite input committed by the protocol. Provenance records where the payload
and schema came from to the extent available.

**[Non-claim]** A representation is not identical to its source, and a digest
of a representation does not prove that the encoding preserved every
source-level distinction.

### 3.2 Presentation

**[Definition OD-D02]** A **presentation** is a representation admitted to a
declared semantic domain:

```text
p = Presented_D(e).
```

Admission establishes that the schema and payload are well formed for the
declared operations. It does not establish objecthood, constructibility,
persistence, or observer-independent identity.

**[Philosophical boundary]** Byte identity, presentation identity, and echo
under an observer are separate metalanguage and object-language judgments.

### 3.3 Observer candidate and observer status

**[Definition OD-D03]** An **observer candidate** is a finite canonical typed
program `o` drawn from a versioned grammar `G` with declared input domain,
response kind, semantics, cost, and resource limits.

**[Definition OD-D04]** Phase II distinguishes three observer statuses:

1. `RESEARCH_SHADOW` — a typed deterministic evaluator usable for bounded
   experiments, including the current R5 callable surface;
2. `FORMALLY_ADMITTED` — a canonical observer program satisfying the syntax,
   typing, domain, semantics, resource, and provenance obligations of doctrine
   `D`;
3. `ONTIC_OBSERVER_ROLE` — a persistent discriminating process admitted through
   a separate observer-emergence principle.

**[Philosophical boundary]** Search may select among previously admitted
observer candidates because of their task performance. Search performance may
not retroactively establish primitive admission or ontic observerhood.

### 3.4 Observer response

**[Definition OD-D05]** Observation is a typed coupling result:

```text
Obs_D(o, p) in {
  Ready(response),
  ResponseSilent(mark),
  DomainBlocked(detail),
  Obstructed(detail),
  ResourceLimited(limit)
}.
```

**[Definition OD-D06]** For ready observations only:

```text
Echo_D,o(p, q)  iff  Obs_D(o,p) = Ready(r) and Obs_D(o,q) = Ready(r)
Rez_D,o(p, q)   iff  Obs_D(o,p) = Ready(rp), Obs_D(o,q) = Ready(rq), rp != rq
```

The displayed equalities are metalanguage checks over canonical typed
responses. They do not assert primitive object identity.

**[Epistemic rule]** Blockage, evaluator failure, resource exhaustion, and
unperformed observation do not count as echo, rez, baseline blindness, or
negative evidence.

### 3.5 Discovery doctrine

**[Definition OD-D07]** A Phase-II discovery doctrine is the versioned tuple

```text
D_disc = (Sigma, G, A, C, B, T, R, V)
```

where:

- `Sigma` is the representation and canonicalization schema;
- `G` is the admitted observer grammar and primitive registry;
- `A` is the typed evaluation semantics;
- `C` is the observer, response, residual, and resource cost contract;
- `B` is the named baseline family;
- `T` is the task and adequacy rule;
- `R` is the train/validation/test, transformation, and refinement protocol;
- `V` is the certificate decision rule.

**[Candidate governance rule]** The doctrine must be committed before the
locked test evidence is observed. A digest establishes content immutability;
historical target independence additionally requires provenance such as prior
registration or a target-blind construction protocol.

### 3.6 Relational simplicity

**[Definition OD-D08]** Simplicity is relative to a doctrine `D`, response
description language `L`, task `T`, observer `o`, and presentation `p`:

```text
K_{D,L,T}(o,p)
  = C_D(o)
  + DL_L(Obs_D(o,p))
  + Residual_T(p | Obs_D(o,p)).
```

- `C_D(o)` is the predeclared observer-program cost;
- `DL_L` is the description length of the ready response under a fixed code;
- `Residual_T` is the task-specific cost of what the response fails to
  reconstruct, predict, or constrain.

For a finite corpus `P`, the corpus cost is the predeclared aggregation of the
per-presentation terms plus any shared observer cost specified by `C`.

**[Definition OD-D09]** Relative to named baseline family `B`, the simplicity
gain is

```text
Gain_{D,L,T}(o,P;B)
  = min_{b in B} K_{D,L,T}(b,P) - K_{D,L,T}(o,P).
```

**[Philosophical boundary]** Positive gain means only that `o` is cheaper under
the declared code, task, corpus, and baseline family. It is not intrinsic
complexity, truth, beauty, causality, or universal optimality.

**[Repository boundary]** Current R5 scoring combines finite task fit with AST
cost. Until response description length and task residual are implemented, an
R5 winner may be called a low-cost finite-task separator, but not a compressed
or explanatory presentation.

### 3.7 Explanation threshold

**[Definition OD-D10]** A ready response crosses the **bounded explanation
threshold** only when all of the following hold under the committed doctrine:

1. the observer and decoder or predictor were fixed without locked-test access;
2. the response achieves the declared adequacy threshold on locked test data;
3. `Gain_{D,L,T}(o,P_test;B) >= delta` for a positive predeclared `delta`;
4. observer cost, response cost, residual cost, and failed cases are all charged;
5. named baselines receive the same information and resource contract;
6. the result survives every mandatory transformation or refinement in `R`;
7. no semantic obstruction was reclassified as evidence.

**[Candidate interpretation]** Explanation here means finite predictive,
reconstructive, or compressive adequacy under a declared task. Mere response
inequality is a distinction witness, not an explanation.

### 3.8 Witness

**[Definition OD-D11]** A **discovery witness** is a replayable finite package

```text
W = (
  doctrine_digest,
  schema_and_payload_digests,
  task_and_split_digests,
  observer_AST_and_semantics,
  selection_trace,
  train_validation_test_evidence,
  baseline_evidence,
  transformation_and_refinement_evidence,
  resource_receipts,
  obstructions,
  claim_boundary
).
```

**[Epistemic rule]** A witness supports only the exact finite judgment encoded
by its doctrine and evidence. Missing evidence remains open. A bound
counterexample may refute a bound claim. Neither state decides absolute
existence.

### 3.9 Discovery

**[Definition OD-D12]** `Discovery_D,S(o;P,B,T,W)` holds as a bounded epistemic
status only when:

1. `o` belongs to the precommitted grammar and has admissible executable
   semantics at the claimed observer-status level;
2. selection uses training evidence only;
3. the winner is frozen before validation and test evaluation;
4. all required test observations are ready and satisfy `T`;
5. baseline comparisons are ready, same-resource, and evaluated under `B`;
6. the claimed baseline gap or explanation threshold is met;
7. required representation transports and refinements pass;
8. `W` binds the complete replay surface and preserves all obstructions;
9. the published wording stays within the status tuple and nonclaims below.

**[Candidate interpretation]** What is discovered is a certified distinction,
compression, or predictive relation among presentations inside `D`. In the
first MVP, novelty means that search selected a composition not designated as a
baseline. It does not mean invention of a new primitive or historical
scientific priority.

## 4. Assumption ledger

The ledger separates adopted philosophical commitments, supplied semantic
assumptions, executable obligations, and still-open inference requirements.

| ID | Class | Assumption or commitment | Phase-II status | Downgrade if absent or false |
|---|---|---|---|---|
| `OD-A01` | philosophical | the engine observes admitted presentations, not observer-free substances | adopted boundary | prohibit object and essence claims |
| `OD-A02` | philosophical | R5 callables are research shadows, not ontic observers | adopted boundary | prohibit OEP or emergence claims |
| `OD-A03` | semantic | `Sigma` preserves the distinctions relevant to task `T` | supplied and scoped | representation-only result |
| `OD-A04` | admission | grammar primitives and their semantics were fixed independently of locked test evidence | provenance obligation | post-hoc fit, not certified discovery |
| `OD-A05` | task | labels, pair relations, decoder, and adequacy score express the declared question | supplied contract | execution transcript only |
| `OD-A06` | cost | `C`, `L`, residual aggregation, and `delta` are meaningful for the declared comparison | conventional and testable | separator claim only |
| `OD-A07` | execution | evaluators are typed and deterministic on the admitted domain | executable obligation | blocked/open, never blindness |
| `OD-A08` | split | train, validation, and test groups and payload components are disjoint | executable obligation | in-sample result only |
| `OD-A09` | sampling | locked test data support any claimed transfer population | external statistical assumption | exact finite-corpus claim only |
| `OD-A10` | baseline | `B` is the complete comparison class named in the wording | declared finite scope | prohibit all-method superiority claims |
| `OD-A11` | robustness | transformations and refinements in `R` preserve the intended subject matter | supplied semantic argument | cosmetic invariance only |
| `OD-A12` | inference | candidate search and repeated comparisons receive declared multiplicity control | future statistical obligation | no significance or population claim |
| `OD-A13` | QA | tests, digests, and receipts attest implementation replay rather than ontology | adopted boundary | prohibit theorem or object promotion |
| `OD-A14` | novelty | “found” means new in the bound search transcript unless independent priority evidence exists | adopted wording rule | prohibit scientific-novelty claim |

## 5. Orthogonal claim status

**[Definition OD-D13]** Phase II publishes a status tuple

```text
(execution_status, interpretation_status, ontology_status)
```

rather than one overloaded word such as `validated`.

### 5.1 Execution axis

`BLOCKED` is a terminal failure to enter or complete this axis; it is not an
`E0` achievement.

| Level | Meaning |
|---|---|
| `E-BLOCKED` | execution did not complete and licenses neither a positive witness nor a nonfinding |
| `E2 BOUNDED_SEARCH_COMPLETE` | the declared finite search completed, whether or not a candidate passed |
| `E3V LOCKED_HOLDOUT_PASSED` | the frozen train winner passed the discovery holdout without reranking |
| `E3T DECLARED_TEST_REPLICATED` | the same winner later passed one disjoint caller-declared third test without reranking |
| `E4 ROBUST_FINITE` | it also survives every mandatory bounded adversarial, transport, and refinement check |

### 5.2 Interpretation axis

`NONE` records that the report licenses no positive interpretation on this
axis; it is distinct from the finite separator level `I0`.

| Level | Meaning |
|---|---|
| `I0 SEPARATOR` | responses satisfy the declared finite distinction task |
| `I1 DECLARED_BASELINE_GAP` | named ready baselines remain blind or weaker under the same contract |
| `I2 BOUNDED_EXPLANATION` | the response crosses OD-D10's held-out net-gain and adequacy threshold |
| `I3 FORMAL_GENERAL_RESULT` | a separately stated mathematical proposition is proved over its exact carrier |

### 5.3 Ontology axis

| Level | Meaning |
|---|---|
| `O0 PRESENTATION_ONLY` | the result concerns supplied presentations and their responses |
| `O1 SCOPED_FORMATION` | a separate P1/SFP bundle licenses one doctrine-relative scoped object |

**[Philosophical rule]** These axes are orthogonal, not a total existence
ladder. A formal theorem does not automatically validate a real dataset. A
robust finite experiment does not establish objecthood. An O1 formation does
not make every interpretation of it true.

## 6. Current MVP classification

**[Repository classification]** The existing R5 parity synthesis is best
described as approximately

```text
(E3V LOCKED_HOLDOUT_PASSED, I1 DECLARED_BASELINE_GAP,
 O0 PRESENTATION_ONLY).
```

It selects a low-cost classical parity observer from a finite grammar, locks it,
and validates it on a different finite parity corpus against declared
proper-marginal baselines. It is not an I2 explanation or an O1 formation.

**[Candidate MVP target]** The first Phase-II data-analysis MVP should target

```text
(E4 ROBUST_FINITE, I1 DECLARED_BASELINE_GAP, O0 PRESENTATION_ONLY).
```

It should use a narrow canonical schema, a fixed small grammar, named baselines,
three-way data separation, representation-transport pressure, and a replayable
witness. I2 remains unavailable until a decoder or predictor, response code,
residual, and positive net-gain threshold are implemented.

## 7. Bounded conjectures and experiments

No item in this section is a theorem. Each conjecture is intentionally
falsifiable within a finite experimental contract.

### C-OD1 — Representation-transport stability

**[Bounded conjecture]** A structural observer gap will survive a precommitted
family of lossless representation transforms, through declared response
translations, more consistently than a gap caused by incidental encoding.

**[Experiment]** Use finite parity, k-wise, de Bruijn, topological, and matched
negative-control corpora. Select and lock the observer on canonical training
presentations. Test row permutations, coordinate or vertex relabellings, symbol
renamings, allowed bit complements, and canonical serialization changes. For
each transform `g`, predeclare a response transport `tau_g` and check

```text
Obs(o, g(p)) = tau_g(Obs(o,p))
```

together with preserved task success and baseline status.

**[Falsifier]** The conjectured instance fails if a required transport is
undefined, the translated response disagrees, the locked observer fails, or the
gap depends on raw names, ordering, or serialization.

**[Allowed conclusion]** Exact finite transport robustness for the tested
transform family only.

### C-OD2 — Observer-gap depth under baseline refinement

**[Candidate definition]** For a pair of presentations, define its bounded
observer-gap depth as the least cost or arity in a predeclared nested baseline
grammar at which a ready observer separates the pair. If none is found within
the exhausted grammar, report `not-found-within-budget`, never infinity or
impossibility.

**[Bounded conjecture]** Encoding artifacts tend to collapse under shallow
baseline refinement, while scaled structural families exhibit a reproducible
gap-depth profile across locked sizes or extensions.

**[Experiment]** Exhaust nested finite baseline classes for the S1 toy pair,
S4/S5 parity families, S6 de Bruijn rows, and S7 finite DAG extensions. Record
the first obstruction-free catcher and repeat the measurement on locked sizes
or isolated extensions.

**[Falsifier]** The conjectured instance fails if cheap admitted observers catch
all scaled rows, if the first-catcher depth changes under lossless transports,
or if apparent depth is produced by evaluator obstruction or an unspent budget.

**[Allowed conclusion]** A finite refinement-lifetime profile relative to the
exact nested grammar.

### C-OD3 — Observer cost and transfer

**[Bounded conjecture]** Among train-perfect candidates in one fixed admitted
grammar, lower predeclared observer cost is associated with lower failure on
locked unseen-size and adversarial cases.

**[Experiment]** Generate multiple independent finite parity-width, k-wise,
de-Bruijn-order, and DAG families. Enumerate every train-perfect AST, freeze the
ordering without test access, and evaluate all candidates on unseen sizes and
the C-OD1 transport suite. Compare failure rates by cost stratum with a
predeclared bootstrap or permutation analysis and multiplicity correction.

**[Falsifier]** The conjecture fails if the association is absent, unstable, or
reversed across the committed families.

**[Allowed conclusion]** Evidence for or against observer cost as a bounded
transfer prior. If falsified, AST cost remains only a deterministic tie-breaker
and must not be described as explanatory simplicity.

## 8. Roadmap ordering

**[Repository checkpoint]** The nonpromoting claim envelope and the logical
fixed-winner confirmation step are now executable. The latter accepts a third
caller-declared test set and forbids reranking, but it is not yet the canonical
schema, isolated evaluator, or atomic one-shot ledger required by steps 2–4.

**[Candidate engineering roadmap]** Phase II should proceed in this order so
that stronger infrastructure cannot silently outrun claim semantics:

1. **Claim semantics first.** Freeze OD-D01–OD-D13, status tuples, exact
   certificate language, obstruction handling, and nonclaims.
2. **Canonical schema and three-way data protocol.** Implement bounded
   representation types plus group- and component-disjoint train, validation,
   and locked test partitions. No automatic split may inspect candidate results.
3. **Typed DSL and isolation.** Replace unrestricted research callables at the
   certified boundary with a small canonical typed observer DSL, deterministic
   semantics, hard budgets, and isolated execution. R5 may remain an explicitly
   labelled exploratory frontend.
4. **One-shot commitment ledger.** Bind doctrine, schema, grammar, baselines,
   task, split manifests, limits, and candidate-selection transcript before the
   locked test is released. Distinguish content immutability from historical
   target independence.
5. **Statistical layer.** Add nested or group-aware resampling, uncertainty,
   permutation testing, multiplicity correction, perturbation stability, and
   explicit population assumptions. These support inference, not ontology.
6. **Signed replay package.** Produce a canonical portable witness with content
   digests, environment/toolchain identity, resource receipts, result status,
   obstructions, and signature verification. Signing establishes artifact
   provenance, not truth.
7. **Richer grammar only after the gates above.** Add mixed data, missingness,
   graph and transition observers, response translations, and explanation
   decoders incrementally. Every added primitive requires admission,
   counterpressure, cost, and baseline updates.

**[Candidate stop rule]** Failure at an earlier stage blocks promotion to later
claim levels. It does not prohibit exploratory execution under a clearly marked
research-shadow status.

## 9. Explicit nonclaims

This Phase-II ontology does **not** claim:

- a theorem, proof, new axiom, or theorem-registry promotion;
- observer-independent objects, identities, essences, or truth;
- physical emergence, consciousness, agency, or an ontic observer produced by
  software search;
- that an encoded dataset exhausts or faithfully represents its source;
- intrinsic, universal, or Kolmogorov complexity from a project-specific cost;
- explanation from separation alone;
- causality, mechanism, understanding, or semantic meaning from a predictive or
  compressive score alone;
- generalization beyond the exact finite corpus without a separate sampling and
  statistical argument;
- global minimality, optimality, grammar completeness, or impossibility from a
  bounded exhausted search;
- superiority over classical mathematics, statistics, machine learning, or any
  method outside the named baseline family;
- invention of a new primitive when search merely composes admitted primitives;
- historical scientific novelty from a local transcript or digest;
- that signing, hashing, isolation, tests, or receipts make a claim true;
- automatic P1/SFP object formation from an E4 or I2 result;
- that absence of a discovered observer means absence of structure.

**[Candidate closing formulation]** Certified observer discovery is the
practice of binding a finite observer switch to its representation, doctrine,
baselines, costs, validation, counterpressure, and obstructions so that the
result can be replayed without turning a scoped distinction into an unscoped
claim about being.
