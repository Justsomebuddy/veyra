import Lean.Elab.Tactic.Omega

namespace Veyra

-- theorem-card: di2 divisor dichotomy
-- The structural dichotomy shadow: under the primality hypothesis every
-- divisor is 1 or the length, so every period is 1 or the length.
theorem THM_DI2_001_divisor_dichotomy (p per : Nat)
    (hp : ∀ d, d ∣ p → d = 1 ∨ d = p) (h : per ∣ p) :
    per = 1 ∨ per = p := hp per h

-- theorem-card: di2 partition congruence
-- The partition ledger shadow: a total that splits as constants plus full
-- orbits leaves exactly the woven part after removing the constants.
theorem THM_DI2_002_partition_congruence (fix full p total : Nat)
    (h : total = fix + p * full) : total - fix = p * full := by
  omega

-- theorem-card: di2 power monotonicity
-- Real induction: enlarging the alphabet never shrinks the word count.
theorem THM_DI2_003_pow_succ_mono (p k : Nat) : k ^ p ≤ (k + 1) ^ p := by
  induction p with
  | zero => exact Nat.le_refl 1
  | succ m ih =>
      rw [Nat.pow_succ, Nat.pow_succ]
      exact Nat.mul_le_mul ih (Nat.le_succ k)

-- theorem-card: di2 delta decomposition
-- Conditional alphabet-step shadow: the new nonconstant words are exactly
-- the previous ones plus the delta, stated under its explicit ordering
-- hypotheses; it does not construct them.
theorem THM_DI2_004_delta_decomposition (p k : Nat)
    (h2 : k ≤ k ^ p) (h3 : k ^ p + 1 ≤ (k + 1) ^ p) :
    (k + 1) ^ p - (k + 1) = (k ^ p - k) + ((k + 1) ^ p - k ^ p - 1) := by
  omega

-- theorem-card: di2 exact fixture p=3 k=2
-- The executable cell (length 3, depth 2): 8 words, 2 constants, 2 full
-- orbits of size 3.
theorem THM_DI2_005_fixture_p3_k2 : (8 : Nat) - 2 = 3 * 2 := rfl

#check THM_DI2_003_pow_succ_mono

end Veyra
