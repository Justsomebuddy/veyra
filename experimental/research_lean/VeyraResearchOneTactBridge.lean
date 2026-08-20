import VeyraResearchShadow
import VeyraRecurrenceModeBridge

/-
Research-only bridge for the singleton-generated one-tact path-word realization.

The carrier below is independently represented as finite words over exactly one
tact symbol (`List Unit`). This matches the external one-symbol path-word
realization used by the historical one-tact proof sketch, but the file does not
prove that AX-007 itself excludes additional tacts or that every Core-0 Mode is
in this carrier.

The bridge is deliberately narrower:
* singleton words are related constructively to `Nat` and unary `Recurrence`;
* the same words are related to the exact R9 `IntrinsicMode` image;
* singleton stitch and length-weave transport to strict-native stitch/weave;
* no arbitrary strict `VeyraMode`, general LEM-001, or stable registry promotion
  is claimed.

The one-node closure is implicit in the singleton-word shadow and becomes the
fixed origin/self-loop realization only through the existing R9 encoding.
-/
namespace Veyra

open VeyraTransport

abbrev OneTactWord := List Unit

def oneTactBijection {α β : Type} (f : α → β) : Prop :=
  (∀ {left right : α}, f left = f right → left = right) ∧
  (∀ target : β, ∃ source : α, f source = target)

def oneTactStitch (left right : OneTactWord) : OneTactWord := left ++ right

def oneTactLengthWeave (left : OneTactWord) : OneTactWord → OneTactWord
  | [] => []
  | _ :: tail => left ++ oneTactLengthWeave left tail

def oneTactWordToRecurrence : OneTactWord → Recurrence
  | [] => .silence
  | _ :: tail => .pulse (oneTactWordToRecurrence tail)

def recurrenceToOneTactWord : Recurrence → OneTactWord
  | .silence => []
  | .pulse tail => () :: recurrenceToOneTactWord tail

theorem RESEARCH_OT_L001_one_tact_word_recurrence_roundtrip (word : OneTactWord) :
    recurrenceToOneTactWord (oneTactWordToRecurrence word) = word := by
  induction word with
  | nil => rfl
  | cons head tail hypothesis =>
      cases head
      change () :: recurrenceToOneTactWord (oneTactWordToRecurrence tail) = () :: tail
      exact congrArg (fun rest : OneTactWord => () :: rest) hypothesis

theorem RESEARCH_OT_L002_recurrence_one_tact_word_roundtrip (value : Recurrence) :
    oneTactWordToRecurrence (recurrenceToOneTactWord value) = value := by
  induction value with
  | silence => rfl
  | pulse tail hypothesis =>
      change Recurrence.pulse
          (oneTactWordToRecurrence (recurrenceToOneTactWord tail)) =
        Recurrence.pulse tail
      exact congrArg Recurrence.pulse hypothesis

theorem RESEARCH_OT_T001_one_tact_word_recurrence_bijection :
    oneTactBijection oneTactWordToRecurrence := by
  unfold oneTactBijection
  constructor
  · intro left right same
    calc
      left = recurrenceToOneTactWord (oneTactWordToRecurrence left) :=
        (RESEARCH_OT_L001_one_tact_word_recurrence_roundtrip left).symm
      _ = recurrenceToOneTactWord (oneTactWordToRecurrence right) :=
        congrArg recurrenceToOneTactWord same
      _ = right := RESEARCH_OT_L001_one_tact_word_recurrence_roundtrip right
  · intro value
    exact
      ⟨recurrenceToOneTactWord value,
        RESEARCH_OT_L002_recurrence_one_tact_word_roundtrip value⟩

theorem RESEARCH_OT_L003_one_tact_stitch_transport (left right : OneTactWord) :
    oneTactWordToRecurrence (oneTactStitch left right) =
      stitch (oneTactWordToRecurrence left) (oneTactWordToRecurrence right) := by
  induction left with
  | nil => rfl
  | cons head tail hypothesis =>
      cases head
      change
        Recurrence.pulse (oneTactWordToRecurrence (oneTactStitch tail right)) =
          Recurrence.pulse
            (stitch (oneTactWordToRecurrence tail) (oneTactWordToRecurrence right))
      exact congrArg Recurrence.pulse hypothesis

theorem RESEARCH_OT_L004_one_tact_length_weave_transport
    (left right : OneTactWord) :
    oneTactWordToRecurrence (oneTactLengthWeave left right) =
      weave (oneTactWordToRecurrence left) (oneTactWordToRecurrence right) := by
  induction right with
  | nil => rfl
  | cons head tail hypothesis =>
      cases head
      change
        oneTactWordToRecurrence
            (oneTactStitch left (oneTactLengthWeave left tail)) =
          stitch
            (oneTactWordToRecurrence left)
            (weave (oneTactWordToRecurrence left) (oneTactWordToRecurrence tail))
      rw [RESEARCH_OT_L003_one_tact_stitch_transport, hypothesis]

