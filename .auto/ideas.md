# Ideas backlog — Veyra open-problem proof campaign

## DONE: Fermat's little theorem (the crown jewel) — VeyraResearchBinomSum.lean
- PROVEN: RESEARCH_BS_T003_fermat (Prime p -> a^p % p = a % p for all a),
  via the binomial sum identity RESEARCH_BS_T001_binomial_sum and the
  freshmen's dream RESEARCH_BS_T002_freshman_dream.
- The key trick that unblocked the list-index shifts: the running invariant
  H(m) := foldl(h(j+1), 0, range m) + h(m+1) = h 1 + foldl(h(j+2), 0, range m)
  holds for ALL m with NO zero hypotheses (pure induction + ac_rfl); the
  h(n+1) = 0 hypothesis enters only at the final step m = n.
- Proven so far (VeyraResearchFermat.lean): RESEARCH_F_T001_choose_factor
  (k*C(p,k)=p*C(p-1,k-1) for all 1<=k<=p) and RESEARCH_F_T002_middle_choose_divisible
  (Prime p -> p | C(p,k) for 0<k<p) — via Euclid's lemma.
- Remaining design (worked out, needs careful list induction):
  1. def binomSum n x := List.foldl (fun s k => s + choose n k * x ^ k) 0 (List.range (n+1))
  2. shift lemma for FIXED n: foldl (fun s j => s + h (j+1)) 0 (range n) = h 1 + foldl (fun s j => s + h (j+2)) 0 (range n)
     with h (n+1) = 0 (choose_above) — prove by induction on n with range (n+1) = 0 :: map (+1) (range n).
     CAREFUL: both sides must use the SAME range; the h(1) extraction makes the tails line up:
     B = h1 + tail, A = tail (+ h(n+1)=0). This is the ONLY missing ingredient.
  3. hsecond: 1 + foldl g 0 (range (n+1)) = binomSum n x  (g j = C(n,j+1) x^(j+1))
  4. T001: (x+1)^n = binomSum n x by induction on n using range_succ + foldl_append + foldl_add + foldl_mul + Pascal (rfl).
  5. T002 freshman: (a+1)^p % p = (a^p + 1) % p via foldl_dvd (p | every middle term) + range p = range (p-1) ++ [p-1] + Nat.add_mul_mod_self_left.
  6. Fermat: by induction on a: a^p % p = a % p.
- Known rw traps (all hit this session): rw with variable-pattern hypotheses rewrites subterms of p-1 (use forward direction/conv); unfold of recursive defs leaves stuck matches (prove Pascal via have+rw, never unfold in the main goal); calc steps carry tactic-rewritten terms into the next step (prove tail steps via dedicated have-lemmas with exact).

## Deferred targets (lower priority)
- Wilson's theorem ((p-1)! ≡ -1 mod p) — needs pairing of inverses mod p via Bezout; large.
- PΩ2 field direction: multiplicative inverse for unit first-digit families (Zp units) — real generalization of THM_POMEGA2_016.
- THM-001/002/003 promotion ceremony (registry entries) — governance, not math.
- General geometry cards (SSS/SAS for arbitrary coordinates) — Int arithmetic grind.
