namespace Veyra

/- A finite atlas uses a patch predicate and one local echo relation per patch. -/
def ExactPatchRestriction {Nod Patch : Type}
    (global : Nod → Nod → Prop) (localEcho : Patch → Nod → Nod → Prop)
    (onPatch : Patch → Nod → Prop) : Prop :=
  ∀ patch x y, onPatch patch x → onPatch patch y →
    (global x y ↔ localEcho patch x y)

def ContainsLocalEchoes {Nod Patch : Type}
    (generated : Nod → Nod → Prop) (localEcho : Patch → Nod → Nod → Prop)
    (onPatch : Patch → Nod → Prop) : Prop :=
  ∀ patch x y, onPatch patch x → onPatch patch y →
    localEcho patch x y → generated x y

def NoLocalContradiction {Nod Patch : Type}
    (generated : Nod → Nod → Prop) (localEcho : Patch → Nod → Nod → Prop)
    (onPatch : Patch → Nod → Prop) : Prop :=
  ∀ patch x y, onPatch patch x → onPatch patch y →
    generated x y → localEcho patch x y

def IsEchoEquivalence {Nod : Type} (relation : Nod → Nod → Prop) : Prop :=
  (∀ x, relation x x) ∧
  (∀ x y, relation x y → relation y x) ∧
  (∀ x y z, relation x y → relation y z → relation x z)

def IsGeneratedClosure {Nod Patch : Type}
    (generated : Nod → Nod → Prop) (localEcho : Patch → Nod → Nod → Prop)
    (onPatch : Patch → Nod → Prop) : Prop :=
  IsEchoEquivalence generated ∧
  ContainsLocalEchoes generated localEcho onPatch ∧
  ∀ global, IsEchoEquivalence global →
    ContainsLocalEchoes global localEcho onPatch →
    ∀ x y, generated x y → global x y

def ExactGlobalGluingExists {Nod Patch : Type}
    (localEcho : Patch → Nod → Nod → Prop)
    (onPatch : Patch → Nod → Prop) : Prop :=
  ∃ global, IsEchoEquivalence global ∧
    ExactPatchRestriction global localEcho onPatch

theorem generated_restriction_iff_no_local_contradiction
    {Nod Patch : Type} (generated : Nod → Nod → Prop)
    (localEcho : Patch → Nod → Nod → Prop) (onPatch : Patch → Nod → Prop)
    (contains : ContainsLocalEchoes generated localEcho onPatch) :
    ExactPatchRestriction generated localEcho onPatch ↔
      NoLocalContradiction generated localEcho onPatch := by
  constructor
  · intro exactRestriction patch x y hx hy generatedXY
    exact (exactRestriction patch x y hx hy).mp generatedXY
  · intro safe patch x y hx hy
    constructor
    · exact safe patch x y hx hy
    · exact contains patch x y hx hy

-- theorem-card: finite-generated-exact-gluing
-- A global equivalence with all exact patch restrictions exists exactly when
-- the generated closure adds no locally distinguished within-patch equality.
theorem THM_G4_001_exact_gluing_exists_iff_no_local_contradiction {Nod Patch : Type}
    (generated : Nod → Nod → Prop)
    (localEcho : Patch → Nod → Nod → Prop) (onPatch : Patch → Nod → Prop)
    (isClosure : IsGeneratedClosure generated localEcho onPatch) :
    ExactGlobalGluingExists localEcho onPatch ↔
      NoLocalContradiction generated localEcho onPatch := by
  rcases isClosure with ⟨generatedEquivalence, contains, least⟩
  constructor
  · rintro ⟨global, globalEquivalence, exactRestriction⟩
    have globalContains : ContainsLocalEchoes global localEcho onPatch := by
      intro patch x y hx hy localXY
      exact (exactRestriction patch x y hx hy).mpr localXY
    intro patch x y hx hy generatedXY
    have globalXY := least global globalEquivalence globalContains x y generatedXY
    exact (exactRestriction patch x y hx hy).mp globalXY
  · intro safe
    refine ⟨generated, generatedEquivalence, ?_⟩
    exact (generated_restriction_iff_no_local_contradiction
      generated localEcho onPatch contains).mpr safe

inductive TriangleNod where
  | a | b | c
  deriving DecidableEq

inductive TrianglePatch where
  | ab | bc | ca
  deriving DecidableEq

def triangleOnPatch : TrianglePatch → TriangleNod → Prop
  | .ab, x => x = .a ∨ x = .b
  | .bc, x => x = .b ∨ x = .c
  | .ca, x => x = .c ∨ x = .a

def triangleLocalEcho : TrianglePatch → TriangleNod → TriangleNod → Prop
  | .ab, x, y => triangleOnPatch .ab x ∧ triangleOnPatch .ab y
  | .bc, x, y => triangleOnPatch .bc x ∧ triangleOnPatch .bc y
  | .ca, x, y => triangleOnPatch .ca x ∧ triangleOnPatch .ca y ∧ x = y

def PairwiseOverlapCompatible
    (left right : TrianglePatch) : Prop :=
  ∀ x y,
    triangleOnPatch left x → triangleOnPatch right x →
    triangleOnPatch left y → triangleOnPatch right y →
    (triangleLocalEcho left x y ↔ triangleLocalEcho right x y)

