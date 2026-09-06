import VeyraPrimitiveRoot

set_option autoImplicit false

/-! # The observer site: apartness, echo, silence and stage-relative equality

Veyra's third inversion taken literally. A *stage* is a finite family of
admitted observers; an observer is partial (`none` is typed silence). The
positive primitive is distinction: `Apart T x y` holds when some admitted
observer is ready on both presentations with different values. Echo
(`Echo T x y`: every admitted observer ready on both with equal values) is the
defeasible negation of distinction and internal equality (`IntEq site x y`) is
"never apart within the site". A pair therefore carries a three-valued status
at every stage: echo, apart or silent.

Cards (all Mathlib-free; axioms `propext`/`Quot.sound` only, no choice):

* `THM_OS_001` distinctions persist under refinement, `THM_OS_002` echo
  retracts under refinement.
* `THM_OS_003` the three statuses are exhaustive and pairwise exclusive;
  `THM_OS_004` total observers leave no silent pair.
* `THM_OS_005` apartness is irreflexive and symmetric; `THM_OS_006` it is
  cotransitive for total observers; `THM_OS_007` one silent observer breaks
  cotransitivity (finite countermodel); `THM_OS_018` the same countermodel
  breaks transitivity of internal equality; `THM_OS_019` total observers make
  internal equality an equivalence.
* `THM_OS_008` internal equality is stable at every stage of the site.
* `THM_OS_009` excluded middle for equality fails at an incomplete stage: with
  the length observer alone `ab` and `ba` echo, the word observer separates
  them, so neither `ab = ba` nor `ab # ba` is forced at the coarse stage;
  `THM_OS_010` a complete finite stage decides equality.
* `THM_OS_013` the truth value of apartness is an up-closed sieve (a Kripke
  proposition); `THM_OS_014` the echo status is not (its sieve is not
  up-closed).
* `THM_OS_017` at every stage echo is a partial equivalence relation whose
  domain is the readable presentations (the presheaf of modes restricts along
  refinement by `THM_OS_002`).
* `THM_OS_011` primitivity relative to a stage is monotone under refinement;
  `THM_OS_015` under the word observer it is literal primitivity;
  `THM_OS_016` under the length observer only the unit tact is primitive;
  `THM_OS_012` the docs/11 word `aba` is composite at the length stage and
  primitive at the word stage.

Host-carried computation: stages are host lists and the metatheory is Lean.
Nothing here is a claim about physical observers, about the manifesto's
generic observer formation, or about anything outside the finite site. -/

namespace Veyra
namespace Site

variable {X R : Type}

/-- An observer answers with a ready value or stays silent. -/
abbrev Observer (X R : Type) := X → Option R
/-- A stage: the finite family of admitted observers. -/
abbrev Stage (X R : Type) := List (Observer X R)

