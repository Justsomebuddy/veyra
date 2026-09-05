/-! # Primitive roots of words — Lyndon–Schützenberger, Mathlib-free

The "resonance-prime" of docs/11 is the primitive word: nonempty and not a
proper literal power. This file proves, for any alphabet type: powers of one
word commute (`THM_RT_001`); two words commute iff they are powers of a
common word (`THM_RT_002`, Lyndon–Schützenberger, strong induction on total
length); every nonempty word is a positive power of a primitive word
(`THM_RT_003`, constructive: a bounded decidable proper-period search, no
classical choice); and the primitive root and its exponent are unique
(`THM_RT_004`). This is the unique-factorization law of the free monoid
under the power relation — the exact content behind "every mode is uniquely
a power of a primitive rhythm" (docs/02 §4–5, docs/11 P2). Host-carried:
the statements quantify over host `List`/`Nat`. -/

namespace Veyra
namespace Root

variable {α : Type}

/-- Literal `n`-th power of a word by left concatenation. -/
def pow (u : List α) : Nat → List α
  | 0 => []
  | n + 1 => u ++ pow u n

theorem pow_succ (u : List α) (n : Nat) : pow u (n + 1) = u ++ pow u n := rfl

theorem pow_add (u : List α) (m n : Nat) : pow u (m + n) = pow u m ++ pow u n := by
  induction m with
  | zero => simp [pow]
  | succ m ih => rw [Nat.succ_add, pow_succ, pow_succ, ih, List.append_assoc]

theorem length_pow (u : List α) (n : Nat) : (pow u n).length = n * u.length := by
  induction n with
  | zero => simp [pow]
  | succ n ih => rw [pow_succ, List.length_append, ih, Nat.succ_mul, Nat.add_comm]

theorem pow_one (u : List α) : pow u 1 = u := by
  simp [pow]

theorem pow_pow (u : List α) (m n : Nat) : pow (pow u m) n = pow u (m * n) := by
  induction n with
  | zero => simp [pow]
  | succ n ih => rw [pow_succ, ih, Nat.mul_succ, Nat.add_comm, pow_add]

theorem pow_comm (u : List α) (m n : Nat) : pow u m ++ pow u n = pow u n ++ pow u m := by
  rw [← pow_add, ← pow_add, Nat.add_comm]

/-- Prefix extraction: if `x ++ l = l' ++ y` and `x` is no longer than `l'`, then `x` is a prefix of `l'`. -/
theorem prefix_of_append_eq {x l l' y : List α} (h : x ++ l = l' ++ y) (hlen : x.length ≤ l'.length) :
    x = l'.take x.length := by
  have hsplit : l' = l'.take x.length ++ l'.drop x.length := (List.take_append_drop _ _).symm
  rw [hsplit, List.append_assoc] at h
  have hlen' : x.length = (l'.take x.length).length := by
    rw [List.length_take, Nat.min_eq_left hlen]
  exact List.append_inj_left h hlen'

/-- A word commuting with a longer word is a prefix of it. -/
theorem prefix_of_comm {x w : List α} (h : x ++ w = w ++ x) (hlen : x.length ≤ w.length) :
    x = w.take x.length :=
  prefix_of_append_eq h hlen

-- theorem-card: powers of a common root commute
theorem THM_RT_001_pow_comm_of_root (z : List α) (i j : Nat) :
    pow z i ++ pow z j = pow z j ++ pow z i :=
  pow_comm z i j

/-- Lyndon–Schützenberger, one direction: commuting words are powers of a common word.
    Strong induction on the total length. -/
