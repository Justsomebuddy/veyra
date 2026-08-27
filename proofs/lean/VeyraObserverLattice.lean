namespace Veyra

/-- Reflexive–transitive reachability by an abstract step relation. -/
inductive Reaches {α : Type} (step : α → α → Prop) : α → α → Prop
  | refl (a : α) : Reaches step a a
  | tail {a b c : α} : Reaches step a b → step b c → Reaches step a c

-- theorem-card: tr1 closure monotonicity
-- The transfer spine: enlarging the allowed steps (a coarser doctrine)
-- preserves every reachability witness. Real induction on the witness.
theorem THM_TR1_001_reaches_monotone {α : Type} {r s : α → α → Prop}
    (mono : ∀ x y, r x y → s x y) {a b : α}
    (h : Reaches r a b) : Reaches s a b := by
  induction h with
  | refl => exact Reaches.refl _
  | tail hprev hstep ih => exact Reaches.tail ih (mono _ _ hstep)

-- theorem-card: tr1 omega transport
-- A power exhibit reachable in the fine class is reachable in the coarse
-- class: the shadow of "imprimitivity transports upward".
theorem THM_TR1_002_witness_transport {α : Type} {r s : α → α → Prop}
    {P : α → Prop} (mono : ∀ x y, r x y → s x y) {a b : α}
    (h : Reaches r a b) (hb : P b) :
    ∃ c, Reaches s a c ∧ P c :=
  ⟨b, THM_TR1_001_reaches_monotone mono h, hb⟩

-- theorem-card: tr1 primitivity stability
-- Contrapositive shadow: if no coarse-reachable element is a power, then no
-- fine-reachable element is — coarse-primitive implies fine-primitive.
theorem THM_TR1_003_primitivity_stability {α : Type} {r s : α → α → Prop}
    {P : α → Prop} (mono : ∀ x y, r x y → s x y) {a : α}
    (hs : ∀ c, Reaches s a c → ¬ P c) :
    ∀ c, Reaches r a c → ¬ P c :=
  fun c hr => hs c (THM_TR1_001_reaches_monotone mono hr)

-- theorem-card: tr1 replay fixture
-- Concrete two-step reachability exhibit, tying the closure to the DI-1
-- replay bookkeeping.
theorem THM_TR1_004_replay_fixture :
    Reaches (fun n m => m = n + 1) 0 2 :=
  Reaches.tail (Reaches.tail (Reaches.refl 0) rfl) rfl

#check THM_TR1_003_primitivity_stability

end Veyra
