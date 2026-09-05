import VeyraPrimitiveRoot

/-! # General necklace theorems — the all-prime, all-alphabet forms of the N8 cards

Mathlib-free. Words are `List α`; a word is read cyclically (`read`), rotated
(`rot`), and the shift stabilizer is shown closed under `Nat.gcd`
(`THM_NO_002`). For a prime length every nontrivial shift forces constancy
(`THM_NO_003`), so the `p` rotations of a nonconstant word are pairwise
distinct (`THM_NO_004`). A duplicate-free list closed under an orbit
assignment with orbits of exact size `p` has length divisible by `p`
(`THM_NO_005`), which with the explicit enumeration `words k p` yields
`k^p = k + p·q` (`THM_NO_006`), `p ∣ k^p − k` (`THM_NO_007`) and
`k^p % p = k % p` (`THM_NO_008`) for every prime `p` and every `k`; the
divisibility content of the N8 Fermat-count cards (`p = 3, 5` with `k = 2`)
plus `p = 7` follows (`THM_NO_009`). Host-carried computation:
"for all primes" is the host `Nat` quantifier (README "How to read claims").
The Gauss divisibility at every positive length — the aperiodic words split
into full rotation orbits, so `n ∣ #aperiodic(k, n)` (`THM_NO_010`) — and the
bridge aperiodic ⇔ primitive (`THM_NO_011`, via `VeyraPrimitiveRoot`) close the
composite-length case for divisibility; the Möbius count identity itself is not
formalized here. -/

namespace Veyra
namespace Necklace

variable {α : Type} [Inhabited α]

/-- Cyclic read of a word: position `t` is read modulo the length. -/
def read (l : List α) (t : Nat) : α := l.getD (t % l.length) default

/-- Rotation by `d`: the word read from position `d` onward, cyclically. -/
def rot (d : Nat) (l : List α) : List α :=
  (List.range l.length).map fun t => read l (t + d)

theorem getD_map_range (f : Nat → α) (n i : Nat) :
    ((List.range n).map f).getD i default = if i < n then f i else default := by
  rw [List.getD_eq_getElem?_getD]
  by_cases h : i < n
  · have hlen : i < ((List.range n).map f).length := by
      rw [List.length_map, List.length_range]; exact h
    rw [List.getElem?_eq_getElem hlen, if_pos h]
    simp
  · have hlen : ((List.range n).map f).length ≤ i := by
      rw [List.length_map, List.length_range]; exact Nat.le_of_not_lt h
    rw [List.getElem?_eq_none_iff.mpr hlen, if_neg h]
    rfl

theorem length_rot (d : Nat) (l : List α) : (rot d l).length = l.length := by
  simp [rot]

theorem read_of_lt (l : List α) (t : Nat) (h : t < l.length) : read l t = l[t] := by
  unfold read
  rw [Nat.mod_eq_of_lt h, List.getD_eq_getElem?_getD, List.getElem?_eq_getElem h]
  rfl

theorem read_add_length (l : List α) (t : Nat) : read l (t + l.length) = read l t := by
  unfold read
  rw [Nat.add_mod_right]

theorem read_mod (l : List α) (t : Nat) : read l (t % l.length) = read l t := by
  unfold read
  rw [Nat.mod_mod]

