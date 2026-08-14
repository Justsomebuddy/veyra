# R10 — Proof-grade Core elaboration

**Date:** 2026-07-14
**Status:** implemented narrow vertical proof slice.
**Certificate:** `proof_elaboration_r10`.
**Boundary:** closed recurrence proof surface only.

## Result

R10 connects one exact, versioned source language to the R7 proof calculus and
the R9 fixed-anchor intrinsic image:

```text
veyra.proof-surface.v1 source
  → captured S-expression / typed surface AST
  → capture-safe de Bruijn R7 proposition and proof
  → independent R7 inference and connected proof artifact
  → structurally computed dependency support
  → generic Lean image semantics over the R9 intrinsic image
```

This is the first source-replayed proof-grade elaboration path. It is **not** a
formal parser in Lean, not a bridge for the general Core Language v0.8 program
syntax, and not a theorem about arbitrary strict or external word modes.

## Exact surface language

A program has one closed claim and one explicit proof:

```text
(veyra-proof 1
  (claim PROP)
  (proof PROOF))
```

The term fragment is `var`, `silence`, `pulse`, `stitch`, and `weave`.
Propositions are `equal`, `implies`, `forall`, and `resonates`. Proof syntax has
one constructor for every R7 rule: assumption, implication introduction and
elimination, universal introduction and elimination, equality
reflexivity/symmetry/transitivity, native law, and resonance introduction. The
five R7 native laws are accepted with exact arities.

Unsupported `iff`, status propositions, foreign types, unknown laws, wrong
arities, non-ASCII input, invalid spans, and inputs exceeding byte, token, AST,
depth, identifier, or binder budgets fail closed with source-spanned errors.

## Capture-safe elaboration

Named term and assumption binders are resolved to de Bruijn indices. Duplicate,
unbound, or term/assumption-crossing binder names are rejected rather than
silently captured. A caller cannot inject an AST or source digest: the public
path captures source bytes, reparses them, validates every typed-node span and
one total node budget, lowers the exact captured AST, and asks the independent
R7 kernel to infer the conclusion.

Acceptance requires the inferred conclusion to equal the declared claim. The
canonical R10 source reproduces the existing `THM-R7-004` proof without theorem
name dispatch. Whitespace changes the source binding but not canonical syntax or
semantics; alpha-renaming may change the surface syntax digest while preserving
the de Bruijn proof semantics.

## Composite artifact

`ProofElaborationArtifact` binds, under one canonical digest:

- exact source size and domain-separated source digest;
- canonical typed surface AST and surface-syntax digest;
- inferred R7 statement, semantic proof digest, connected R7 artifact, rule
  closure, and native-law closure;
- structurally computed dependency support;
- exact R9 schema, theorem IDs, source digests, binding, and pinned toolchain;
- the closed-recurrence/fixed-image non-claim boundary.

Verification rebuilds all representations from origins, reparses the source,
replays R7 inference, revalidates the embedded canonical graph, and rechecks R9.
A changed source, AST, claim, proof, R7 graph, support, R9 report, or binding is
rejected.

## Structural dependency support

Dependencies are derived by traversing the actual R7 term, proposition, proof,
and native-law constructors. Stable IDs are partitioned into six roles:

| Category | Meaning |
|---|---|
| formation | recurrence and proposition formation used by the syntax |
| definition | silence/pulse/stitch/weave and proposition constructors used |
| logical | proof rules that occur in the proof tree |
| domain | exact native laws that occur |
| observer | R9 intrinsic-image observer needed for composition |
| obstruction | explicit foreign-mode obstruction dependencies, when used |

Python and Lean compute matching support for the canonical proof. This is exact
**structurally used support**, not a proof that the set is semantically minimal.
It does not retroactively derive every legacy `RULE_AXIOMS` or every layer's
manually documented dependencies.

## Lean theorem chain

`VeyraElaborationSemantics.lean` defines image semantics for every R7 formula,
not merely for the canonical theorem. `VeyraProofElaboration.lean` is generated
from the exact source-replayed artifact.

| ID | Checked statement |
|---|---|
| `THM-R10-001` | R7 recurrence semantics are equivalent to R9 intrinsic-image semantics for every supported formula and environment |
| `THM-R10-002` | any accepted R7 proof with a satisfied context is sound in those image semantics |
| `THM-R10-003` | the exact source-elaborated canonical proof is accepted by the R7 checker |
| `THM-R10-004` | that exact elaborated statement holds in the intrinsic image |
| `THM-R10-005` | Lean-computed structural support matches the generated support bitset |

