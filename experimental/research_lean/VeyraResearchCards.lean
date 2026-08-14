import VeyraCombinatorics
import VeyraCyclic

namespace Veyra

/- Classical Nat identities adjacent to several fixed finite theorem cards.

The shared `choose` and cyclic definitions make some rows useful candidate
generalizations of B001/C002. The bare counting equalities are only arithmetic
lemmas: without finite-set/event semantics they do not generalize the P001-P003
probability cards. Compilation alone adds no registry status or axiom audit.
-/

-- Helper: choose n k vanishes above the diagonal.
theorem RESEARCH_L001_choose_above (n : Nat) : ∀ k, n < k → choose n k = 0 := by
  induction n with
  | zero =>
      intro k h
      cases k with
      | zero => cases h
      | succ k => rfl
  | succ n ih =>
      intro k h
      cases k with
      | zero => cases h
      | succ k =>
          unfold choose
          rw [ih k (Nat.lt_of_succ_lt_succ h)]
          rw [ih (k + 1) (Nat.lt_trans (Nat.lt_of_succ_lt_succ h) (Nat.lt_succ_self k))]

-- Helper: diagonal binomial coefficients equal one.
theorem RESEARCH_L002_choose_diag (n : Nat) : choose n n = 1 := by
  induction n with
  | zero => rfl
  | succ n ih =>
      unfold choose
      rw [ih]
      rw [RESEARCH_L001_choose_above n (n + 1) (Nat.lt_succ_self n)]

-- Helper: n - (k+1) = (n - k) - 1 for all naturals.
theorem RESEARCH_L003_sub_succ (n : Nat) : ∀ k, n - (k + 1) = (n - k) - 1 := by
  induction n with
  | zero =>
      intro k
      simp
  | succ n ih =>
      intro k
      cases k with
      | zero => rfl
      | succ k =>
          rw [Nat.succ_sub_succ]
          rw [Nat.succ_sub_succ]
          exact ih k

-- Helper: n - k = 0 forces n ≤ k.
theorem RESEARCH_L004_sub_eq_zero_of (n : Nat) : ∀ k, n - k = 0 → n ≤ k := by
  induction n with
  | zero =>
      intro k _
      exact Nat.zero_le k
  | succ n ih =>
      intro k h
      cases k with
      | zero =>
          have h0 : n + 1 = 0 := by
            simpa only [Nat.sub_zero] using h
          exact False.elim (Nat.succ_ne_zero n h0)
      | succ k =>
          have h' : n - k = 0 := by
            simp [Nat.succ_sub_succ] at h
            exact h
          exact Nat.succ_le_succ (ih k h')

-- Helper: a positive difference witnesses a strict comparison.
theorem RESEARCH_L005_sub_pos (n : Nat) : ∀ k, 0 < n - k → k < n := by
  induction n with
  | zero =>
      intro k h
      have h0 : 0 < 0 := by
        simp at h
      exact False.elim (Nat.lt_irrefl 0 h0)
  | succ n ih =>
      intro k h
      cases k with
      | zero => exact Nat.zero_lt_succ n
      | succ k =>
          have h' : 0 < n - k := by
            simp [Nat.succ_sub_succ] at h
            exact h
          exact Nat.succ_lt_succ (ih k h')

-- T1: general binomial symmetry, valid exactly below the diagonal.
theorem RESEARCH_T001_choose_sym (n : Nat) : ∀ k, k ≤ n → choose n k = choose n (n - k) := by
  induction n with
  | zero =>
      intro k h
      have hk : k = 0 := Nat.eq_zero_of_le_zero h
      subst k
      rfl
  | succ n ih =>
      intro k h
      cases k with
      | zero =>
          simp [choose]
          rw [RESEARCH_L002_choose_diag n]
          rw [RESEARCH_L001_choose_above n (n + 1) (Nat.lt_succ_self n)]
      | succ k =>
          have hk : k ≤ n := Nat.le_of_succ_le_succ h
          rw [Nat.succ_sub_succ]
          unfold choose
          cases hnk : n - k with
          | zero =>
              have hkn : n ≤ k := RESEARCH_L004_sub_eq_zero_of n k hnk
              have hkeq : k = n := Nat.le_antisymm hk hkn
              rw [hkeq]
              rw [RESEARCH_L002_choose_diag]
              rw [RESEARCH_L001_choose_above n (n + 1) (Nat.lt_succ_self n)]
          | succ m =>
              have hkn : k < n := by
                have hpos : 0 < n - k := by
                  rw [hnk]
                  exact Nat.succ_pos m
                exact RESEARCH_L005_sub_pos n k hpos
              have hsub : n - (k + 1) = m := by
                rw [RESEARCH_L003_sub_succ]
                rw [hnk]
                rfl
              have h1 : choose n k = choose n (m + 1) := by
                have := ih k hk
                rwa [hnk] at this
              have h2 : choose n (k + 1) = choose n m := by
                have := ih (k + 1) (Nat.succ_le_of_lt hkn)
                rwa [hsub] at this
              rw [h1, h2]
              rw [Nat.add_comm]

-- T5: general chord shadow symmetry for an arbitrary modulus and phase.
theorem RESEARCH_T005_chord_reflection (m p : Nat) (hp : p ≤ m) :
    Nat.min p (m - p) = Nat.min (m - p) p ∧
    m - (m - p) = p ∧
    4 * p * (m - p) = 4 * (m - p) * (m - (m - p)) := by
  constructor
  · exact Nat.min_comm p (m - p)
  constructor
  · exact Nat.sub_sub_self hp
  · rw [Nat.sub_sub_self hp]
    calc
      4 * p * (m - p) = 4 * (p * (m - p)) := by rw [Nat.mul_assoc]
      _ = 4 * ((m - p) * p) := by rw [Nat.mul_comm p (m - p)]
      _ = 4 * (m - p) * p := by rw [Nat.mul_assoc]

-- Arithmetic complement-count rearrangement; no probability/event model.
theorem RESEARCH_T006_complement_counts (t e : Nat) (h : e ≤ t) :
    (t - e) + e = t := by
  exact Nat.sub_add_cancel h

-- Arithmetic overlap-count rearrangement; no set-union semantics.
theorem RESEARCH_T007_union_counts (a b c : Nat) (ha : c ≤ a) (hb : c ≤ b) :
    (a - c) + (b - c) + c + c = a + b := by
  calc
    (a - c) + (b - c) + c + c = (a - c) + c + ((b - c) + c) := by ac_rfl
    _ = a + b := by rw [Nat.sub_add_cancel ha, Nat.sub_add_cancel hb]

-- Commutative-semiring cross-product reassociation; no independence semantics.
theorem RESEARCH_T008_cross_product_reassociation (a b t : Nat) :
    (a * b) * t = (a * t) * b := by
  calc
    (a * b) * t = a * (b * t) := by rw [Nat.mul_assoc]
    _ = a * (t * b) := by rw [Nat.mul_comm b t]
    _ = (a * t) * b := by rw [Nat.mul_assoc]

-- T8: reflected phase completes its period (general cyclic law).
theorem RESEARCH_T009_reflected_period (m p : Nat) (hp : p ≤ m) :
    (m - p + p) % m = 0 := by
  rw [Nat.sub_add_cancel hp]
  rw [Nat.mod_self]

#check RESEARCH_T001_choose_sym
#check RESEARCH_T005_chord_reflection
#check RESEARCH_T006_complement_counts
#check RESEARCH_T007_union_counts
#check RESEARCH_T008_cross_product_reassociation
#check RESEARCH_T009_reflected_period

end Veyra
