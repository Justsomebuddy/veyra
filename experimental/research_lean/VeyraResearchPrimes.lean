import Std.Tactic

namespace Veyra

/- Classical prime-number theory over Nat using the local predicate below.

These declarations do not identify this predicate with Veyra resonance-prime
or numeric-prime modes and do not close the native number-theory repair track.
The checker reports dependency closure separately from source compilation.
-/

def Prime (n : Nat) : Prop := 2 ≤ n ∧ ∀ d, d ∣ n → d = 1 ∨ d = n

def listProd : List Nat → Nat
  | [] => 1
  | a :: rest => a * listProd rest

theorem RESEARCH_P_L001_prime_positive (p : Nat) (h : Prime p) : 0 < p := by
  exact Nat.lt_of_lt_of_le (Nat.zero_lt_succ 1) h.1

theorem RESEARCH_P_L002_mem_dvd_listProd (L : List Nat) : ∀ p, p ∈ L → p ∣ listProd L := by
  induction L with
  | nil =>
      intro p h
      exact False.elim ((List.mem_nil_iff p).mp h)
  | cons a rest ih =>
      intro p h
      have hmem : p = a ∨ p ∈ rest := (List.mem_cons.mp h)
      cases hmem with
      | inl hpa =>
          rw [hpa]
          exact Nat.dvd_mul_right a (listProd rest)
      | inr hpr =>
          have hrest : p ∣ listProd rest := ih p hpr
          exact Nat.dvd_trans hrest (Nat.dvd_mul_left (listProd rest) a)

-- Every number ≥ 2 has a prime divisor.
theorem RESEARCH_P_T001_exists_prime_divisor : ∀ n, 2 ≤ n → ∃ p, Prime p ∧ p ∣ n := by
  intro n
  induction n using Nat.strongRecOn with
  | ind n ih =>
      intro h2
      classical
      by_cases hpr : Prime n
      · exact ⟨n, hpr, Nat.dvd_refl n⟩
      · have hnotall : ¬ ∀ d, d ∣ n → d = 1 ∨ d = n := by
          intro hall
          exact hpr ⟨h2, hall⟩
        have hex : ∃ d, d ∣ n ∧ ¬ (d = 1 ∨ d = n) := by
          apply Classical.byContradiction
          intro hno
          apply hnotall
          intro d hd
          apply Classical.byContradiction
          intro hnd
          exact hno ⟨d, hd, hnd⟩
        rcases hex with ⟨d, hd, hnd⟩
        have hne1 : d ≠ 1 := by
          intro h
          exact hnd (Or.inl h)
        have hnen : d ≠ n := by
          intro h
          exact hnd (Or.inr h)
        have hnpos : 0 < n := Nat.lt_of_lt_of_le (Nat.zero_lt_succ 1) h2
        have hle : d ≤ n := Nat.le_of_dvd hnpos hd
        have hdn : d < n := Nat.lt_of_le_of_ne hle hnen
        have hd0 : d ≠ 0 := by
          intro hdzero
          have hn0 : n = 0 := by
            rw [hdzero] at hd
            exact Nat.eq_zero_of_zero_dvd hd
          exact (Nat.ne_of_gt hnpos) hn0
        have hdpos : 0 < d := Nat.pos_of_ne_zero hd0
        have hd2 : 2 ≤ d := by
          cases d with
          | zero => exact False.elim (Nat.lt_irrefl 0 hdpos)
          | succ d' =>
              cases d' with
              | zero => exact False.elim (hne1 rfl)
              | succ d'' =>
                  exact Nat.succ_le_succ (Nat.succ_le_succ (Nat.zero_le d''))
        rcases ih d hdn hd2 with ⟨p, hpp, hpd⟩
        exact ⟨p, hpp, Nat.dvd_trans hpd hd⟩

-- A divisor of both the product and product-plus-one divides one.
theorem RESEARCH_P_T002_dvd_one_of_dvd_prod_succ (L : List Nat) (q : Nat) :
    q ∣ listProd L → q ∣ listProd L + 1 → q ∣ 1 := by
  intro h1 h2
  have hsub : q ∣ (listProd L + 1) - listProd L := Nat.dvd_sub h2 h1
  have hcalc : (listProd L + 1) - listProd L = 1 := by
    rw [Nat.add_comm]
    exact Nat.add_sub_cancel 1 (listProd L)
  simpa [hcalc] using hsub

-- Euclid: every finite list of primes misses a prime.
theorem RESEARCH_P_T003_euclid (L : List Nat) (hL : ∀ p ∈ L, Prime p) :
    ∃ q, Prime q ∧ ∀ p ∈ L, q ≠ p := by
  have hone : 1 ≤ listProd L := by
    induction L with
    | nil => exact Nat.le_refl 1
    | cons a rest ih =>
        have hpa : Prime a := hL a (by exact List.mem_cons_self)
        have ha1 : 1 ≤ a := Nat.le_trans (Nat.le_succ 1) hpa.1
        have hrest : 1 ≤ listProd rest := ih (fun p hp => hL p (List.mem_cons_of_mem a hp))
        have hle : listProd rest ≤ a * listProd rest :=
          Nat.le_mul_of_pos_left (listProd rest) (Nat.lt_of_lt_of_le (Nat.zero_lt_succ 0) ha1)
        exact Nat.le_trans hrest hle
  have hprod2 : 2 ≤ listProd L + 1 := Nat.succ_le_succ hone
  rcases RESEARCH_P_T001_exists_prime_divisor (listProd L + 1) hprod2 with ⟨q, hq, hqd⟩
  refine ⟨q, hq, ?_⟩
  intro p hp hqp
  have hpd : p ∣ listProd L := RESEARCH_P_L002_mem_dvd_listProd L p hp
  have hq_prod : q ∣ listProd L := by
    simpa [hqp] using hpd
  have hq1 : q ∣ 1 := RESEARCH_P_T002_dvd_one_of_dvd_prod_succ L q hq_prod hqd
  have hqeq1 : q = 1 := (Nat.dvd_one.mp hq1)
  have h1ltq : 1 < q := Nat.lt_of_lt_of_le (by decide : 1 < 2) hq.1
  exact (Nat.ne_of_gt h1ltq) hqeq1

-- The smallest prime exists.
theorem RESEARCH_P_T004_two_prime : Prime 2 := by
  constructor
  · decide
  · intro d hd
    have hle : d ≤ 2 := Nat.le_of_dvd (by decide : 0 < 2) hd
    cases d with
    | zero =>
        exfalso
        have h2zero : (2 : Nat) = 0 := Nat.eq_zero_of_zero_dvd hd
        exact (by decide : (2 : Nat) ≠ 0) h2zero
    | succ d' =>
        cases d' with
        | zero => exact Or.inl rfl
        | succ d'' =>
            have hle2 : 2 ≤ d'' + 2 := Nat.succ_le_succ (Nat.succ_le_succ (Nat.zero_le d''))
            have heq : d'' + 2 = 2 := Nat.le_antisymm hle hle2
            have hz : d'' = 0 := by
              have := Nat.add_right_cancel (show d'' + 2 = 0 + 2 from by
                rw [Nat.zero_add]
                exact heq)
              simpa using this
            subst hz
            exact Or.inr rfl

#check RESEARCH_P_T001_exists_prime_divisor
#check RESEARCH_P_T003_euclid
#check RESEARCH_P_T004_two_prime

end Veyra