The generality is semantic after elaboration: Lean does not parse or prove the
Python parser, name resolver, or source hashing. They remain reviewed Python
TCB components.

## Trust and promotion contract

The fail-closed R10 bridge binds 37 reviewed Python/R7/R9/Lean sources and
compiles a content-addressed immutable ten-stage Lean snapshot. The first nine
stages emit exact reviewed filename/size/SHA `.olean` records into fresh
per-run, per-stage directories; `LEAN_PATH` contains only prior reviewed stage
directories, and the final stage emits no trusted object. Snapshot and prior
object directories have exact shapes, while 25 reviewed-absent paths block
project-module and dynamic-loader/hwcaps shadows inside the same-UID toolchain.

Union tracing of `--version` and all ten stages found 2,365 Lean userspace
regular inputs, all of which are Merkle-bound: 522,231,408 bytes, digest
`990d68ab...2f761a`. The runtime closure alone installs 2,365 file-inode watches
plus 94 direct-parent/ancestor-to-`/` directory watches (2,459 targets; 87 are
direct runtime-file parents); each stage adds snapshot and prior-object watches.
Before every subprocess the guard watches first, checks exact shape/absence,
and performs pre/post closure hashes. Modify/restore, hardlink writes, path
remaps, resolver injection, loader shadows, overflow, unmount, or ignored-watch
events block. It also requires content-bound Lean `v4.30.0-rc2`, warnings as
errors, exact generated export bytes, placeholder rejection, live-source cache
keys, independent report/snapshot rehash, and fresh Lean replay.

Frozen evidence:

```text
snapshot = bde6b2d5da19b35bdc7a5c224345e0f1666386bff8f3249df28c08dce5954bf7
binding  = 291aed1ee8eb913b42c6d77be8701ee10c6429f625a5cd9dec53aab3e4317664
```

The sole production promotion contract still promotes only R7
`THM-R7-004` for `intrinsic-resonance`. Its semantic carrier is unchanged:

```text
semantic carrier = veyra.proof.recurrence-equiv-strict-intrinsic-mode.v1
formal bridge    = veyra.lean.r10.proof-elaboration-tcb.v1
```

Thus R10 renews the required bridge evidence; it adds neither a layer nor a
second theorem-derived nucleus.

## Legacy theorem lane containment

`theorem_language.py` remains a finite-environment obligation/status harness.
R10 hardens exact `$identifier` substitution and rejects duplicate quantifiers,
undeclared or malformed placeholders, malformed/direct statement graphs, and
empty environment sets. Its evidence class is fixed to `finite-obligation`, and
promotion verification rejects it. Implication/equivalence text in that lane is
still evaluated as bounded status data, not as R7 proof semantics.

## Mandatory non-claims

R10 does not prove:

1. parsing or name resolution inside Lean;
2. semantics for the general Core Language v0.8 or VAM instruction language;
3. equivalence with arbitrary strict `Mode` or external word/cyclic modes;
4. cyclic/phase, weighted, approximate, or profile resonance;
5. minimality of structural support or formal derivation of all layer axioms;
6. a general observer-synthesis algorithm or a second theorem nucleus.

The pinned userspace closure does not verify the OS loader, glibc/ld-cache,
proc/sys inputs, entropy source, mount namespace, kernel, ptrace, or root; those
remain explicit platform TCB boundaries rather than silently certified inputs.

The readiness taxonomy therefore remains exactly `1/4/25/5`:

```text
layers=35; theorem-derived=1; witness-only=4; shadow=25; meta=5
execution_ready=True; proof_complete=False
```

## Verification

Acceptance requires surface/elaboration/support/bridge/legacy adversarial tests,
all ten pinned Lean stages, Rust VAM parity, the 66-certificate root suite, Sage,
doctests, hygiene, Ruff, and diff checks. Mutation tests cover source/AST/span,
binder capture, resource limits, graph/support/R9/manifest/export/toolchain,
snapshot/cache/report, source/object/runtime TOCTOU, hardlink/path remap,
resolver/loader shadow, handler transplantation, and finite-obligation
promotion attacks.

## Next

R11 should extend the proof core with observer-indexed echo semantics and the
proof rules needed to reason about observers without collapsing them into
equality. Only after that should the project attempt a second narrow contracted
theorem nucleus. General Core/VAM elaboration, arbitrary native modes, and
observer synthesis remain separate future tracks.
