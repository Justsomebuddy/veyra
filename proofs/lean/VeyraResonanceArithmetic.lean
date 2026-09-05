import VeyraNativeArithmetic
import VeyraNecklaceOrbit

set_option autoImplicit false

/-! # Resonance arithmetic over the native `Recurrence`

The vocabulary of docs/02 made into definitions with theorems on the native
one-tact type: divisibility is resonance (`resonates`, from
`VeyraNativeArithmetic`), a prime is an indecomposable rhythm
(`ResonancePrime`), congruence is the phase obstruction left after maximal
extraction of the modulus (`PhaseCongruent`, via structural division with a
uniqueness theorem), gcd is the strongest shared echo (`sharedEcho`) and lcm the
smallest shared closure (`sharedClosure`). Every theorem is stated in that
vocabulary; the proofs pass through the one-tact length observer `toNat`,
which is proved to be a bijective stitch/weave homomorphism onto `Nat`
(`THM_RA_001`–`003`). That observer is the declared consistency anchor of the
shadow layer (README "Host-carried computation"), now a theorem rather than a
convention. Mathlib-free. -/

namespace Veyra
namespace Resonance

/-- The one-tact length observer: pulse count of a recurrence. -/
def toNat : Recurrence → Nat
  | Recurrence.silence => 0
  | Recurrence.pulse tail => toNat tail + 1

/-- Unary transport of a number into a recurrence. -/
def ofNat : Nat → Recurrence
  | 0 => Recurrence.silence
  | n + 1 => Recurrence.pulse (ofNat n)

/-- The single pulse: the unit of weave. -/
def pulseOne : Recurrence := Recurrence.pulse Recurrence.silence

theorem toNat_ofNat (n : Nat) : toNat (ofNat n) = n := by
  induction n with
  | zero => rfl
  | succ n ih => simp [ofNat, toNat, ih]

theorem ofNat_toNat (r : Recurrence) : ofNat (toNat r) = r := by
  induction r with
  | silence => rfl
  | pulse tail ih => simp [toNat, ofNat, ih]

theorem toNat_injective {a b : Recurrence} (h : toNat a = toNat b) : a = b := by
  rw [← ofNat_toNat a, ← ofNat_toNat b, h]

theorem toNat_stitch (a b : Recurrence) : toNat (stitch a b) = toNat a + toNat b := by
  induction a with
  | silence => simp [stitch, toNat]
  | pulse tail ih => simp [stitch, toNat, ih]; omega

theorem toNat_weave (a b : Recurrence) : toNat (weave a b) = toNat a * toNat b := by
  induction b with
  | silence => simp [weave, toNat]
  | pulse tail ih => rw [weave, toNat_stitch, ih, toNat, Nat.mul_succ, Nat.add_comm]

theorem toNat_pulseOne : toNat pulseOne = 1 := rfl

theorem toNat_silence : toNat Recurrence.silence = 0 := rfl

theorem toNat_eq_zero_iff (r : Recurrence) : toNat r = 0 ↔ r = Recurrence.silence := by
  constructor
  · intro h; exact toNat_injective (by rw [h]; rfl)
  · intro h; rw [h]; rfl

-- theorem-card: the one-tact length observer is a bijection onto Nat
theorem THM_RA_001_one_tact_shadow_bijective :
    (∀ n, toNat (ofNat n) = n) ∧ (∀ r, ofNat (toNat r) = r) :=
  ⟨toNat_ofNat, ofNat_toNat⟩

-- theorem-card: stitch shadows addition
theorem THM_RA_002_stitch_shadow (a b : Recurrence) : toNat (stitch a b) = toNat a + toNat b :=
  toNat_stitch a b

-- theorem-card: weave shadows multiplication
theorem THM_RA_003_weave_shadow (a b : Recurrence) : toNat (weave a b) = toNat a * toNat b :=
  toNat_weave a b

/-! ## Laws of stitch and weave, transported through the observer -/

theorem stitch_comm (a b : Recurrence) : stitch a b = stitch b a :=
  toNat_injective (by rw [toNat_stitch, toNat_stitch, Nat.add_comm])

