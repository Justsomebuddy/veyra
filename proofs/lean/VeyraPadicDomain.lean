import VeyraPadicCompletion

set_option autoImplicit false

namespace Veyra
namespace PadicDomain

/-! # `ZpVeyra` has no zero divisors — the first theorem that consumes primality

Every declaration of the PΩ2/N-family holds for an arbitrary base `b ≥ 2`
(`lim← Z/bⁿ`), because none of them uses `VeyraPrimeWitness.no_proper_divisor`.
This file makes the primality field load-bearing: a product of two families
that are nonzero at depths `n` and `m` is nonzero at depth `n + m`. The
argument is the classical valuation argument (`x = pᵃ·u` with `p ∤ u`), with
Euclid's lemma derived from `Nat.Coprime` in Lean core; no Mathlib. -/

/-- The prime witness in divisor form: every divisor of `p` is `1` or `p`. -/
theorem prime_divisor_dichotomy {p : Nat} (hp : VeyraPrimeWitness p) (d : Nat) (hd : d ∣ p) :
    d = 1 ∨ d = p := by
  have hp0 : 0 < p := Nat.lt_of_lt_of_le (Nat.zero_lt_succ 1) hp.two_le
  have hdle : d ≤ p := Nat.le_of_dvd hp0 hd
  rcases Nat.lt_or_ge d 2 with hlt | hge
  · -- d = 0 or d = 1
    cases d with
    | zero =>
        exfalso
        have : p = 0 := Nat.eq_zero_of_zero_dvd hd
        omega
    | succ d' =>
        cases d' with
        | zero => exact Or.inl rfl
        | succ _ => omega
  · rcases Nat.lt_or_eq_of_le hdle with hlt | heq
    · exfalso
      have hne := hp.no_proper_divisor ⟨d, hlt⟩ hge
      have hmod : p % d = 0 := Nat.mod_eq_zero_of_dvd hd
      rw [hmod] at hne
      exact absurd rfl (bne_iff_ne.mp hne)
    · exact Or.inr heq

/-- Euclid's lemma for the prime witness. -/
theorem prime_dvd_mul {p : Nat} (hp : VeyraPrimeWitness p) (u v : Nat) (h : p ∣ u * v) :
    p ∣ u ∨ p ∣ v := by
  by_cases hu : p ∣ u
  · exact Or.inl hu
  · right
    have hcop : Nat.Coprime p u := by
      rcases prime_divisor_dichotomy hp (Nat.gcd p u) (Nat.gcd_dvd_left p u) with h1 | h1
      · exact h1
      · exfalso
        exact hu (h1 ▸ Nat.gcd_dvd_right p u)
    exact Nat.Coprime.dvd_of_dvd_mul_left hcop h

/-- Coordinates of one family are compatible: the depth-`m` value is the depth-`n`
    value reduced modulo `p^(m+1)`. -/
theorem rho_val_mod {p : Nat} {hp : VeyraPrimeWitness p} (x : ZpVeyra hp) {m n : Nat}
    (h : m <= n) : (veyraRho m x).val = (veyraRho n x).val % veyraModulus p m := by
  have := congrArg Fin.val (x.property m n h)
  exact this.symm

/-- The canonical multiplication acts coordinatewise as `Fin` multiplication. -/
theorem mul_val {p : Nat} (hp : VeyraPrimeWitness p) (x y : ZpVeyra hp) (n : Nat) :
    (veyraRho n (veyraMulFamily (veyraCanonicalStageRingLaws hp) x y)).val =
      ((veyraRho n x).val * (veyraRho n y).val) % veyraModulus p n := by
  show ((x.val n) * (y.val n)).val = _
  rw [Fin.val_mul]
  rfl

/-- Valuation extraction: a value nonzero modulo `p^(n+1)` has a least depth `a ≤ n`
    at which it becomes nonzero; below it, it vanishes. -/
theorem exists_valuation (p X : Nat) :
    ∀ n, X % p ^ (n + 1) ≠ 0 → ∃ a, a ≤ n ∧ X % p ^ (a + 1) ≠ 0 ∧ X % p ^ a = 0 := by
  intro n
  induction n with
  | zero =>
      intro h
      exact ⟨0, Nat.le_refl 0, h, by rw [Nat.pow_zero, Nat.mod_one]⟩
  | succ n ih =>
      intro h
      by_cases hn : X % p ^ (n + 1) = 0
      · exact ⟨n + 1, Nat.le_refl _, h, hn⟩
      · obtain ⟨a, ha, h1, h2⟩ := ih hn
        exact ⟨a, Nat.le_succ_of_le ha, h1, h2⟩

