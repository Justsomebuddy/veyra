import VeyraResearchCards
import VeyraResearchGcd

namespace Veyra

/- Classical Nat steps toward Fermat's little theorem. They do not discharge
the native resonance-prime repair track in docs/102. This module proves the
binomial factor identity and divisibility of every middle coefficient.
-/

theorem RESEARCH_F_L001_choose_one (n : Nat) : choose (n + 1) 1 = n + 1 := by
  induction n with
  | zero => rfl
  | succ n ih =>
      unfold choose
      rw [ih]
      rw [show choose (n + 1) 0 = 1 from rfl]
      rw [Nat.add_comm]

theorem RESEARCH_F_L003_succ_mul_add (p A : Nat) :
    p * A + A = (p + 1) * A := by
  rw [Nat.add_mul]
  rw [Nat.one_mul]

theorem RESEARCH_F_T001_step5 (p : Nat) : ∀ k', 0 < k' + 1 → k' + 1 < p →
    p * (choose (p - 1) k' + choose (p - 1) (k' + 1)) + choose p (k' + 1) =
      (p + 1) * choose p (k' + 1) := by
  intro k' hpos hlt
  have h1p : 1 ≤ p := Nat.le_trans (Nat.succ_le_of_lt hpos) (Nat.le_of_lt hlt)
  have hp : p - 1 + 1 = p := Nat.sub_add_cancel h1p
  have hpascal : choose p (k' + 1) =
      choose (p - 1) k' + choose (p - 1) (k' + 1) := by
    rw [← hp]
    simp [choose]
  rw [hpascal]
  exact RESEARCH_F_L003_succ_mul_add p (choose (p - 1) k' + choose (p - 1) (k' + 1))

-- k * C(p, k) = p * C(p-1, k-1) for 1 <= k <= p.
theorem RESEARCH_F_T001_choose_factor : ∀ p k, 0 < k → k ≤ p →
    k * choose p k = p * choose (p - 1) (k - 1) := by
  intro p
  induction p with
  | zero =>
      intro k hk hle
      have hk0 : k = 0 := Nat.eq_zero_of_le_zero hle
      subst hk0
      exact False.elim (Nat.lt_irrefl 0 hk)
  | succ p ih =>
      intro k hk hle
      cases k with
      | zero => cases hk
      | succ k =>
          cases k with
          | zero =>
              rw [RESEARCH_F_L001_choose_one]
              simp [choose]
          | succ k' =>
              have hkp : k' + 1 ≤ p := Nat.le_of_succ_le_succ hle
              classical
              by_cases hlt : k' + 1 < p
              · -- general step: both induction hypotheses apply
                have h2a : 0 < k' + 1 := Nat.succ_pos k'
                have h2b : k' + 2 ≤ p := Nat.succ_le_of_lt hlt
                have ih1 := ih (k' + 1) h2a hkp
                have ih2 := ih (k' + 2) (Nat.succ_pos (k' + 1)) h2b
                have hpascal1 : choose (p + 1) (k' + 2) =
                    choose p (k' + 1) + choose p (k' + 2) := by rfl
                rw [hpascal1]
                rw [Nat.mul_add]
                rw [ih2, Nat.add_sub_cancel (k' + 1) 1]
                rw [Nat.succ_mul]
                rw [ih1, Nat.add_sub_cancel k' 1]
                rw [Nat.add_assoc]
                rw [Nat.add_comm (choose p (k' + 1)) (p * choose (p - 1) (k' + 1))]
                rw [← Nat.add_assoc]
                rw [← Nat.mul_add]
                exact RESEARCH_F_T001_step5 p k' h2a hlt
              · -- boundary: k'+1 = p
                have hkpp : k' + 1 = p := by
                  have hge : p ≤ k' + 1 := Nat.le_of_not_gt hlt
                  exact Nat.le_antisymm hkp hge
                rw [hkpp]
                rw [RESEARCH_L002_choose_diag, RESEARCH_L002_choose_diag]

-- p prime divides every middle binomial coefficient.
theorem RESEARCH_F_T002_middle_choose_divisible (p k : Nat) (hp : Prime p) (h1 : 0 < k)
    (h2 : k < p) : p ∣ choose p k := by
  have hfac : k * choose p k = p * choose (p - 1) (k - 1) :=
    RESEARCH_F_T001_choose_factor p k h1 (Nat.le_of_lt h2)
  have hpd : p ∣ k * choose p k := by
    rw [hfac]
    exact Nat.dvd_mul_right p (choose (p - 1) (k - 1))
  have hpk : ¬ p ∣ k := by
    intro hdiv
    have hle : p ≤ k := Nat.le_of_dvd h1 hdiv
    exact Nat.not_lt_of_ge hle h2
  exact (RESEARCH_G_T003_prime_dvd_mul p k (choose p k) hp hpd).resolve_left hpk

#check RESEARCH_F_T001_choose_factor
#check RESEARCH_F_T002_middle_choose_divisible

end Veyra
