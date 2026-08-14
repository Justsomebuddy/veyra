# Proof-carrying Core R7

**Status:** implemented and checked on 2026-07-14.
**Scope:** one small typed recurrence calculus, independent proof replay, general Lean checker soundness, and one honestly promoted theorem nucleus.
**Certificate:** `proof_carrying_core_r7`.

## Why R7 exists

The earlier Core theorem layer parsed finite statement templates and evaluated environment rows. Semantic receipts replayed computations. Neither mechanism established a reusable judgment calculus. R7 therefore adds a narrow proof spine before adding more domain rows:

```text
typed syntax → proof term → independent Python inference → canonical graph
             → generated Lean proof → general Lean soundness → bound certificate
```

The chain is deliberately small. It is stronger than a workability ledger, but it is not a proof of every Core program or every Veyra layer.

## Judgment and syntax

The first judgment is `Γ; Δ ⊢ p : P`:

- `Γ` is an innermost-first tuple of typed term binders;
- `Δ` is an innermost-first tuple of proposition assumptions;
- `p` is a proof term;
- `P` is inferred by the kernel, never supplied as trusted output.

The only current type is `recurrence`. Terms are de Bruijn variables, silence, pulse, stitch, and weave. Propositions are equality, implication, universal quantification, and intrinsic resonance.

`proof_core_substitution.py` implements shifting, substitution, top-level instantiation, and free-index discovery. Binder traversal increments depth, so replacement cannot capture variables by string collision or prefix replacement.

## Proof rules

`proof_core_kernel.py` independently checks:

| Family | Rules |
|---|---|
| Context | assumption |
| Implication | introduction, elimination |
| Universal | introduction, elimination |
| Equality | reflexivity, symmetry, transitivity |
| Native | one fixed native-law instance |
| Resonance | introduction from exact `weave(factor,witness)=carrier` evidence |

Universal introduction weakens all existing assumptions before entering the new binder. Equality transitivity preserves premise order. Object-identity cycles, unbound/bool indices, invalid containers, bad native-law arity, and conclusion mismatch are rejected.

### Native law closure

The trusted Python templates are exactly:

1. stitch-silence-left;
2. stitch-silence-right;
3. weave-silence-right;
4. weave-pulse recursion;
5. weave-unit-right.

They are mirrored in `VeyraProofKernel.lean`, and `nativeConclusion_sound` proves each template against the canonical inductive semantics imported from `VeyraNativeArithmetic.lean`.

## Canonical proof artifact

`proof_core_artifact.py` emits tagged canonical JSON only. The shared codec
accepts only actual JSON containers: arrays must be explicit Python `list`
values, while tuples are rejected at every nesting depth instead of silently
colliding with arrays. Trusted callers normalize their immutable tuples to
lists before hashing. It binds:

- theorem ID;
- complete typed context;
- inferred statement;
- every rule node and ordered premise ID;
- each node's local-context digest and inferred conclusion;
- exact rule and native-law closures;
- one whole-artifact SHA-256 digest.

Nodes are content-addressed. Replay rejects unknown rules/tags, noncanonical JSON, malformed containers, duplicate nodes, dangling premises, disconnected extras, cycles, reordered premises, forged node IDs, context/conclusion drift, closure drift, and digest drift.

This is a computation/proof certificate for the supported calculus. It does not turn unrelated semantic receipts or ordinary Python result objects into proofs.

## Lean soundness and source binding

The formal chain is modular:

| File | Role |
|---|---|
| `VeyraNativeArithmetic.lean` | canonical recurrence/stitch/weave/resonance semantics |
| `VeyraProofKernel.lean` | mirrored terms, propositions, substitution, contexts, proof AST, inference/checker |
| `VeyraProofSoundness.lean` | `infer_sound` for every proof constructor and `THM-R7-001` for `check` |
| `VeyraProofResonance.lean` | generated canonical proof and `THM-R7-002..004` |

`proof_core_lean_render.py` renders the checked Python AST, rather than copying a separately maintained statement/proof. The export embeds the Python artifact digest. `proof_core_manifest.py` locks the independently reviewed arithmetic/kernel/soundness hashes, preventing a newly compiling but semantically weakened TCB from silently recertifying itself. `proof_core_bridge.py` rehashes live inputs on every call, requires byte identity, rejects `sorry`/`admit`/`sorryAx`/`axiom`/`unsafe` across all four sources, treats warnings as errors, requires an exact pinned Lean `v4.30.0-rc2`, and binds artifact, TCB, export, and toolchain identity.

`proof_core_snapshot.py` closes original-source time-of-check/time-of-use drift: the four already-read byte arrays are materialized into a content-addressed read-only snapshot, and Lean compiles only those captured paths with an isolated object directory. Mutating the original after capture cannot change the compiled semantics. The remaining trust boundary is the local build account itself: hostile same-user mutation of the snapshot or pinned toolchain during invocation is not modeled.

Compilation or theorem-name scanning alone is not the acceptance condition: theorem fields must exactly replay the artifact; the reviewed TCB manifest, deterministic rendering, byte identity, pinned toolchain, and general soundness proof must all pass. The manifest locks reviewed parity; it is not a claim of automatic Python-to-Lean extraction.

## First theorem-derived nucleus

`THM-R7-004` states:

```text
∀ r : recurrence, intrinsic-resonates(r, r)
```

Its witness is the unit recurrence `pulse(silence)`, and its equality premise is `weave(r,pulse(silence))=r`. The kernel-derived closure is:

```text
forall-intro, native-law, resonance-intro
native law: weave-unit-right
```

The new `intrinsic-resonance` layer consumes this exact artifact and Lean binding. It is the sole `theorem-derived` layer.

## Readiness taxonomy

The 35-layer report now separates mathematical evidence from execution assembly:

| Class | Count | Meaning |
|---|---:|---|
| theorem-derived | 1 | exact proof artifact plus checked Lean soundness binding |
| witness-only | 4 | replayed native computation witnesses, not whole-layer proofs |
| shadow | 25 | finite/classical external models without kernel derivation |
| meta | 5 | ledgers, diagnostics, or coordination rows |

`core_ready`/`execution_ready` means all registered artifacts execute. `proof_complete=False` remains mandatory while witness-only or shadow layers exist.

## Critical semantic boundary

The existing `resonance` layer is cyclic/phase word-shadow mathematics using rotations, offsets, and other ordinary operations. It is **not** the intrinsic inductive relation proved by R7 and remains one of the 25 shadows. Approximate, weighted, spectrum, compression, and profile resonance also remain shadows until explicit bridges are proved.

Post-R7 promotion is fail-closed: R8 binds this exact theorem/artifact to `intrinsic-resonance`; R9 supplies only the fixed-anchor unary image carrier; R10 now requires exact closed-source elaboration and generic image semantics through bridge `veyra.lean.r10.proof-elaboration-tcb.v1`. The R7 theorem/artifact are unchanged, and no other layer inherits them by name.

## Verification

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. python3 -m pytest -q \
  tests/test_proof_core_*.py tests/test_layer_derivations.py tests/test_axiom_kernel.py \
  tests/test_essence_core.py tests/test_veyra_sage_essence.py
PYTHONPATH=. python3 -c 'from src.core.proof_core_bridge import proof_core_bridge_report as r; assert r().status == "checked"'
the complete verification suite
git diff --check
```

Adversarial tests cover 2,000 seeded nested-binder substitution cases, malformed proof graphs, source drift, and snapshot mutation. The formal R7 evidence is listed by exact declaration in `THEOREMS.md`. R10 later replays the canonical proof; it does not make its Python parser part of the R7 Lean theorem.
