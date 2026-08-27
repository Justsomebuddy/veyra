namespace Veyra

/-- Depth-indexed replay: apply a step function `n` times to a base value. -/
def replay (step : Nat → Nat) (base : Nat) : Nat → Nat
  | 0 => base
  | n + 1 => step (replay step base n)

-- theorem-card: di1 shadow bridge
-- The declared classical shadow of a DI-1 license: base plus uniform step
-- yields every depth. This is the host recursor, exposed deliberately so the
-- shadow semantics of the license is pinned; DI-1 itself licenses only
-- replayable depths and never a completed carrier.
theorem THM_DI1_001_family_from_base_and_step (P : Nat → Prop)
    (base : P 0) (step : ∀ m, P m → P (m + 1)) : ∀ n, P n := by
  intro n
  induction n with
  | zero => exact base
  | succ m ih => exact step m ih

-- theorem-card: di1 replay base law
theorem THM_DI1_002_replay_zero (step : Nat → Nat) (base : Nat) :
    replay step base 0 = base := rfl

-- theorem-card: di1 replay step law
theorem THM_DI1_003_replay_succ (step : Nat → Nat) (base : Nat) (n : Nat) :
    replay step base (n + 1) = step (replay step base n) := rfl

-- theorem-card: di1 exact replay count
-- Counting step applications replays the depth itself: the license's
-- "exactly n steps at depth n" bookkeeping law, proved by real induction.
theorem THM_DI1_004_replay_count (n : Nat) :
    replay (fun k => k + 1) 0 n = n := by
  induction n with
  | zero => rfl
  | succ m ih =>
      rw [THM_DI1_003_replay_succ]
      rw [ih]

-- theorem-card: di1 one-block extension shadow
-- The divides-family step in shadow form: extending by one block adds one
-- block's worth, (n+1)·u = n·u + u.
theorem THM_DI1_005_block_extension_shadow (n u : Nat) :
    (n + 1) * u = n * u + u := by
  rw [Nat.succ_mul]

#check THM_DI1_004_replay_count

end Veyra
