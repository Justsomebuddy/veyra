/-!
Abstract observer-synthesis v5 pruning, transport, and exhaustion boundary.

These results concern explicit finite catalogs and caller-supplied laws. They
do not formalize Rust, concrete cost functions, hashes, signatures, worker
isolation, or the admissibility of any production pruning heuristic.
-/

namespace VeyraObserverSynthesisV5

variable {Candidate Node Abstract Physical : Type}

/-- A pruning certificate is admissible only when its lower bound applies to
every catalog candidate represented below that node. -/
structure AdmissibleBound
    (represents : Node → Candidate → Prop)
    (cost : Candidate → Nat)
    (lowerBound : Node → Nat) : Prop where
  lower_le_cost : ∀ node candidate, represents node candidate →
    lowerBound node ≤ cost candidate

def prunable (lowerBound : Node → Nat) (incumbent : Nat) (node : Node) : Prop :=
  incumbent ≤ lowerBound node

theorem admissible_pruning_cannot_hide_improvement
    (represents : Node → Candidate → Prop)
    (cost : Candidate → Nat) (lowerBound : Node → Nat)
    (admissible : AdmissibleBound represents cost lowerBound)
    (incumbent : Nat) (node : Node)
    (pruned : prunable lowerBound incumbent node)
    (candidate : Candidate) (below : represents node candidate) :
    incumbent ≤ cost candidate := by
  exact Nat.le_trans pruned (admissible.lower_le_cost node candidate below)

/-- A bounded branch-and-bound result records exactly why every catalog row is
either visited or covered by an admissibly pruned node. -/
structure BranchAndBoundCover
    (catalog : List Candidate)
    (visited : Candidate → Prop)
    (represents : Node → Candidate → Prop)
    (pruned : Node → Prop) : Prop where
  covers : ∀ candidate ∈ catalog,
    visited candidate ∨ ∃ node, pruned node ∧ represents node candidate

theorem branch_and_bound_catalog_completeness
    (catalog : List Candidate)
    (visited : Candidate → Prop)
    (represents : Node → Candidate → Prop)
    (cost : Candidate → Nat) (lowerBound : Node → Nat)
    (incumbent : Nat)
    (admissible : AdmissibleBound represents cost lowerBound)
    (cover : BranchAndBoundCover catalog visited represents
      (prunable lowerBound incumbent))
    (visitedBound : ∀ candidate, visited candidate → incumbent ≤ cost candidate)
    (candidate : Candidate) (member : candidate ∈ catalog) :
    incumbent ≤ cost candidate := by
  rcases cover.covers candidate member with seen | ⟨node, pruned, below⟩
  · exact visitedBound candidate seen
  · exact admissible_pruning_cannot_hide_improvement
      represents cost lowerBound admissible incumbent node pruned candidate below

/-- An explicitly admitted transport supplies inverse laws and an explicit
predicate-preservation law; bijectivity alone does not invent that law. -/
structure AdmissibleTransport
    (abstractAccepts : Abstract → Prop)
    (physicalAccepts : Physical → Prop) where
  encode : Abstract → Physical
  decode : Physical → Abstract
  decodeEncode : ∀ state, decode (encode state) = state
  encodeDecode : ∀ state, encode (decode state) = state
  preserves : ∀ state, physicalAccepts (encode state) ↔ abstractAccepts state

theorem explicit_admissible_transport_preserves_acceptance
    (abstractAccepts : Abstract → Prop)
    (physicalAccepts : Physical → Prop)
    (transport : AdmissibleTransport abstractAccepts physicalAccepts)
    (state : Abstract) :
    physicalAccepts (transport.encode state) ↔ abstractAccepts state := by
  exact transport.preserves state

/-- Exact exhaustion means every row of one explicit finite catalog was
checked and rejected. -/
def exactCatalogExhaustion
    (catalog : List Candidate) (accepts : Candidate → Bool) : Prop :=
  ∀ candidate ∈ catalog, accepts candidate = false

theorem exact_finite_catalog_exhaustion
    (catalog : List Candidate) (accepts : Candidate → Bool)
    (exhausted : exactCatalogExhaustion catalog accepts) :
    ¬ ∃ candidate, candidate ∈ catalog ∧ accepts candidate = true := by
  intro witness
  rcases witness with ⟨candidate, member, accepted⟩
  have rejected := exhausted candidate member
  rw [rejected] at accepted
  contradiction

#print axioms admissible_pruning_cannot_hide_improvement
#print axioms branch_and_bound_catalog_completeness
#print axioms explicit_admissible_transport_preserves_acceptance
#print axioms exact_finite_catalog_exhaustion

end VeyraObserverSynthesisV5