/-- `X = pᵃ·u` with `p ∤ u`, from `pᵃ ∣ X` and `pᵃ⁺¹ ∤ X`. -/
theorem split_valuation {p : Nat} (hp : VeyraPrimeWitness p) (X a : Nat)
    (hdvd : X % p ^ a = 0) (hnot : X % p ^ (a + 1) ≠ 0) :
    ∃ u, X = p ^ a * u ∧ ¬ p ∣ u := by
  have hp0 : 0 < p := Nat.lt_of_lt_of_le (Nat.zero_lt_succ 1) hp.two_le
  have _hpa : 0 < p ^ a := Nat.pow_pos hp0
  have hd : p ^ a ∣ X := Nat.dvd_of_mod_eq_zero hdvd
  refine ⟨X / p ^ a, (Nat.mul_div_cancel' hd).symm, ?_⟩
  intro hpu
  apply hnot
  apply Nat.mod_eq_zero_of_dvd
  rw [Nat.pow_succ, ← Nat.mul_div_cancel' hd]
  exact Nat.mul_dvd_mul_left (p ^ a) hpu

-- theorem-card: product of families nonzero at depths n and m is nonzero at depth n+m
-- This is the integral-domain law of `ZpVeyra(p)` in coordinate form; it is the
-- first statement in the PΩ2 family whose proof consumes `no_proper_divisor`.
theorem THM_PD_001_product_nonzero_at_sum_depth {p : Nat} (hp : VeyraPrimeWitness p)
    (x y : ZpVeyra hp) (n m : Nat)
    (hx : (veyraRho n x).val ≠ 0) (hy : (veyraRho m y).val ≠ 0) :
    (veyraRho (n + m) (veyraMulFamily (veyraCanonicalStageRingLaws hp) x y)).val ≠ 0 := by
  have hp0 : 0 < p := Nat.lt_of_lt_of_le (Nat.zero_lt_succ 1) hp.two_le
  -- work with the depth-(n+m) values
  have hxN : (veyraRho n x).val = (veyraRho (n + m) x).val % p ^ (n + 1) :=
    rho_val_mod x (Nat.le_add_right n m)
  have hyN : (veyraRho m y).val = (veyraRho (n + m) y).val % p ^ (m + 1) :=
    rho_val_mod y (Nat.le_add_left m n)
  rw [hxN] at hx
  rw [hyN] at hy
  obtain ⟨a, ha, hxa, hxa'⟩ := exists_valuation p _ n hx
  obtain ⟨b, hb, hyb, hyb'⟩ := exists_valuation p _ m hy
  obtain ⟨u, hu, hpu⟩ := split_valuation hp _ a hxa' hxa
  obtain ⟨v, hv, hpv⟩ := split_valuation hp _ b hyb' hyb
  rw [mul_val, hu, hv]
  intro hzero
  have hdvd : p ^ (n + m + 1) ∣ p ^ a * u * (p ^ b * v) := Nat.dvd_of_mod_eq_zero hzero
  have hprod : p ^ a * u * (p ^ b * v) = p ^ (a + b) * (u * v) := by
    rw [Nat.mul_mul_mul_comm, ← Nat.pow_add]
  rw [hprod] at hdvd
  have hsplit : p ^ (n + m + 1) = p ^ (a + b) * p ^ (n + m + 1 - (a + b)) := by
    rw [← Nat.pow_add, Nat.add_sub_cancel' (by omega)]
  rw [hsplit] at hdvd
  have hpab : 0 < p ^ (a + b) := Nat.pow_pos hp0
  have hrest : p ^ (n + m + 1 - (a + b)) ∣ u * v := Nat.dvd_of_mul_dvd_mul_left hpab hdvd
  have hp1 : p ∣ p ^ (n + m + 1 - (a + b)) := by
    have hc : 1 ≤ n + m + 1 - (a + b) := by omega
    have := Nat.pow_dvd_pow p hc
    rw [Nat.pow_one] at this
    exact this
  rcases prime_dvd_mul hp u v (Nat.dvd_trans hp1 hrest) with h | h
  · exact hpu h
  · exact hpv h

-- theorem-card: nonzero families have a nonzero product at some depth (constructive form)
theorem THM_PD_002_nonzero_product_depth {p : Nat} (hp : VeyraPrimeWitness p)
    (x y : ZpVeyra hp) (hx : ∃ n, (veyraRho n x).val ≠ 0) (hy : ∃ m, (veyraRho m y).val ≠ 0) :
    ∃ k, (veyraRho k (veyraMulFamily (veyraCanonicalStageRingLaws hp) x y)).val ≠ 0 := by
  obtain ⟨n, hn⟩ := hx
  obtain ⟨m, hm⟩ := hy
  exact ⟨n + m, THM_PD_001_product_nonzero_at_sum_depth hp x y n m hn hm⟩

theorem zero_val {p : Nat} (hp : VeyraPrimeWitness p) (n : Nat) :
    (veyraRho n (veyraZeroFamily (veyraCanonicalStageRingLaws hp))).val = 0 := rfl

-- theorem-card: ZpVeyra(p) has no zero divisors (classical corollary; uses Classical.choice)
theorem THM_PD_003_no_zero_divisors {p : Nat} (hp : VeyraPrimeWitness p) (x y : ZpVeyra hp)
    (h : veyraMulFamily (veyraCanonicalStageRingLaws hp) x y =
      veyraZeroFamily (veyraCanonicalStageRingLaws hp)) :
    x = veyraZeroFamily (veyraCanonicalStageRingLaws hp) ∨
      y = veyraZeroFamily (veyraCanonicalStageRingLaws hp) := by
  by_cases hx : ∀ n, (veyraRho n x).val = 0
  · left
    apply THM_POMEGA2_009_joint_separation
    intro n
    apply Fin.ext
    rw [hx n]
    rfl
  · right
    apply THM_POMEGA2_009_joint_separation
    intro m
    apply Fin.ext
    show (veyraRho m y).val = 0
    apply Classical.byContradiction
    intro hy
    obtain ⟨n, hn⟩ := Classical.not_forall.mp hx
    have := THM_PD_001_product_nonzero_at_sum_depth hp x y n m hn hy
    apply this
    rw [h]
    rfl

#print axioms THM_PD_001_product_nonzero_at_sum_depth
#print axioms THM_PD_002_nonzero_product_depth
#print axioms THM_PD_003_no_zero_divisors

end PadicDomain
end Veyra
