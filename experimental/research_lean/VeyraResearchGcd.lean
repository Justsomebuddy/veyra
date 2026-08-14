import VeyraResearchPrimes

namespace Veyra

/- Classical Euclidean gcd and Bezout laws over Nat/Int.

These declarations support the local classical-prime lemmas only. They do not
bridge to Veyra resonance-prime modes, and compilation is not an axiom audit.
-/

theorem RESEARCH_G_L001_mod_lt (m n : Nat) (h : 0 < n) : m % n < n := by
  induction m using Nat.strongRecOn with
  | ind m ih =>
      classical
      by_cases hlt : m < n
      · exact (Nat.mod_eq_of_lt hlt).symm ▸ hlt
      · have hge : n ≤ m := Nat.le_of_not_gt hlt
        have hsub : m % n = (m - n) % n := Nat.mod_eq_sub_mod hge
        rw [hsub]
        have hmpos : 0 < m := Nat.lt_of_lt_of_le h hge
        have hmn : m - n < m := Nat.sub_lt hmpos h
        exact ih (m - n) hmn

def gcd (a b : Nat) : Nat :=
  if a = 0 then b
  else if b = 0 then a
  else if a ≤ b then gcd a (b % a) else gcd (a % b) b
termination_by a + b
decreasing_by
  simp_wf
  all_goals
    rename_i hna hnb hle
    first
    | exact Nat.lt_of_lt_of_le (RESEARCH_G_L001_mod_lt b a (Nat.pos_of_ne_zero hna)) hle
    | exact Nat.add_lt_add_right
        (Nat.lt_of_lt_of_le (RESEARCH_G_L001_mod_lt a b (Nat.pos_of_ne_zero hnb))
          (Nat.le_of_lt (Nat.lt_of_not_ge hle))) b

theorem RESEARCH_G_L002_gcd_dvd (a b : Nat) : gcd a b ∣ a ∧ gcd a b ∣ b := by
  induction h : a + b using Nat.strongRecOn generalizing a b with
  | ind s ih =>
      classical
      by_cases ha0 : a = 0
      · rw [ha0]
        unfold gcd
        simp only [↓reduceIte]
        exact ⟨Nat.dvd_zero b, Nat.dvd_refl b⟩
      · by_cases hb0 : b = 0
        · rw [hb0]
          unfold gcd
          simp only [ha0, ↓reduceIte]
          exact ⟨Nat.dvd_refl a, Nat.dvd_zero a⟩
        · by_cases hle : a ≤ b
          · unfold gcd
            simp only [ha0, hb0, hle, ↓reduceIte]
            have hdec : a + b % a < a + b := by
              exact Nat.add_lt_add_left (Nat.lt_of_lt_of_le (RESEARCH_G_L001_mod_lt b a (Nat.pos_of_ne_zero ha0)) hle) a
            have hdec' : a + b % a < s := by
              simpa [h] using hdec
            rcases ih (a + b % a) hdec' a (b % a) rfl with ⟨hga, hgba⟩
            -- b = a * (b / a) + b % a; gcd ∣ a and gcd ∣ b % a -> gcd ∣ b
            have h1 : gcd a (b % a) ∣ a * (b / a) :=
              Nat.dvd_trans hga (Nat.dvd_mul_right a (b / a))
            have hsum : gcd a (b % a) ∣ a * (b / a) + b % a := Nat.dvd_add h1 hgba
            have hb : a * (b / a) + b % a = b := Nat.div_add_mod b a
            exact ⟨hga, by simpa [hb] using hsum⟩
          · unfold gcd
            simp only [ha0, hb0, hle, ↓reduceIte]
            have hdec : a % b + b < a + b := by
              exact Nat.add_lt_add_right
                (Nat.lt_of_lt_of_le (RESEARCH_G_L001_mod_lt a b (Nat.pos_of_ne_zero hb0))
                  (Nat.le_of_lt (Nat.lt_of_not_ge hle))) b
            have hdec' : a % b + b < s := by
              simpa [h] using hdec
            rcases ih (a % b + b) hdec' (a % b) b rfl with ⟨hgab, hgb⟩
            -- a = b * (a / b) + a % b; gcd ∣ b and gcd ∣ a % b -> gcd ∣ a
            have h1 : gcd (a % b) b ∣ b * (a / b) :=
              Nat.dvd_trans hgb (Nat.dvd_mul_right b (a / b))
            have hsum : gcd (a % b) b ∣ b * (a / b) + a % b := Nat.dvd_add h1 hgab
            have ha : b * (a / b) + a % b = a := Nat.div_add_mod a b
            exact ⟨by simpa [ha] using hsum, hgb⟩