theorem read_rot (d : Nat) (l : List α) (t : Nat) : read (rot d l) t = read l (t + d) := by
  unfold read
  rw [length_rot]
  show ((List.range l.length).map fun t => read l (t + d)).getD (t % l.length) default = _
  rw [getD_map_range]
  cases l with
  | nil => simp
  | cons a l' =>
      have hlt : t % (a :: l').length < (a :: l').length := Nat.mod_lt _ (Nat.succ_pos _)
      rw [if_pos hlt]
      show read (a :: l') (t % (a :: l').length + d) = read (a :: l') (t + d)
      unfold read
      rw [Nat.mod_add_mod]

theorem ext_read (l₁ l₂ : List α) (hlen : l₁.length = l₂.length)
    (h : ∀ t, t < l₁.length → read l₁ t = read l₂ t) : l₁ = l₂ := by
  apply List.ext_getElem hlen
  intro i h₁ h₂
  rw [← read_of_lt l₁ i h₁, ← read_of_lt l₂ i h₂]
  exact h i h₁

-- theorem-card: necklace rotation group law
theorem THM_NO_001_rot_rot (a b : Nat) (l : List α) : rot a (rot b l) = rot (a + b) l := by
  apply ext_read
  · rw [length_rot, length_rot, length_rot]
  · intro t _
    rw [read_rot, read_rot, read_rot, Nat.add_assoc]

theorem rot_zero (l : List α) : rot 0 l = l := by
  apply ext_read
  · exact length_rot 0 l
  · intro t _
    rw [read_rot, Nat.add_zero]

theorem rot_length (l : List α) : rot l.length l = l := by
  apply ext_read
  · exact length_rot _ l
  · intro t _
    rw [read_rot, read_add_length]

theorem rot_mod (d : Nat) (l : List α) : rot d l = rot (d % l.length) l := by
  apply ext_read
  · rw [length_rot, length_rot]
  · intro t _
    rw [read_rot, read_rot]
    unfold read
    rw [Nat.add_mod_mod]

/-- The shift `d` fixes the word. -/
def Fix (l : List α) (d : Nat) : Prop := rot d l = l

theorem fix_add {l : List α} {a b : Nat} (ha : Fix l a) (hb : Fix l b) : Fix l (a + b) := by
  unfold Fix at *
  rw [← THM_NO_001_rot_rot, hb, ha]

theorem fix_mul {l : List α} {a : Nat} (ha : Fix l a) (q : Nat) : Fix l (a * q) := by
  induction q with
  | zero => exact rot_zero l
  | succ q ih =>
      rw [Nat.mul_succ]
      exact fix_add ih ha

theorem fix_mod {l : List α} {a b : Nat} (ha : Fix l a) (hb : Fix l b) : Fix l (b % a) := by
  unfold Fix at *
  have hsplit : b = b % a + a * (b / a) := (Nat.mod_add_div b a).symm
  have hmul : rot (a * (b / a)) l = l := fix_mul ha (b / a)
  rw [hsplit, ← THM_NO_001_rot_rot, hmul] at hb
  exact hb

-- theorem-card: necklace stabilizer is closed under gcd
theorem THM_NO_002_fix_gcd (l : List α) (a b : Nat) (ha : Fix l a) (hb : Fix l b) :
    Fix l (Nat.gcd a b) := by
  induction a, b using Nat.gcd.induction with
  | H0 n => rw [Nat.gcd_zero_left]; exact hb
  | H1 m n _ ih =>
      rw [Nat.gcd_rec]
      exact ih (fix_mod ha hb) ha

theorem read_const_of_fix_one {l : List α} (h : Fix l 1) : ∀ t, read l t = read l 0 := by
  intro t
  induction t with
  | zero => rfl
  | succ t ih =>
      have := read_rot 1 l t
      unfold Fix at h
      rw [h] at this
      rw [← this, ih]

/-- Constant word: any two letters agree. -/
def IsConst (l : List α) : Prop := ∀ a ∈ l, ∀ b ∈ l, a = b

theorem isConst_of_fix_one {l : List α} (h : Fix l 1) : IsConst l := by
  intro a ha b hb
  obtain ⟨i, hi⟩ := List.mem_iff_getElem.mp ha
  obtain ⟨j, hj⟩ := List.mem_iff_getElem.mp hb
  obtain ⟨hi₁, hi₂⟩ := hi
  obtain ⟨hj₁, hj₂⟩ := hj
  rw [← hi₂, ← hj₂, ← read_of_lt l i hi₁, ← read_of_lt l j hj₁,
    read_const_of_fix_one h i, read_const_of_fix_one h j]

/-- Local primality predicate (no Mathlib): at least 2 and only trivial divisors. -/
def IsPrime (p : Nat) : Prop := 2 ≤ p ∧ ∀ d, d ∣ p → d = 1 ∨ d = p

theorem gcd_eq_one_of_prime {p d : Nat} (hp : IsPrime p) (hd : 0 < d) (hdp : d < p) :
    Nat.gcd d p = 1 := by
  rcases hp.2 (Nat.gcd d p) (Nat.gcd_dvd_right d p) with h | h
  · exact h
  · exfalso
    have hdiv : p ∣ d := h ▸ Nat.gcd_dvd_left d p
    exact Nat.lt_irrefl _ (Nat.lt_of_lt_of_le hdp (Nat.le_of_dvd hd hdiv))

-- theorem-card: prime-length orbit dichotomy, all primes, any alphabet
-- A word of prime length fixed by a nontrivial shift is constant.
theorem THM_NO_003_prime_dichotomy (p : Nat) (hp : IsPrime p) (l : List α)
    (hlen : l.length = p) (d : Nat) (hd : 0 < d) (hdp : d < p) (hfix : rot d l = l) :
    IsConst l := by
  have hp' : Fix l p := by
    unfold Fix
    rw [← hlen]
    exact rot_length l
  have hg : Fix l (Nat.gcd d p) := THM_NO_002_fix_gcd l d p hfix hp'
  rw [gcd_eq_one_of_prime hp hd hdp] at hg
  exact isConst_of_fix_one hg


theorem mem_of_mem_rot {d : Nat} {l : List α} {a : α} (h : a ∈ rot d l) : a ∈ l := by
  unfold rot at h
  rw [List.mem_map] at h
  obtain ⟨t, ht, rfl⟩ := h
  rw [List.mem_range] at ht
  cases l with
  | nil => exact absurd ht (Nat.not_lt_zero _)
  | cons b l' =>
      have hlt : (t + d) % (b :: l').length < (b :: l').length := Nat.mod_lt _ (Nat.succ_pos _)
      rw [← read_mod, read_of_lt _ _ hlt]
      exact List.getElem_mem hlt

theorem rot_rot_sub (d : Nat) (l : List α) : rot (l.length - d % l.length) (rot d l) = l := by
  rw [rot_mod d l, THM_NO_001_rot_rot]
  cases l with
  | nil => rfl
  | cons b l' =>
      have hlt : d % (b :: l').length < (b :: l').length := Nat.mod_lt _ (Nat.succ_pos _)
      rw [Nat.sub_add_cancel (Nat.le_of_lt hlt)]
      exact rot_length (b :: l')

theorem mem_rot_iff (d : Nat) (l : List α) (a : α) : a ∈ rot d l ↔ a ∈ l := by
  constructor
  · exact mem_of_mem_rot
  · intro h
    have h' : a ∈ rot (l.length - d % l.length) (rot d l) := by
      rw [rot_rot_sub]; exact h
    exact mem_of_mem_rot h'

theorem isConst_rot_iff (d : Nat) (l : List α) : IsConst (rot d l) ↔ IsConst l := by
  unfold IsConst
  constructor
  · intro h a ha b hb
    exact h a ((mem_rot_iff d l a).mpr ha) b ((mem_rot_iff d l b).mpr hb)
  · intro h a ha b hb
    exact h a ((mem_rot_iff d l a).mp ha) b ((mem_rot_iff d l b).mp hb)

theorem rot_add_length (d : Nat) (l : List α) : rot (d + l.length) l = rot d l := by
  rw [← THM_NO_001_rot_rot, rot_length]

-- theorem-card: the p rotations of a nonconstant prime-length word are pairwise distinct
theorem THM_NO_004_rotations_distinct (p : Nat) (hp : IsPrime p) (l : List α)
    (hlen : l.length = p) (hnc : ¬ IsConst l) (i j : Nat) (hi : i < p) (hj : j < p)
    (h : rot i l = rot j l) : i = j := by
  -- reduce to the case i < j by symmetry
  have key : ∀ i j, i < j → j < p → rot i l = rot j l → False := by
    intro i j hij hjp hrot
    have h1 : rot (p - i) (rot i l) = l := by
      rw [THM_NO_001_rot_rot, Nat.sub_add_cancel (Nat.le_of_lt (Nat.lt_trans hij hjp)), ← hlen]
      exact rot_length l
    have h2 : rot (p - i) (rot j l) = rot (j - i) l := by
      rw [THM_NO_001_rot_rot]
      have harith : p - i + j = (j - i) + p := by omega
      rw [harith, ← hlen, rot_add_length]
    rw [hrot, h2] at h1
    exact hnc (THM_NO_003_prime_dichotomy p hp l hlen (j - i) (by omega) (by omega) h1)
  rcases Nat.lt_trichotomy i j with hlt | heq | hgt
  · exact absurd h (fun h => key i j hlt hj h)
  · exact heq
  · exact absurd h.symm (fun h => key j i hgt hi h)

/-! ## Enumeration of all words of a fixed length over `{0, …, k-1}` -/

/-- Prepend every letter of `as` to every word of `ws`. -/
def prepAll : List Nat → List (List Nat) → List (List Nat)
  | [], _ => []
  | a :: as, ws => ws.map (fun w => a :: w) ++ prepAll as ws

/-- All words of length `n` over the alphabet `{0, …, k-1}`. -/
def words (k : Nat) : Nat → List (List Nat)
  | 0 => [[]]
  | n + 1 => prepAll (List.range k) (words k n)

theorem length_prepAll (as : List Nat) (ws : List (List Nat)) :
    (prepAll as ws).length = as.length * ws.length := by
  induction as with
  | nil => simp [prepAll]
  | cons a as ih =>
      simp only [prepAll, List.length_append, List.length_map, List.length_cons, ih]
      rw [Nat.succ_mul, Nat.add_comm]

theorem length_words (k n : Nat) : (words k n).length = k ^ n := by
  induction n with
  | zero => rfl
  | succ n ih =>
      simp only [words, length_prepAll, List.length_range, ih, Nat.pow_succ]
      rw [Nat.mul_comm]

theorem mem_prepAll (as : List Nat) (ws : List (List Nat)) (w : List Nat) :
    w ∈ prepAll as ws ↔ ∃ a ∈ as, ∃ v ∈ ws, w = a :: v := by
  induction as with
  | nil => simp [prepAll]
  | cons a as ih =>
      simp only [prepAll, List.mem_append, List.mem_map, ih, List.mem_cons]
      constructor
      · rintro (⟨v, hv, rfl⟩ | ⟨b, hb, v, hv, rfl⟩)
        · exact ⟨a, Or.inl rfl, v, hv, rfl⟩
        · exact ⟨b, Or.inr hb, v, hv, rfl⟩
      · rintro ⟨b, hb | hb, v, hv, rfl⟩
        · exact Or.inl ⟨v, hv, hb ▸ rfl⟩
        · exact Or.inr ⟨b, hb, v, hv, rfl⟩

theorem mem_words (k n : Nat) (w : List Nat) :
    w ∈ words k n ↔ w.length = n ∧ ∀ a ∈ w, a < k := by
  induction n generalizing w with
  | zero =>
      cases w with
      | nil => simp [words]
      | cons a t => simp [words]
  | succ n ih =>
      simp only [words, mem_prepAll, List.mem_range]
      cases w with
      | nil =>
          constructor
          · rintro ⟨a, _, v, _, h⟩; cases h
          · rintro ⟨h, _⟩; cases h
      | cons b t =>
          constructor
          · rintro ⟨a, ha, v, hv, h⟩
            obtain ⟨rfl, rfl⟩ := List.cons_eq_cons.mp h
            obtain ⟨hlen, hall⟩ := (ih t).mp hv
            refine ⟨by rw [List.length_cons, hlen], ?_⟩
            intro c hc
            rw [List.mem_cons] at hc
            rcases hc with rfl | hc
            · exact ha
            · exact hall c hc
          · rintro ⟨hlen, hall⟩
            refine ⟨b, hall b (List.mem_cons_self), t, (ih t).mpr ⟨by simpa using hlen, ?_⟩, rfl⟩
            intro c hc
            exact hall c (List.mem_cons_of_mem b hc)

theorem nodup_map_cons (a : Nat) (ws : List (List Nat)) (h : ws.Nodup) :
    (ws.map (fun w => a :: w)).Nodup := by
  unfold List.Nodup at *
  rw [List.pairwise_map]
  exact h.imp fun hne heq => hne (List.cons_inj_right a |>.mp heq)

theorem nodup_prepAll (as : List Nat) (ws : List (List Nat)) (has : as.Nodup) (hws : ws.Nodup) :
    (prepAll as ws).Nodup := by
  induction as with
  | nil => exact List.nodup_nil
  | cons a as ih =>
      rw [List.nodup_cons] at has
      simp only [prepAll]
      rw [List.nodup_append]
      refine ⟨nodup_map_cons a ws hws, ih has.2, ?_⟩
      intro w hw w' hw' heq
      rw [List.mem_map] at hw
      obtain ⟨v, _, rfl⟩ := hw
      rw [mem_prepAll] at hw'
      obtain ⟨b, hb, u, _, hbu⟩ := hw'
      have : a = b := (List.cons_eq_cons.mp (heq.trans hbu)).1
      exact has.1 (this ▸ hb)

theorem nodup_words (k n : Nat) : (words k n).Nodup := by
  induction n with
  | zero => exact List.nodup_cons.mpr ⟨List.not_mem_nil, List.nodup_nil⟩
  | succ n ih => exact nodup_prepAll _ _ (List.nodup_range) ih


/-! ## Counting: a duplicate-free list partitioned into blocks of size `p` -/

theorem nodup_length_le {β : Type} [DecidableEq β] (l₁ l₂ : List β) (h₁ : l₁.Nodup)
    (hsub : ∀ a ∈ l₁, a ∈ l₂) : l₁.length ≤ l₂.length := by
  induction l₁ generalizing l₂ with
  | nil => exact Nat.zero_le _
  | cons a t ih =>
      rw [List.nodup_cons] at h₁
      have ha : a ∈ l₂ := hsub a List.mem_cons_self
      have hsub' : ∀ b ∈ t, b ∈ l₂.erase a := by
        intro b hb
        have hne : b ≠ a := fun h => h₁.1 (h ▸ hb)
        exact (List.mem_erase_of_ne hne).mpr (hsub b (List.mem_cons_of_mem a hb))
      have hrec := ih (l₂.erase a) h₁.2 hsub'
      rw [List.length_erase_of_mem ha] at hrec
      have hpos : 0 < l₂.length := List.length_pos_of_mem ha
      rw [List.length_cons]
      omega

theorem nodup_length_eq {β : Type} [DecidableEq β] (l₁ l₂ : List β) (h₁ : l₁.Nodup) (h₂ : l₂.Nodup)
    (h : ∀ a, a ∈ l₁ ↔ a ∈ l₂) : l₁.length = l₂.length :=
  Nat.le_antisymm (nodup_length_le l₁ l₂ h₁ fun a ha => (h a).mp ha)
    (nodup_length_le l₂ l₁ h₂ fun a ha => (h a).mpr ha)

theorem length_filter_split {β : Type} (q : β → Bool) (l : List β) :
    l.length = (l.filter q).length + (l.filter fun a => decide (¬ q a = true)).length := by
  rw [← List.countP_eq_length_filter, ← List.countP_eq_length_filter]
  exact List.length_eq_countP_add_countP q

-- theorem-card: orbit partition counting law
-- A duplicate-free list closed under an orbit assignment whose orbits all
-- have exactly `p` members, are reflexive, and coincide along their members,
-- has length divisible by `p`.
theorem THM_NO_005_partition_dvd {β : Type} [DecidableEq β] (orb : β → List β) (p : Nat) (m : Nat) :
    ∀ (L : List β), L.length ≤ m → L.Nodup →
      (∀ x ∈ L, (orb x).Nodup ∧ (orb x).length = p) →
      (∀ x ∈ L, ∀ y ∈ orb x, y ∈ L) →
      (∀ x ∈ L, x ∈ orb x) →
      (∀ x ∈ L, ∀ y ∈ orb x, ∀ z, z ∈ orb y ↔ z ∈ orb x) →
      p ∣ L.length := by
  induction m with
  | zero =>
      intro L hL _ _ _ _ _
      rw [Nat.le_zero.mp hL]
      exact Nat.dvd_zero p
  | succ m ih =>
      intro L hL hnd hsize hclosed hrefl hsame
      cases L with
      | nil => exact Nat.dvd_zero p
      | cons x t =>
          have hx : x ∈ x :: t := List.mem_cons_self
          have hsplit := length_filter_split (fun y => decide (y ∈ orb x)) (x :: t)
          have hfirst : ((x :: t).filter fun y => decide (y ∈ orb x)).length = p := by
            rw [← (hsize x hx).2]
            apply nodup_length_eq _ _ (List.Nodup.sublist List.filter_sublist hnd) (hsize x hx).1
            intro a
            rw [List.mem_filter, decide_eq_true_iff]
            exact ⟨fun h => h.2, fun h => ⟨hclosed x hx a h, h⟩⟩
          have hp : 0 < p := by
            rw [← (hsize x hx).2]
            exact List.length_pos_of_mem (hrefl x hx)
          have hmem : ∀ y, y ∈ ((x :: t).filter fun y => decide (¬ decide (y ∈ orb x) = true)) ↔
              y ∈ x :: t ∧ ¬ y ∈ orb x := by
            intro y
            rw [List.mem_filter, decide_eq_true_iff, decide_eq_true_iff]
          rw [List.length_cons] at hL hsplit
          rw [hfirst] at hsplit
          have hrest := ih ((x :: t).filter fun y => decide (¬ decide (y ∈ orb x) = true))
            (by omega)
            (List.Nodup.sublist List.filter_sublist hnd)
            (fun y hy => hsize y ((hmem y).mp hy).1)
            (by
              intro y hy z hz
              obtain ⟨hyL, hynot⟩ := (hmem y).mp hy
              rw [hmem]
              refine ⟨hclosed y hyL z hz, ?_⟩
              intro hzx
              apply hynot
              -- z lies in both orbits, so the two orbits coincide and y ∈ orb x
              have h₁ := hsame x hx z hzx
              have h₂ := hsame y hyL z hz
              exact (h₁ y).mp ((h₂ y).mpr (hrefl y hyL)))
            (fun y hy => hrefl y ((hmem y).mp hy).1)
            (fun y hy => hsame y ((hmem y).mp hy).1)
          rw [List.length_cons, hsplit]
          exact Nat.dvd_add (Nat.dvd_refl p) hrest

/-! ## Fermat's congruence from the orbit partition -/

/-- Rotation orbit of a word of length `p`, listed rotation by rotation. -/
def orbitList (p : Nat) (w : List Nat) : List (List Nat) := (List.range p).map fun i => rot i w

/-- Boolean constancy test used for filtering. -/
def constB : List Nat → Bool
  | [] => true
  | a :: t => t.all (· == a)

theorem constB_iff (w : List Nat) : constB w = true ↔ IsConst w := by
  cases w with
  | nil =>
      simp only [constB, IsConst, List.not_mem_nil, false_implies, implies_true]
  | cons a t =>
      simp only [constB, List.all_eq_true, beq_iff_eq, IsConst, List.mem_cons]
      constructor
      · intro h x hx y hy
        have hx' : x = a := by
          rcases hx with rfl | hx
          · rfl
          · exact h x hx
        have hy' : y = a := by
          rcases hy with rfl | hy
          · rfl
          · exact h y hy
        rw [hx', hy']
      · intro h x hx
        exact h x (Or.inr hx) a (Or.inl rfl)

theorem nodup_orbitList (p : Nat) (hp : IsPrime p) (w : List Nat) (hlen : w.length = p)
    (hnc : ¬ IsConst w) : (orbitList p w).Nodup := by
  unfold orbitList List.Nodup
  rw [List.pairwise_map]
  apply List.Pairwise.imp_of_mem _ (List.nodup_range)
  intro i j hi hj hne heq
  rw [List.mem_range] at hi hj
  exact hne (THM_NO_004_rotations_distinct p hp w hlen hnc i j hi hj heq)

theorem mem_orbitList (p : Nat) (w z : List Nat) : z ∈ orbitList p w ↔ ∃ i, i < p ∧ z = rot i w := by
  unfold orbitList
  rw [List.mem_map]
  constructor
  · rintro ⟨i, hi, rfl⟩
    exact ⟨i, List.mem_range.mp hi, rfl⟩
  · rintro ⟨i, hi, rfl⟩
    exact ⟨i, List.mem_range.mpr hi, rfl⟩

theorem rot_rot_cancel (p j : Nat) (w : List Nat) (hlen : w.length = p) (hj : j < p) :
    rot (p - j) (rot j w) = w := by
  rw [THM_NO_001_rot_rot, Nat.sub_add_cancel (Nat.le_of_lt hj), ← hlen]
  exact rot_length w

theorem orbitList_same (p : Nat) (hp0 : 0 < p) (w y : List Nat) (hlen : w.length = p)
    (hy : y ∈ orbitList p w) : ∀ z, z ∈ orbitList p y ↔ z ∈ orbitList p w := by
  obtain ⟨j, hj, rfl⟩ := (mem_orbitList p w y).mp hy
  intro z
  rw [mem_orbitList, mem_orbitList]
  constructor
  · rintro ⟨i, _, rfl⟩
    refine ⟨(i + j) % p, Nat.mod_lt _ hp0, ?_⟩
    rw [THM_NO_001_rot_rot, rot_mod (i + j) w, hlen]
  · rintro ⟨i, _, rfl⟩
    refine ⟨(i + (p - j)) % p, Nat.mod_lt _ hp0, ?_⟩
    have hlen' : (rot j w).length = p := by rw [length_rot, hlen]
    have h1 : rot (i + (p - j)) (rot j w) = rot ((i + (p - j)) % p) (rot j w) := by
      rw [rot_mod (i + (p - j)) (rot j w), hlen']
    rw [← h1, THM_NO_001_rot_rot, Nat.add_assoc, Nat.sub_add_cancel (Nat.le_of_lt hj), ← hlen,
      rot_add_length]

theorem replicate_injective (p : Nat) (hp0 : 0 < p) (a b : Nat)
    (h : List.replicate p a = List.replicate p b) : a = b := by
  cases p with
  | zero => exact absurd hp0 (Nat.lt_irrefl 0)
  | succ n =>
      rw [List.replicate_succ, List.replicate_succ] at h
      exact (List.cons_eq_cons.mp h).1

theorem nodup_constants (p : Nat) (hp0 : 0 < p) (k : Nat) :
    ((List.range k).map fun a => List.replicate p a).Nodup := by
  unfold List.Nodup
  rw [List.pairwise_map]
  exact List.Pairwise.imp (fun hne heq => hne (replicate_injective p hp0 _ _ heq)) List.nodup_range

-- theorem-card: Fermat decomposition by orbit counting, all primes, all alphabets
-- `k^p = k + p·q`: the `k` constant words plus `q` full rotation orbits of size `p`.
theorem THM_NO_006_fermat_decomposition (p : Nat) (hp : IsPrime p) (k : Nat) :
    ∃ q, k ^ p = k + p * q := by
  have hp0 : 0 < p := Nat.lt_of_lt_of_le (Nat.zero_lt_succ 1) hp.1
  have hsplit := length_filter_split constB (words k p)
  -- the constant block has exactly k members
  have hconst : ((words k p).filter constB).length = k := by
    have hlen_rep : ((List.range k).map fun a => List.replicate p a).length = k := by
      rw [List.length_map, List.length_range]
    have hmemc : ∀ w, w ∈ (words k p).filter constB ↔
        w ∈ ((List.range k).map fun a => List.replicate p a) := by
      intro w
      rw [List.mem_filter, mem_words, constB_iff, List.mem_map]
      constructor
      · rintro ⟨⟨hlen, hall⟩, hc⟩
        have hne : w ≠ [] := by
          intro h; rw [h, List.length_nil] at hlen; omega
        obtain ⟨a, hmem⟩ : ∃ a, a ∈ w := by
          cases w with
          | nil => exact absurd rfl hne
          | cons a t => exact ⟨a, List.mem_cons_self⟩
        refine ⟨a, List.mem_range.mpr (hall a hmem), ?_⟩
        symm
        exact List.eq_replicate_iff.mpr ⟨hlen, fun b hb => hc b hb a hmem⟩
      · rintro ⟨a, ha, rfl⟩
        rw [List.mem_range] at ha
        refine ⟨⟨List.length_replicate, fun b hb => ?_⟩, fun b hb c hc => ?_⟩
        · rw [(List.mem_replicate.mp hb).2]; exact ha
        · rw [(List.mem_replicate.mp hb).2, (List.mem_replicate.mp hc).2]
    have h := nodup_length_eq ((words k p).filter constB) ((List.range k).map fun a => List.replicate p a)
      (List.Nodup.sublist List.filter_sublist (nodup_words k p)) (nodup_constants p hp0 k) hmemc
    rw [hlen_rep] at h
    exact h
  -- the nonconstant block is a union of full orbits
  have hnonconst : p ∣ ((words k p).filter fun w => decide (¬ constB w = true)).length := by
    have hmem : ∀ w, w ∈ ((words k p).filter fun w => decide (¬ constB w = true)) ↔
        (w.length = p ∧ ∀ a ∈ w, a < k) ∧ ¬ IsConst w := by
      intro w
      rw [List.mem_filter, mem_words, decide_eq_true_iff, constB_iff]
    apply THM_NO_005_partition_dvd (orbitList p) p _ _ (Nat.le_refl _)
      (List.Nodup.sublist List.filter_sublist (nodup_words k p))
    · intro w hw
      obtain ⟨⟨hlen, _⟩, hnc⟩ := (hmem w).mp hw
      refine ⟨nodup_orbitList p hp w hlen hnc, ?_⟩
      unfold orbitList
      rw [List.length_map, List.length_range]
    · intro w hw y hy
      obtain ⟨⟨hlen, hall⟩, hnc⟩ := (hmem w).mp hw
      obtain ⟨i, _, rfl⟩ := (mem_orbitList p w y).mp hy
      rw [hmem]
      refine ⟨⟨by rw [length_rot, hlen], fun a ha => hall a ((mem_rot_iff i w a).mp ha)⟩, ?_⟩
      rw [isConst_rot_iff]
      exact hnc
    · intro w _
      rw [mem_orbitList]
      exact ⟨0, hp0, (rot_zero w).symm⟩
    · intro w hw y hy
      obtain ⟨⟨hlen, _⟩, _⟩ := (hmem w).mp hw
      exact orbitList_same p hp0 w y hlen hy
  obtain ⟨q, hq⟩ := hnonconst
  refine ⟨q, ?_⟩
  rw [← length_words k p, hsplit, hconst, hq]

-- theorem-card: Fermat's little theorem (necklace form), all primes, all bases
theorem THM_NO_007_fermat_dvd (p : Nat) (hp : IsPrime p) (k : Nat) : p ∣ k ^ p - k := by
  obtain ⟨q, hq⟩ := THM_NO_006_fermat_decomposition p hp k
  rw [hq, Nat.add_sub_cancel_left]
  exact Nat.dvd_mul_right p q

-- theorem-card: Fermat's little theorem (congruence form)
theorem THM_NO_008_fermat_mod (p : Nat) (hp : IsPrime p) (k : Nat) : k ^ p % p = k % p := by
  obtain ⟨q, hq⟩ := THM_NO_006_fermat_decomposition p hp k
  rw [hq, Nat.add_mul_mod_self_left]

/-- Bounded primality check: enough to discharge concrete instances by `decide`. -/
theorem isPrime_of_bounded (p : Nat) (h2 : 2 ≤ p) (h : ∀ d, d < p → d ∣ p → d = 1) : IsPrime p := by
  refine ⟨h2, fun d hd => ?_⟩
  rcases Nat.lt_or_ge d p with hlt | hge
  · exact Or.inl (h d hlt hd)
  · exact Or.inr (Nat.le_antisymm (Nat.le_of_dvd (Nat.lt_of_lt_of_le (Nat.zero_lt_succ 1) h2) hd) hge)

-- theorem-card: divisibility content of the N8 Fermat-count cards recovered from the
-- general theorem (p = 3, 5 with k = 2, as in THM_N8_004/005) plus p = 7 with k = 2, 3;
-- the dichotomy cards follow from THM_NO_003/004, while the Gauss n = 4 card and the
-- composite counterexample are not covered here.
theorem THM_NO_009_n8_instances :
    3 ∣ 2 ^ 3 - 2 ∧ 5 ∣ 2 ^ 5 - 2 ∧ 7 ∣ 2 ^ 7 - 2 ∧ 7 ∣ 3 ^ 7 - 3 :=
  ⟨THM_NO_007_fermat_dvd 3 (isPrime_of_bounded 3 (by decide) (by decide)) 2,
   THM_NO_007_fermat_dvd 5 (isPrime_of_bounded 5 (by decide) (by decide)) 2,
   THM_NO_007_fermat_dvd 7 (isPrime_of_bounded 7 (by decide) (by decide)) 2,
   THM_NO_007_fermat_dvd 7 (isPrime_of_bounded 7 (by decide) (by decide)) 3⟩

#check THM_NO_008_fermat_mod


/-! ## Aperiodic words and the Gauss divisibility at every length -/

/-- A word is aperiodic when no shift strictly between `0` and its length fixes it. -/
def Aperiodic (l : List α) : Prop := ∀ d, 0 < d → d < l.length → rot d l ≠ l

theorem rot_eq_rot_imp_fix {l : List α} {n i j : Nat} (hlen : l.length = n) (hij : i < j) (hj : j < n)
    (h : rot i l = rot j l) : rot (j - i) l = l := by
  have h1 : rot (n - i) (rot i l) = l := by
    rw [THM_NO_001_rot_rot, Nat.sub_add_cancel (Nat.le_of_lt (Nat.lt_trans hij hj)), ← hlen]
    exact rot_length l
  have h2 : rot (n - i) (rot j l) = rot (j - i) l := by
    rw [THM_NO_001_rot_rot]
    have harith : n - i + j = (j - i) + n := by omega
    rw [harith, ← hlen, rot_add_length]
  rw [h, h2] at h1
  exact h1

theorem aperiodic_rot {l : List α} (ha : Aperiodic l) (d : Nat) : Aperiodic (rot d l) := by
  intro e he hen hfix
  rw [length_rot] at hen
  -- rot e (rot d l) = rot d l ⇒ rot e l = l via the inverse rotation
  have hcancel : rot (l.length - d % l.length) (rot d l) = l := rot_rot_sub d l
  have h1 : rot (l.length - d % l.length) (rot e (rot d l)) = rot e l := by
    rw [THM_NO_001_rot_rot, Nat.add_comm, ← THM_NO_001_rot_rot, hcancel]
  rw [hfix, hcancel] at h1
  exact ha e he hen h1.symm

theorem rotations_distinct_of_aperiodic {l : List α} {n : Nat} (hlen : l.length = n) (ha : Aperiodic l)
    (i j : Nat) (hi : i < n) (hj : j < n) (h : rot i l = rot j l) : i = j := by
  rcases Nat.lt_trichotomy i j with hlt | heq | hgt
  · exact absurd (rot_eq_rot_imp_fix hlen hlt hj h) (ha (j - i) (by omega) (by omega))
  · exact heq
  · exact absurd (rot_eq_rot_imp_fix hlen hgt hi h.symm) (ha (i - j) (by omega) (by omega))

/-- Boolean aperiodicity test used for filtering. -/
def aperiodicB (w : List Nat) : Bool :=
  (List.range w.length).all fun d => decide (d = 0) || decide (rot d w ≠ w)

theorem aperiodicB_iff (w : List Nat) : aperiodicB w = true ↔ Aperiodic w := by
  unfold aperiodicB Aperiodic
  rw [List.all_eq_true]
  constructor
  · intro h d hd hdn
    have := h d (List.mem_range.mpr hdn)
    rw [Bool.or_eq_true, decide_eq_true_iff, decide_eq_true_iff] at this
    rcases this with h0 | hne
    · omega
    · exact hne
  · intro h d hd
    rw [List.mem_range] at hd
    rw [Bool.or_eq_true, decide_eq_true_iff, decide_eq_true_iff]
    by_cases h0 : d = 0
    · exact Or.inl h0
    · exact Or.inr (h d (Nat.pos_of_ne_zero h0) hd)

theorem nodup_orbitList_of_aperiodic (n : Nat) (w : List Nat) (hlen : w.length = n) (ha : Aperiodic w) :
    (orbitList n w).Nodup := by
  unfold orbitList List.Nodup
  rw [List.pairwise_map]
  apply List.Pairwise.imp_of_mem _ (List.nodup_range)
  intro i j hi hj hne heq
  rw [List.mem_range] at hi hj
  exact hne (rotations_distinct_of_aperiodic hlen ha i j hi hj heq)

-- theorem-card: Gauss divisibility — the aperiodic words of every positive length n
-- over every alphabet split into full rotation orbits of size n, so n divides their number.
theorem THM_NO_010_gauss_aperiodic_dvd (k n : Nat) (hn : 0 < n) :
    n ∣ ((words k n).filter aperiodicB).length := by
  have hmem : ∀ w, w ∈ (words k n).filter aperiodicB ↔ (w.length = n ∧ ∀ a ∈ w, a < k) ∧ Aperiodic w := by
    intro w
    rw [List.mem_filter, mem_words, aperiodicB_iff]
  apply THM_NO_005_partition_dvd (orbitList n) n _ _ (Nat.le_refl _)
    (List.Nodup.sublist List.filter_sublist (nodup_words k n))
  · intro w hw
    obtain ⟨⟨hlen, _⟩, ha⟩ := (hmem w).mp hw
    refine ⟨nodup_orbitList_of_aperiodic n w hlen ha, ?_⟩
    unfold orbitList
    rw [List.length_map, List.length_range]
  · intro w hw y hy
    obtain ⟨⟨hlen, hall⟩, ha⟩ := (hmem w).mp hw
    obtain ⟨i, _, rfl⟩ := (mem_orbitList n w y).mp hy
    rw [hmem]
    exact ⟨⟨by rw [length_rot, hlen], fun a haa => hall a ((mem_rot_iff i w a).mp haa)⟩, aperiodic_rot ha i⟩
  · intro w _
    rw [mem_orbitList]
    exact ⟨0, hn, (rot_zero w).symm⟩
  · intro w hw y hy
    obtain ⟨⟨hlen, _⟩, _⟩ := (hmem w).mp hw
    exact orbitList_same n hn w y hlen hy

/-! ## Aperiodic = primitive: the bridge to the primitive-root theory -/

theorem getD_pow (z : List α) (k i : Nat) (hi : i < (Root.pow z k).length) :
    (Root.pow z k).getD i default = z.getD (i % z.length) default := by
  induction k generalizing i with
  | zero =>
      rw [Root.pow_zero_eq, List.length_nil] at hi
      exact absurd hi (Nat.not_lt_zero i)
  | succ k ih =>
      rw [Root.pow_succ] at hi ⊢
      rw [List.getD_eq_getElem?_getD]
      by_cases hlt : i < z.length
      · rw [List.getElem?_append_left hlt, ← List.getD_eq_getElem?_getD, Nat.mod_eq_of_lt hlt]
      · have hge : z.length ≤ i := Nat.le_of_not_lt hlt
        rw [List.getElem?_append_right hge, ← List.getD_eq_getElem?_getD]
        rw [List.length_append] at hi
        have hi' : i - z.length < (Root.pow z k).length := by omega
        rw [ih (i - z.length) hi', Nat.mod_eq_sub_mod hge]

/-- A positive power reads cyclically exactly like its root. -/
theorem read_pow (z : List α) (k t : Nat) (hz : 0 < z.length) (hk : 0 < k) :
    read (Root.pow z k) t = read z t := by
  unfold read
  have hlen : (Root.pow z k).length = k * z.length := Root.length_pow z k
  have hpos : 0 < (Root.pow z k).length := by rw [hlen]; exact Nat.mul_pos hk hz
  have hlt : t % (Root.pow z k).length < (Root.pow z k).length := Nat.mod_lt _ hpos
  rw [getD_pow z k _ hlt, hlen, Nat.mod_mod_of_dvd t (Nat.dvd_mul_left z.length k)]

/-- A positive power is fixed by the shift of its root length. -/
theorem rot_root_length_pow (z : List α) (k : Nat) (hz : 0 < z.length) (hk : 0 < k) :
    rot z.length (Root.pow z k) = Root.pow z k := by
  apply ext_read
  · exact length_rot _ _
  · intro t _
    rw [read_rot, read_pow z k _ hz hk, read_pow z k t hz hk, read_add_length]

theorem read_mod_of_fix {l : List α} {g : Nat} (hg : Fix l g) (t : Nat) : read l t = read l (t % g) := by
  have hsplit : t % g + g * (t / g) = t := Nat.mod_add_div t g
  have hfix : Fix l (g * (t / g)) := fix_mul hg (t / g)
  unfold Fix at hfix
  have key : read l (t % g + g * (t / g)) = read l (t % g) := by
    rw [← read_rot, hfix]
  rw [hsplit] at key
  exact key

/-- A word fixed by a positive shift `g` dividing its length is the `length/g`-th power
    of its first `g` letters. -/
theorem pow_take_of_fix {l : List α} {g : Nat} (hlen : 0 < l.length) (hg0 : 0 < g)
    (hdvd : g ∣ l.length) (hfix : Fix l g) :
    l = Root.pow (l.take g) (l.length / g) := by
  have hgle : g ≤ l.length := Nat.le_of_dvd hlen hdvd
  have htake : (l.take g).length = g := by
    rw [List.length_take, Nat.min_eq_left hgle]
  have hq : 0 < l.length / g := Nat.div_pos hgle hg0
  have hz' : 0 < (l.take g).length := by rw [htake]; exact hg0
  apply ext_read
  · rw [Root.length_pow, htake, Nat.div_mul_cancel hdvd]
  · intro t _
    rw [read_pow _ _ _ hz' hq, read_mod_of_fix hfix t]
    unfold read
    rw [htake]
    have hmod : t % g < g := Nat.mod_lt t hg0
    have hmod' : t % g < l.length := Nat.lt_of_lt_of_le hmod hgle
    have hmod_take : t % g < (l.take g).length := by rw [htake]; exact hmod
    rw [Nat.mod_eq_of_lt hmod', List.getD_eq_getElem?_getD, List.getD_eq_getElem?_getD,
      List.getElem?_eq_getElem hmod', List.getElem?_eq_getElem hmod_take, List.getElem_take]

theorem aperiodic_of_primitive {w : List α} (hw : Root.Primitive w) : Aperiodic w := by
  intro d hd hdn hfix
  have hn : 0 < w.length := Nat.lt_trans hd hdn
  have hfull : Fix w w.length := by unfold Fix; exact rot_length w
  have hg : Fix w (Nat.gcd d w.length) := THM_NO_002_fix_gcd w d w.length hfix hfull
  have hg0 : 0 < Nat.gcd d w.length := Nat.gcd_pos_of_pos_left _ hd
  have hgdvd : Nat.gcd d w.length ∣ w.length := Nat.gcd_dvd_right _ _
  have hglt : Nat.gcd d w.length < w.length := Nat.lt_of_le_of_lt (Nat.gcd_le_left _ hd) hdn
  have hpow := pow_take_of_fix hn hg0 hgdvd hg
  have hone := hw.2 _ _ hpow
  have hcancel := Nat.div_mul_cancel hgdvd
  rw [hone, Nat.one_mul] at hcancel
  omega

theorem primitive_of_aperiodic {w : List α} (hne : w ≠ []) (ha : Aperiodic w) : Root.Primitive w := by
  refine ⟨hne, fun z i hzi => ?_⟩
  cases i with
  | zero => exact absurd hzi hne
  | succ i' =>
      cases i' with
      | zero => rfl
      | succ i'' =>
          exfalso
          have hz : 0 < z.length := by
            cases z with
            | nil => rw [Root.pow_nil] at hzi; exact absurd hzi hne
            | cons a t => exact Nat.succ_pos _
          have hlen : w.length = (i'' + 2) * z.length := by rw [hzi, Root.length_pow]
          have hzlt : z.length < w.length := by
            rw [hlen]
            have : 1 * z.length < (i'' + 2) * z.length := Nat.mul_lt_mul_of_pos_right (by omega) hz
            omega
          have hfix : rot z.length w = w := by
            rw [hzi]
            exact rot_root_length_pow z _ hz (Nat.succ_pos _)
          exact ha z.length hz hzlt hfix

-- theorem-card: aperiodic (no proper cyclic period) coincides with primitive (no proper power)
theorem THM_NO_011_aperiodic_iff_primitive (w : List α) (hne : w ≠ []) :
    Aperiodic w ↔ Root.Primitive w :=
  ⟨primitive_of_aperiodic hne, aperiodic_of_primitive⟩

#check THM_NO_011_aperiodic_iff_primitive

end Necklace
end Veyra
