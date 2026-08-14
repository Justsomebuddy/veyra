import VeyraResearchBinomSum
import VeyraResearchGcd

namespace Veyra

/- A classical Nat Fermat corollary for the local `Prime` predicate.

It is separate candidate research, not a native resonance-prime theorem or
registry promotion.
-/

-- mod-equality bridge: x % p = y % p with y ≤ x forces p ∣ x - y.
theorem RESEARCH_FC_L001_dvd_sub_of_mod_eq (x y p : Nat) (hmod : x % p = y % p) :
    p ∣ x - y := by
  have hdivx : p * (x / p) + x % p = x := Nat.div_add_mod x p
  have hdivy : p * (y / p) + y % p = y := Nat.div_add_mod y p
  refine ⟨x / p - y / p, ?_⟩
  calc
    x - y = (p * (x / p) + x % p) - (p * (y / p) + y % p) := by
      conv =>
        lhs
        rw [← hdivx, ← hdivy]
    _ = (p * (x / p) + y % p) - (p * (y / p) + y % p) := by rw [hmod]
    _ = p * (x / p) - p * (y / p) := Nat.add_sub_add_right (p * (x / p)) (y % p) (p * (y / p))
    _ = p * (x / p - y / p) := by rw [← Nat.mul_sub]

-- cancellation in mod-prime arithmetic: (a*b) ≡ a (mod p), p ∤ a → b ≡ 1.
theorem RESEARCH_FC_L002_prime_cancel_mod (p a b : Nat) (hp : Prime p) (hpa : ¬ p ∣ a)
    (hb1 : 1 ≤ b) (hmod : (a * b) % p = a % p) : b % p = 1 % p := by
  have hab : a ≤ a * b := by
    have hmul := Nat.mul_le_mul_left a hb1
    simpa using hmul
  have hsub : p ∣ a * b - a := RESEARCH_FC_L001_dvd_sub_of_mod_eq (a * b) a p hmod
  have hfactor : a * b - a = a * (b - 1) := by
    calc
      a * b - a = a * b - a * 1 := by
        simp only [Nat.mul_one]
      _ = a * (b - 1) := by rw [← Nat.mul_sub a b 1]
  have hdiv : p ∣ a * (b - 1) := by simpa [hfactor] using hsub
  have hprime := RESEARCH_G_T003_prime_dvd_mul p a (b - 1) hp hdiv
  have hb : p ∣ b - 1 := hprime.resolve_left hpa
  rcases hb with ⟨k, hk⟩
  have hbrec : b = p * k + 1 := by
    rw [← hk]
    exact (Nat.sub_add_cancel hb1).symm
  calc
    b % p = (p * k + 1) % p := by rw [hbrec]
    _ = (1 + p * k) % p := by rw [Nat.add_comm]
    _ = 1 % p := Nat.add_mul_mod_self_left 1 p k

-- The classical corollary: p ∤ a → a^(p-1) ≡ 1 (mod p).
theorem RESEARCH_FC_T001_fermat_corollary (p a : Nat) (hp : Prime p) (hpa : ¬ p ∣ a) :
    a ^ (p - 1) % p = 1 % p := by
  have h1p : 1 ≤ p := Nat.le_trans (Nat.le_succ 1) hp.1
  have hpsub : p = p - 1 + 1 := (Nat.sub_add_cancel h1p).symm
  have hfermat := RESEARCH_BS_T003_fermat p a hp
  have hpow : a ^ p = a * a ^ (p - 1) := by
    conv =>
      lhs
      rw [hpsub]
    rw [Nat.pow_succ]
    rw [Nat.mul_comm]
  rw [hpow] at hfermat
  have ha0 : a ≠ 0 := by
    intro h
    subst h
    exact hpa (Nat.dvd_zero p)
  have ha1 : 1 ≤ a := Nat.succ_le_of_lt (Nat.pos_of_ne_zero ha0)
  have hb1 : 1 ≤ a ^ (p - 1) :=
    Nat.one_le_pow (p - 1) a (Nat.lt_of_lt_of_le (Nat.zero_lt_succ 0) ha1)
  exact RESEARCH_FC_L002_prime_cancel_mod p a (a ^ (p - 1)) hp hpa hb1 hfermat

-- The textbook form: a^(p-1) % p = 1 for prime p ≥ 2 and p ∤ a.
theorem RESEARCH_FC_T002_fermat_corollary_one (p a : Nat) (hp : Prime p) (hpa : ¬ p ∣ a) :
    a ^ (p - 1) % p = 1 := by
  have hmain := RESEARCH_FC_T001_fermat_corollary p a hp hpa
  rw [hmain]
  exact Nat.mod_eq_of_lt (Nat.lt_of_lt_of_le (by decide : 1 < 2) hp.1)

#check RESEARCH_FC_T001_fermat_corollary
#check RESEARCH_FC_T002_fermat_corollary_one

end Veyra
