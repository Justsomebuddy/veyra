import VeyraResearchCards
import VeyraResearchFermat
import Std.Tactic

namespace Veyra

/- Classical Nat binomial and Fermat-little-theorem identities.

The local `Prime` predicate is not a Veyra resonance-prime bridge, so these
results do not close the native number-theory repair track.
-/

def binomSum (n x : Nat) : Nat :=
  List.foldl (fun s k => s + choose n k * x ^ k) 0 (List.range (n + 1))

theorem RESEARCH_BS_L001_foldl_append {α : Type} (f : α → Nat → α) (init : α)
    (l1 l2 : List Nat) :
    List.foldl f init (l1 ++ l2) = List.foldl f (List.foldl f init l1) l2 := by
  induction l1 generalizing init with
  | nil => rfl
  | cons h t ih => simp [List.foldl, ih]

theorem RESEARCH_BS_L002_foldl_congr (f g : Nat → Nat) :
    ∀ l init, (∀ k, k ∈ l → f k = g k) →
      List.foldl (fun s k => s + f k) init l = List.foldl (fun s k => s + g k) init l := by
  intro l
  induction l with
  | nil => intro init _; rfl
  | cons h t ih =>
      intro init hcongr
      simp [List.foldl]
      rw [hcongr h (by exact List.mem_cons_self)]
      exact ih (init + g h) (fun k hk => hcongr k (List.mem_cons_of_mem h hk))

theorem RESEARCH_BS_L003_foldl_add (f g : Nat → Nat) :
    ∀ l a b, List.foldl (fun s k => s + (f k + g k)) (a + b) l =
      List.foldl (fun s k => s + f k) a l + List.foldl (fun s k => s + g k) b l := by
  intro l
  induction l with
  | nil => intro a b; rfl
  | cons h t ih =>
      intro a b
      simp [List.foldl]
      have hre : a + b + (f h + g h) = a + f h + (b + g h) := by ac_rfl
      rw [hre]
      exact ih (a + f h) (b + g h)

theorem RESEARCH_BS_L004_foldl_mul (x : Nat) (f : Nat → Nat) :
    ∀ l init, x * List.foldl (fun s k => s + f k) init l =
      List.foldl (fun s k => s + x * f k) (x * init) l := by
  intro l
  induction l with
  | nil => intro init; simp
  | cons h t ih =>
      intro init
      simp [List.foldl]
      simpa [Nat.mul_add] using ih (init + f h)

theorem RESEARCH_BS_L005_range_succ (n : Nat) :
    List.range (n + 2) = 0 :: List.map (fun i => i + 1) (List.range (n + 1)) := by
  induction n with
  | zero => rfl
  | succ n ih =>
      conv =>
        lhs
        rw [List.range_succ]
      conv =>
        lhs
        rw [ih]
      conv =>
        rhs
        rw [List.range_succ]
      simp [List.map]

theorem RESEARCH_BS_L005b_range_succ_head (n : Nat) :
    List.range (n + 1) = 0 :: List.map (fun i => i + 1) (List.range n) := by
  induction n with
  | zero => rfl
  | succ n ih =>
      conv =>
        lhs
        rw [List.range_succ]
      conv =>
        lhs
        rw [ih]
      conv =>
        rhs
        rw [List.range_succ]
      simp [List.map]

-- The aligned running invariant: for every m, the 1..m+1 tail sum plus the
-- h(m+1) term equals h 1 plus the 2..m+2 tail sum. No zero hypothesis is
-- needed until the final step.
theorem RESEARCH_BS_L006_shift_aux (h : Nat → Nat) :
    ∀ m, List.foldl (fun s j => s + h (j + 1)) 0 (List.range m) + h (m + 1) =
      h 1 + List.foldl (fun s j => s + h (j + 2)) 0 (List.range m) := by
  intro m
  induction m with
  | zero => simp
  | succ m ih =>
      conv =>
        lhs
        rw [List.range_succ]
      rw [RESEARCH_BS_L001_foldl_append]
      simp [List.foldl]
      conv =>
        rhs
        rw [List.range_succ]
      rw [RESEARCH_BS_L001_foldl_append]
      simp [List.foldl]
      rw [ih]
      ac_rfl

theorem RESEARCH_BS_L006_shift (n : Nat) (h : Nat → Nat) (hzero : h (n + 1) = 0) :
    List.foldl (fun s j => s + h (j + 1)) 0 (List.range n) =
      h 1 + List.foldl (fun s j => s + h (j + 2)) 0 (List.range n) := by
  have hmain := RESEARCH_BS_L006_shift_aux h n
  rw [hzero] at hmain
  simpa using hmain