def oneTactRank (word : OneTactWord) : Nat := word.length

def oneTactWordOfNat : Nat → OneTactWord
  | 0 => []
  | n + 1 => () :: oneTactWordOfNat n

theorem RESEARCH_OT_L005_rank_wordOfNat (value : Nat) :
    oneTactRank (oneTactWordOfNat value) = value := by
  induction value with
  | zero => rfl
  | succ value hypothesis =>
      change Nat.succ (oneTactRank (oneTactWordOfNat value)) = Nat.succ value
      exact congrArg Nat.succ hypothesis

theorem RESEARCH_OT_L006_wordOfNat_rank (word : OneTactWord) :
    oneTactWordOfNat (oneTactRank word) = word := by
  induction word with
  | nil => rfl
  | cons head tail hypothesis =>
      cases head
      change () :: oneTactWordOfNat (oneTactRank tail) = () :: tail
      exact congrArg (fun rest : OneTactWord => () :: rest) hypothesis

theorem RESEARCH_OT_T002_one_tact_word_nat_bijection :
    oneTactBijection oneTactRank := by
  unfold oneTactBijection
  constructor
  · intro left right same
    calc
      left = oneTactWordOfNat (oneTactRank left) :=
        (RESEARCH_OT_L006_wordOfNat_rank left).symm
      _ = oneTactWordOfNat (oneTactRank right) := congrArg oneTactWordOfNat same
      _ = right := RESEARCH_OT_L006_wordOfNat_rank right
  · intro value
    exact ⟨oneTactWordOfNat value, RESEARCH_OT_L005_rank_wordOfNat value⟩

theorem RESEARCH_OT_T003_one_tact_rank_stitch_add (left right : OneTactWord) :
    oneTactRank (oneTactStitch left right) =
      oneTactRank left + oneTactRank right := by
  change (left ++ right).length = left.length + right.length
  exact List.length_append

theorem RESEARCH_OT_T004_one_tact_rank_length_weave_mul
    (left right : OneTactWord) :
    oneTactRank (oneTactLengthWeave left right) =
      oneTactRank left * oneTactRank right := by
  induction right with
  | nil => rfl
  | cons head tail hypothesis =>
      cases head
      have tailRank :
          (oneTactLengthWeave left tail).length = left.length * tail.length := by
        change
          (oneTactLengthWeave left tail).length = left.length * tail.length at hypothesis
        exact hypothesis
      calc
        (oneTactLengthWeave left (() :: tail)).length =
            (left ++ oneTactLengthWeave left tail).length := rfl
        _ = left.length + (oneTactLengthWeave left tail).length :=
            List.length_append
        _ = left.length + left.length * tail.length := by rw [tailRank]
        _ = left.length * tail.length + left.length := Nat.add_comm _ _
        _ = left.length * Nat.succ tail.length := (Nat.mul_succ _ _).symm

theorem RESEARCH_OT_L007_wordOfNat_realizes_shadow (value : Nat) :
    oneTactWordToRecurrence (oneTactWordOfNat value) = shadow value := by
  induction value with
  | zero => rfl
  | succ value hypothesis =>
      change
        Recurrence.pulse (oneTactWordToRecurrence (oneTactWordOfNat value)) =
          Recurrence.pulse (shadow value)
      exact congrArg Recurrence.pulse hypothesis

def oneTactIntrinsicToRecurrence (native : IntrinsicMode) : Recurrence :=
  match decodeMode native.1 with
  | some value => value
  | none => .silence

theorem RESEARCH_OT_L008_intrinsic_decode_roundtrip (value : Recurrence) :
    oneTactIntrinsicToRecurrence (intrinsicMode value) = value := by
  unfold oneTactIntrinsicToRecurrence
  change
    (match decodeMode (encodeMode value) with
      | some decoded => decoded
      | none => Recurrence.silence) = value
  rw [THM_R9_002_decode_encode]

theorem RESEARCH_OT_L009_intrinsic_encode_roundtrip (native : IntrinsicMode) :
    intrinsicMode (oneTactIntrinsicToRecurrence native) = native := by
  rcases native.property with ⟨value, encoded⟩
  have decoded : decodeMode native.1 = some value := by
    rw [← encoded]
    exact THM_R9_002_decode_encode value
  apply Subtype.ext
  change encodeMode (oneTactIntrinsicToRecurrence native) = native.1
  unfold oneTactIntrinsicToRecurrence
  rw [decoded]
  exact encoded

