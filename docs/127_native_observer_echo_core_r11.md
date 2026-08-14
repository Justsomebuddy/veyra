# R11 — Native observer/echo proof core v2

**Date:** 2026-07-15
**Status:** release-hardened conservative proof slice; completed and independently reviewed.
**Certificate:** `observer_core_r11`.
**Boundary:** finite closed R7 recurrences and a closed, serializable observer AST.

## Result

R11 adds a separate typed observer calculus above unchanged R7 evidence and the
exact R9 intrinsic image used by R10:

```text
closed recurrence + closed observer AST
  → unique response kind
  → ready response | ordered domain obstruction
  → echo | mismatch | domain-blocked
  → replayed observer proof/artifact
  → Lean THM-R11-001..006
```

An **echo is not equality**. It states that two defined observations have the
same branded response. `crest(Pulse(_))` therefore gives a deliberate
non-collapse witness: different recurrences can echo as the same `pulse` mark.
Conversely, `tail(Silence)` is outside the native domain and yields an exact
obstruction; blockage never counts as echo.

## Closed syntax and response types

The canonical schema is `veyra.observer-core.v2`. Its complete Python AST is:

```text
ObserverExpr ::= Input
               | Apply(PrimitiveId, ObserverExpr)
               | Pair(ObserverExpr, ObserverExpr)
PrimitiveId ::= TAIL | CREST
```

`Input` returns a recurrence. `TAIL` consumes and returns a recurrence;
`CREST` consumes a recurrence and returns a mark. `Pair` returns the product of
its two branch kinds. The inferred kinds are `RECURRENCE`, `MARK`, and recursive
`PairKind(left, right)`.

Responses are branded values, never `int`, Boolean, string, percentage, or
ordinary arithmetic payloads:

```text
ResponseValue ::= RecurrenceValue(CoreTerm)
                | MarkValue(SILENT | PULSE)
                | PairValue(ResponseValue, ResponseValue)
```

Only finite, closed, exact `Silence`/`Pulse` R7 values enter evaluation.
Subclassed nodes, cycles, excessive depth/node count, unknown tags or keys,
duplicate JSON keys, trailing data, and non-canonical types fail closed. There
is no callable, evaluator registry, dynamic import, or extension hook.

## Typed partial semantics

For a closed recurrence `r`:

```text
observe(Input, r)                 = Ready(RecurrenceValue(r))
observe(tail, Silence)            = Blocked(tail-of-silence, [apply-tail])
observe(tail, Pulse(t))           = Ready(RecurrenceValue(t))
observe(crest, Silence)           = Ready(MarkValue(silent))
observe(crest, Pulse(t))          = Ready(MarkValue(pulse))
```

Application prefixes an inner obstruction with its `apply-tail` or
`apply-crest` step. Pair evaluates both branches, prefixes their paths with
`pair-left` and `pair-right`, and concatenates obstructions left before right.
Paths are stored outer-to-inner and evaluator-produced blocked results are
nonempty.

`echo(o, x, y)` is exactly:

1. `DomainBlocked(left_paths, right_paths)` if either observation blocks;
2. `Echo(response)` if both are ready with the same branded response;
3. `Mismatch(left_response, right_response)` otherwise.

Thus partiality is explicit data. It is never converted to an exception-based
fallback, a false echo, or a classical numeric shadow.

## Python ↔ Lean correspondence

| Python | Lean `VeyraObserver` | Correspondence |
|---|---|---|
| `LeafKind` / `PairKind` | `Kind.recurrence` / `.mark` / `.pair` | unique response kind |
| `Input`, `Apply`, `Pair` | indexed `Observer` constructors | same closed tree; Lean enforces kinds by indices |
| `PrimitiveId.TAIL/CREST` | indexed `Primitive.tail/crest` | recurrence→recurrence / recurrence→mark |
| branded response classes | indexed `Response` | recurrence, mark, or product only |
| `Ready` / `Blocked` | `Observation.ready/blocked` | same partial observation |
| `Echo` / `Mismatch` / `DomainBlocked` | `EchoOutcome` | same three-way result |
| `PathStep`, `ObstructionCode` | matching inductives | exact ordered paths and `tailOfSilence` code |
| `observe`, `echo` | `runObserver`/`observe`, `echo` | same branch and obstruction order |

