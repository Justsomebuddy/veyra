namespace Veyra

/-- Two-letter projection as a Boolean filter, defined locally. -/
def pick (q : Nat → Bool) : List Nat → List Nat
  | [] => []
  | a :: t => if q a then a :: pick q t else pick q t

/-- Literal k-th power by left concatenation. -/
def powL (u : List Nat) : Nat → List Nat
  | 0 => []
  | n + 1 => u ++ powL u n

-- theorem-card: tr2 projection append homomorphism
theorem THM_TR2_002_pick_append (q : Nat → Bool) (l r : List Nat) :
    pick q (l ++ r) = pick q l ++ pick q r := by
  induction l with
  | nil => rfl
  | cons a t ih =>
      cases hq : q a <;> simp [pick, hq, ih]

-- theorem-card: tr2 projection of a power is a power
-- The engine of Lemma A: every pairwise projection of u^k equals
-- (projection of u)^k, so a pair whose projection of w is not a k-th
-- power must lie in every exponent-k delta set.
theorem THM_TR2_003_projection_of_power (q : Nat → Bool) (u : List Nat) (k : Nat) :
    pick q (powL u k) = powL (pick q u) k := by
  induction k with
  | zero => rfl
  | succ n ih =>
      simp [powL, THM_TR2_002_pick_append, ih]

-- theorem-card: tr2 power addition law
theorem THM_TR2_004_pow_add (u : List Nat) (m n : Nat) :
    powL u (m + n) = powL u m ++ powL u n := by
  induction m with
  | zero => simp [powL]
  | succ t ih =>
      simp [powL, ih, Nat.succ_add, List.append_assoc]

-- theorem-card: tr2 divisor law
-- The engine of Lemma B: a (b·a)-th power is an a-th power of the b-th
-- power, so k | k' sends k'-power projections to k-power projections and
-- the forced floors are monotone along divisibility.
theorem THM_TR2_005_pow_mul (u : List Nat) (a b : Nat) :
    powL u (b * a) = powL (powL u b) a := by
  induction a with
  | zero => simp [powL]
  | succ n ih =>
      have step : b * (n + 1) = b + b * n := by
        calc b * (n + 1) = b * n + b := Nat.mul_succ b n
          _ = b + b * n := Nat.add_comm (b * n) b
      simp [step, THM_TR2_004_pow_add, powL, ih]

-- theorem-card: tr2 first block of a concatenation
-- The Achievability engine, pair level: taking the first |r| letters of
-- r ++ s recovers r exactly.
theorem THM_TR2_006_first_block (r s : List Nat) :
    (r ++ s).take r.length = r := by
  induction r with
  | nil => rfl
  | cons a t ih =>
      show a :: (t ++ s).take t.length = a :: t
      rw [ih]

-- theorem-card: tr2 the root of a power is its first block
-- For every pair in the matched set, the projection root r_p is recovered
-- as the first block of the power projection - the machine-checked heart
-- of the firstSlice construction that attains the floor F_k(w).
theorem THM_TR2_007_power_first_block (r : List Nat) (n : Nat) :
    (powL r (n + 1)).take r.length = r :=
  THM_TR2_006_first_block r (powL r n)

#check THM_TR2_003_projection_of_power
#check THM_TR2_007_power_first_block

end Veyra
