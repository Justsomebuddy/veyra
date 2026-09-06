# The observer site: internal logic of echo (apartness, silence, stage-relative equality)

Status: 19 `FORMALLY_PROVED` Lean cards (`proofs/lean/VeyraObserverSite.lean`,
Mathlib-free, axioms `propext`/`Quot.sound` only, no classical choice) with an
`EXECUTABLE_EVIDENCE` twin (`src/core/observer_site.py`, certificate
`observer_site_os`). Not `PUBLICLY_VALIDATED`. Nothing here is a claim about
physical observers, observer formation, or the manifesto's generic observer.

## 1. What this document changes

`docs/00` anti-default 1 says: no primitive equality, use echo-equivalence.
`docs/06` DEF-015 defines `x ≈_T y` as agreement of every observer in the
test family `T`, and §4 notes that `≈_T` is an equivalence *if every observer
has ordinary equality in its response type*. Both statements were prose. This
document makes the third inversion executable and formal on a finite
*observer site*, and the formalization corrects the reading in one place:

> The primitive is not echo but **distinction** (P0's rez, `docs/149`).
> Echo is the *absence so far* of distinction; it is retractable. Internal
> equality relative to a site is "never distinguishable within the site".

Three consequences follow, each a theorem rather than a slogan: excluded
middle for equality fails at every incomplete stage; typed silence breaks
cotransitivity of apartness and hence transitivity of internal equality; and
primality (primitivity) is a monotone function on the lattice of stages.

## 2. Definitions

Let `X` be presentations and `R` response values. An **observer** is a partial
map `o : X → R ∪ {silent}` (`none` is typed silence, `docs/149` P0-O4). A
**stage** `T` is a finite family of admitted observers; a **site** is the
largest admitted stage, and its sub-families ordered by inclusion are its
stages (`docs/06` §5 refinement: `T ⊆ T'` means `T'` is finer).

- **DEF-761 — Apartness at a stage.** `Apart_T(x, y)` iff some `o ∈ T` is
  ready on both with different values. **Echo at a stage** (`DEF-015` made
  exact for partial observers): `Echo_T(x, y)` iff every `o ∈ T` is ready on
  both with the same value. **Silent**: neither.
- **DEF-762 — Internal equality relative to a site.**
  `IntEq_site(x, y) := ¬Apart_site(x, y)`.
- **DEF-763 — Forcing of decided equality.** Stage `T` of the site forces
  `x = y ∨ x # y` iff `IntEq_site(x, y) ∨ Apart_T(x, y)`. The **truth value**
  of a stage predicate `P` at `T` is the sieve of stages `T'` with
  `T ⊆ T' ⊆ site` and `P(T')`.
- **DEF-764 — Primitivity at a stage.** For words, `PrimeAt_T(x)` iff `x ≠ ε`
  and no literal power `u^k` (`k ≥ 2`, `u ≠ ε`) satisfies `Echo_T(x, u^k)`.

Host-carried computation (`README`, `docs/06` §3): values are compared by the
host `=`/`==`, stages are host lists/tuples, the metatheory is Lean over
`List`/`Option`.

## 3. Theorem cards

| Card | Statement |
|---|---|
| `THM_OS_001_apart_persists` | `T ⊆ T'` and `Apart_T(x,y)` imply `Apart_T'(x,y)`. |
| `THM_OS_002_echo_retracts` | `T ⊆ T'` and `Echo_T'(x,y)` imply `Echo_T(x,y)`. |
| `THM_OS_003_status_trichotomy` | echo / apart / silent is exhaustive and pairwise exclusive. |
| `THM_OS_004_total_no_silence` | total observers leave no silent pair. |
| `THM_OS_005_apart_irrefl_symm` | apartness is irreflexive and symmetric. |
| `THM_OS_006_cotransitive_of_total` | with total observers `Apart(x,z)` implies `Apart(x,y) ∨ Apart(y,z)`. |
| `THM_OS_007_silence_breaks_cotransitivity` | one observer silent on `1` gives `Apart(0,2)` with neither `Apart(0,1)` nor `Apart(1,2)` (finite countermodel). |
| `THM_OS_008_intEq_stable` | internal equality is never apart at any stage of the site. |
| `THM_OS_009_excluded_middle_fails` | at stage `{length}` of the site `{length, word}`, `ab` and `ba` echo, are not apart, are apart in the site, and neither `ab = ba` nor `ab # ba` is forced (finite countermodel). |
| `THM_OS_010_complete_stage_decides` | at the complete stage `Apart ∨ IntEq` holds. |
| `THM_OS_011_prime_monotone` | `T ⊆ T'` and `PrimeAt_T(x)` imply `PrimeAt_T'(x)`. |
| `THM_OS_012_prime_depends_on_stage` | `aba` is not primitive at `{length}` and is primitive at `{word}`. |
| `THM_OS_013_apart_sieve_upclosed` | the truth value of apartness is up-closed (a Kripke proposition). |
| `THM_OS_014_echo_not_kripke` | the truth value of echo for `ab`/`ba` is not up-closed. |
| `THM_OS_015_word_stage_prime_iff_primitive` | at `{word}`, stage-primitivity is literal primitivity (`Root.Primitive`, `docs/188`). |
| `THM_OS_016_length_stage_prime_iff_unit` | at `{length}`, only one-letter words are primitive. |
| `THM_OS_017_echo_is_per` | at every stage echo is symmetric and transitive, and reflexive exactly on readable presentations. |
| `THM_OS_018_silence_breaks_intEq_trans` | the countermodel of 007 makes internal equality non-transitive. |
| `THM_OS_019_intEq_equivalence_of_total` | with total observers internal equality is an equivalence relation. |

Cards 007 and 009 are finite countermodels checked by `decide`; 012 combines
015/016 with a hand proof that `aba` is not a literal power.

## 4. Reading

**Echo is not an internal proposition.** In a Kripke or presheaf semantics
over the poset of stages, a proposition is a persistent fact: once true it
stays true at every finer stage. Apartness is such a fact (001, 013). Echo is
not (002, 014): its truth value is down-closed. So `x ≈_T y` is not the
internal statement "`x = y`"; it is the status "not yet apart at `T`". The
internal equality is `IntEq_site`, "never apart within the site" (008), and
it coincides with echo only at the complete stage.

**Excluded middle fails at incomplete stages.** 009 is a Kripke countermodel
in the textbook sense: at `{length}` the pair `ab`/`ba` is neither internally
equal (the word observer will split it) nor apart (nothing admitted so far
splits it). At the complete stage the disjunction is decided (010), and
decidably so because the site is finite. The logic of echo-equality is
therefore intuitionistic in the exact, not the rhetorical, sense, and this is
the formal content of `docs/06` §5: "identity can become more detailed when
the universe admits stronger tests".

**Silence is not neutral.** With total observers apartness is a Brouwer
apartness (irreflexive, symmetric, cotransitive: 005, 006) and internal
equality is an equivalence (019). One silent observer breaks cotransitivity
(007) and therefore transitivity of internal equality (018): a reader bounded
at one letter never separates `a` from `ab`, nor `ab` from `b`, yet separates
`a` from `b`. The proviso of `docs/06` §4 is exactly this boundary. Echo
itself remains a partial equivalence relation at every stage, with domain the
readable presentations (017): the fibre of the presheaf of modes at `T` is the
quotient of the readable presentations by echo, and 002 is the restriction
map along refinement.

**Primality is a function on the stage lattice.** Finer stages see more
primitives (011); `aba` is the cube `a³` under the length observer and
primitive under the word observer (012). The length observer collapses
primitivity to the unit tact (016), so `docs/11`'s *numeric prime* is a
different notion (no non-unit factor of the shadow number), not the length
stage of primitivity. `THM_TR1_003` (coarse-primitive implies fine-primitive on
the doctrine lattice, `docs/179`) is an instance of 011 read on trace-class
stages.

Executable table on the standard site (`length ⊂ bag ⊂ cycle ⊂ word`):

| Word | `{length}` | `{bag}` | `{cycle}` | `{word}` |
|---|---|---|---|---|
| `a` | primitive | primitive | primitive | primitive |
| `ab` | `a²` | primitive | primitive | primitive |
| `aba` | `a³` | primitive | primitive | primitive |
| `baab` | `a⁴` | `(ab)²` | primitive | primitive |
| `abab` | `a⁴` | `(ab)²` | `(ab)²` | `(ab)²` |

## 5. Executable counterpart

`src/core/observer_site.py` replays every card on bounded sites (at most six
observers, 256 presentations): `apart`/`echo`/`pair_status`, `internal_equal`,
`forces_decided`, `site_law_report` (001–003 over the whole stage lattice),
`undecided_pairs` (009 witnesses with the splitting observers),
`cotransitivity_failures` (006/007), `echo_classes`/`restriction` (017/002),
`power_at`/`primitive_at`/`prime_table`/`prime_monotonicity_violations`
(011–016), the standard observers `LENGTH`, `BAG`, `CYCLE`, `WORD` and the
partial `bounded_reader(limit)`. `observer_site_checklist()` maps the 19
cards to their replay. Certificate `observer_site_os` (suite 112) checks the
laws on 16 stages and 225 pairs, the `ab`/`ba` split, the bounded-reader
countermodel, restriction totality and the primitivity table.

## 6. Claims and non-claims

- Claimed: the 19 cards as stated, on finite sites of partial observers over
  host lists; the executable replay on the standard site.
- Not claimed: anything about physical observers, generic observer formation,
  observer translation (`docs/149` §5.2), or the P1/R16 doctrines beyond the
  stated instance reading of `THM_TR1_003`; no topos-theoretic result
  ("Kripke"/"presheaf" are used in their elementary finite-poset sense; no
  subobject classifier or sheaf condition is constructed); no native
  (host-free) formulation; not `PUBLICLY_VALIDATED`.
- Continued: `docs/191` makes stitch, weave and resonance variable objects
  over the same site (arithmetic commutes with restriction, the natural
  numbers are the length fibre, laws as stage properties, AX-005 refuted for
  canonical-cut stitching of closed modes).
- Open: apartness under declared response translations; the doctrine lattices
  of `docs/179`–`184` as sites with a formal bridge to 011; obstruction
  *reasons* as a many-valued truth object beyond the three statuses; a native
  formulation on `Recurrence` (`docs/189`) instead of host lists.

## 7. Verification

```bash
python scripts/check_lean_sources.py --jobs 8        # 59/59
python scripts/check_research_lean.py               # 68/68
python -m pytest -q tests/test_observer_site.py tests/test_certify.py
```