-- theorem-card: triangle-singleton-overlap-compatibility
-- AB∩BC={b}, BC∩CA={c}, and CA∩AB={a}; all restricted relations agree.
theorem THM_G4_002_triangle_singleton_overlaps_pass :
    PairwiseOverlapCompatible .ab .bc ∧
    PairwiseOverlapCompatible .bc .ca ∧
    PairwiseOverlapCompatible .ca .ab := by
  constructor
  · intro x y habx hbcx haby hbcy
    cases x <;> cases y <;> simp_all [triangleOnPatch, triangleLocalEcho]
  · constructor
    · intro x y hbcx hcax hbcy hcay
      cases x <;> cases y <;> simp_all [triangleOnPatch, triangleLocalEcho]
    · intro x y hcax habx hcay haby
      cases x <;> cases y <;> simp_all [triangleOnPatch, triangleLocalEcho]

-- theorem-card: triangle-global-gluing-obstruction
-- Exact AB and BC restrictions force a~c by transitivity, contradicting the
-- CA section, which keeps a and c in distinct blocks.
theorem THM_G4_003_triangle_exact_gluing_impossible :
    ¬ ∃ global : TriangleNod → TriangleNod → Prop,
      (∀ x y z, global x y → global y z → global x z) ∧
      ExactPatchRestriction global triangleLocalEcho triangleOnPatch := by
  rintro ⟨global, transitive, exactRestriction⟩
  have gab : global .a .b :=
    (exactRestriction .ab .a .b (by simp [triangleOnPatch])
      (by simp [triangleOnPatch])).mpr (by simp [triangleLocalEcho, triangleOnPatch])
  have gbc : global .b .c :=
    (exactRestriction .bc .b .c (by simp [triangleOnPatch])
      (by simp [triangleOnPatch])).mpr (by simp [triangleLocalEcho, triangleOnPatch])
  have gac : global .a .c := transitive .a .b .c gab gbc
  have localAC : triangleLocalEcho .ca .a .c :=
    (exactRestriction .ca .a .c (by simp [triangleOnPatch])
      (by simp [triangleOnPatch])).mp gac
  simp [triangleLocalEcho, triangleOnPatch] at localAC

/- Digest-bound helper, not a promoted theorem card.  If every pair not already
in the generated closure is jointly inspected by some patch, exact restriction
prevents any exact global gluing from adding that pair. -/
theorem g4_generated_pair_coverage_unique_exact_gluing {Nod Patch : Type}
    (generated global : Nod → Nod → Prop)
    (localEcho : Patch → Nod → Nod → Prop) (onPatch : Patch → Nod → Prop)
    (isClosure : IsGeneratedClosure generated localEcho onPatch)
    (globalEquivalence : IsEchoEquivalence global)
    (exactRestriction : ExactPatchRestriction global localEcho onPatch)
    (pairCoverage : ∀ x y, ¬ generated x y →
      ∃ patch, onPatch patch x ∧ onPatch patch y) :
    ∀ x y, global x y ↔ generated x y := by
  rcases isClosure with ⟨_, generatedContains, least⟩
  have globalContains : ContainsLocalEchoes global localEcho onPatch := by
    intro patch x y hx hy localXY
    exact (exactRestriction patch x y hx hy).mpr localXY
  intro x y
  constructor
  · intro globalXY
    apply Classical.byContradiction
    intro notGenerated
    rcases pairCoverage x y notGenerated with ⟨patch, hx, hy⟩
    have localXY := (exactRestriction patch x y hx hy).mp globalXY
    exact notGenerated (generatedContains patch x y hx hy localXY)
  · intro generatedXY
    exact least global globalEquivalence globalContains x y generatedXY

inductive SingletonNod where
  | a | b
  deriving DecidableEq

inductive SingletonPatch where
  | a | b
  deriving DecidableEq

def singletonOnPatch : SingletonPatch → SingletonNod → Prop
  | .a, x => x = .a
  | .b, x => x = .b

def singletonLocalEcho : SingletonPatch → SingletonNod → SingletonNod → Prop
  | patch, x, y => singletonOnPatch patch x ∧ singletonOnPatch patch y

def singletonIdentity : SingletonNod → SingletonNod → Prop := Eq

def singletonUniversal : SingletonNod → SingletonNod → Prop := fun _ _ => True

/- Digest-bound helper, not a promoted theorem card.  The two disjoint singleton
patches admit both identity and universal exact gluings, hence existence does
not imply extensional uniqueness. -/
theorem g4_disjoint_singletons_exact_gluing_not_unique :
    IsEchoEquivalence singletonIdentity ∧
    IsEchoEquivalence singletonUniversal ∧
    ExactPatchRestriction singletonIdentity singletonLocalEcho singletonOnPatch ∧
    ExactPatchRestriction singletonUniversal singletonLocalEcho singletonOnPatch ∧
    ¬ (∀ x y, singletonIdentity x y ↔ singletonUniversal x y) := by
  constructor
  · exact ⟨fun _ => rfl, fun _ _ h => h.symm, fun _ _ _ hxy hyz => hxy.trans hyz⟩
  · constructor
    · exact ⟨fun _ => trivial, fun _ _ _ => trivial, fun _ _ _ _ _ => trivial⟩
    · constructor
      · intro patch x y hx hy
        cases patch <;> cases x <;> cases y <;>
          simp_all [singletonIdentity, singletonLocalEcho, singletonOnPatch]
      · constructor
        · intro patch x y hx hy
          cases patch <;> cases x <;> cases y <;>
            simp_all [singletonUniversal, singletonLocalEcho, singletonOnPatch]
        · intro same
          have impossible := (same .a .b).mpr trivial
          simp [singletonIdentity] at impossible

#check THM_G4_001_exact_gluing_exists_iff_no_local_contradiction
#check THM_G4_002_triangle_singleton_overlaps_pass
#check THM_G4_003_triangle_exact_gluing_impossible
#check g4_generated_pair_coverage_unique_exact_gluing
#check g4_disjoint_singletons_exact_gluing_not_unique

end Veyra
