import Std.Tactic

namespace Veyra

/- A standalone algebraic identity over Int with the Euclid-formula terms
`m² - n²`, `2mn`, and `m² + n²`. It proves no primitivity, positivity,
converse, or geometric classification. The pinned tree registers only the
fixed 3-4-5 Nat card (THM_G001); this candidate does not promote or bridge it.
-/

theorem RESEARCH_PY_L001_sq_add (x y : Int) :
    (x + y) * (x + y) = x * x + 2 * (x * y) + y * y := by
  calc
    (x + y) * (x + y) = x * (x + y) + y * (x + y) := by rw [Int.add_mul]
    _ = (x * x + x * y) + (y * x + y * y) := by rw [Int.mul_add, Int.mul_add]
    _ = x * x + x * y + (x * y + y * y) := by rw [Int.mul_comm y x]
    _ = x * x + (x * y + x * y) + y * y := by omega
    _ = x * x + (1 + 1) * (x * y) + y * y := by
          have htwo : x * y + x * y = (1 + 1) * (x * y) := by
            conv =>
              lhs
              rw [← Int.one_mul (x * y)]
              rw [← Int.add_mul]
          rw [htwo]
    _ = x * x + 2 * (x * y) + y * y := rfl

theorem RESEARCH_PY_L002_sq_sub (x y : Int) :
    (x - y) * (x - y) = x * x - 2 * (x * y) + y * y := by
  calc
    (x - y) * (x - y) = x * (x - y) - y * (x - y) := by rw [Int.sub_mul]
    _ = (x * x - x * y) - (y * x - y * y) := by rw [Int.mul_sub, Int.mul_sub]
    _ = (x * x - x * y) - (x * y - y * y) := by rw [Int.mul_comm y x]
    _ = x * x - x * y + -(x * y - y * y) := by rw [Int.sub_eq_add_neg]
    _ = x * x - x * y + (y * y - x * y) := by rw [Int.neg_sub]
    _ = x * x + -(x * y) + (y * y + -(x * y)) := by omega
    _ = x * x + (y * y + (-(x * y) + -(x * y))) := by omega
    _ = x * x + (y * y + (-((1 + 1) * (x * y)))) := by
          have hneg : -(x * y) + -(x * y) = -((1 + 1) * (x * y)) := by
            have htwo : x * y + x * y = (1 + 1) * (x * y) := by
              conv =>
                lhs
                rw [← Int.one_mul (x * y)]
                rw [← Int.add_mul]
            calc
              -(x * y) + -(x * y) = -(x * y + x * y) := by rw [Int.neg_add]
              _ = -((1 + 1) * (x * y)) := by rw [htwo]
          rw [hneg]
    _ = x * x + (y * y + (-(2 * (x * y)))) := rfl
    _ = x * x - 2 * (x * y) + y * y := by omega

theorem RESEARCH_PY_L003_sq_mul_two (x : Int) :
    (2 * x) * (2 * x) = 4 * (x * x) := by
  calc
    (2 * x) * (2 * x) = 2 * (x * (2 * x)) := by rw [Int.mul_assoc]
    _ = 2 * (x * (x * 2)) := by rw [Int.mul_comm 2 x]
    _ = 2 * ((x * x) * 2) := by rw [← Int.mul_assoc x x 2]
    _ = 2 * (2 * (x * x)) := by rw [Int.mul_comm (x * x) 2]
    _ = (2 * 2) * (x * x) := by rw [Int.mul_assoc]
    _ = 4 * (x * x) := by rfl

theorem RESEARCH_PY_L004_mul_sq (x y : Int) :
    (x * y) * (x * y) = (x * x) * (y * y) := by
  calc
    (x * y) * (x * y) = x * (y * (x * y)) := by rw [Int.mul_assoc]
    _ = x * ((x * y) * y) := by rw [← Int.mul_assoc y x y, Int.mul_comm y x]
    _ = (x * (x * y)) * y := by rw [← Int.mul_assoc x (x * y) y]
    _ = ((x * x) * y) * y := by rw [← Int.mul_assoc x x y]
    _ = (x * x) * (y * y) := by rw [Int.mul_assoc]

theorem RESEARCH_PY_L005_ring_tail (a b c : Int) :
    a - 2 * c + b + 4 * c = a + 2 * c + b := by
  omega

theorem RESEARCH_PY_T001_pythagorean_triple_formula (m n : Int) :
    (m * m - n * n) * (m * m - n * n) + (2 * m * n) * (2 * m * n) =
      (m * m + n * n) * (m * m + n * n) := by
  rw [RESEARCH_PY_L002_sq_sub]
  rw [Int.mul_assoc 2 m n]
  rw [RESEARCH_PY_L003_sq_mul_two]
  rw [RESEARCH_PY_L004_mul_sq m n]
  rw [RESEARCH_PY_L001_sq_add]
  exact RESEARCH_PY_L005_ring_tail (m * m * (m * m)) ((n * n) * (n * n)) ((m * m) * (n * n))

#check RESEARCH_PY_T001_pythagorean_triple_formula

end Veyra