Lean also defines `observeDecodedMode` and `observeIntrinsic`. The R9 image
lemmas show that observing `encodeMode r` or `intrinsicMode r` agrees with
observing `r`. This is exact-image composition, not semantics for arbitrary
strict/external modes. Python↔Lean parity is checked against the same closed
constructors and canonical generated export; the Python parser and hashing are
reviewed TCB components, not functions proved in Lean.

## Conservative R7 embedding

R11 adds four proof constructors without changing the R7 calculus:

| Rule | Replay condition |
|---|---|
| `EmbedR7` | the unchanged R7 kernel infers the embedded evidence |
| `EqualityReadyEcho` | child is an R7 equality, values are closed, observer is structurally total, and concrete replay returns `Echo` |
| `CrestPulseEcho` | concrete crest/pulse replay returns the exact `pulse` mark |
| `TailSilenceObstruction` | concrete tail/silence replay returns the exact code and path |

The direction is intentionally one-way:

```text
checked R7 equality + defined/total observation  ⇒  observer echo
observer echo                                    ⇏  R7 equality
```

The reverse would be unsound because observers may discard information;
`THM-R11-006` is the checked counterexample. R7 proof terms, conclusions, rule
closures, native-law closures, and R7 artifacts are re-inferred rather than
accepted from caller-declared fields.

## Explicit-origin artifact

`veyra.observer-proof.v2` records the exact context, inferred statement and
outcome, ordered proof nodes/premises, root, rule/law closures, structural used
support, obstruction paths, embedded R7 artifact digests, and one canonical
proof digest. Node identifiers are content-derived.

Verification starts from the supplied proof origin and rebuilds the expected
artifact. It rejects altered conclusions/outcomes/support, reordered or
duplicate nodes, dangling/cyclic/disconnected graphs, type subclasses, excess
resources, and R7 origin drift. The canonical export is the direct
`THM-R11-006` crest law, so its artifact correctly has no embedded R7 digest;
artifacts using `EmbedR7` bind the complete replayed R7 artifact explicitly.
Before recursive R7 replay, exact proof structure is iteratively bounded to 128
levels and 2,048 node occurrences; aggregate artifact text is capped at 2 MiB
of UTF-8 before the final artifact digest and full serialization. Content-derived
node IDs are computed during bounded graph construction before that aggregate gate.

Canonical focused artifact:

```text
theorem  = THM-R11-006
artifact = 2bcf57b5dda6b92569328da5de0b5477058dcde08f57a986ced8882b1f5c6c95
law      = crest-pulse-echo
support  = observer-core-semantics, observer-core-codec, crest-pulse-law
```

## Lean theorem chain

| ID | Checked statement |
|---|---|
| `THM-R11-001` | echo of a response iff both observations are ready with that response |
| `THM-R11-002` | a ready observation echoes reflexively inside its defined domain |
| `THM-R11-003` | checked R7 equality plus readiness implies echo |
| `THM-R11-004` | `tail(Silence)` has exactly `tailOfSilence@[applyTail]` |
| `THM-R11-005` | echoing tail on silence/silence is blocked on both sides with that exact obstruction |
| `THM-R11-006` | two unequal pulse recurrences echo under crest as `pulse` |

The general theorems live in [`VeyraObserverProof.lean`](../proofs/lean/VeyraObserverProof.lean);
the typed executable semantics live in
[`VeyraObserverCore.lean`](../proofs/lean/VeyraObserverCore.lean).

## Fail-closed R10-bound bridge

The separate bridge `veyra.lean.r11.observer-echo-tcb.v1` first validates the
immutable nine-row snapshot-name root, before any R10 continuity replay,
filesystem access, or Lean work. A corrupted live proxy blocks bridge checking,
report verification, and default trust-key construction while the regression
asserts zero `_verified_r10()` calls. Snapshot materialization and verification
then use those captured rows without mutable filename rereads. Only after this
pre-continuity gate does the bridge independently reverify R10 and replay the
R11 artifact, manifest, generated export, immutable snapshot, reviewed objects,
pinned Lean toolchain, and runtime closure. The post-hardening chain binds 34
source/export inputs, nine Lean stages, eight reviewed intermediate `.olean`
objects, and the unchanged traced runtime
closure of 2,365 files / 522,231,408 bytes
(`990d68ab...2f761a`). The necessarily non-self-bound manual trust root is
`observer_core_manifest.py`, externally recorded here at SHA-256
`5ddf6cd03b2f1089e147a91cb080f98f6fde2512a4e7e64a184ef58586e16b4a`.
The post-hardening focused replay checked all nine stages
and produced the exact current bindings:

```text
artifact = 2bcf57b5dda6b92569328da5de0b5477058dcde08f57a986ced8882b1f5c6c95
r10      = 291aed1ee8eb913b42c6d77be8701ee10c6429f625a5cd9dec53aab3e4317664
snapshot = 1bc6a303307e093d350bcd48428da48ea5d7daeeb7d075862c9c94051d8091f9
binding  = 79039a32670ea305a70129e80d6299eae0f2428393f2f28018b74ccbdbc8701f
```

This R11 certificate does **not** renew or widen the R8 promotion contract.
The readiness taxonomy remains exactly `1/4/25/5`, and
`proof_complete=False`.

## Acceptance and final evidence

Acceptance requires canonical codec round trips and mutations, exact kind and
partial-semantics parity, ordered obstruction paths, all four proof rules,
artifact replay/forgery attacks, both deterministic Lean chains, R10
continuity, manifest/snapshot/object/runtime attacks, standalone certificate,
R7/R10 non-drift, Ruff, diff checks, and the final project verification.

Release-hardening evidence: focused observer/bridge tests `80/80`, bridge
manifest `34/34`, and guarded Lean replay `9/9` pass. Exact source snapshots,
pinned ancestor dirfds, strict outcome containers, immutable manifest/object/
snapshot-name rows, the pre-continuity zero-call gate, and canonical R7/support
serialization close all hardening waves. Final the complete verification suite exited 0: pytest
collection/run reached 100% at `1315/1315`, certificates passed `67/67`, Sage
smoke reported `errors=0`, doctest reported `attempted=41` and `failed=0`, and
hygiene was clean. Independent final review found no blocker/high/medium.

Two reviewed TCB limits remain explicit. First, Python modules already loaded
in the verifier process are not independently re-attested as code objects
against source bytes hashed later by the bridge; the manifest therefore proves
source continuity, not Python interpreter/code-object identity. Second,
`THM-R11-003` takes readiness as an explicit Lean premise rather than proving
the Python evaluator total on all closed structural observers, and the canonical
export replays the crest non-collapse witness rather than every R11 proof rule.
These limits preserve soundness and non-promotion, but rule out a claim of full
Python↔Lean extraction or rule-by-rule correspondence.

## Mandatory non-claims

R11 does not provide:

1. observer-callable execution, registries, plugins, or arbitrary payloads;
2. a parser/proof of the Python codec or bridge inside Lean;
3. a general observer-synthesis, completeness, or minimality algorithm;
4. reflection from echo to equality, or equality of echoing recurrences;
5. semantics for arbitrary native objects, strict modes, cyclic/phase modes,
   approximate/weighted resonance, general Core programs, or VAM IR;
6. a new promoted layer, second theorem-derived nucleus, or taxonomy change.

General synthesis remains R14 work. A second substantive theorem nucleus and
any promotion proposal remain R13 work.

## Implementation map

- AST/codec/semantics: [`observer_core_types.py`](../src/core/observer_core_types.py),
  [`observer_core_codec.py`](../src/core/observer_core_codec.py),
  [`observer_core_semantics.py`](../src/core/observer_core_semantics.py)
- proof/artifact: [`observer_core_kernel.py`](../src/core/observer_core_kernel.py),
  [`observer_core_artifact.py`](../src/core/observer_core_artifact.py)
- bridge/export: [`observer_core_bridge.py`](../src/core/observer_core_bridge.py),
  [`observer_core_snapshot.py`](../src/core/observer_core_snapshot.py),
  [`observer_core_lean_render.py`](../src/core/observer_core_lean_render.py)
- precursor boundaries: [R7](123_proof_carrying_core_r7.md),
  [R9](125_intrinsic_mode_transport_r9.md),
  [R10](126_proof_grade_core_elaboration_r10.md)
- separate relative finite realization: [P1→R16 contract](161_p1_r16_realization_contract.md)
