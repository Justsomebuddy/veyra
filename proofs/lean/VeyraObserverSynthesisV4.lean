/-!
Abstract observer-synthesis v4 replay and finite-exhaustion boundary.

The results below cover only exact codec round trips, replay comparison,
explicit representation bijections, and a caller-supplied finite catalog. They
do not formalize Rust, hashes, signatures, system calls, worker isolation, or
the completeness of any concrete observer grammar.
-/

namespace VeyraObserverSynthesisV4

variable {Abstract Physical Class Config Result Wire Candidate : Type}

/-- A canonical codec exposes the one round-trip law used by replay. -/
structure CanonicalCodec (Value Wire : Type) where
  encode : Value → Wire
  decode : Wire → Option Value
  decodeEncode : ∀ value, decode (encode value) = some value

/-- Replay accepts only the exact decoded expected result. -/
def acceptsReplay
    (codec : CanonicalCodec Result Wire) (wire : Wire) (expected : Result) : Prop :=
  codec.decode wire = some expected

theorem encoded_replay_accepts
    (codec : CanonicalCodec Result Wire) (result : Result) :
    acceptsReplay codec (codec.encode result) result := by
  unfold acceptsReplay
  exact codec.decodeEncode result

theorem replay_acceptance_is_exact
    (codec : CanonicalCodec Result Wire) (wire : Wire) (expected : Result)
    (accepted : acceptsReplay codec wire expected) :
    codec.decode wire = some expected := by
  exact accepted

/-- Representation transport is admitted only with both inverse laws. -/
structure RepresentationBijection (Abstract Physical : Type) where
  encode : Abstract → Physical
  decode : Physical → Abstract
  decodeEncode : ∀ state, decode (encode state) = state
  encodeDecode : ∀ state, encode (decode state) = state

def transportedTask (transport : RepresentationBijection Abstract Physical)
    (task : Abstract → Class) : Physical → Class :=
  task ∘ transport.decode

theorem explicit_bijection_preserves_task
    (transport : RepresentationBijection Abstract Physical)
    (task : Abstract → Class) (state : Abstract) :
    transportedTask transport task (transport.encode state) = task state := by
  change task (transport.decode (transport.encode state)) = task state
  rw [transport.decodeEncode]

/-- Exhaustion is relative to every row in one explicit finite catalog. -/
def exhaustsCatalog (catalog : List Candidate) (accepts : Candidate → Bool) : Prop :=
  ∀ candidate ∈ catalog, accepts candidate = false

theorem finite_exhaustion_excludes_catalog_witness
    (catalog : List Candidate) (accepts : Candidate → Bool)
    (exhausted : exhaustsCatalog catalog accepts)
    (candidate : Candidate) (member : candidate ∈ catalog) :
    accepts candidate = false := by
  exact exhausted candidate member

#print axioms encoded_replay_accepts
#print axioms replay_acceptance_is_exact
#print axioms explicit_bijection_preserves_task
#print axioms finite_exhaustion_excludes_catalog_witness

end VeyraObserverSynthesisV4
