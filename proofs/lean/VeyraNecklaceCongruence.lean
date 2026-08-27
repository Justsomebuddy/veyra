namespace Veyra

/-- Left rotation of a word by `i` positions. -/
def rotN (i : Nat) (l : List Nat) : List Nat :=
  l.drop i ++ l.take i

/-- All words of length `n` over the alphabet `{0, …, k-1}`. -/
def words (k : Nat) : Nat → List (List Nat)
  | 0 => [[]]
  | n + 1 => (words k n).foldr (fun w acc => ((List.range k).map fun a => a :: w) ++ acc) []

/-- Constant-word test. -/
def isConst : List Nat → Bool
  | [] => true
  | a :: t => t.all (· == a)

/-- Number of distinct rotations of a word. -/
def orbitSize (l : List Nat) : Nat :=
  (((List.range l.length).map fun i => rotN i l).eraseDups).length

-- theorem-card: rotation-composition-instance
-- Exact length-3 fixture: composing rotations adds offsets modulo the length.
theorem THM_N8_001_rotation_composition_len3 :
    rotN 1 (rotN 2 [0, 1, 2]) = rotN 0 [0, 1, 2] ∧
    rotN 2 (rotN 2 [0, 1, 2]) = rotN 1 [0, 1, 2] := by
  decide

-- theorem-card: orbit-dichotomy p=3 k=2
-- Every nonconstant length-3 binary word has exactly 3 distinct rotations;
-- every constant word has exactly 1.
theorem THM_N8_002_orbit_dichotomy_p3_k2 :
    (((words 2 3).filter fun w => !isConst w).all fun w => orbitSize w == 3) = true ∧
    (((words 2 3).filter fun w => isConst w).all fun w => orbitSize w == 1) = true := by
  decide

-- theorem-card: orbit-dichotomy p=5 k=2
theorem THM_N8_003_orbit_dichotomy_p5_k2 :
    (((words 2 5).filter fun w => !isConst w).all fun w => orbitSize w == 5) = true ∧
    (((words 2 5).filter fun w => isConst w).all fun w => orbitSize w == 1) = true := by
  decide

-- theorem-card: fermat-count p=3 k=2
-- The 2^3 - 2 = 6 nonconstant words are exactly 2 full orbits of size 3.
theorem THM_N8_004_fermat_count_p3_k2 :
    ((words 2 3).filter fun w => !isConst w).length = 6 ∧ 6 = 2 * 3 := by
  decide

-- theorem-card: fermat-count p=5 k=2
-- The 2^5 - 2 = 30 nonconstant words are exactly 6 full orbits of size 5.
theorem THM_N8_005_fermat_count_p5_k2 :
    ((words 2 5).filter fun w => !isConst w).length = 30 ∧ 30 = 6 * 5 := by
  decide

-- theorem-card: gauss-primitive-count n=4 k=2
-- Exactly 12 aperiodic length-4 binary words; 12 = 3 full orbits of size 4.
theorem THM_N8_006_gauss_primitive_count_n4_k2 :
    ((words 2 4).filter fun w => orbitSize w == 4).length = 12 ∧ 12 = 3 * 4 := by
  decide

-- theorem-card: composite-length counterpressure
-- The dichotomy fails at composite length: [0,1,0,1] has orbit size 2,
-- which is neither 1 nor 4.
theorem THM_N8_007_composite_dichotomy_counterexample :
    orbitSize [0, 1, 0, 1] = 2 ∧ (2 == 1) = false ∧ (2 == 4) = false := by
  decide

#check THM_N8_007_composite_dichotomy_counterexample

end Veyra