theorem RESEARCH_G_L002_gcd_dvd_left (a b : Nat) : gcd a b ∣ a := (RESEARCH_G_L002_gcd_dvd a b).1

theorem RESEARCH_G_L003_gcd_dvd_right (a b : Nat) : gcd a b ∣ b := (RESEARCH_G_L002_gcd_dvd a b).2

theorem RESEARCH_G_L004_dvd_gcd (a b c : Nat) (hc1 : c ∣ a) (hc2 : c ∣ b) : c ∣ gcd a b := by
  induction h : a + b using Nat.strongRecOn generalizing a b with
  | ind s ih =>
      classical
      by_cases ha0 : a = 0
      · rw [ha0]
        unfold gcd
        simp only [↓reduceIte]
        exact hc2
      · by_cases hb0 : b = 0
        · rw [hb0]
          unfold gcd
          simp only [ha0, ↓reduceIte]
          exact hc1
        · by_cases hle : a ≤ b
          · unfold gcd
            simp only [ha0, hb0, hle, ↓reduceIte]
            have hc : c ∣ b % a := by
              have hba : c ∣ a * (b / a) := Nat.dvd_trans hc1 (Nat.dvd_mul_right a (b / a))
              have hsum : c ∣ a * (b / a) + b % a := by
                simpa [Nat.div_add_mod b a] using hc2
              have hsub : c ∣ (a * (b / a) + b % a) - a * (b / a) := Nat.dvd_sub hsum hba
              have hcalc : (a * (b / a) + b % a) - a * (b / a) = b % a := by
                rw [Nat.add_comm]
                exact Nat.add_sub_cancel (b % a) (a * (b / a))
              simpa [hcalc] using hsub
            have hdec : a + b % a < a + b := by
              exact Nat.add_lt_add_left (Nat.lt_of_lt_of_le (RESEARCH_G_L001_mod_lt b a (Nat.pos_of_ne_zero ha0)) hle) a
            have hdec' : a + b % a < s := by
              simpa [h] using hdec
            exact ih (a + b % a) hdec' a (b % a) hc1 hc rfl
          · unfold gcd
            simp only [ha0, hb0, hle, ↓reduceIte]
            have hc : c ∣ a % b := by
              have hab : c ∣ b * (a / b) := Nat.dvd_trans hc2 (Nat.dvd_mul_right b (a / b))
              have hsum : c ∣ b * (a / b) + a % b := by
                simpa [Nat.div_add_mod a b] using hc1
              have hsub : c ∣ (b * (a / b) + a % b) - b * (a / b) := Nat.dvd_sub hsum hab
              have hcalc : (b * (a / b) + a % b) - b * (a / b) = a % b := by
                rw [Nat.add_comm]
                exact Nat.add_sub_cancel (a % b) (b * (a / b))
              simpa [hcalc] using hsub
            have hdec : a % b + b < a + b := by
              exact Nat.add_lt_add_right
                (Nat.lt_of_lt_of_le (RESEARCH_G_L001_mod_lt a b (Nat.pos_of_ne_zero hb0))
                  (Nat.le_of_lt (Nat.lt_of_not_ge hle))) b
            have hdec' : a % b + b < s := by
              simpa [h] using hdec
            exact ih (a % b + b) hdec' (a % b) b hc hc2 rfl