theorem weave_comm (a b : Recurrence) : weave a b = weave b a :=
  toNat_injective (by rw [toNat_weave, toNat_weave, Nat.mul_comm])

theorem weave_assoc (a b c : Recurrence) : weave (weave a b) c = weave a (weave b c) :=
  toNat_injective (by rw [toNat_weave, toNat_weave, toNat_weave, toNat_weave, Nat.mul_assoc])

theorem weave_stitch_left (a b c : Recurrence) :
    weave a (stitch b c) = stitch (weave a b) (weave a c) :=
  toNat_injective (by
    rw [toNat_weave, toNat_stitch, toNat_stitch, toNat_weave, toNat_weave, Nat.left_distrib])

theorem weave_stitch_right (a b c : Recurrence) :
    weave (stitch a b) c = stitch (weave a c) (weave b c) :=
  toNat_injective (by
    rw [toNat_weave, toNat_stitch, toNat_stitch, toNat_weave, toNat_weave, Nat.right_distrib])

theorem weave_pulseOne_left (a : Recurrence) : weave pulseOne a = a :=
  toNat_injective (by rw [toNat_weave, toNat_pulseOne, Nat.one_mul])

theorem weave_pulseOne_right (a : Recurrence) : weave a pulseOne = a :=
  toNat_injective (by rw [toNat_weave, toNat_pulseOne, Nat.mul_one])

theorem weave_silence_left (a : Recurrence) : weave Recurrence.silence a = Recurrence.silence :=
  toNat_injective (by rw [toNat_weave, toNat_silence, Nat.zero_mul])

-- theorem-card: the weave laws (commutative, associative, distributive over stitch, unit)
theorem THM_RA_004_weave_laws :
    (∀ a b : Recurrence, weave a b = weave b a) ∧
    (∀ a b c : Recurrence, weave (weave a b) c = weave a (weave b c)) ∧
    (∀ a b c : Recurrence, weave a (stitch b c) = stitch (weave a b) (weave a c)) ∧
    (∀ a : Recurrence, weave pulseOne a = a) :=
  ⟨weave_comm, weave_assoc, weave_stitch_left, weave_pulseOne_left⟩

/-! ## Resonance is divisibility -/

theorem resonates_iff_dvd (f c : Recurrence) : resonates f c ↔ toNat f ∣ toNat c := by
  constructor
  · rintro ⟨w, hw⟩
    exact ⟨toNat w, by rw [← hw, toNat_weave]⟩
  · rintro ⟨k, hk⟩
    refine ⟨ofNat k, toNat_injective ?_⟩
    rw [toNat_weave, toNat_ofNat, hk]

theorem resonates_refl (a : Recurrence) : resonates a a :=
  (resonates_iff_dvd a a).mpr (Nat.dvd_refl _)

theorem resonates_trans {a b c : Recurrence} (hab : resonates a b) (hbc : resonates b c) :
    resonates a c :=
  (resonates_iff_dvd a c).mpr
    (Nat.dvd_trans ((resonates_iff_dvd a b).mp hab) ((resonates_iff_dvd b c).mp hbc))

theorem resonates_antisymm {a b : Recurrence} (hab : resonates a b) (hba : resonates b a) : a = b :=
  toNat_injective (Nat.dvd_antisymm ((resonates_iff_dvd a b).mp hab) ((resonates_iff_dvd b a).mp hba))

theorem resonates_silence (a : Recurrence) : resonates a Recurrence.silence :=
  ⟨Recurrence.silence, rfl⟩

-- theorem-card: resonance is the divisibility preorder (reflexive, transitive, antisymmetric)
theorem THM_RA_005_resonance_order :
    (∀ f c : Recurrence, resonates f c ↔ toNat f ∣ toNat c) ∧
    (∀ a : Recurrence, resonates a a) ∧
    (∀ a b c : Recurrence, resonates a b → resonates b c → resonates a c) ∧
    (∀ a b : Recurrence, resonates a b → resonates b a → a = b) :=
  ⟨resonates_iff_dvd, resonates_refl, fun _ _ _ => resonates_trans, fun _ _ => resonates_antisymm⟩

