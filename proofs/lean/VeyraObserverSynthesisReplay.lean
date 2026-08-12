/-!
Abstract proof slice for the atomic native observer-synthesis v2 artifact.

The declarations below model only three structural facts: exact functional
replay is deterministic, a declared bijective relabeling preserves the pulled-
back abstract target, and exhaustion excludes witnesses only inside the named
finite catalog. They do not formalize Rust, binary framing, SHA-256/HMAC, either
closed grammar profile, joint synthesis, resource custody, or concrete outcomes.
-/

namespace VeyraObserverSynthesisReplay

structure Receipt (Config Evidence : Type) where
  config : Config
  evidence : Evidence

variable {Config Evidence Abstract Physical Class Candidate : Type}

/-- Abstract exact replay: accept only the receipt rebuilt from its bound config. -/
def replay [DecidableEq Evidence]
    (rebuild : Config → Option Evidence) (receipt : Receipt Config Evidence) :
    Option (Receipt Config Evidence) :=
  if rebuild receipt.config = some receipt.evidence then some receipt else none

theorem replay_acceptance_sound [DecidableEq Evidence]
    (rebuild : Config → Option Evidence) (receipt : Receipt Config Evidence)
    (accepted : replay rebuild receipt = some receipt) :
    rebuild receipt.config = some receipt.evidence := by
  unfold replay at accepted
  split at accepted
  next same => exact same
  next _ => contradiction

theorem replay_deterministic [DecidableEq Evidence]
    (rebuild : Config → Option Evidence) (receipt : Receipt Config Evidence)
    {left right : Receipt Config Evidence}
    (leftReplay : replay rebuild receipt = some left)
    (rightReplay : replay rebuild receipt = some right) :
    left = right := by
  exact Option.some.inj (leftReplay.symm.trans rightReplay)

structure AbstractTask (State Class : Type) where
  targetClass : State → Class

/-- Explicit bijection data, without importing a larger equivalence library. -/
structure EncodingEquiv (Abstract Physical : Type) where
  encode : Abstract → Physical
  decode : Physical → Abstract
  decode_encode : ∀ state, decode (encode state) = state
  encode_decode : ∀ state, encode (decode state) = state

/-- Relabel a task onto its physical representation by decoding before classification. -/
def transportTask (encoding : EncodingEquiv Abstract Physical)
    (task : AbstractTask Abstract Class) : AbstractTask Physical Class where
  targetClass := task.targetClass ∘ encoding.decode

theorem bijective_encoding_preserves_abstract_task
    (encoding : EncodingEquiv Abstract Physical)
    (task : AbstractTask Abstract Class) (state : Abstract) :
    (transportTask encoding task).targetClass (encoding.encode state) =
      task.targetClass state := by
  change task.targetClass (encoding.decode (encoding.encode state)) = task.targetClass state
  rw [encoding.decode_encode]

/-- Exhaustion is deliberately relative to membership in one explicit list. -/
def CatalogExhausted (catalog : List Candidate) (accepts : Candidate → Prop) : Prop :=
  ∀ candidate, candidate ∈ catalog → ¬ accepts candidate

theorem finite_catalog_exhausted_iff_no_member_accepts
    (catalog : List Candidate) (accepts : Candidate → Prop) :
    CatalogExhausted catalog accepts ↔
      ¬ ∃ candidate, candidate ∈ catalog ∧ accepts candidate := by
  constructor
  · intro exhausted witness
    obtain ⟨candidate, member, accepted⟩ := witness
    exact exhausted candidate member accepted
  · intro absent candidate member accepted
    exact absent ⟨candidate, member, accepted⟩

#print axioms replay_acceptance_sound
#print axioms replay_deterministic
#print axioms bijective_encoding_preserves_abstract_task
#print axioms finite_catalog_exhausted_iff_no_member_accepts

end VeyraObserverSynthesisReplay
