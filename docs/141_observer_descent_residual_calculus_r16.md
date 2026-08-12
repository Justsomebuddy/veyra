# R16 — Observer-Descent Residual Calculus
**Status:** finite partial kernel + checked conditional Lean partition; reduced research candidate
**Date:** 2026-08-04
**Contract clarified:** 2026-08-11
**Primary API:** `src.core.observer_descent`

## Purpose

Ordinary calculus asks how a chosen coordinate changes. VODC asks a prior
question:

> Which admitted observer is the strongest one through which a transformation
> can be seen, and exactly which distinctions are lost by that descent?

The construction begins with Veyra's observer-indexed distinctions rather than
primitive points, subtraction, distance, or infinitesimals. Classical sets and
finite response tables are the current executable shadow model, not the
claimed ontology.

## Finite doctrine and partial descent

Let \(X\) be a finite carrier and \(O_X\) a finite family of total observers
\(p:X\to R_p\). Define the ordered distinction relation

\[
\Delta(p)=\{(x,x')\in X^2:x\ne x'\ \land\ p(x)\ne p(x')\}.
\]

Observer refinement is extensional:

\[
p\preceq p' \iff \Delta(p)\subseteq\Delta(p').
\]

`DEF-414` requires distinct extensional observers, a silence/bottom observer,
and a unique admitted join for every pair. Thus \(O_X\) is a finite
join-semilattice of available ways to distinguish.

The first implementation deliberately accepts only bounded exact slotted
DTOs, tuple tables, and canonical scalar/tuple payloads. Dynamic callables,
subclassed DTOs, hostile hash/equality payloads, Boolean-as-integer costs,
missing slots, oversized carriers, and non-join doctrines fail closed.

The executable doctrinal boundary mirrors the typing premise explicitly:

```python
observer_descent(O_X, F, q, target_doctrine=O_Y)
```

`O_X` and `O_Y` are both validated, `F.target` must exactly equal the ordered
carrier of `O_Y`, and `(name, responses, cost)` for `q` must exactly match one
admitted member. A detached DTO with the same canonical value is accepted;
Python object identity, name-only matching, extensional equivalence, and
carrier-totality alone are not admission evidence. Omitting `target_doctrine`
fails closed. `residual_chain_balance` and the per-row
`descent_reduces_to_best_lower` checker require the same keyword-only target
binding; the fixed `z4_reduction_audit()` aggregate supplies its canonical
doctrine internally. This is call-time validation, not a serialized or
authenticated membership receipt and not a P1-to-R16 realization bridge.

## Pullback, descent, and residual

For \(F:X\to Y\) and target observer \(q\in O_Y\), the raw pullback is

\[
F^\sharp q=q\circ F.
\]

The lower-level `pullback_observer(F, q)` deliberately accepts any exact-total
response table on `Y`; it establishes only the ambient pullback and never the
premise `q in O_Y`. The public descent operation performs that separate
admission check before using a detached validated value.

It need not belong to the admitted observer language \(O_X\). The
**observer descent** is its greatest admitted approximation:

\[
\boxed{
D_F(q)=\bigvee\{p\in O_X:\Delta(p)\subseteq\Delta(F^\sharp q)\}.
}
\]

The **descent residual** is not numeric subtraction. It is the typed relation
of exact pullback distinctions not expressible by the source doctrine:

\[
\boxed{
R_F(q)=\Delta(F^\sharp q)\setminus\Delta(D_Fq).
}
\]

Internal join closure alone does **not** imply that the join of candidates
remains below an arbitrary pullback admitted by a different target doctrine.
A five-state source diamond `{bottom,a,b,top}` can omit a target-admitted
partition `j`: both `a` and `b` lie below `j`, while source-admitted `top`
overshoots it, leaving two maximal candidates. The implementation correctly
raises `descent-not-unique` even though `j in O_Y` is validated.

Consequently \(D_F(q)\) is partial under the current doctrine contract. It is
unique exactly when the candidate set has a greatest element. Totality needs
an additional right-adjoint/ambient-join-closure hypothesis. The earlier
finite+bottom+internal-join totality argument is withdrawn; `PROP-R16-001` is
retained only as a conditional statement under that stronger hypothesis.

## Composition and synergy

For \(X\xrightarrow{F}Y\xrightarrow{G}Z\), with exact doctrines `O_X`, `O_Y`,
and `O_Z` and target `q in O_Z`, staged descent can be weaker than direct
descent. The chain API validates `q` against `O_Z`; its first staged descent
uses the exact member selected from `O_Y`. Define:

\[
\boxed{
S_{F,G}(q)=
\Delta(D_{G\circ F}q)\setminus\Delta(D_FD_Gq).
}
\]

This **direct-versus-staged precision gap** (the code retains the historical
field name `synergy`) records distinctions recoverable from the composite
transformation but absent after the intermediate observer language has
already discarded them.

Write

\[
\begin{aligned}
A&=\Delta((G\circ F)^\sharp q),\\
B&=F^{[2]*}\Delta(D_Gq),\\
C&=\Delta(D_FD_Gq),\\
D&=\Delta(D_{G\circ F}q).
\end{aligned}
\]

The doctrine laws give

\[
C\subseteq D\subseteq A,\qquad C\subseteq B\subseteq A.
\]

Moreover:

\[
F^{[2]*}R_G(q)=A\setminus B,\quad
R_F(D_Gq)=B\setminus C.
\]

Therefore both sides below are disjoint decompositions of \(A\setminus C\):

\[
\boxed{
F^{[2]*}R_G(q)\sqcup R_F(D_Gq)
=
R_{G\circ F}(q)\sqcup S_{F,G}(q).
}
\tag{THM-R16-001}
\]

For finite carriers, cardinalities give:

\[
|F^{[2]*}R_G(q)|+|R_F(D_Gq)|
=|R_{G\circ F}(q)|+|S_{F,G}(q)|.
\tag{THM-R16-002}
\]

When \(S_{F,G}(q)=\varnothing\), direct and staged admitted distinction
relations coincide, yielding the exact residual chain rule
`THM-R16-003`.

`proofs/lean/VeyraObserverDescent.lean` checks the abstract predicate
partition, disjointness, and zero-synergy law with pinned Lean
`4.30.0-rc2`. It does **not** formalize Python DTO validation, finite
semilattice construction, or a proof-carrying R8 promotion bridge.

## Canonical \(Z/4\) witness

The carrier is \(X=\{0,1,2,3\}\) with observers:

| Observer | Response | Distinctions |
|---|---|---:|
| silence | \(0\) | 0 |
| parity | \(x\bmod 2\) | 8 ordered pairs |
| threshold | \([x\ge2]\) | 8 ordered pairs |
| phase-pair | \((x\bmod2,[x\ge2])\) | 12 ordered pairs |

These form a diamond: silence is bottom and phase-pair is the join of the
incomparable parity and threshold observers.

For successor \(F(x)=x+1\bmod4\):

- parity descends to parity with residual \(0\);
- threshold's pulled response is `0,1,1,0`, so its greatest admitted descent
  is silence and its residual has eight ordered pairs;
- two successors recover threshold exactly at the composite level;
- staged descent remains silence, producing synergy \(8\) and composite
  residual \(0\).

The certificate exhausts all \(4\times4\times4=64\) pairs of cyclic shifts and
target observers, plus 16 one-map descents. It also accepts a detached exact
member and rejects four non-admitted name/cost/order/response variants. This is
a bounded model check, not the proof of the general theorem.

## Claim boundary

Established:

- exact finite doctrine validation;
- exact call-time target-doctrine/carrier/value admission;
- deterministic pullback plus fail-closed partial descent/residual computation;
- exact five-state counterexample to unconditional descent totality;
- conditional existence/uniqueness when the best admitted lower element exists;
- checked abstract residual partition in Lean;
- 64/64 canonical shift-chain balances;
- explicit nonzero synergy.

Not established:

- partial/blocked-response composition;
- infinite or topological doctrine completion;
- measure/probability/operator-valued residuals;
- any novelty beyond the established best-lower-approximation/interior pattern;
- computational advantage;
- historical novelty or revolutionary status;
- R8 theorem-derived layer promotion.
- a self-contained authenticated target-membership or realization receipt. The
  separate [P1→R16 contract](161_p1_r16_realization_contract.md) supplies one
  bounded context-relative replay witness, not a canonical map or signature.

The finite `Z/4` rows reduce exactly to best admitted lower approximation;
residual is ordinary precision loss and the composition field is an abstraction
completeness gap. R16.6 therefore rejects novelty promotion. See
[the literature reduction](146_r16_literature_reduction.md).

## Cross-links

- Derived path invariant: [doc 142](142_crest_braid_derived_path_invariant_r16.md)
- Observer synthesis v2: [doc 140](140_observer_synthesis_v2_r14.md)
- Native observer core: [doc 127](127_native_observer_echo_core_r11.md)
- Relative P1 realization: [doc 161](161_p1_r16_realization_contract.md)
- Definitions and theorems: [`../THEOREMS.md`](../THEOREMS.md)
- Notation: [`../NOTATION.md`](../NOTATION.md)
- API: [`reference/api.md`](reference/api.md)
