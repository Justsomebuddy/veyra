/-!
Abstract laws for the restricted realization-context transport boundary.

The executable contract uses total finite state reindexings and acts on
extensional response partitions by inverse image.  This file proves only the
corresponding relation-level identity, composition, indiscrete-bottom,
common-refinement, and conditional cost laws.  It does not formalize Python,
R11 replay, R16 admission, canonical bytes, digests, finite resource bounds,
receipt reconstruction, P1-A, or cross-doctrine transport.
-/

namespace VeyraRealizationTransport

universe u v w

/-- A response partition is represented extensionally by its binary relation. -/
abbrev PartitionRel (State : Type u) := State → State → Prop

/-- Reindex a target relation along a total source-to-target state map. -/
def pullback {Source : Type u} {Target : Type v}
    (stateMap : Source → Target) (relation : PartitionRel Target) :
    PartitionRel Source :=
  fun left right => relation (stateMap left) (stateMap right)

/-- The R16 realization bottom is the indiscrete partition. -/
def indiscrete (State : Type u) : PartitionRel State :=
  fun _ _ => True

/-- Common refinement is pointwise intersection of partition relations. -/
def commonRefinement {State : Type u}
    (left right : PartitionRel State) : PartitionRel State :=
  fun first second => left first second ∧ right first second

theorem pullback_identity {State : Type u} (relation : PartitionRel State) :
    pullback (fun state : State => state) relation = relation := by
  rfl

theorem pullback_composition
    {Source : Type u} {Middle : Type v} {Target : Type w}
    (sourceToMiddle : Source → Middle)
    (middleToTarget : Middle → Target)
    (relation : PartitionRel Target) :
    pullback (middleToTarget ∘ sourceToMiddle) relation =
      pullback sourceToMiddle (pullback middleToTarget relation) := by
  rfl

theorem pullback_indiscrete
    {Source : Type u} {Target : Type v}
    (stateMap : Source → Target) :
    pullback stateMap (indiscrete Target) = indiscrete Source := by
  rfl

theorem pullback_commonRefinement
    {Source : Type u} {Target : Type v}
    (stateMap : Source → Target)
    (left right : PartitionRel Target) :
    pullback stateMap (commonRefinement left right) =
      commonRefinement (pullback stateMap left) (pullback stateMap right) := by
  rfl

/-- Cost nonincrease is an explicit hypothesis on an admitted closure action;
it is not inferred from relation pullback alone. -/
def CostNonincreasing {SourceClosure : Type u} {TargetClosure : Type v}
    (action : TargetClosure → SourceClosure)
    (sourceCost : SourceClosure → Nat)
    (targetCost : TargetClosure → Nat) : Prop :=
  ∀ target, sourceCost (action target) ≤ targetCost target

theorem cost_nonincrease_identity
    {Closure : Type u} (cost : Closure → Nat) :
    CostNonincreasing (fun value : Closure => value) cost cost := by
  intro value
  exact Nat.le_refl (cost value)

theorem cost_nonincrease_composition
    {SourceClosure : Type u} {MiddleClosure : Type v}
    {TargetClosure : Type w}
    (targetToMiddle : TargetClosure → MiddleClosure)
    (middleToSource : MiddleClosure → SourceClosure)
    (sourceCost : SourceClosure → Nat)
    (middleCost : MiddleClosure → Nat)
    (targetCost : TargetClosure → Nat)
    (firstLaw : CostNonincreasing middleToSource sourceCost middleCost)
    (secondLaw : CostNonincreasing targetToMiddle middleCost targetCost) :
    CostNonincreasing (middleToSource ∘ targetToMiddle) sourceCost targetCost := by
  intro target
  exact Nat.le_trans (firstLaw (targetToMiddle target)) (secondLaw target)

#print axioms pullback_identity
#print axioms pullback_composition
#print axioms pullback_indiscrete
#print axioms pullback_commonRefinement
#print axioms cost_nonincrease_identity
#print axioms cost_nonincrease_composition

end VeyraRealizationTransport