/-! ## Structural division: maximal extraction of a modulus -/

/-- Quotient of the structural division of `c` by `d`. -/
def quotient (d c : Recurrence) : Recurrence := ofNat (toNat c / toNat d)

/-- Residual (phase obstruction) of the structural division of `c` by `d`. -/
def residual (d c : Recurrence) : Recurrence := ofNat (toNat c % toNat d)

theorem toNat_residual (d c : Recurrence) : toNat (residual d c) = toNat c % toNat d := by
  unfold residual; rw [toNat_ofNat]

theorem division_reconstructs (d c : Recurrence) :
    c = stitch (weave d (quotient d c)) (residual d c) :=
  toNat_injective (by
    unfold quotient residual
    rw [toNat_stitch, toNat_weave, toNat_ofNat, toNat_ofNat, Nat.div_add_mod])

theorem residual_bounded (d c : Recurrence) (hd : d ≠ Recurrence.silence) :
    toNat (residual d c) < toNat d := by
  rw [toNat_residual]
  apply Nat.mod_lt
  rcases Nat.eq_zero_or_pos (toNat d) with h | h
  · exact absurd ((toNat_eq_zero_iff d).mp h) hd
  · exact h

theorem division_unique (d q r q' r' : Recurrence)
    (h : stitch (weave d q) r = stitch (weave d q') r')
    (hr : toNat r < toNat d) (hr' : toNat r' < toNat d) : q = q' ∧ r = r' := by
  have hn := congrArg toNat h
  rw [toNat_stitch, toNat_stitch, toNat_weave, toNat_weave] at hn
  have hq : toNat q = toNat q' := by
    have h1 : (toNat r + toNat d * toNat q) / toNat d = toNat q := by
      rw [Nat.add_mul_div_left _ _ (Nat.lt_of_le_of_lt (Nat.zero_le _) hr), Nat.div_eq_of_lt hr, Nat.zero_add]
    have h2 : (toNat r' + toNat d * toNat q') / toNat d = toNat q' := by
      rw [Nat.add_mul_div_left _ _ (Nat.lt_of_le_of_lt (Nat.zero_le _) hr'), Nat.div_eq_of_lt hr', Nat.zero_add]
    rw [← h1, ← h2, Nat.add_comm (toNat r), Nat.add_comm (toNat r'), hn]
  have hrr : toNat r = toNat r' := by
    have h1 : (toNat r + toNat d * toNat q) % toNat d = toNat r := by
      rw [Nat.add_mul_mod_self_left, Nat.mod_eq_of_lt hr]
    have h2 : (toNat r' + toNat d * toNat q') % toNat d = toNat r' := by
      rw [Nat.add_mul_mod_self_left, Nat.mod_eq_of_lt hr']
    rw [← h1, ← h2, Nat.add_comm (toNat r), Nat.add_comm (toNat r'), hn]
  exact ⟨toNat_injective hq, toNat_injective hrr⟩

-- theorem-card: structural division reconstructs, bounds the residual, and is unique
theorem THM_RA_006_structural_division (d c : Recurrence) (hd : d ≠ Recurrence.silence) :
    c = stitch (weave d (quotient d c)) (residual d c) ∧
    toNat (residual d c) < toNat d ∧
    (∀ q r, toNat r < toNat d → c = stitch (weave d q) r → q = quotient d c ∧ r = residual d c) := by
  refine ⟨division_reconstructs d c, residual_bounded d c hd, fun q r hr hc => ?_⟩
  exact division_unique d q r (quotient d c) (residual d c) (hc.symm.trans (division_reconstructs d c))
    hr (residual_bounded d c hd)

/-! ## Phase congruence: the same obstruction after maximal extraction -/

/-- `x` and `y` are phase-congruent modulo `m` when maximal `m`-extraction leaves the same residual. -/
def PhaseCongruent (m x y : Recurrence) : Prop := residual m x = residual m y

theorem phaseCongruent_iff_nat (m x y : Recurrence) :
    PhaseCongruent m x y ↔ toNat x % toNat m = toNat y % toNat m := by
  unfold PhaseCongruent residual
  constructor
  · intro h
    have := congrArg toNat h
    rw [toNat_ofNat, toNat_ofNat] at this
    exact this
  · intro h; rw [h]

-- theorem-card: phase congruence is exactly "same leftover phase after maximal m-extraction"
theorem THM_RA_007_phase_congruence_characterization (m x y : Recurrence)
    (hm : m ≠ Recurrence.silence) :
    PhaseCongruent m x y ↔
      ∃ q₁ q₂ r, toNat r < toNat m ∧ x = stitch (weave m q₁) r ∧ y = stitch (weave m q₂) r := by
  constructor
  · intro h
    refine ⟨quotient m x, quotient m y, residual m x, residual_bounded m x hm,
      division_reconstructs m x, ?_⟩
    have hy := division_reconstructs m y
    unfold PhaseCongruent at h
    rw [h]; exact hy
  · rintro ⟨q₁, q₂, r, hr, hx, hy⟩
    unfold PhaseCongruent
    have h1 := division_unique m q₁ r (quotient m x) (residual m x)
      (hx.symm.trans (division_reconstructs m x)) hr (residual_bounded m x hm)
    have h2 := division_unique m q₂ r (quotient m y) (residual m y)
      (hy.symm.trans (division_reconstructs m y)) hr (residual_bounded m y hm)
    rw [← h1.2, ← h2.2]

theorem phaseCongruent_refl (m x : Recurrence) : PhaseCongruent m x x := rfl

theorem phaseCongruent_symm {m x y : Recurrence} (h : PhaseCongruent m x y) : PhaseCongruent m y x :=
  h.symm

theorem phaseCongruent_trans {m x y z : Recurrence} (h₁ : PhaseCongruent m x y)
    (h₂ : PhaseCongruent m y z) : PhaseCongruent m x z :=
  h₁.trans h₂

theorem phaseCongruent_stitch {m x y x' y' : Recurrence} (h : PhaseCongruent m x y)
    (h' : PhaseCongruent m x' y') : PhaseCongruent m (stitch x x') (stitch y y') := by
  rw [phaseCongruent_iff_nat] at h h' ⊢
  rw [toNat_stitch, toNat_stitch, Nat.add_mod, h, h', ← Nat.add_mod]

theorem phaseCongruent_weave {m x y x' y' : Recurrence} (h : PhaseCongruent m x y)
    (h' : PhaseCongruent m x' y') : PhaseCongruent m (weave x x') (weave y y') := by
  rw [phaseCongruent_iff_nat] at h h' ⊢
  rw [toNat_weave, toNat_weave, Nat.mul_mod, h, h', ← Nat.mul_mod]

-- theorem-card: phase congruence is an equivalence compatible with stitch and weave
theorem THM_RA_008_phase_congruence_laws (m : Recurrence) :
    (∀ x, PhaseCongruent m x x) ∧
    (∀ x y, PhaseCongruent m x y → PhaseCongruent m y x) ∧
    (∀ x y z, PhaseCongruent m x y → PhaseCongruent m y z → PhaseCongruent m x z) ∧
    (∀ x y x' y', PhaseCongruent m x y → PhaseCongruent m x' y' →
      PhaseCongruent m (stitch x x') (stitch y y')) ∧
    (∀ x y x' y', PhaseCongruent m x y → PhaseCongruent m x' y' →
      PhaseCongruent m (weave x x') (weave y y')) :=
  ⟨phaseCongruent_refl m, fun _ _ => phaseCongruent_symm, fun _ _ _ => phaseCongruent_trans,
   fun _ _ _ _ => phaseCongruent_stitch, fun _ _ _ _ => phaseCongruent_weave⟩

/-! ## Resonance primes: indecomposable rhythms -/

/-- A resonance prime: at least two pulses, and its only resonators are the unit pulse and itself. -/
def ResonancePrime (p : Recurrence) : Prop :=
  2 ≤ toNat p ∧ ∀ d, resonates d p → d = pulseOne ∨ d = p

-- theorem-card: resonance primes are exactly the primes of the length observer
theorem THM_RA_009_resonance_prime_iff (p : Recurrence) :
    ResonancePrime p ↔ Necklace.IsPrime (toNat p) := by
  constructor
  · rintro ⟨h2, h⟩
    refine ⟨h2, fun d hd => ?_⟩
    rcases h (ofNat d) ((resonates_iff_dvd _ _).mpr (by rw [toNat_ofNat]; exact hd)) with h1 | h1
    · left; have := congrArg toNat h1; rw [toNat_ofNat] at this; exact this
    · right; have := congrArg toNat h1; rw [toNat_ofNat] at this; exact this
  · rintro ⟨h2, h⟩
    refine ⟨h2, fun d hd => ?_⟩
    rcases h (toNat d) ((resonates_iff_dvd _ _).mp hd) with h1 | h1
    · left; exact toNat_injective (by rw [h1]; rfl)
    · right; exact toNat_injective h1

/-- Native power: iterate weave once per pulse of the exponent. -/
def rpow (base : Recurrence) : Recurrence → Recurrence
  | Recurrence.silence => pulseOne
  | Recurrence.pulse tail => weave base (rpow base tail)

theorem toNat_rpow (base e : Recurrence) : toNat (rpow base e) = toNat base ^ toNat e := by
  induction e with
  | silence => rfl
  | pulse tail ih => rw [rpow, toNat_weave, ih, toNat, Nat.pow_succ, Nat.mul_comm]

-- theorem-card: Fermat's little theorem in the resonance vocabulary
-- For a resonance prime p and any recurrence k, weaving k with itself once per pulse of p
-- leaves the same phase obstruction modulo p as k itself.
theorem THM_RA_010_fermat_phase (p k : Recurrence) (hp : ResonancePrime p) :
    PhaseCongruent p (rpow k p) k := by
  rw [phaseCongruent_iff_nat, toNat_rpow]
  exact Necklace.THM_NO_008_fermat_mod (toNat p) ((THM_RA_009_resonance_prime_iff p).mp hp) (toNat k)

/-! ## Euclid: the product-plus-one escape, natively -/

/-- Weave every listed recurrence together (unit pulse for the empty list). -/
def weaveAll : List Recurrence → Recurrence
  | [] => pulseOne
  | f :: rest => weave f (weaveAll rest)

/-- The escape of a list: one pulse stitched after the weave of the list. -/
def escape (fs : List Recurrence) : Recurrence := stitch (weaveAll fs) pulseOne

theorem toNat_weaveAll_dvd {fs : List Recurrence} {f : Recurrence} (hf : f ∈ fs) :
    toNat f ∣ toNat (weaveAll fs) := by
  induction fs with
  | nil => exact absurd hf List.not_mem_nil
  | cons g rest ih =>
      rw [weaveAll, toNat_weave]
      rcases List.mem_cons.mp hf with rfl | hmem
      · exact Nat.dvd_mul_right _ _
      · exact Nat.dvd_mul_left_of_dvd (ih hmem) _

theorem toNat_weaveAll_pos {fs : List Recurrence} (h : ∀ f ∈ fs, 2 ≤ toNat f) :
    0 < toNat (weaveAll fs) := by
  induction fs with
  | nil => exact Nat.one_pos
  | cons g rest ih =>
      rw [weaveAll, toNat_weave]
      exact Nat.mul_pos (Nat.lt_of_lt_of_le (Nat.zero_lt_succ 1) (h g List.mem_cons_self))
        (ih fun f hf => h f (List.mem_cons_of_mem g hf))

-- theorem-card: the escape leaves exactly the unit phase under every listed factor
theorem THM_RA_011_escape_residual (fs : List Recurrence) (f : Recurrence) (hf : f ∈ fs)
    (h2 : 2 ≤ toNat f) : residual f (escape fs) = pulseOne := by
  apply toNat_injective
  rw [toNat_residual, escape, toNat_stitch, toNat_pulseOne]
  obtain ⟨k, hk⟩ := toNat_weaveAll_dvd hf
  rw [hk, Nat.add_comm, Nat.add_mul_mod_self_left, Nat.mod_eq_of_lt h2]

/-- Least divisor search from `d` upward with explicit fuel. -/
def leastFactorFrom (n : Nat) : Nat → Nat → Nat
  | _, 0 => n
  | d, fuel + 1 => if d ∣ n then d else leastFactorFrom n (d + 1) fuel

theorem leastFactorFrom_dvd (n d fuel : Nat) : leastFactorFrom n d fuel ∣ n := by
  induction fuel generalizing d with
  | zero => exact Nat.dvd_refl n
  | succ fuel ih =>
      unfold leastFactorFrom
      by_cases h : d ∣ n
      · rw [if_pos h]; exact h
      · rw [if_neg h]; exact ih (d + 1)

theorem leastFactorFrom_ge (n d fuel : Nat) : d ≤ leastFactorFrom n d fuel ∨ leastFactorFrom n d fuel = n := by
  induction fuel generalizing d with
  | zero => exact Or.inr rfl
  | succ fuel ih =>
      unfold leastFactorFrom
      by_cases h : d ∣ n
      · rw [if_pos h]; exact Or.inl (Nat.le_refl d)
      · rw [if_neg h]
        rcases ih (d + 1) with h1 | h1
        · exact Or.inl (Nat.le_trans (Nat.le_succ d) h1)
        · exact Or.inr h1

theorem leastFactorFrom_minimal (n d fuel : Nat) (e : Nat) (hde : d ≤ e) (he : e ∣ n)
    (hfuel : e < d + fuel) : leastFactorFrom n d fuel ≤ e := by
  induction fuel generalizing d with
  | zero => omega
  | succ fuel ih =>
      unfold leastFactorFrom
      by_cases h : d ∣ n
      · rw [if_pos h]; exact hde
      · rw [if_neg h]
        have hne : d ≠ e := fun hdeq => h (hdeq ▸ he)
        exact ih (d + 1) (by omega) (by omega)

/-- The least factor `≥ 2` of `n` (for `n ≥ 2`). -/
def leastFactor (n : Nat) : Nat := leastFactorFrom n 2 n

theorem leastFactor_dvd (n : Nat) : leastFactor n ∣ n := leastFactorFrom_dvd n 2 n

theorem leastFactor_ge_two (n : Nat) (hn : 2 ≤ n) : 2 ≤ leastFactor n := by
  rcases leastFactorFrom_ge n 2 n with h | h
  · exact h
  · unfold leastFactor; rw [h]; exact hn

theorem leastFactor_minimal (n : Nat) (hn : 2 ≤ n) (e : Nat) (h2 : 2 ≤ e) (he : e ∣ n) :
    leastFactor n ≤ e := by
  have hen : e ≤ n := Nat.le_of_dvd (by omega) he
  exact leastFactorFrom_minimal n 2 n e h2 he (by omega)

theorem leastFactor_prime (n : Nat) (hn : 2 ≤ n) : Necklace.IsPrime (leastFactor n) := by
  refine ⟨leastFactor_ge_two n hn, fun d hd => ?_⟩
  have hpos : 0 < leastFactor n := by have := leastFactor_ge_two n hn; omega
  have hdle : d ≤ leastFactor n := Nat.le_of_dvd hpos hd
  rcases Nat.lt_or_ge d 2 with hlt | hge
  · cases d with
    | zero => exfalso; have := Nat.eq_zero_of_zero_dvd hd; omega
    | succ d' => cases d' with
      | zero => exact Or.inl rfl
      | succ _ => omega
  · have hdn : d ∣ n := Nat.dvd_trans hd (leastFactor_dvd n)
    have := leastFactor_minimal n hn d hge hdn
    exact Or.inr (Nat.le_antisymm hdle this)

theorem exists_resonance_prime_factor (r : Recurrence) (h2 : 2 ≤ toNat r) :
    ∃ p, ResonancePrime p ∧ resonates p r := by
  refine ⟨ofNat (leastFactor (toNat r)), ?_, ?_⟩
  · rw [THM_RA_009_resonance_prime_iff, toNat_ofNat]; exact leastFactor_prime _ h2
  · rw [resonates_iff_dvd, toNat_ofNat]; exact leastFactor_dvd _

theorem pulseOne_ne_silence : pulseOne ≠ Recurrence.silence := by
  intro h; cases h

-- theorem-card: Euclid natively — no finite list of resonance primes exhausts them
theorem THM_RA_012_euclid_escape (fs : List Recurrence) (hfs : ∀ f ∈ fs, ResonancePrime f) :
    ∃ p, ResonancePrime p ∧ resonates p (escape fs) ∧ p ∉ fs := by
  have hpos : 0 < toNat (weaveAll fs) := toNat_weaveAll_pos fun f hf => (hfs f hf).1
  have h2 : 2 ≤ toNat (escape fs) := by
    unfold escape; rw [toNat_stitch, toNat_pulseOne]; omega
  obtain ⟨p, hp, hres⟩ := exists_resonance_prime_factor (escape fs) h2
  refine ⟨p, hp, hres, fun hmem => ?_⟩
  have hres1 := THM_RA_011_escape_residual fs p hmem hp.1
  have hzero : toNat (residual p (escape fs)) = 0 := by
    rw [toNat_residual]
    exact Nat.mod_eq_zero_of_dvd ((resonates_iff_dvd _ _).mp hres)
  rw [hres1, toNat_pulseOne] at hzero
  exact Nat.one_ne_zero hzero

/-! ## Strongest shared echo and smallest shared closure -/

/-- The strongest shared echo of two recurrences (gcd). -/
def sharedEcho (a b : Recurrence) : Recurrence := ofNat (Nat.gcd (toNat a) (toNat b))

/-- The smallest shared closure of two recurrences (lcm). -/
def sharedClosure (a b : Recurrence) : Recurrence := ofNat (Nat.lcm (toNat a) (toNat b))

-- theorem-card: the shared echo resonates in both and every common resonator resonates in it
theorem THM_RA_013_shared_echo (a b : Recurrence) :
    resonates (sharedEcho a b) a ∧ resonates (sharedEcho a b) b ∧
    ∀ d, resonates d a → resonates d b → resonates d (sharedEcho a b) := by
  refine ⟨?_, ?_, fun d ha hb => ?_⟩
  · rw [resonates_iff_dvd]; unfold sharedEcho; rw [toNat_ofNat]; exact Nat.gcd_dvd_left _ _
  · rw [resonates_iff_dvd]; unfold sharedEcho; rw [toNat_ofNat]; exact Nat.gcd_dvd_right _ _
  · rw [resonates_iff_dvd] at ha hb ⊢; unfold sharedEcho; rw [toNat_ofNat]; exact Nat.dvd_gcd ha hb

-- theorem-card: both resonate in the shared closure and it resonates in every common closure
theorem THM_RA_014_shared_closure (a b : Recurrence) :
    resonates a (sharedClosure a b) ∧ resonates b (sharedClosure a b) ∧
    ∀ c, resonates a c → resonates b c → resonates (sharedClosure a b) c := by
  refine ⟨?_, ?_, fun c ha hb => ?_⟩
  · rw [resonates_iff_dvd]; unfold sharedClosure; rw [toNat_ofNat]; exact Nat.dvd_lcm_left _ _
  · rw [resonates_iff_dvd]; unfold sharedClosure; rw [toNat_ofNat]; exact Nat.dvd_lcm_right _ _
  · rw [resonates_iff_dvd] at ha hb ⊢; unfold sharedClosure; rw [toNat_ofNat]; exact Nat.lcm_dvd ha hb

#check THM_RA_010_fermat_phase
#check THM_RA_012_euclid_escape

end Resonance
end Veyra
