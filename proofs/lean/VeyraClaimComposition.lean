import Std

/-!
Bounded abstract contract for exact finite conjunction.

This module proves preservation and non-upgrade laws for the abstract
composition schema only. It is not a proof that Python receipts are valid, a
P2 introduction rule, or a source-truth theorem.
-/

namespace VeyraClaimComposition

structure Contract where
  claimRoot : Nat → Prop
  scopeRoot : Nat → Prop
  assumptionRoot : Nat → Prop
  observerRoot : Nat → Prop
  doctrineRoot : Nat → Prop

def unionField (field : Contract → Nat → Prop) (sources : List Contract) : Nat → Prop :=
  fun root => ∃ source ∈ sources, field source root

def exactConjunction (sources : List Contract) : Contract where
  claimRoot := unionField Contract.claimRoot sources
  scopeRoot := unionField Contract.scopeRoot sources
  assumptionRoot := unionField Contract.assumptionRoot sources
  observerRoot := unionField Contract.observerRoot sources
  doctrineRoot := unionField Contract.doctrineRoot sources

theorem unionField_mem_iff
    (field : Contract → Nat → Prop) (sources : List Contract) (root : Nat) :
    unionField field sources root ↔ ∃ source ∈ sources, field source root := by
  rfl

theorem unionField_permutation
    (field : Contract → Nat → Prop) {left right : List Contract}
    (permutation : left.Perm right) :
    unionField field left = unionField field right := by
  funext root
  apply propext
  constructor
  · rintro ⟨source, member, evidence⟩
    exact ⟨source, permutation.mem_iff.mp member, evidence⟩
  · rintro ⟨source, member, evidence⟩
    exact ⟨source, permutation.mem_iff.mpr member, evidence⟩

theorem exactConjunction_claim_permutation
    {left right : List Contract} (permutation : left.Perm right) :
    (exactConjunction left).claimRoot = (exactConjunction right).claimRoot :=
  unionField_permutation Contract.claimRoot permutation

theorem exactConjunction_scope_permutation
    {left right : List Contract} (permutation : left.Perm right) :
    (exactConjunction left).scopeRoot = (exactConjunction right).scopeRoot :=
  unionField_permutation Contract.scopeRoot permutation

theorem exactConjunction_assumption_permutation
    {left right : List Contract} (permutation : left.Perm right) :
    (exactConjunction left).assumptionRoot = (exactConjunction right).assumptionRoot :=
  unionField_permutation Contract.assumptionRoot permutation

theorem exactConjunction_observer_permutation
    {left right : List Contract} (permutation : left.Perm right) :
    (exactConjunction left).observerRoot = (exactConjunction right).observerRoot :=
  unionField_permutation Contract.observerRoot permutation

theorem exactConjunction_doctrine_permutation
    {left right : List Contract} (permutation : left.Perm right) :
    (exactConjunction left).doctrineRoot = (exactConjunction right).doctrineRoot :=
  unionField_permutation Contract.doctrineRoot permutation

theorem unionField_append
    (field : Contract → Nat → Prop) (left right : List Contract) (root : Nat) :
    unionField field (left ++ right) root ↔
      unionField field left root ∨ unionField field right root := by
  constructor
  · rintro ⟨source, member, evidence⟩
    rcases List.mem_append.mp member with member | member
    · exact Or.inl ⟨source, member, evidence⟩
    · exact Or.inr ⟨source, member, evidence⟩
  · rintro (⟨source, member, evidence⟩ | ⟨source, member, evidence⟩)
    · exact ⟨source, List.mem_append.mpr (Or.inl member), evidence⟩
    · exact ⟨source, List.mem_append.mpr (Or.inr member), evidence⟩

structure CompositionReceipt where
  sourceCount : Nat
  p2PromotionEstablished : Bool
  independenceEstablished : Bool
  assumptionsDischarged : Bool
  universalized : Bool

def exactReceipt (sources : List Contract) : CompositionReceipt where
  sourceCount := sources.length
  p2PromotionEstablished := false
  independenceEstablished := false
  assumptionsDischarged := false
  universalized := false

theorem exactReceipt_no_p2_promotion (sources : List Contract) :
    (exactReceipt sources).p2PromotionEstablished = false := by
  rfl

theorem exactReceipt_no_independence (sources : List Contract) :
    (exactReceipt sources).independenceEstablished = false := by
  rfl

theorem exactReceipt_no_assumption_discharge (sources : List Contract) :
    (exactReceipt sources).assumptionsDischarged = false := by
  rfl

theorem exactReceipt_no_universalization (sources : List Contract) :
    (exactReceipt sources).universalized = false := by
  rfl

end VeyraClaimComposition
