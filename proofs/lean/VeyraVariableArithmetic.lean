import VeyraObserverSite
import VeyraNecklaceOrbit

set_option autoImplicit false

/-! # Arithmetic as a variable object over the observer site

Step 2 of the observer-site program (docs/190 → docs/191). The presheaf of
modes has, at every stage `T`, the fibre `Fibre T := Quot (Echo T)` of
presentations up to echo, and restriction along refinement given by
`THM_OS_002`. Stitch (`x ++ y`, docs/02 §2) and weave (every tact of `x`
replaced by a copy of `y`, docs/02 §3) are *variable objects*: they act on the
fibre at `T` exactly when echo at `T` is a congruence for them (`Descends`),
and then they commute with restriction. The laws of arithmetic become
properties of stages.

Cards (Mathlib-free; axioms `propext`/`Quot.sound` only, no choice):

* `THM_VA_001` arithmetic commutes with restriction; `THM_VA_002` stitch and
  weave descend to the length and word stages; `THM_VA_004` to the bag
  (Parikh) stage.
* `THM_VA_003` the natural numbers are the length fibre: `toNat`/`ofNat` are
  inverse and carry stitch to `+` and weave to `×` (docs/02 §1–3 made exact).
* `THM_VA_005` stitch does not respect cyclic echo (closed modes have no
  native stitch: a cut is needed, cf. the anchor-relative zero of docs/02);
  `THM_VA_006` weave does respect it.
* `THM_VA_007`–`010` the laws as stage properties: commutativity of stitch
  holds at the bag stage and fails at the word stage; commutativity of weave
  holds at the length stage and fails at the bag stage; right distributivity
  is literal while left distributivity holds at the bag stage and fails at the
  word stage; open stitch and weave are literally associative.
* `THM_VA_011` AX-005 demoted: stitching closed modes through their canonical
  (lexicographically least) cuts is not associative up to cyclic echo (finite
  countermodel `a`, `b`, `ab`).
* `THM_VA_012` bag-stage primitivity is Parikh primitivity: coprime letter
  counts.
* `THM_VA_013` resonance (docs/02 §4) retracts under refinement; `THM_VA_014`
  at the length stage it is divisibility of lengths (the docs/189 order).

Host-carried computation: words are host lists, the metatheory is Lean over
`List`/`Quot`; binary words (`List Bool`) carry the bag and cyclic stages.
Nothing here concerns the AX-007 `Mode`, W-001, or physical observers. -/

namespace Veyra
namespace VarArith

open Site

variable {X R : Type}

/-- Stitch of open breaths: concatenation (docs/02 §2). -/
def stitch {α : Type} (x y : List α) : List α := x ++ y

/-- Weave: every tact of `x` replaced by a full copy of `y` (docs/02 §3). -/
def weave {α : Type} (x y : List α) : List α := Root.pow y x.length

