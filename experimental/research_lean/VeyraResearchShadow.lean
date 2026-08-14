import VeyraNativeArithmetic

namespace Veyra

/- Unary image laws for the closed `Recurrence` calculus.

The map below proves addition/multiplication behavior only for the pulse/silence
image of `VeyraNativeArithmetic`. It does not construct the AX-007/LEM-001
one-nod/one-tact Mode bridge required by registry THM-001..003 or W-001, so
those registry rows remain conjectures.
-/

def shadow : Nat → Recurrence
  | 0 => Recurrence.silence
  | n + 1 => Recurrence.pulse (shadow n)

theorem RESEARCH_S_T001_stitch_shadows_add (a b : Nat) :
    stitch (shadow a) (shadow b) = shadow (a + b) := by
  induction a with
  | zero =>
      rw [Nat.zero_add]
      rfl
  | succ a ih =>
      simp [shadow, stitch, ih]
      congr 1
      rw [Nat.add_assoc, Nat.add_comm 1 b]
      rfl

theorem RESEARCH_S_T002_weave_shadows_mul (a b : Nat) :
    weave (shadow a) (shadow b) = shadow (a * b) := by
  induction b with
  | zero => rfl
  | succ b ih =>
      simp [shadow, weave, ih]
      rw [RESEARCH_S_T001_stitch_shadows_add a (a * b)]
      congr 1
      rw [Nat.mul_succ]
      exact Nat.add_comm a (a * b)

theorem RESEARCH_S_T003_shadow_injective : Function.Injective shadow := by
  intro a b h
  induction a generalizing b with
  | zero =>
      cases b with
      | zero => rfl
      | succ b => cases h
  | succ a ih =>
      cases b with
      | zero => cases h
      | succ b =>
          have h' : shadow a = shadow b := by
            injection h with h'
          have hab : a = b := ih h'
          subst hab
          rfl

theorem RESEARCH_S_T004_stitch_commutes (a b : Nat) :
    stitch (shadow a) (shadow b) = stitch (shadow b) (shadow a) := by
  rw [RESEARCH_S_T001_stitch_shadows_add, RESEARCH_S_T001_stitch_shadows_add]
  congr 1
  exact Nat.add_comm a b

theorem RESEARCH_S_T005_stitch_assoc_shadows (a b c : Nat) :
    stitch (stitch (shadow a) (shadow b)) (shadow c) =
      stitch (shadow a) (stitch (shadow b) (shadow c)) := by
  calc
    stitch (stitch (shadow a) (shadow b)) (shadow c)
        = stitch (shadow (a + b)) (shadow c) := by rw [RESEARCH_S_T001_stitch_shadows_add]
    _ = shadow (a + b + c) := by rw [RESEARCH_S_T001_stitch_shadows_add]
    _ = shadow (a + (b + c)) := by rw [Nat.add_assoc]
    _ = stitch (shadow a) (shadow (b + c)) := by rw [← RESEARCH_S_T001_stitch_shadows_add]
    _ = stitch (shadow a) (stitch (shadow b) (shadow c)) := by rw [← RESEARCH_S_T001_stitch_shadows_add]

theorem RESEARCH_S_T006_weave_commutes (a b : Nat) :
    weave (shadow a) (shadow b) = weave (shadow b) (shadow a) := by
  rw [RESEARCH_S_T002_weave_shadows_mul, RESEARCH_S_T002_weave_shadows_mul]
  congr 1
  exact Nat.mul_comm a b

theorem RESEARCH_S_T007_weave_assoc_shadows (a b c : Nat) :
    weave (weave (shadow a) (shadow b)) (shadow c) =
      weave (shadow a) (weave (shadow b) (shadow c)) := by
  calc
    weave (weave (shadow a) (shadow b)) (shadow c)
        = weave (shadow (a * b)) (shadow c) := by rw [RESEARCH_S_T002_weave_shadows_mul]
    _ = shadow (a * b * c) := by rw [RESEARCH_S_T002_weave_shadows_mul]
    _ = shadow (a * (b * c)) := by rw [Nat.mul_assoc]
    _ = weave (shadow a) (shadow (b * c)) := by rw [← RESEARCH_S_T002_weave_shadows_mul]
    _ = weave (shadow a) (weave (shadow b) (shadow c)) := by rw [← RESEARCH_S_T002_weave_shadows_mul]

theorem RESEARCH_S_T008_weave_distributes (a b c : Nat) :
    weave (shadow a) (stitch (shadow b) (shadow c)) =
      stitch (weave (shadow a) (shadow b)) (weave (shadow a) (shadow c)) := by
  calc
    weave (shadow a) (stitch (shadow b) (shadow c))
        = weave (shadow a) (shadow (b + c)) := by rw [RESEARCH_S_T001_stitch_shadows_add]
    _ = shadow (a * (b + c)) := by rw [RESEARCH_S_T002_weave_shadows_mul]
    _ = shadow (a * b + a * c) := by rw [Nat.mul_add]
    _ = stitch (shadow (a * b)) (shadow (a * c)) := by rw [← RESEARCH_S_T001_stitch_shadows_add]
    _ = stitch (weave (shadow a) (shadow b)) (weave (shadow a) (shadow c)) := by
          rw [← RESEARCH_S_T002_weave_shadows_mul, ← RESEARCH_S_T002_weave_shadows_mul]

theorem RESEARCH_S_T009_zero_is_silence : shadow 0 = Recurrence.silence := rfl

theorem RESEARCH_S_T010_stitch_units (a : Nat) :
    stitch (shadow 0) (shadow a) = shadow a ∧
    stitch (shadow a) (shadow 0) = shadow a := by
  constructor
  · rw [RESEARCH_S_T001_stitch_shadows_add]
    rw [Nat.zero_add]
  · rw [RESEARCH_S_T001_stitch_shadows_add]
    rw [Nat.add_comm a 0]
    rw [Nat.zero_add]

theorem RESEARCH_S_T011_weave_units (a : Nat) :
    weave (shadow 1) (shadow a) = shadow a ∧
    weave (shadow a) (shadow 1) = shadow a := by
  constructor
  · rw [RESEARCH_S_T002_weave_shadows_mul]
    congr 1
    exact Nat.one_mul a
  · rw [RESEARCH_S_T002_weave_shadows_mul]
    congr 1
    exact Nat.mul_one a

#check RESEARCH_S_T001_stitch_shadows_add
#check RESEARCH_S_T002_weave_shadows_mul
#check RESEARCH_S_T003_shadow_injective
#check RESEARCH_S_T008_weave_distributes

end Veyra