theorem RESEARCH_BS_L007_foldl_dvd (p : Nat) (f : Nat → Nat) :
    ∀ l init, p ∣ init → (∀ k, k ∈ l → p ∣ f k) →
      p ∣ List.foldl (fun s k => s + f k) init l := by
  intro l
  induction l with
  | nil => intro init hinit _; exact hinit
  | cons h t ih =>
      intro init hinit hdvd
      simp [List.foldl]
      exact ih (init + f h)
        (Nat.dvd_add hinit (hdvd h (by exact List.mem_cons_self)))
        (fun k hk => hdvd k (List.mem_cons_of_mem h hk))

theorem RESEARCH_BS_L008_foldl_init (f : Nat → Nat) :
    ∀ l init, List.foldl (fun s k => s + f k) init l =
      init + List.foldl (fun s k => s + f k) 0 l := by
  intro l
  induction l with
  | nil => intro init; simp
  | cons h t ih =>
      intro init
      simp [List.foldl]
      rw [ih (init + f h)]
      rw [ih (f h)]
      ac_rfl

-- Binomial theorem as a sum identity: (x+1)^n = binomSum n x.
theorem RESEARCH_BS_T001_binomial_sum (n : Nat) : ∀ x, (x + 1) ^ n = binomSum n x := by
  induction n with
  | zero =>
      intro x
      simp [binomSum, choose]
  | succ n ih =>
      intro x
      rw [Nat.pow_succ]
      rw [ih]
      rw [Nat.mul_comm]
      unfold binomSum
      rw [RESEARCH_BS_L005_range_succ]
      simp [List.foldl]
      -- goal: (x+1) * S = foldl (choose (n+1) k x^k) (choose (n+1) 0) (map(+1)(range (n+1)))
      rw [List.foldl_map]
      rw [show choose (n + 1) 0 = 1 from rfl]
      -- goal: (x+1) * S = foldl (fun s j => s + choose (n+1) (j+1) * x^(j+1)) 1 (range (n+1))
      have hpascal : ∀ j, j ∈ List.range (n + 1) →
          choose (n + 1) (j + 1) * x ^ (j + 1) =
            (choose n j + choose n (j + 1)) * x ^ (j + 1) := by
        intro j _
        simp [choose]
      rw [RESEARCH_BS_L002_foldl_congr
        (fun j => choose (n + 1) (j + 1) * x ^ (j + 1))
        (fun j => (choose n j + choose n (j + 1)) * x ^ (j + 1))
        (List.range (n + 1)) 1 hpascal]
      rw [RESEARCH_BS_L002_foldl_congr
        (fun j => (choose n j + choose n (j + 1)) * x ^ (j + 1))
        (fun j => choose n j * x ^ (j + 1) + choose n (j + 1) * x ^ (j + 1))
        (List.range (n + 1)) 1 (by intro j _; simp only [Nat.add_mul])]
      rw [RESEARCH_BS_L008_foldl_init
        (fun j => choose n j * x ^ (j + 1) + choose n (j + 1) * x ^ (j + 1))
        (List.range (n + 1)) 1]
      rw [RESEARCH_BS_L003_foldl_add (fun j => choose n j * x ^ (j + 1))
        (fun j => choose n (j + 1) * x ^ (j + 1))
        (List.range (n + 1)) 0 0]
      -- goal: (x+1) * S = 1 + (foldl A + foldl B)
      have hfirst : List.foldl (fun s j => s + choose n j * x ^ (j + 1)) 0
            (List.range (n + 1)) = x * binomSum n x := by
        have hcong : (∀ j, j ∈ List.range (n + 1) →
            choose n j * x ^ (j + 1) = x * (choose n j * x ^ j)) := by
          intro j _
          rw [Nat.pow_succ]
          rw [Nat.mul_comm (x ^ j) x]
          rw [← Nat.mul_assoc (choose n j) x (x ^ j)]
          rw [Nat.mul_comm (choose n j) x]
          rw [Nat.mul_assoc]
        rw [RESEARCH_BS_L002_foldl_congr
          (fun j => choose n j * x ^ (j + 1))
          (fun j => x * (choose n j * x ^ j))
          (List.range (n + 1)) 0 hcong]
        rw [← Nat.mul_zero x]
        rw [← RESEARCH_BS_L004_foldl_mul x (fun j => choose n j * x ^ j)
          (List.range (n + 1)) 0]
        rfl
      rw [hfirst]
      have hsecond : 1 + List.foldl (fun s j => s + choose n (j + 1) * x ^ (j + 1)) 0
            (List.range (n + 1)) = binomSum n x := by
        unfold binomSum
        rw [RESEARCH_BS_L005b_range_succ_head]
        simp [List.foldl]
        rw [RESEARCH_BS_L008_foldl_init (fun j => choose n (j + 1) * x ^ (j + 1))
          (List.map (fun i => i + 1) (List.range n)) (choose n 1 * x)]
        rw [RESEARCH_BS_L008_foldl_init (fun k => choose n k * x ^ k)
          (List.map (fun i => i + 1) (List.range n)) (choose n 0)]
        rw [show choose n 0 = 1 from by simp [choose]]
        congr 1
        rw [List.foldl_map]
        rw [List.foldl_map]
        rw [RESEARCH_BS_L006_shift n (fun k => choose n k * x ^ k) (by
          simp [RESEARCH_L001_choose_above n (n + 1) (Nat.lt_succ_self n)])]
        have hcongrB : List.foldl (fun s j => s + choose n (j + 2) * x ^ (j + 2)) 0
              (List.range n) =
            List.foldl (fun s y => s + choose n (y + 1 + 1) * x ^ (y + 1 + 1)) 0
              (List.range n) := by
          exact RESEARCH_BS_L002_foldl_congr (fun j => choose n (j + 2) * x ^ (j + 2))
            (fun y => choose n (y + 1 + 1) * x ^ (y + 1 + 1)) (List.range n) 0
            (by intro j _; rfl)
        rw [hcongrB]
        rw [Nat.pow_one]
      calc
        (x + 1) * binomSum n x = x * binomSum n x + binomSum n x := by
          rw [Nat.add_mul, Nat.one_mul]
        _ = 1 + (x * binomSum n x +
              List.foldl (fun s j => s + choose n (j + 1) * x ^ (j + 1)) 0
                (List.range (n + 1))) := by
          rw [← hsecond]
          rw [hsecond]
          omega