def oneTactIntrinsicMode (word : OneTactWord) : IntrinsicMode :=
  intrinsicMode (oneTactWordToRecurrence word)

def intrinsicToOneTactWord (native : IntrinsicMode) : OneTactWord :=
  recurrenceToOneTactWord (oneTactIntrinsicToRecurrence native)

theorem RESEARCH_OT_L010_one_tact_intrinsic_word_roundtrip (word : OneTactWord) :
    intrinsicToOneTactWord (oneTactIntrinsicMode word) = word := by
  unfold intrinsicToOneTactWord oneTactIntrinsicMode
  rw [RESEARCH_OT_L008_intrinsic_decode_roundtrip]
  exact RESEARCH_OT_L001_one_tact_word_recurrence_roundtrip word

theorem RESEARCH_OT_L011_one_tact_intrinsic_mode_roundtrip (native : IntrinsicMode) :
    oneTactIntrinsicMode (intrinsicToOneTactWord native) = native := by
  unfold oneTactIntrinsicMode intrinsicToOneTactWord
  rw [RESEARCH_OT_L002_recurrence_one_tact_word_roundtrip]
  exact RESEARCH_OT_L009_intrinsic_encode_roundtrip native

theorem RESEARCH_OT_T005_one_tact_word_intrinsic_bijection :
    oneTactBijection oneTactIntrinsicMode := by
  unfold oneTactBijection
  constructor
  · intro left right same
    calc
      left = intrinsicToOneTactWord (oneTactIntrinsicMode left) :=
        (RESEARCH_OT_L010_one_tact_intrinsic_word_roundtrip left).symm
      _ = intrinsicToOneTactWord (oneTactIntrinsicMode right) :=
        congrArg intrinsicToOneTactWord same
      _ = right := RESEARCH_OT_L010_one_tact_intrinsic_word_roundtrip right
  · intro native
    exact
      ⟨intrinsicToOneTactWord native,
        RESEARCH_OT_L011_one_tact_intrinsic_mode_roundtrip native⟩

theorem RESEARCH_OT_L012_one_tact_nat_realization_agrees (value : Nat) :
    oneTactIntrinsicMode (oneTactWordOfNat value) = intrinsicMode (shadow value) := by
  apply Subtype.ext
  change
    encodeMode (oneTactWordToRecurrence (oneTactWordOfNat value)) =
      encodeMode (shadow value)
  rw [RESEARCH_OT_L007_wordOfNat_realizes_shadow]

theorem RESEARCH_OT_T006_native_stitch_realizes_one_tact_stitch
    (left right : OneTactWord) :
    VeyraIntrinsicRuntime.stitch
        (oneTactIntrinsicMode left).1 (oneTactIntrinsicMode right).1 =
      .ready (oneTactIntrinsicMode (oneTactStitch left right)).1 := by
  change
    VeyraIntrinsicRuntime.stitch
        (encodeMode (oneTactWordToRecurrence left))
        (encodeMode (oneTactWordToRecurrence right)) =
      .ready (encodeMode (oneTactWordToRecurrence (oneTactStitch left right)))
  rw [THM_R9_005_stitch_preserved, RESEARCH_OT_L003_one_tact_stitch_transport]

theorem RESEARCH_OT_T007_native_weave_realizes_one_tact_length_weave
    (left right : OneTactWord) :
    VeyraIntrinsicRuntime.weave
        (oneTactIntrinsicMode left).1 (oneTactIntrinsicMode right).1 =
      .ready (oneTactIntrinsicMode (oneTactLengthWeave left right)).1 := by
  change
    VeyraIntrinsicRuntime.weave
        (encodeMode (oneTactWordToRecurrence left))
        (encodeMode (oneTactWordToRecurrence right)) =
      .ready (encodeMode (oneTactWordToRecurrence (oneTactLengthWeave left right)))
  rw [THM_R9_006_weave_preserved, RESEARCH_OT_L004_one_tact_length_weave_transport]

theorem RESEARCH_OT_L013_one_tact_zero_native :
    (oneTactIntrinsicMode []).1 = VeyraIntrinsicRuntime.zero := by
  change encodeMode .silence = VeyraIntrinsicRuntime.zero
  exact encode_silence_preserved.symm

theorem RESEARCH_OT_L014_one_tact_one_native :
    VeyraIntrinsicRuntime.successor VeyraIntrinsicRuntime.zero =
      .ready (oneTactIntrinsicMode [()]).1 := by
  rw [encode_silence_preserved]
  change
    VeyraIntrinsicRuntime.successor (encodeMode .silence) =
      .ready (encodeMode (.pulse .silence))
  exact encode_pulse_preserved .silence

end Veyra