theorem comm_imp_common_root_aux (n : Nat) :
    ∀ (u v : List α), u.length + v.length ≤ n → u ++ v = v ++ u →
      ∃ z : List α, ∃ i j : Nat, u = pow z i ∧ v = pow z j := by
  induction n with
  | zero =>
      intro u v hn _
      have hu : u = [] := List.eq_nil_of_length_eq_zero (by omega)
      have hv : v = [] := List.eq_nil_of_length_eq_zero (by omega)
      exact ⟨[], 0, 0, by simp [hu, pow], by simp [hv, pow]⟩
  | succ n ih =>
      intro u v hn h
      -- symmetric reduction: assume |u| ≤ |v|
      have main : ∀ (u v : List α), u.length + v.length ≤ n + 1 → u ++ v = v ++ u →
          u.length ≤ v.length → ∃ z : List α, ∃ i j : Nat, u = pow z i ∧ v = pow z j := by
        intro u v hn h hle
        cases u with
        | nil => exact ⟨v, 0, 1, rfl, (pow_one v).symm⟩
        | cons a u' =>
            have hpre : (a :: u') = v.take (a :: u').length := prefix_of_comm h hle
            -- v = u ++ v'
            have hv : v = (a :: u') ++ v.drop (a :: u').length := by
              have hsplit := List.take_append_drop (a :: u').length v
              rw [← hpre] at hsplit
              exact hsplit.symm
            -- u ++ v' = v' ++ u
            have hcomm : (a :: u') ++ v.drop (a :: u').length = v.drop (a :: u').length ++ (a :: u') := by
              have h' := h
              rw [hv, List.append_assoc] at h'
              exact List.append_cancel_left h'
            have hlen' : (a :: u').length + (v.drop (a :: u').length).length ≤ n := by
              rw [List.length_drop]
              have : 0 < (a :: u').length := Nat.succ_pos _
              omega
            obtain ⟨z, i, j, hu, hv'⟩ := ih (a :: u') (v.drop (a :: u').length) hlen' hcomm
            have hv2 : v = pow z i ++ pow z j := by
              rw [← hu, ← hv']
              exact hv
            exact ⟨z, i, i + j, hu, by rw [hv2, pow_add]⟩
      rcases Nat.le_total u.length v.length with hle | hle
      · exact main u v hn h hle
      · obtain ⟨z, i, j, hv, hu⟩ := main v u (by omega) h.symm hle
        exact ⟨z, j, i, hu, hv⟩

-- theorem-card: Lyndon–Schützenberger commutation theorem for words
theorem THM_RT_002_comm_iff_common_root (u v : List α) :
    u ++ v = v ++ u ↔ ∃ z : List α, ∃ i j : Nat, u = pow z i ∧ v = pow z j := by
  constructor
  · intro h
    exact comm_imp_common_root_aux (u.length + v.length) u v (Nat.le_refl _) h
  · rintro ⟨z, i, j, rfl, rfl⟩
    exact pow_comm z i j


/-! ## Primitive words and the unique primitive root -/

/-- A word is primitive when it is nonempty and not a proper power. -/
def Primitive (u : List α) : Prop := u ≠ [] ∧ ∀ (z : List α) (i : Nat), u = pow z i → i = 1

theorem pow_nil (i : Nat) : pow ([] : List α) i = [] := by
  induction i with
  | zero => rfl
  | succ i ih => rw [pow_succ, ih]; rfl

theorem pow_zero_eq (u : List α) : pow u 0 = [] := rfl

theorem length_pos_of_primitive {u : List α} (h : Primitive u) : 0 < u.length := by
  cases u with
  | nil => exact absurd rfl h.1
  | cons a t => exact Nat.succ_pos _

/-- Prefix of a power: the first block of `pow z (i+1)` is `z`. -/
theorem take_pow_succ (z : List α) (i : Nat) : (pow z (i + 1)).take z.length = z := by
  rw [pow_succ, List.take_left]

theorem pow_comm_self (z : List α) (i : Nat) : z ++ pow z i = pow z i ++ z := by
  rw [← pow_one z, pow_pow, Nat.one_mul, pow_comm, pow_one]

/-- A primitive word that is a power of `t` equals `t`. -/
theorem primitive_pow_eq {z t : List α} (hz : Primitive z) (i : Nat) (h : z = pow t i) : z = t := by
  have := hz.2 t i h
  rw [h, this, pow_one]

/-- If two words commute and both are primitive, they are equal. -/
theorem primitive_comm_eq {z z' : List α} (hz : Primitive z) (hz' : Primitive z')
    (h : z ++ z' = z' ++ z) : z = z' := by
  obtain ⟨t, i, j, hi, hj⟩ := (THM_RT_002_comm_iff_common_root z z').mp h
  rw [primitive_pow_eq hz i hi, primitive_pow_eq hz' j hj]

/-- A word commuting with `u = z^i` (i ≥ 1) … : z commutes with every power of itself. -/
theorem comm_with_pow (z : List α) (i : Nat) : z ++ pow z i = pow z i ++ z :=
  pow_comm_self z i

-- theorem-card: the primitive root is unique (Lyndon–Schützenberger corollary)
theorem THM_RT_004_primitive_root_unique (u z z' : List α) (i j : Nat)
    (hz : Primitive z) (hz' : Primitive z') (hi : 0 < i) (hj : 0 < j)
    (hu : u = pow z i) (hu' : u = pow z' j) : z = z' ∧ i = j := by
  -- both roots commute with u, hence with each other via prefix comparison
  have hzu : z ++ u = u ++ z := by rw [hu]; exact comm_with_pow z i
  have hz'u : z' ++ u = u ++ z' := by rw [hu']; exact comm_with_pow z' j
  have hzz' : z ++ z' = z' ++ z := by
    -- case split on whether i = 1 or j = 1; otherwise both are ≤ half of u
    rcases Nat.lt_or_ge 1 i with hi2 | hi1
    · rcases Nat.lt_or_ge 1 j with hj2 | hj1
      · -- both proper powers: x := z ++ z' and y := z' ++ z both commute with u and are
        -- no longer than u, so both are the prefix of u of the same length
        have hlenz : 2 * z.length ≤ u.length := by
          rw [hu, length_pow]; exact Nat.mul_le_mul_right _ hi2
        have hlenz' : 2 * z'.length ≤ u.length := by
          rw [hu', length_pow]; exact Nat.mul_le_mul_right _ hj2
        have hx : (z ++ z') ++ u = u ++ (z ++ z') := by
          rw [List.append_assoc, hz'u, ← List.append_assoc, hzu, List.append_assoc]
        have hy : (z' ++ z) ++ u = u ++ (z' ++ z) := by
          rw [List.append_assoc, hzu, ← List.append_assoc, hz'u, List.append_assoc]
        have hlx : (z ++ z').length ≤ u.length := by rw [List.length_append]; omega
        have hly : (z' ++ z).length ≤ u.length := by rw [List.length_append]; omega
        have px := prefix_of_comm hx hlx
        have py := prefix_of_comm hy hly
        rw [px, py, List.length_append, List.length_append, Nat.add_comm]
      · -- j = 1: u = z', so z' = z^i and primitivity of z' gives i = 1
        have hj1' : j = 1 := Nat.le_antisymm hj1 hj
        rw [hj1', pow_one] at hu'
        rw [← hu', hu]
        exact comm_with_pow z i
    · have hi1' : i = 1 := Nat.le_antisymm hi1 hi
      rw [hi1', pow_one] at hu
      rw [← hu, hu']
      exact (comm_with_pow z' j).symm
  have hzeq : z = z' := primitive_comm_eq hz hz' hzz'
  refine ⟨hzeq, ?_⟩
  -- equal roots force equal exponents by length
  have hlen := congrArg List.length (hu.symm.trans hu')
  rw [length_pow, length_pow, hzeq] at hlen
  exact Nat.eq_of_mul_eq_mul_right (length_pos_of_primitive hz') hlen

section Existence

variable [DecidableEq α]

/-- Bounded proper-root test: `d` is a proper period of `u` when `0 < d < |u|`, `d ∣ |u|`
    and `u` is the `|u|/d`-th power of its length-`d` prefix. -/
def properRootAt (u : List α) (d : Nat) : Bool :=
  decide (0 < d) && decide (u.length % d = 0) && decide (u = pow (u.take d) (u.length / d))

theorem properRootAt_iff (u : List α) (d : Nat) :
    properRootAt u d = true ↔ 0 < d ∧ u.length % d = 0 ∧ u = pow (u.take d) (u.length / d) := by
  unfold properRootAt
  simp only [Bool.and_eq_true, decide_eq_true_iff]
  exact ⟨fun h => ⟨h.1.1, h.1.2, h.2⟩, fun h => ⟨⟨h.1, h.2.1⟩, h.2.2⟩⟩

/-- Existence: every nonempty word is a positive power of a primitive word.
    Strong induction on the length, with a bounded decidable search for a
    proper period; no classical choice is used. -/
theorem exists_primitive_root_aux (n : Nat) :
    ∀ (u : List α), u.length ≤ n → u ≠ [] →
      ∃ (z : List α) (i : Nat), Primitive z ∧ 0 < i ∧ u = pow z i := by
  induction n with
  | zero =>
      intro u hn hne
      exact absurd (List.eq_nil_of_length_eq_zero (Nat.le_zero.mp hn)) hne
  | succ n ih =>
      intro u hn hne
      have hupos : 0 < u.length := by
        cases u with
        | nil => exact absurd rfl hne
        | cons a t => exact Nat.succ_pos _
      cases hfind : (List.range u.length).find? (properRootAt u) with
      | some d =>
          have hd := (properRootAt_iff u d).mp (List.find?_some hfind)
          have hdlt : d < u.length := List.mem_range.mp (List.mem_of_find?_eq_some hfind)
          obtain ⟨hd0, hdvd, hpow⟩ := hd
          have hdvd' : d ∣ u.length := Nat.dvd_of_mod_eq_zero hdvd
          have htake_len : (u.take d).length = d := by
            rw [List.length_take, Nat.min_eq_left (Nat.le_of_lt hdlt)]
          have htake_ne : u.take d ≠ [] := by
            intro h; rw [h, List.length_nil] at htake_len; omega
          have hle : (u.take d).length ≤ n := by rw [htake_len]; omega
          obtain ⟨t, j, ht, hj, hz⟩ := ih (u.take d) hle htake_ne
          have hq : 0 < u.length / d := Nat.div_pos (Nat.le_of_lt hdlt) hd0
          have key : pow (u.take d) (u.length / d) = pow t (j * (u.length / d)) := by
            rw [hz, pow_pow]
          exact ⟨t, j * (u.length / d), ht, Nat.mul_pos hj hq, hpow.trans key⟩
      | none =>
          -- no proper period: u itself is primitive
          refine ⟨u, 1, ⟨hne, ?_⟩, Nat.one_pos, (pow_one u).symm⟩
          intro z i hzi
          have hnone := List.find?_eq_none.mp hfind
          -- i = 0 is impossible (u ≠ []), so i ≥ 1; show i ≤ 1
          cases i with
          | zero => exact absurd hzi hne
          | succ i' =>
              cases i' with
              | zero => rfl
              | succ i'' =>
                  exfalso
                  -- z is a proper period of u
                  have hz : z ≠ [] := by
                    intro h; rw [h, pow_nil] at hzi; exact hne hzi
                  have hzpos : 0 < z.length := by
                    cases z with
                    | nil => exact absurd rfl hz
                    | cons a t => exact Nat.succ_pos _
                  have hlen : u.length = (i'' + 2) * z.length := by
                    rw [hzi, length_pow]
                  have hzlt : z.length < u.length := by
                    rw [hlen]
                    have : 1 * z.length < (i'' + 2) * z.length :=
                      Nat.mul_lt_mul_of_pos_right (by omega) hzpos
                    omega
                  apply hnone z.length (List.mem_range.mpr hzlt)
                  rw [properRootAt_iff]
                  refine ⟨hzpos, ?_, ?_⟩
                  · rw [hlen, Nat.mul_mod_left]
                  · rw [hzi, take_pow_succ, length_pow, Nat.mul_div_cancel _ hzpos]

-- theorem-card: every nonempty word is a positive power of a primitive word
theorem THM_RT_003_primitive_root_exists (u : List α) (hne : u ≠ []) :
    ∃ (z : List α) (i : Nat), Primitive z ∧ 0 < i ∧ u = pow z i :=
  exists_primitive_root_aux u.length u (Nat.le_refl _) hne

end Existence

end Root
end Veyra