/-- An operation descends to stage `T`: echo at `T` is a congruence for it, one argument at a time. -/
def Descends (T : Stage X R) (op : X → X → X) : Prop :=
  (∀ x y y', Echo T y y' → Echo T (op x y) (op x y')) ∧
  (∀ x x' y, Echo T x x' → Echo T (op x y) (op x' y))

/-- The fibre of the presheaf of modes at a stage: presentations up to echo. -/
abbrev Fibre (T : Stage X R) : Type := Quot (Echo T)

/-- The class of a presentation at a stage. -/
abbrev cls (T : Stage X R) (x : X) : Fibre T := Quot.mk (Echo T) x

/-- Restriction along refinement: finer classes coarsen (well defined by `THM_OS_002`). -/
def restrict {T T' : Stage X R} (h : Refines T T') : Fibre T' → Fibre T :=
  Quot.lift (fun x => cls T x) (fun _ _ hab => Quot.sound (THM_OS_002_echo_retracts h hab))

/-- A descending operation acts on the fibre. -/
def act {T : Stage X R} (op : X → X → X) (hd : Descends T op) : Fibre T → Fibre T → Fibre T :=
  Quot.lift
    (fun x => Quot.lift (fun y => cls T (op x y)) (fun _ _ h => Quot.sound (hd.1 x _ _ h)))
    (by
      intro x x' h
      funext q
      induction q using Quot.ind with
      | mk y => exact Quot.sound (hd.2 x x' y h))

theorem act_cls {T : Stage X R} (op : X → X → X) (hd : Descends T op) (x y : X) :
    act op hd (cls T x) (cls T y) = cls T (op x y) := rfl

theorem restrict_cls {T T' : Stage X R} (h : Refines T T') (x : X) :
    restrict h (cls T' x) = cls T x := rfl

-- theorem-card: arithmetic commutes with restriction
theorem THM_VA_001_restriction_homomorphism {T T' : Stage X R} (h : Refines T T')
    (op : X → X → X) (hd : Descends T op) (hd' : Descends T' op) (p q : Fibre T') :
    restrict h (act op hd' p q) = act op hd (restrict h p) (restrict h q) := by
  induction p using Quot.ind
  induction q using Quot.ind
  rfl

/-! ## The length stage -/

/-- The length observer on words over any alphabet. -/
def lenObs {α : Type} : Observer (List α) (List Nat) := fun w => some [w.length]

theorem echoes_lenObs_iff {α : Type} (x y : List α) : Echoes lenObs x y ↔ x.length = y.length := by
  constructor
  · rintro ⟨r, hr, hr'⟩
    simp only [lenObs, Option.some.injEq] at hr hr'
    have := hr.trans hr'.symm
    simp only [List.cons.injEq, and_true] at this
    exact this
  · intro h; exact ⟨[x.length], rfl, by simp [lenObs, h]⟩

theorem echo_lenObs_iff {α : Type} (x y : List α) : Echo [lenObs] x y ↔ x.length = y.length := by
  constructor
  · intro h; exact (echoes_lenObs_iff x y).mp (h lenObs List.mem_cons_self)
  · intro h o ho
    rw [List.mem_singleton] at ho
    rw [ho, echoes_lenObs_iff]; exact h

theorem echo_wordObs_iff {α : Type} (x y : List α) : Echo [wordObs] x y ↔ x = y := by
  constructor
  · intro h; exact (echoes_wordObs_iff x y).mp (h wordObs List.mem_cons_self)
  · intro h o ho
    rw [List.mem_singleton] at ho
    rw [ho, echoes_wordObs_iff]; exact h

theorem length_weave {α : Type} (x y : List α) : (weave x y).length = x.length * y.length := by
  unfold weave; rw [Root.length_pow]

-- theorem-card: stitch and weave descend to the length stage and to the word stage
theorem THM_VA_002_descends_length_word {α : Type} :
    Descends (X := List α) [lenObs] stitch ∧ Descends (X := List α) [lenObs] weave ∧
    Descends (X := List α) [wordObs] stitch ∧ Descends (X := List α) [wordObs] weave := by
  refine ⟨⟨fun x y y' h => ?_, fun x x' y h => ?_⟩, ⟨fun x y y' h => ?_, fun x x' y h => ?_⟩,
    ⟨fun x y y' h => ?_, fun x x' y h => ?_⟩, ⟨fun x y y' h => ?_, fun x x' y h => ?_⟩⟩
  · rw [echo_lenObs_iff] at h ⊢; simp [stitch, h]
  · rw [echo_lenObs_iff] at h ⊢; simp [stitch, h]
  · rw [echo_lenObs_iff] at h ⊢; rw [length_weave, length_weave, h]
  · rw [echo_lenObs_iff] at h ⊢; rw [length_weave, length_weave, h]
  · rw [echo_wordObs_iff] at h ⊢; rw [h]
  · rw [echo_wordObs_iff] at h ⊢; rw [h]
  · rw [echo_wordObs_iff] at h ⊢; rw [h]
  · rw [echo_wordObs_iff] at h ⊢; rw [h]

/-- The length fibre over binary words. -/
abbrev LenFibre : Type := Fibre (X := List Bool) (R := List Nat) [lenObs]

/-- Shadow of a length-stage class: the length. -/
def toNat : LenFibre → Nat :=
  Quot.lift List.length (fun _ _ h => (echo_lenObs_iff _ _).mp h)

/-- The one-tact mode of length `n` at the length stage. -/
def ofNat (n : Nat) : LenFibre := cls [lenObs] (List.replicate n false)

-- theorem-card: the natural numbers are the length fibre of the presheaf of modes, with stitch as
-- addition and weave as multiplication
theorem THM_VA_003_nat_is_length_fibre :
    (∀ n, toNat (ofNat n) = n) ∧ (∀ q, ofNat (toNat q) = q) ∧
    (∀ p q : LenFibre, toNat (act stitch (THM_VA_002_descends_length_word (α := Bool)).1 p q) =
      toNat p + toNat q) ∧
    (∀ p q : LenFibre, toNat (act weave (THM_VA_002_descends_length_word (α := Bool)).2.1 p q) =
      toNat p * toNat q) := by
  refine ⟨fun n => ?_, fun q => ?_, fun p q => ?_, fun p q => ?_⟩
  · show (List.replicate n false).length = n
    exact List.length_replicate
  · induction q using Quot.ind with
    | mk x =>
      apply Quot.sound
      rw [echo_lenObs_iff]
      exact List.length_replicate
  · induction p using Quot.ind with
    | mk x =>
      induction q using Quot.ind with
      | mk y =>
        show List.length (x ++ y) = List.length x + List.length y
        exact List.length_append
  · induction p using Quot.ind with
    | mk x =>
      induction q using Quot.ind with
      | mk y =>
        show List.length (Root.pow y x.length) = List.length x * List.length y
        rw [Root.length_pow, Nat.mul_comm]


/-! ## Binary words: the bag stage, cyclic echo, and the laws as stage properties -/

/-- The bag (Parikh) observer on binary words: the counts of `false` and `true`. -/
def bagObs : Observer (List Bool) (List Nat) := fun w => some [w.count false, w.count true]

theorem echoes_bagObs_iff (x y : List Bool) :
    Echoes bagObs x y ↔ x.count false = y.count false ∧ x.count true = y.count true := by
  constructor
  · rintro ⟨r, hr, hr'⟩
    simp only [bagObs, Option.some.injEq] at hr hr'
    have := hr.trans hr'.symm
    simp only [List.cons.injEq, and_true] at this
    exact this
  · rintro ⟨h0, h1⟩; exact ⟨[x.count false, x.count true], rfl, by simp [bagObs, h0, h1]⟩

theorem echo_bagObs_iff (x y : List Bool) :
    Echo [bagObs] x y ↔ x.count false = y.count false ∧ x.count true = y.count true := by
  constructor
  · intro h; exact (echoes_bagObs_iff x y).mp (h bagObs List.mem_cons_self)
  · intro h o ho
    rw [List.mem_singleton] at ho
    rw [ho, echoes_bagObs_iff]; exact h

theorem count_pow (a : Bool) (y : List Bool) (k : Nat) : (Root.pow y k).count a = k * y.count a := by
  induction k with
  | zero => simp [Root.pow]
  | succ k ih => rw [Root.pow_succ, List.count_append, ih, Nat.succ_mul, Nat.add_comm]

theorem count_false_add_count_true (x : List Bool) : x.count false + x.count true = x.length := by
  induction x with
  | nil => rfl
  | cons a t ih =>
    cases a <;> simp [← ih] <;> omega

-- theorem-card: stitch and weave descend to the bag stage
theorem THM_VA_004_descends_bag : Descends [bagObs] stitch ∧ Descends [bagObs] weave := by
  refine ⟨⟨fun x y y' h => ?_, fun x x' y h => ?_⟩, ⟨fun x y y' h => ?_, fun x x' y h => ?_⟩⟩
  · rw [echo_bagObs_iff] at h ⊢; simp [stitch, List.count_append, h.1, h.2]
  · rw [echo_bagObs_iff] at h ⊢; simp [stitch, List.count_append, h.1, h.2]
  · rw [echo_bagObs_iff] at h ⊢; simp [weave, count_pow, h.1, h.2]
  · rw [echo_bagObs_iff] at h ⊢
    have hlen : x.length = x'.length := by
      have h0 := h.1; have h1 := h.2
      rw [← count_false_add_count_true, ← count_false_add_count_true x', h0, h1]
    simp [weave, count_pow, hlen]

/-- Cyclic echo: `y` is a rotation of `x` (the cycle stage of docs/06 as a relation). -/
def Cyc (x y : List Bool) : Prop := ∃ d, Necklace.rot d x = y

/-- Boolean decision of cyclic echo for nonempty `x`. -/
def cycB (x y : List Bool) : Bool := (List.range x.length).any fun d => Necklace.rot d x == y

theorem cycB_iff (x y : List Bool) (hx : x ≠ []) : cycB x y = true ↔ Cyc x y := by
  unfold cycB Cyc
  rw [List.any_eq_true]
  constructor
  · rintro ⟨d, _, hd⟩; exact ⟨d, beq_iff_eq.mp hd⟩
  · rintro ⟨d, hd⟩
    have hpos : 0 < x.length := by
      cases x with
      | nil => exact absurd rfl hx
      | cons a t => simp
    refine ⟨d % x.length, List.mem_range.mpr (Nat.mod_lt _ hpos), ?_⟩
    rw [beq_iff_eq, ← Necklace.rot_mod, hd]

-- theorem-card: stitch does not respect cyclic echo (closed modes have no native stitch)
theorem THM_VA_005_stitch_breaks_cyclic :
    Cyc [false, true] [true, false] ∧
    ¬ Cyc (stitch [false, true] [false, true]) (stitch [true, false] [false, true]) := by
  constructor
  · exact (cycB_iff _ _ (by decide)).mp (by decide)
  · intro h
    have := (cycB_iff _ _ (by decide)).mpr h
    revert this; decide

theorem rot_pow (d : Nat) (y : List Bool) (k : Nat) :
    Necklace.rot d (Root.pow y k) = Root.pow (Necklace.rot d y) k := by
  rcases Nat.eq_zero_or_pos y.length with hy | hy
  · have : y = [] := List.eq_nil_of_length_eq_zero hy
    subst this
    rw [Root.pow_nil]; simp [Necklace.rot, Root.pow_nil]
  rcases Nat.eq_zero_or_pos k with hk | hk
  · subst hk; simp [Root.pow, Necklace.rot]
  apply Necklace.ext_read
  · rw [Necklace.length_rot, Root.length_pow, Root.length_pow, Necklace.length_rot]
  · intro t _
    rw [Necklace.read_rot, Necklace.read_pow y k _ hy hk,
      Necklace.read_pow (Necklace.rot d y) k t (by rw [Necklace.length_rot]; exact hy) hk,
      Necklace.read_rot]

-- theorem-card: weave respects cyclic echo (closed modes can be woven)
theorem THM_VA_006_weave_respects_cyclic (y y' : List Bool) (k : Nat) (h : Cyc y y') :
    Cyc (Root.pow y k) (Root.pow y' k) := by
  obtain ⟨d, hd⟩ := h
  exact ⟨d, by rw [rot_pow, hd]⟩

-- theorem-card: commutativity of stitch holds at the bag stage and fails at the word stage
theorem THM_VA_007_stitch_comm_stage :
    (∀ x y : List Bool, Echo [bagObs] (stitch x y) (stitch y x)) ∧
    ¬ Echo (X := List Bool) [wordObs] (stitch [false] [true]) (stitch [true] [false]) := by
  constructor
  · intro x y; rw [echo_bagObs_iff]; simp [stitch, List.count_append, Nat.add_comm]
  · rw [echo_wordObs_iff]; decide

-- theorem-card: commutativity of weave holds at the length stage and fails at the bag stage
theorem THM_VA_008_weave_comm_stage :
    (∀ x y : List Bool, Echo [lenObs] (weave x y) (weave y x)) ∧
    ¬ Echo [bagObs] (weave [false] [false, true]) (weave [false, true] [false]) := by
  constructor
  · intro x y; rw [echo_lenObs_iff, length_weave, length_weave, Nat.mul_comm]
  · rw [echo_bagObs_iff]; decide

-- theorem-card: right distributivity is literal; left distributivity holds at the bag stage
-- and fails at the word stage
theorem THM_VA_009_distributivity_stage :
    (∀ x x' y : List Bool, weave (stitch x x') y = stitch (weave x y) (weave x' y)) ∧
    (∀ x y y' : List Bool, Echo [bagObs] (weave x (stitch y y')) (stitch (weave x y) (weave x y'))) ∧
    ¬ Echo (X := List Bool) [wordObs] (weave [false, false] (stitch [false] [true]))
      (stitch (weave [false, false] [false]) (weave [false, false] [true])) := by
  refine ⟨fun x x' y => ?_, fun x y y' => ?_, ?_⟩
  · unfold weave stitch; rw [List.length_append, Root.pow_add]
  · rw [echo_bagObs_iff]; simp [weave, stitch, count_pow, List.count_append, Nat.mul_add]
  · rw [echo_wordObs_iff]; decide

-- theorem-card: open stitch and weave are literally associative, hence at every stage
theorem THM_VA_010_open_associativity :
    (∀ x y z : List Bool, stitch (stitch x y) z = stitch x (stitch y z)) ∧
    (∀ x y z : List Bool, weave (weave x y) z = weave x (weave y z)) := by
  constructor
  · intro x y z; exact List.append_assoc x y z
  · intro x y z
    unfold weave
    rw [Root.length_pow, Root.pow_pow, Nat.mul_comm]

/-- Lexicographic order on binary words with `false < true`. -/
def lexLt : List Bool → List Bool → Bool
  | [], [] => false
  | [], _ :: _ => true
  | _ :: _, [] => false
  | a :: as, b :: bs => if a = b then lexLt as bs else (!a && b)

/-- All rotations of a word. -/
def rotations (l : List Bool) : List (List Bool) := (List.range l.length).map fun d => Necklace.rot d l

/-- The canonical (lexicographically least) cut of a closed mode. -/
def minRot (l : List Bool) : List Bool :=
  (rotations l).foldl (fun acc r => if lexLt r acc then r else acc) l

/-- Stitching closed modes through their canonical cuts. -/
def cutStitch (x y : List Bool) : List Bool := minRot x ++ minRot y

-- theorem-card: AX-005 fails for the canonical-cut stitch of closed modes (finite countermodel)
theorem THM_VA_011_canonical_cut_not_associative :
    ¬ Cyc (cutStitch (cutStitch [false] [true]) [false, true])
      (cutStitch [false] (cutStitch [true] [false, true])) := by
  intro h
  have := (cycB_iff _ _ (by decide)).mpr h
  revert this; decide

-- theorem-card: bag-stage primitivity is Parikh primitivity (coprime letter counts)
theorem THM_VA_012_bag_prime_iff_coprime (x : List Bool) :
    PrimeAt [bagObs] x ↔ x ≠ [] ∧ Nat.gcd (x.count false) (x.count true) = 1 := by
  constructor
  · rintro ⟨hne, hnp⟩
    refine ⟨hne, ?_⟩
    have hlen : 0 < x.length := by
      cases x with
      | nil => exact absurd rfl hne
      | cons a t => simp
    have hsum := count_false_add_count_true x
    rcases Nat.lt_or_ge (Nat.gcd (x.count false) (x.count true)) 2 with hlt | hge
    · have hne0 : Nat.gcd (x.count false) (x.count true) ≠ 0 := by
        intro h0
        rw [Nat.gcd_eq_zero_iff] at h0
        omega
      omega
    · exfalso
      apply hnp
      have hd0 := Nat.gcd_dvd_left (x.count false) (x.count true)
      have hd1 := Nat.gcd_dvd_right (x.count false) (x.count true)
      refine ⟨List.replicate (x.count false / Nat.gcd (x.count false) (x.count true)) false ++
        List.replicate (x.count true / Nat.gcd (x.count false) (x.count true)) true,
        Nat.gcd (x.count false) (x.count true), hge, ?_, ?_⟩
      · rw [List.length_append, List.length_replicate, List.length_replicate]
        have hgpos : 0 < Nat.gcd (x.count false) (x.count true) := by omega
        rcases Nat.eq_zero_or_pos (x.count false) with h0 | h0
        · have h1 : 0 < x.count true := by omega
          exact Nat.lt_of_lt_of_le (Nat.div_pos (Nat.le_of_dvd h1 hd1) hgpos) (Nat.le_add_left _ _)
        · exact Nat.lt_of_lt_of_le (Nat.div_pos (Nat.le_of_dvd h0 hd0) hgpos) (Nat.le_add_right _ _)
      · rw [echo_bagObs_iff, count_pow, count_pow, List.count_append, List.count_append,
          List.count_replicate, List.count_replicate, List.count_replicate, List.count_replicate]
        simp only [beq_self_eq_true, Bool.false_eq_true, beq_iff_eq, if_true, if_false, Nat.zero_add]
        exact ⟨(Nat.mul_div_cancel' hd0).symm, (Nat.mul_div_cancel' hd1).symm⟩
  · rintro ⟨hne, hg⟩
    refine ⟨hne, ?_⟩
    rintro ⟨u, k, hk, _, he⟩
    rw [echo_bagObs_iff, count_pow, count_pow] at he
    have hdk : k ∣ Nat.gcd (x.count false) (x.count true) :=
      Nat.dvd_gcd ⟨u.count false, he.1⟩ ⟨u.count true, he.2⟩
    rw [hg] at hdk
    have := Nat.le_of_dvd Nat.one_pos hdk
    omega


/-! ## Resonance as a variable object -/

/-- `u` resonates inside `x` at stage `T`: `x` is echoed there to some power of `u` (docs/02 §4). -/
def ResonatesAt {α : Type} (T : Stage (List α) R) (u x : List α) : Prop := ∃ k, Echo T x (Root.pow u k)

-- theorem-card: resonance retracts under refinement (finer stages see fewer resonances)
theorem THM_VA_013_resonance_retracts {α : Type} {T T' : Stage (List α) R} (h : Refines T T')
    {u x : List α} (hr : ResonatesAt T' u x) : ResonatesAt T u x := by
  obtain ⟨k, hk⟩ := hr
  exact ⟨k, THM_OS_002_echo_retracts h hk⟩

-- theorem-card: at the length stage resonance is divisibility of lengths
theorem THM_VA_014_length_resonance_is_divisibility {α : Type} (u x : List α) :
    ResonatesAt [lenObs] u x ↔ u.length ∣ x.length := by
  constructor
  · rintro ⟨k, hk⟩
    rw [echo_lenObs_iff, Root.length_pow] at hk
    exact ⟨k, by rw [hk, Nat.mul_comm]⟩
  · rintro ⟨k, hk⟩
    exact ⟨k, by rw [echo_lenObs_iff, Root.length_pow, hk, Nat.mul_comm]⟩

end VarArith
end Veyra