/-- `T` is refined by `T'`: every observer admitted at `T` is still admitted. -/
def Refines (T T' : Stage X R) : Prop := ∀ o, o ∈ T → o ∈ T'
/-- One observer positively distinguishes two presentations. -/
def Distinguishes (o : Observer X R) (x y : X) : Prop :=
  ∃ r r', o x = some r ∧ o y = some r' ∧ r ≠ r'
/-- One observer echoes two presentations: ready on both with the same value. -/
def Echoes (o : Observer X R) (x y : X) : Prop := ∃ r, o x = some r ∧ o y = some r
/-- Apartness at a stage: some admitted observer distinguishes. -/
def Apart (T : Stage X R) (x y : X) : Prop := ∃ o, o ∈ T ∧ Distinguishes o x y
/-- Echo at a stage: every admitted observer echoes. -/
def Echo (T : Stage X R) (x y : X) : Prop := ∀ o, o ∈ T → Echoes o x y
/-- Silence at a stage: neither apart nor echoed. -/
def Silent (T : Stage X R) (x y : X) : Prop := ¬ Apart T x y ∧ ¬ Echo T x y
/-- Internal equality relative to a site: never apart within the site. -/
def IntEq (site : Stage X R) (x y : X) : Prop := ¬ Apart site x y
/-- A presentation every admitted observer is ready on. -/
def Readable (T : Stage X R) (x : X) : Prop := ∀ o, o ∈ T → ∃ r, o x = some r
/-- Every admitted observer is ready on every presentation. -/
def Total (T : Stage X R) : Prop := ∀ o, o ∈ T → ∀ z : X, Readable [o] z

-- theorem-card: distinctions persist under refinement
theorem THM_OS_001_apart_persists {T T' : Stage X R} {x y : X}
    (h : Refines T T') (ha : Apart T x y) : Apart T' x y := by
  obtain ⟨o, ho, hd⟩ := ha
  exact ⟨o, h o ho, hd⟩

-- theorem-card: echo retracts under refinement (finer stages echo less)
theorem THM_OS_002_echo_retracts {T T' : Stage X R} {x y : X}
    (h : Refines T T') (he : Echo T' x y) : Echo T x y :=
  fun o ho => he o (h o ho)

theorem not_echo_and_apart {T : Stage X R} {x y : X} (he : Echo T x y) (ha : Apart T x y) :
    False := by
  obtain ⟨o, ho, r, r', hr, hr', hne⟩ := ha
  obtain ⟨s, hs, hs'⟩ := he o ho
  rw [hr] at hs; rw [hr'] at hs'
  cases hs; cases hs'
  exact hne rfl

-- theorem-card: apartness is irreflexive and symmetric
theorem THM_OS_005_apart_irrefl_symm (T : Stage X R) (x y : X) :
    ¬ Apart T x x ∧ (Apart T x y → Apart T y x) := by
  constructor
  · rintro ⟨o, _, r, r', hr, hr', hne⟩
    rw [hr] at hr'; cases hr'; exact hne rfl
  · rintro ⟨o, ho, r, r', hr, hr', hne⟩
    exact ⟨o, ho, r', r, hr', hr, fun h => hne h.symm⟩

-- theorem-card: internal equality is never apart at any stage of the site
theorem THM_OS_008_intEq_stable {site T : Stage X R} {x y : X}
    (h : IntEq site x y) (hT : Refines T site) : ¬ Apart T x y :=
  fun ha => h (THM_OS_001_apart_persists hT ha)

/-- Kripke forcing of `x = y ∨ x # y` at stage `T` of the site. -/
def ForcesDecided (site T : Stage X R) (x y : X) : Prop := IntEq site x y ∨ Apart T x y

theorem not_decided_of_split {site T : Stage X R} {x y : X}
    (hna : ¬ Apart T x y) (hsite : Apart site x y) : ¬ ForcesDecided site T x y := by
  rintro (h | h)
  · exact h hsite
  · exact hna h

-- theorem-card: stage echo is a partial equivalence relation with domain the readable presentations
theorem THM_OS_017_echo_is_per (T : Stage X R) (x y z : X) :
    (Echo T x x ↔ Readable T x) ∧ (Echo T x y → Echo T y x) ∧
    (Echo T x y → Echo T y z → Echo T x z) := by
  refine ⟨⟨fun h o ho => ?_, fun h o ho => ?_⟩, fun h o ho => ?_, fun hxy hyz o ho => ?_⟩
  · obtain ⟨r, hr, _⟩ := h o ho; exact ⟨r, hr⟩
  · obtain ⟨r, hr⟩ := h o ho; exact ⟨r, hr, hr⟩
  · obtain ⟨r, hr, hr'⟩ := h o ho; exact ⟨r, hr', hr⟩
  · obtain ⟨r, hr, hr'⟩ := hxy o ho
    obtain ⟨s, hs, hs'⟩ := hyz o ho
    rw [hr'] at hs; cases hs
    exact ⟨r, hr, hs'⟩

/-- The stages between `T` and the site at which `P` holds: the truth value of `P` at `T`. -/
def Sieve (site T : Stage X R) (P : Stage X R → Prop) : Stage X R → Prop :=
  fun T' => Refines T T' ∧ Refines T' site ∧ P T'
/-- Up-closure within the site: what a Kripke truth value must satisfy. -/
def UpClosed (site : Stage X R) (S : Stage X R → Prop) : Prop :=
  ∀ T₁ T₂, S T₁ → Refines T₁ T₂ → Refines T₂ site → S T₂

theorem refines_trans {T₁ T₂ T₃ : Stage X R} (h₁ : Refines T₁ T₂) (h₂ : Refines T₂ T₃) :
    Refines T₁ T₃ := fun o ho => h₂ o (h₁ o ho)

-- theorem-card: the truth value of apartness is an up-closed sieve (a Kripke proposition)
theorem THM_OS_013_apart_sieve_upclosed (site T : Stage X R) (x y : X) :
    UpClosed site (Sieve site T fun T' => Apart T' x y) := by
  rintro T₁ T₂ ⟨h₁, _, ha⟩ h₁₂ h₂
  exact ⟨refines_trans h₁ h₁₂, h₂, THM_OS_001_apart_persists h₁₂ ha⟩

section Decision

variable [DecidableEq R]

/-- Boolean decision of one observer's distinction. -/
def distinguishesB (o : Observer X R) (x y : X) : Bool :=
  match o x, o y with
  | some r, some r' => decide (r ≠ r')
  | _, _ => false

/-- Boolean decision of one observer's echo. -/
def echoesB (o : Observer X R) (x y : X) : Bool :=
  match o x, o y with
  | some r, some r' => decide (r = r')
  | _, _ => false

theorem distinguishesB_iff (o : Observer X R) (x y : X) :
    distinguishesB o x y = true ↔ Distinguishes o x y := by
  unfold distinguishesB Distinguishes
  cases hx : o x with
  | none => simp
  | some r =>
      cases hy : o y with
      | none => simp
      | some r' =>
          simp only [decide_eq_true_iff]
          constructor
          · intro h; exact ⟨r, r', rfl, rfl, h⟩
          · rintro ⟨a, b, ha, hb, hab⟩
            cases ha; cases hb; exact hab

theorem echoesB_iff (o : Observer X R) (x y : X) : echoesB o x y = true ↔ Echoes o x y := by
  unfold echoesB Echoes
  cases hx : o x with
  | none => simp
  | some r =>
      cases hy : o y with
      | none => simp
      | some r' =>
          simp only [decide_eq_true_iff]
          constructor
          · intro h; exact ⟨r, rfl, by rw [h]⟩
          · rintro ⟨a, ha, hb⟩
            cases ha; cases hb; rfl

/-- Boolean apartness at a stage. -/
def apartB (T : Stage X R) (x y : X) : Bool := T.any fun o => distinguishesB o x y
/-- Boolean echo at a stage. -/
def echoB (T : Stage X R) (x y : X) : Bool := T.all fun o => echoesB o x y

theorem apartB_iff (T : Stage X R) (x y : X) : apartB T x y = true ↔ Apart T x y := by
  unfold apartB Apart
  rw [List.any_eq_true]
  constructor
  · rintro ⟨o, ho, h⟩; exact ⟨o, ho, (distinguishesB_iff o x y).mp h⟩
  · rintro ⟨o, ho, h⟩; exact ⟨o, ho, (distinguishesB_iff o x y).mpr h⟩

theorem echoB_iff (T : Stage X R) (x y : X) : echoB T x y = true ↔ Echo T x y := by
  unfold echoB Echo
  rw [List.all_eq_true]
  constructor
  · intro h o ho; exact (echoesB_iff o x y).mp (h o ho)
  · intro h o ho; exact (echoesB_iff o x y).mpr (h o ho)

instance (T : Stage X R) (x y : X) : Decidable (Apart T x y) :=
  decidable_of_iff _ (apartB_iff T x y)
instance (T : Stage X R) (x y : X) : Decidable (Echo T x y) :=
  decidable_of_iff _ (echoB_iff T x y)

-- theorem-card: the pair status is three-valued, exhaustive and exclusive
theorem THM_OS_003_status_trichotomy (T : Stage X R) (x y : X) :
    (Echo T x y ∨ Apart T x y ∨ Silent T x y) ∧
    ¬ (Echo T x y ∧ Apart T x y) ∧
    ¬ (Echo T x y ∧ Silent T x y) ∧ ¬ (Apart T x y ∧ Silent T x y) := by
  refine ⟨?_, fun h => not_echo_and_apart h.1 h.2, fun h => h.2.2 h.1, fun h => h.2.1 h.1⟩
  by_cases he : Echo T x y
  · exact Or.inl he
  · by_cases ha : Apart T x y
    · exact Or.inr (Or.inl ha)
    · exact Or.inr (Or.inr ⟨ha, he⟩)

-- theorem-card: total observers leave no silent pair
theorem THM_OS_004_total_no_silence {T : Stage X R} (ht : Total T) (x y : X) :
    ¬ Silent T x y := by
  rintro ⟨ha, he⟩
  apply he
  intro o ho
  obtain ⟨r, hr⟩ := ht o ho x o List.mem_cons_self
  obtain ⟨r', hr'⟩ := ht o ho y o List.mem_cons_self
  by_cases hrr : r = r'
  · exact ⟨r, hr, by rw [hr', hrr]⟩
  · exact absurd ⟨o, ho, r, r', hr, hr', hrr⟩ ha

-- theorem-card: with total observers apartness is cotransitive
theorem THM_OS_006_cotransitive_of_total {T : Stage X R} (ht : Total T) (x y z : X)
    (h : Apart T x z) : Apart T x y ∨ Apart T y z := by
  obtain ⟨o, ho, r, r'', hr, hr'', hne⟩ := h
  obtain ⟨r', hr'⟩ := ht o ho y o List.mem_cons_self
  by_cases h1 : r = r'
  · right
    refine ⟨o, ho, r', r'', hr', hr'', ?_⟩
    intro h2; exact hne (h1.trans h2)
  · left
    exact ⟨o, ho, r, r', hr, hr', h1⟩

-- theorem-card: a complete finite stage decides equality
theorem THM_OS_010_complete_stage_decides (site : Stage X R) (x y : X) :
    Apart site x y ∨ IntEq site x y := by
  by_cases h : Apart site x y
  · exact Or.inl h
  · exact Or.inr h

end Decision

/-- A partial observer: the identity, silent exactly on `1`. -/
def silentAtOne : Observer Nat Nat := fun n => if n = 1 then none else some n

-- theorem-card: one silent observer breaks cotransitivity (finite countermodel)
theorem THM_OS_007_silence_breaks_cotransitivity :
    Apart [silentAtOne] 0 2 ∧ ¬ Apart [silentAtOne] 0 1 ∧ ¬ Apart [silentAtOne] 1 2 := by
  refine ⟨(apartB_iff _ _ _).mp (by decide), ?_, ?_⟩
  · intro h; have := (apartB_iff [silentAtOne] 0 1).mpr h; revert this; decide
  · intro h; have := (apartB_iff [silentAtOne] 1 2).mpr h; revert this; decide

-- theorem-card: the same silent observer breaks transitivity of internal equality
theorem THM_OS_018_silence_breaks_intEq_trans :
    IntEq [silentAtOne] 0 1 ∧ IntEq [silentAtOne] 1 2 ∧ ¬ IntEq [silentAtOne] 0 2 := by
  obtain ⟨h02, h01, h12⟩ := THM_OS_007_silence_breaks_cotransitivity
  exact ⟨h01, h12, fun h => h h02⟩

-- theorem-card: with total observers internal equality is an equivalence relation
theorem THM_OS_019_intEq_equivalence_of_total [DecidableEq R] {site : Stage X R}
    (ht : Total site) (x y z : X) :
    IntEq site x x ∧ (IntEq site x y → IntEq site y x) ∧
    (IntEq site x y → IntEq site y z → IntEq site x z) := by
  refine ⟨(THM_OS_005_apart_irrefl_symm site x x).1, fun h ha => ?_, fun hxy hyz hxz => ?_⟩
  · exact h ((THM_OS_005_apart_irrefl_symm site y x).2 ha)
  · rcases THM_OS_006_cotransitive_of_total ht x y z hxz with h | h
    · exact hxy h
    · exact hyz h

/-- The length observer on words, valued in words so that stages can mix it with `wordObs`. -/
def lengthObs : Observer (List Nat) (List Nat) := fun w => some [w.length]
/-- The word (identity) observer. -/
def wordObs {α : Type} : Observer (List α) (List α) := fun w => some w

-- theorem-card: excluded middle for equality fails at an incomplete stage (finite countermodel)
theorem THM_OS_009_excluded_middle_fails :
    Refines [lengthObs] [lengthObs, wordObs] ∧
    Echo [lengthObs] [0, 1] [1, 0] ∧
    ¬ Apart [lengthObs] [0, 1] [1, 0] ∧
    Apart [lengthObs, wordObs] [0, 1] [1, 0] ∧
    ¬ ForcesDecided [lengthObs, wordObs] [lengthObs] [0, 1] [1, 0] := by
  have hna : ¬ Apart [lengthObs] [0, 1] [1, 0] := by
    intro h; have := (apartB_iff [lengthObs] [0, 1] [1, 0]).mpr h; revert this; decide
  have hsite : Apart [lengthObs, wordObs] [0, 1] [1, 0] :=
    (apartB_iff _ _ _).mp (by decide)
  refine ⟨?_, (echoB_iff _ _ _).mp (by decide), hna, hsite, not_decided_of_split hna hsite⟩
  intro o ho
  rw [List.mem_singleton] at ho
  rw [ho]; exact List.mem_cons_self

-- theorem-card: the echo status is not a Kripke proposition (its sieve is not up-closed)
theorem THM_OS_014_echo_not_kripke :
    ¬ UpClosed [lengthObs, wordObs]
      (Sieve [lengthObs, wordObs] [lengthObs] fun T' => Echo T' [0, 1] [1, 0]) := by
  intro hup
  obtain ⟨href, he, _, hsite, _⟩ := THM_OS_009_excluded_middle_fails
  have h := hup [lengthObs] [lengthObs, wordObs] ⟨fun o ho => ho, href, he⟩ href
    (fun o ho => ho)
  exact not_echo_and_apart h.2.2 hsite

section Primitivity

variable {α : Type}

/-- `x` is a proper power at stage `T`: echoed there to a literal power `u^k`, `k ≥ 2`, `u` nonempty. -/
def PowerAt (T : Stage (List α) R) (x : List α) : Prop :=
  ∃ u : List α, ∃ k, 2 ≤ k ∧ 0 < u.length ∧ Echo T x (Root.pow u k)
/-- `x` is primitive at stage `T`: nonempty and not a proper power there. -/
def PrimeAt (T : Stage (List α) R) (x : List α) : Prop := x ≠ [] ∧ ¬ PowerAt T x

-- theorem-card: primitivity is monotone under refinement (finer stages see more primitives)
theorem THM_OS_011_prime_monotone {T T' : Stage (List α) R}
    (h : Refines T T') {x : List α} (hp : PrimeAt T x) : PrimeAt T' x := by
  refine ⟨hp.1, fun hpow => hp.2 ?_⟩
  obtain ⟨u, k, hk, hu, he⟩ := hpow
  exact ⟨u, k, hk, hu, THM_OS_002_echo_retracts h he⟩

theorem echoes_wordObs_iff (x y : List α) : Echoes wordObs x y ↔ x = y := by
  constructor
  · rintro ⟨r, hr, hr'⟩
    simp only [wordObs, Option.some.injEq] at hr hr'
    exact hr.trans hr'.symm
  · rintro rfl; exact ⟨x, rfl, rfl⟩

theorem echoes_lengthObs_iff (x y : List Nat) : Echoes lengthObs x y ↔ x.length = y.length := by
  constructor
  · rintro ⟨r, hr, hr'⟩
    simp only [lengthObs, Option.some.injEq] at hr hr'
    have := hr.trans hr'.symm
    simp only [List.cons.injEq, and_true] at this
    exact this
  · intro h; exact ⟨[x.length], rfl, by simp [lengthObs, h]⟩

-- theorem-card: at the word stage, stage-primitivity is literal primitivity
theorem THM_OS_015_word_stage_prime_iff_primitive (x : List α) :
    PrimeAt [wordObs] x ↔ Root.Primitive x := by
  constructor
  · rintro ⟨hne, hnp⟩
    refine ⟨hne, fun z i hzi => ?_⟩
    rcases i with _ | _ | i
    · exact absurd hzi hne
    · rfl
    · exfalso
      apply hnp
      refine ⟨z, i + 2, by omega, ?_, ?_⟩
      · rcases z with _ | ⟨a, t⟩
        · exact absurd (hzi.trans (Root.pow_nil _)) hne
        · simp
      · intro o ho
        rw [List.mem_singleton] at ho
        rw [ho, echoes_wordObs_iff]
        exact hzi
  · rintro ⟨hne, hprim⟩
    refine ⟨hne, ?_⟩
    rintro ⟨u, k, hk, _, he⟩
    have h := (echoes_wordObs_iff _ _).mp (he wordObs List.mem_cons_self)
    have := hprim u k h
    omega

-- theorem-card: at the length stage only the unit tact is primitive
theorem THM_OS_016_length_stage_prime_iff_unit (x : List Nat) :
    PrimeAt [lengthObs] x ↔ x.length = 1 := by
  constructor
  · rintro ⟨hne, hnp⟩
    have hpos : 0 < x.length := by
      cases x with
      | nil => exact absurd rfl hne
      | cons a t => simp
    rcases Nat.lt_or_ge x.length 2 with hlt | hge
    · omega
    · exfalso
      apply hnp
      refine ⟨x.take 1, x.length, hge, ?_, ?_⟩
      · rw [List.length_take]; omega
      · intro o ho
        rw [List.mem_singleton] at ho
        rw [ho, echoes_lengthObs_iff, Root.length_pow, List.length_take]
        have : min 1 x.length = 1 := by omega
        rw [this, Nat.mul_one]
  · intro h1
    refine ⟨fun h => by simp [h] at h1, ?_⟩
    rintro ⟨u, k, hk, hu, he⟩
    have h := (echoes_lengthObs_iff _ _).mp (he lengthObs List.mem_cons_self)
    rw [Root.length_pow, h1] at h
    have : 2 * 1 ≤ k * u.length := Nat.mul_le_mul hk hu
    omega

theorem aba_not_literal_power (u : List Nat) (k : Nat) (hk : 2 ≤ k)
    (h : [0, 1, 0] = Root.pow u k) : False := by
  have hlen := congrArg List.length h
  rw [Root.length_pow] at hlen
  simp only [List.length_cons, List.length_nil] at hlen
  rcases u with _ | ⟨a, _ | ⟨b, t⟩⟩
  · simp at hlen
  · have hk3 : k = 3 := by simp at hlen; omega
    subst hk3
    simp [Root.pow] at h
    omega
  · have : 2 * 2 ≤ k * (a :: b :: t).length := Nat.mul_le_mul hk (by simp)
    omega

-- theorem-card: primitivity depends on the stage (docs/11 row `aba`)
theorem THM_OS_012_prime_depends_on_stage :
    ¬ PrimeAt [lengthObs] [0, 1, 0] ∧ PrimeAt [wordObs] [0, 1, 0] := by
  constructor
  · intro hp
    have := (THM_OS_016_length_stage_prime_iff_unit _).mp hp
    simp at this
  · rw [THM_OS_015_word_stage_prime_iff_primitive]
    refine ⟨by decide, fun z i hzi => ?_⟩
    rcases i with _ | _ | i
    · exact absurd (hzi.trans (Root.pow_zero_eq z)) (List.cons_ne_nil _ _)
    · rfl
    · exact absurd hzi (aba_not_literal_power z (i + 2) (by omega))

end Primitivity

end Site
end Veyra
