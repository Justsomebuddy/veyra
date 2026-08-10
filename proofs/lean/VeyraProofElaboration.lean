import VeyraElaborationSemantics

/- Generated from one source-replayed, kernel-checked R10 elaboration artifact. -/
namespace VeyraElaborationExport
open VeyraProof
open VeyraElaboration

def sourceDigest : String := "ff6c6c1a73c57691940d717ebf71d6144a0e78de84cb375a3f6b0b2253f8bcb4"
def surfaceSyntaxDigest : String := "582e4cd06e19ed99d9f3d8d0ac68fb6e3b77b03854af9db192478bebe49fa6e2"
def semanticDigest : String := "9055f4b8ccc13a2d053e938bc4506529ccb2ff3310882416cf677d0d00223e0a"
def r7ArtifactDigest : String := "aca33a6a76af8b0f9958e722a11133dc851876ba718dce59c2486fba8232e362"
def r9BindingDigest : String := "8d20f686e617adad8b9905435919904780e56e39f2857b2db648e0c81edcd600"
def elaborationBindingDigest : String := "7d00e260c86abf07d849f7292e84e1c626735ee275924d37a86b2bac25779edc"
def elaboratedStatement : Formula 0 := (.forallE .recurrence (.resonates (.var ⟨0, by decide⟩) (.var ⟨0, by decide⟩)))
def elaboratedProof : Proof 0 := (.forallIntro .recurrence (.resonanceIntro (.var ⟨0, by decide⟩) (.var ⟨0, by decide⟩) (.pulse .silence) (.nativeLaw .weaveUnitRight [(.var ⟨0, by decide⟩)])))
def dependencyCatalog : List DependencyId := [.recurrenceFormation, .propositionFormation, .silenceDefinition, .pulseDefinition, .stitchDefinition, .weaveDefinition, .equalDefinition, .impliesDefinition, .forallDefinition, .resonatesDefinition, .assumeRule, .impIntroRule, .impElimRule, .forallIntroRule, .forallElimRule, .eqReflRule, .eqSymRule, .eqTransRule, .resonanceIntroRule, .stitchSilenceLeftLaw, .stitchSilenceRightLaw, .weaveSilenceRightLaw, .weavePulseLaw, .weaveUnitRightLaw, .intrinsicModeObserver, .foreignModeObstruction]
def declaredSupportIds : List DependencyId := [.propositionFormation, .recurrenceFormation, .equalDefinition, .forallDefinition, .pulseDefinition, .resonatesDefinition, .silenceDefinition, .weaveDefinition, .forallIntroRule, .resonanceIntroRule, .weaveUnitRightLaw, .intrinsicModeObserver]
def supportBits (support : DependencySupport) : List Bool :=
  dependencyCatalog.map fun dependency => support.contains dependency

theorem THM_R10_003_elaborated_proof_accepted :
    check [] elaboratedProof elaboratedStatement = true := by decide

def elaborationEmptyEnv : Env 0 := fun index => Fin.elim0 index

theorem THM_R10_004_elaborated_image_sound :
    ImageSemantics elaborationEmptyEnv elaboratedStatement := by
  exact THM_R10_002_checked_elaboration_image_sound elaborationEmptyEnv
    (context := []) (proof := elaboratedProof) (goal := elaboratedStatement)
    trivial THM_R10_003_elaborated_proof_accepted

theorem THM_R10_005_structural_support_matches :
    supportBits (elaborationSupport elaboratedProof elaboratedStatement) =
      supportBits (dependencies declaredSupportIds) := by decide

end VeyraElaborationExport