theorem RESEARCH_G_L005_natAbs_ofNat (n : Nat) : ((n : Int).natAbs) = n := by
  have hnonneg : 0 ≤ (n : Int) := by
    cases n with
    | zero => exact Int.ofNat_le.mpr (Nat.zero_le 0)
    | succ n => exact Int.ofNat_le.mpr (Nat.zero_le _)
  have hcast := Int.ofNat_natAbs_of_nonneg hnonneg
  exact (Int.ofNat_inj.mp hcast)

theorem RESEARCH_G_T001_bezout : ∀ a b, ∃ x y : Int,
    (gcd a b : Int) = (a : Int) * x + (b : Int) * y := by
  intro a b
  induction h : a + b using Nat.strongRecOn generalizing a b with
  | ind s ih =>
      classical
      by_cases ha0 : a = 0
      · rw [ha0]
        unfold gcd
        simp only [↓reduceIte]
        refine ⟨0, 1, ?_⟩
        simp
      · by_cases hb0 : b = 0
        · rw [hb0]
          unfold gcd
          simp only [ha0, ↓reduceIte]
          refine ⟨1, 0, ?_⟩
          simp
        · by_cases hle : a ≤ b
          · unfold gcd
            simp only [ha0, hb0, hle, ↓reduceIte]
            have hdec : a + b % a < a + b := by
              exact Nat.add_lt_add_left (Nat.lt_of_lt_of_le (RESEARCH_G_L001_mod_lt b a (Nat.pos_of_ne_zero ha0)) hle) a
            have hdec' : a + b % a < s := by
              simpa [h] using hdec
            rcases ih (a + b % a) hdec' a (b % a) rfl with ⟨x, y, hxy⟩
            have hsum_nat : b % a + a * (b / a) = b := by
              rw [Nat.add_comm]
              exact Nat.div_add_mod b a
            have hmod_nat : b % a = b - a * (b / a) := Nat.eq_sub_of_add_eq hsum_nat
            have hle' : a * (b / a) ≤ b := by
              simpa [Nat.div_add_mod b a] using Nat.le_add_right (a * (b / a)) (b % a)
            have hmod_int : ((b % a : Nat) : Int) = (b : Int) - (a : Int) * ((b / a : Nat) : Int) := by
              rw [hmod_nat]
              rw [Int.ofNat_sub hle']
              rw [Int.natCast_mul]
            refine ⟨x - ((b / a : Nat) : Int) * y, y, ?_⟩
            rw [hxy]
            rw [hmod_int]
            rw [Int.sub_mul]
            rw [Int.mul_sub]
            rw [Int.mul_assoc]
            omega
          · unfold gcd
            simp only [ha0, hb0, hle, ↓reduceIte]
            have hdec : a % b + b < a + b := by
              exact Nat.add_lt_add_right
                (Nat.lt_of_lt_of_le (RESEARCH_G_L001_mod_lt a b (Nat.pos_of_ne_zero hb0))
                  (Nat.le_of_lt (Nat.lt_of_not_ge hle))) b
            have hdec' : a % b + b < s := by
              simpa [h] using hdec
            rcases ih (a % b + b) hdec' (a % b) b rfl with ⟨x, y, hxy⟩
            have hsum_nat : a % b + b * (a / b) = a := by
              rw [Nat.add_comm]
              exact Nat.div_add_mod a b
            have hmod_nat : a % b = a - b * (a / b) := Nat.eq_sub_of_add_eq hsum_nat
            have hle' : b * (a / b) ≤ a := by
              simpa [Nat.div_add_mod a b] using Nat.le_add_right (b * (a / b)) (a % b)
            have hmod_int : ((a % b : Nat) : Int) = (a : Int) - (b : Int) * ((a / b : Nat) : Int) := by
              rw [hmod_nat]
              rw [Int.ofNat_sub hle']
              rw [Int.natCast_mul]
            refine ⟨x, y - ((a / b : Nat) : Int) * x, ?_⟩
            rw [hxy]
            rw [hmod_int]
            rw [Int.sub_mul]
            rw [Int.mul_sub]
            rw [Int.mul_assoc]
            omega

theorem RESEARCH_G_T002_prime_gcd_one_or_p (p a : Nat) (hp : Prime p) :
    gcd p a = 1 ∨ gcd p a = p := by
  have hdp : gcd p a ∣ p := RESEARCH_G_L002_gcd_dvd_left p a
  exact hp.2 (gcd p a) hdp

theorem RESEARCH_G_T003_prime_dvd_mul (p a b : Nat) (hp : Prime p) (h : p ∣ a * b) :
    p ∣ a ∨ p ∣ b := by
  classical
  by_cases ha : p ∣ a
  · exact Or.inl ha
  · right
    have hg : gcd p a = 1 := by
      rcases RESEARCH_G_T002_prime_gcd_one_or_p p a hp with h1 | h2
      · exact h1
      · exfalso
        have hpa : p ∣ a := by
          rw [← h2]
          exact RESEARCH_G_L003_gcd_dvd_right p a
        exact ha hpa
    rcases RESEARCH_G_T001_bezout p a with ⟨x, y, hxy⟩
    have hone : (1 : Int) = (p : Int) * x + (a : Int) * y := by
      simpa [hg] using hxy
    have hpd : (p : Int) ∣ (a : Int) * (b : Int) := by
      rcases h with ⟨c, hc⟩
      refine ⟨(c : Int), ?_⟩
      rw [← Int.natCast_mul]
      rw [hc]
      rw [Int.natCast_mul]
    have hpd_mul : (p : Int) ∣ (a : Int) * (b : Int) * y :=
      Int.dvd_trans hpd (Int.dvd_mul_right ((a : Int) * (b : Int)) y)
    have h1 : (p : Int) ∣ (b : Int) * ((p : Int) * x) := by
      refine ⟨(b : Int) * x, ?_⟩
      rw [← Int.mul_assoc]
      rw [Int.mul_comm (b : Int) (p : Int)]
      rw [Int.mul_assoc]
    have h2 : (p : Int) ∣ (b : Int) * ((a : Int) * y) := by
      have hre : (b : Int) * ((a : Int) * y) = (a : Int) * (b : Int) * y := by
        rw [← Int.mul_assoc]
        rw [Int.mul_comm (b : Int) (a : Int)]
      simpa [hre] using hpd_mul
    have hsum : (p : Int) ∣ (b : Int) * ((p : Int) * x) + (b : Int) * ((a : Int) * y) :=
      Int.dvd_add h1 h2
    have hpb : (p : Int) ∣ (b : Int) := by
      have hrewrite : (b : Int) * ((p : Int) * x) + (b : Int) * ((a : Int) * y) =
          (b : Int) * ((p : Int) * x + (a : Int) * y) := by
        rw [Int.mul_add]
      have hb : (b : Int) = (b : Int) * ((p : Int) * x + (a : Int) * y) := by
        calc
          (b : Int) = (b : Int) * 1 := by rw [Int.mul_one]
          _ = (b : Int) * ((p : Int) * x + (a : Int) * y) := by rw [hone]
      have hsum' : (p : Int) ∣ (b : Int) * ((p : Int) * x + (a : Int) * y) := by
        simpa [hrewrite] using hsum
      rcases hsum' with ⟨k, hk⟩
      refine ⟨k, ?_⟩
      calc
        (b : Int) = (b : Int) * ((p : Int) * x + (a : Int) * y) := hb
        _ = (p : Int) * k := hk
    rcases hpb with ⟨c, hc⟩
    refine ⟨c.natAbs, ?_⟩
    have hnat : b = p * c.natAbs := by
      have hrev : p * c.natAbs = b := by
        simpa [RESEARCH_G_L005_natAbs_ofNat, Int.natAbs_mul] using
          (congrArg Int.natAbs hc.symm)
      exact hrev.symm
    exact hnat

#check RESEARCH_G_T001_bezout
#check RESEARCH_G_T003_prime_dvd_mul

end Veyra
