# Literature Positioning of the Break-Locus Lane — TR-2/5

**Date:** 2026-08-27
**Status:** due-diligence record. It **downgrades** part of the lane's
implicit standing and corrects an attribution error. Method: web search
(arXiv, RAIRO/NumDam, DBLP, Springer) plus Scholar; two papers read in
full text, the rest at abstract/snippet/citation-chain level. zbMATH and
MathSciNet were **not** accessible; the 1980s–90s French trace-theory
corpus is thinly indexed. Absence below therefore means *not found in
searched sources*, never *does not exist*.

## Correction of attribution (was wrong in docs 183 and the registry)

The pairwise-projection characterization of trace equivalence is **not**
Cori–Perrin. The citation trail (verified inside Lohrey–Stober–Weiß 2024,
Lemma 2 and §2.4.2) is:

- **C. Duboc, "Some properties of commutation in free partially
  commutative monoids," *IPL* 20(1):1–4, 1985** — dependent *pairs*
  (not just maximal cliques) suffice;
- **C. Duboc, "On some equations in free partially commutative monoids,"
  *TCS* 46:159–174, 1986, Prop. 1.2** — the projection lemma;
- **C. Wrathall, "The word problem for free partially commutative
  groups," *JSC* 6(1):99–104, 1988** — independent statement.

Cori–Perrin 1985 (*RAIRO Inform. Théor.* 19(1):21–32) is real,
contemporaneous background, but its authorship of this particular lemma
was **not** confirmed. Docs 183 and the active registry are corrected in
place with a visible note.

## Layer-by-layer verdict

| Layer | Verdict |
|---|---|
| **L1** — fixed-relation characterization: `w` is a proper trace power ⟺ every dependent-pair projection is a literal k-th power for a common k | **KNOWN.** This is **Duboc 1986, Proposition 1.7**, quoted verbatim in current literature. Our `firstSlice` root construction was not found spelled out, but is very likely an easy corollary of the same machinery. **Not a new result.** |
| **Up-closedness** of the breaking region (`THM_TR1_001`/`003`) | **FOLKLORE.** For `I ⊆ J` there is a canonical surjective morphism `M(Σ,I) → M(Σ,J)`; morphisms preserve powers. One line from standard facts. Our Lean proof remains a valid *formalization*, not a discovery. |
| **L2** — the lattice-parametric objects: `B(w)`, prime floors, the closed formula, tightness, the singleton criterion | **NOT FOUND.** Extensive multi-vocabulary search (see the report in the module log) returned nothing studying primitivity of a fixed word *as a function of a varying independence relation*. Closest structural precedent: Earnshaw–Sobociński, "String Diagrammatic Trace Theory," arXiv:2306.16341 (2023), which does treat the poset `Ind_Σ` as a first-class object — for a category-theoretic purpose, unrelated to powers. |
| **L3a** — partial words ≠ traces | **CONFIRMED distinct fields** (Cartier–Foata 1969 vs Berstel–Boasson 1999). Must be stated explicitly in any write-up. |
| **L3b** — Fine–Wilf for traces | **ACTIVE, RECENT.** Lohrey–Stober–Weiß (arXiv:2201.06543; DLT 2022; *ToCS* 2024) prove a Fine–Wilf-style theorem for connected primitive traces as machinery for the power word problem; Halava–Harju–Kärki, *RAIRO-ITA* 43(2):209–220 (2009) is adjacent. Any future TR work here must position against both — **not virgin territory**. |
| **L3c** — realizability from prescribed pairwise projections | **NOT FOUND.** Uniqueness (injectivity of Π) is classical; a characterization of *which* projection tuples are jointly realizable was not found. This is exactly the lane's open question (docs 184/186). |

## Effect on this lane's claims

1. The Lean cores `THM_TR2_002`–`007` formalize **classical** facts. They
   keep their `FORMALLY_PROVED` rung as artifacts; they carry **no**
   novelty claim.
2. `THM-TR2-008` (Break-Locus Formula), `THM-TR2-009` (Tightness), the
   refutation witness, and the singleton criterion remain the lane's
   candidate contributions — **built on Duboc's classical theorem**, which
   must be cited as the engine wherever the formula is stated.
3. Before any external submission, three checks remain mandatory:
   zbMATH/MathSciNet searches; full text of Choffrut ("Combinatorics in
   Trace Monoids I") and Duchamp–Krob (ibid. II) in *The Book of Traces*
   (1995), whose sections on primitivity, conjugacy and Lyndon traces are
   the likeliest place for a pre-existing `B(w)`-style statement; and a
   forward citation search on the 2022–2024 Lohrey–Stober–Weiß line.
4. Applied spin-offs discussed for cryptanalysis inherit this: "power and
   root detection in trace monoids is easy, so it cannot found a hardness
   assumption" is itself a consequence of Duboc — **folklore, not our
   contribution**.

## Non-claims

1. No novelty is claimed for any layer marked KNOWN or FOLKLORE.
2. NOT FOUND is a statement about our searched sources under our
   vocabulary, not about the literature as a whole; the mandatory checks
   above are unperformed.
3. This document changes no evidence rung of any Lean declaration or
   certificate; it changes only what may be *said* about them.
