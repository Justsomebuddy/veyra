/-!
Narrow abstract bridge for observer-synthesis v3.

This file formalizes only canonical rebuild acceptance, task preservation under
an explicitly supplied finite bijection, and consequences of an explicit
optimized/reference search equivalence hypothesis. It does not formalize Rust,
SHA-256, Ed25519, HMAC, worker isolation, a concrete catalog, or a benchmark.
-/

namespace VeyraObserverSynthesisV3

structure Bundle (Root Payload : Type) where
  registryRoot : Root
  transportRoot : Root
  stageRoots : List Root
  payload : Payload
  deriving DecidableEq

variable {Root Payload Abstract Physical Class Config Result : Type}

/-- Canonical acceptance compares one supplied bundle with an exact rebuild. -/
def acceptsCanonical [DecidableEq Root] [DecidableEq Payload]
    (rebuild : Config → Option (Bundle Root Payload))
    (config : Config) (bundle : Bundle Root Payload) : Bool :=
  decide (rebuild config = some bundle)

theorem canonical_acceptance_sound [DecidableEq Root] [DecidableEq Payload]
    (rebuild : Config → Option (Bundle Root Payload))
    (config : Config) (bundle : Bundle Root Payload)
    (accepted : acceptsCanonical rebuild config bundle = true) :
    rebuild config = some bundle := by
  unfold acceptsCanonical at accepted
  exact of_decide_eq_true accepted

/-- A representation equivalence carries both inverse laws explicitly. -/
structure RepresentationBijection (Abstract Physical : Type) where
  encode : Abstract → Physical
  decode : Physical → Abstract
  decodeEncode : ∀ state, decode (encode state) = state
  encodeDecode : ∀ state, encode (decode state) = state

/-- Pull a task onto the physical carrier through the declared decoder. -/
def transportedTask (transport : RepresentationBijection Abstract Physical)
    (task : Abstract → Class) : Physical → Class :=
  task ∘ transport.decode

theorem bijective_transport_commutes
    (transport : RepresentationBijection Abstract Physical)
    (task : Abstract → Class) (state : Abstract) :
    transportedTask transport task (transport.encode state) = task state := by
  change task (transport.decode (transport.encode state)) = task state
  rw [transport.decodeEncode]

/-- The optimized engine is admitted only through an explicit equality witness. -/
structure SearchEquivalence
    (reference optimized : Config → Result) : Prop where
  sameResult : ∀ config, optimized config = reference config

theorem optimized_acceptance_replays_reference
    (reference optimized : Config → Result)
    (equivalent : SearchEquivalence reference optimized)
    (accepts : Result → Prop) (config : Config)
    (optimizedAccepted : accepts (optimized config)) :
    accepts (reference config) := by
  rw [← equivalent.sameResult config]
  exact optimizedAccepted

theorem optimized_exhaustion_requires_reference_exhaustion
    (reference optimized : Config → Result)
    (equivalent : SearchEquivalence reference optimized)
    (isExhausted : Result → Prop) (config : Config)
    (optimizedExhausted : isExhausted (optimized config)) :
    isExhausted (reference config) := by
  rw [← equivalent.sameResult config]
  exact optimizedExhausted

#print axioms canonical_acceptance_sound
#print axioms bijective_transport_commutes
#print axioms optimized_acceptance_replays_reference
#print axioms optimized_exhaustion_requires_reference_exhaustion

end VeyraObserverSynthesisV3