-- Freshmen's dream: (a+1)^p ≡ a^p + 1 (mod p) for prime p.
theorem RESEARCH_BS_T002_freshman_dream (p a : Nat) (hp : Prime p) :
    (a + 1) ^ p % p = (a ^ p + 1) % p := by
  rw [RESEARCH_BS_T001_binomial_sum]
  unfold binomSum
  rw [RESEARCH_BS_L005b_range_succ_head]
  simp [List.foldl]
  rw [List.foldl_map]
  rw [show choose p 0 = 1 from by simp [choose]]
  rw [RESEARCH_BS_L008_foldl_init (fun j => choose p (j + 1) * a ^ (j + 1)) (List.range p) 1]
  have hdecomp : List.foldl (fun s j => s + choose p (j + 1) * a ^ (j + 1)) 0
        (List.range p) =
      List.foldl (fun s j => s + choose p (j + 1) * a ^ (j + 1)) 0
        (List.range (p - 1)) + a ^ p := by
    have h1p : 1 ≤ p := Nat.le_trans (Nat.le_succ 1) hp.1
    have hpsub : p = p - 1 + 1 := (Nat.sub_add_cancel h1p).symm
    rw [hpsub]
    rw [List.range_succ]
    rw [RESEARCH_BS_L001_foldl_append]
    simp [List.foldl, Nat.sub_add_cancel h1p, RESEARCH_L002_choose_diag,
      Nat.pow_succ, Nat.one_mul]
  rw [hdecomp]
  have hmiddle : p ∣ List.foldl (fun s j => s + choose p (j + 1) * a ^ (j + 1)) 0
      (List.range (p - 1)) := by
    refine RESEARCH_BS_L007_foldl_dvd p (fun j => choose p (j + 1) * a ^ (j + 1))
      (List.range (p - 1)) 0 (Nat.dvd_zero p) ?_
    intro j hj
    have h1p : 1 ≤ p := Nat.le_trans (Nat.le_succ 1) hp.1
    have hjlt : j < p - 1 := List.mem_range.mp hj
    have hjlt' : j + 1 < p := by
      have := Nat.add_lt_add_right hjlt 1
      rwa [Nat.sub_add_cancel h1p] at this
    have hdivc : p ∣ choose p (j + 1) :=
      RESEARCH_F_T002_middle_choose_divisible p (j + 1) hp (Nat.succ_pos j) hjlt'
    exact Nat.dvd_trans hdivc (Nat.dvd_mul_right (choose p (j + 1)) (a ^ (j + 1)))
  rcases hmiddle with ⟨c, hc⟩
  rw [hc]
  rw [← Nat.add_assoc]
  rw [Nat.add_comm (1 + p * c) (a ^ p)]
  rw [← Nat.add_assoc]
  rw [Nat.add_mul_mod_self_left]

-- Fermat's little theorem, unbounded: for prime p and all a, a^p ≡ a (mod p).
theorem RESEARCH_BS_T003_fermat (p a : Nat) (hp : Prime p) :
    a ^ p % p = a % p := by
  induction a with
  | zero =>
      have hp0 : 0 < p := Nat.lt_of_lt_of_le (Nat.zero_lt_succ 1) hp.1
      cases p with
      | zero => cases hp0
      | succ p => simp
  | succ a ih =>
      rw [RESEARCH_BS_T002_freshman_dream p a hp]
      rw [Nat.add_mod]
      rw [ih]
      rw [← Nat.add_mod]

#check RESEARCH_BS_T001_binomial_sum
#check RESEARCH_BS_T002_freshman_dream
#check RESEARCH_BS_T003_fermat

end Veyra
