# VAM bounded optimizer, quantified-schema, and native completion slice

**Status:** implemented diagnostic completion; general proofs remain open  
**Profiles:** `bounded-optimizer-completion-skeleton`, `veyra.vam.quantified-theorem.v1`  
**Updated:** 2026-08-06

## Scope

This slice closes three old roadmap families by giving each one an executable,
fail-closed boundary instead of leaving an ambiguous future promise:

1. stricter optimizer visible-use diagnostics and a whole-optimizer theorem skeleton;
2. symbolic universally quantified theorem declarations and specialization;
3. an independently compiled Rust parity mirror, plus an explicit obstruction to
   optimized `VAMD` emission.

It does not change legacy opcodes, byte formats, the native CLI, certificates,
the formal bridge, or the layer taxonomy.

No certificate is added intentionally: every new status is `open`,
`proof_complete=false`, `proof_grade=false`, or `allowed=false`. Certifying
those rows as correctness/completion evidence would invert their obstruction
meaning; focused tests are the appropriate executable gate.

## Optimizer guard completion

`vam/src/optimizer_completion.py` validates every instruction and derives one
unique `COMPRESS` definition plus its single prior unique `OBSERVER`. Caller
`after_index` and observer values are fail-closed equality assertions against
those derived boundaries; neither can hide evidence-bearing uses. A use is admitted only
in these positions:

- source of `OBSERVE` or `COMPRESS` under the same observer;
- either value operand of `ECHO` under the same observer.

The guard rejects missing/multiple or wrong-kind candidate/observer definitions,
missing visible uses, foreign observers, direct `CERT`, `OBSTRUCT`, and unsupported operations.

`optimizer_theorem_skeleton()` executes the existing optimizer and bounded
equivalence oracle, records decision counts for all four passes, and fixes the
remaining general premises. Its status is always `open` and `proof_complete` is
always false. The outstanding proof obligations are:

- domain closure for all well-formed programs;
- compositional preservation between passes;
- side-effect and obstruction-trace bisimulation;
- checked correspondence between implementation and local laws.

Thus the new object is a theorem-shaped obligation ledger, not a theorem.

## Quantified schema model

`vam/src/quantified_theorem.py` introduces an isolated schema row:

```text
DECLARE_FORALL theorem-id (name : kind)* assumptions* conclusions+
```

The declaration is intensional: it exists without enumerating finite theorem
environments or finite proof-object rows. The isolated helper validates the
schema envelope, binder uniqueness, identifier grammar, byte bounds, and
closure of all structurally scanned `$binder` references. It is not registered
as a legacy opcode or interpreter/native-runtime instruction. The resulting
state is `well-formed-open`.

Specialization requires exactly one bounded `kind:atom` value for every binder,
enforces the declared kind, rejects punctuation, non-ASCII atoms, extra/missing
assignments, malformed placeholders, and expanded rows over 4096 UTF-8 bytes,
then performs deterministic structural substitution. The result is
`instantiated-open`, never `verified`. Neither declaration nor specialization
checks a proposition or creates proof evidence.

The canonical JSON row is deterministic and shared with the Rust mirror. It is
a parity surface, not an authenticated encoding or a new VAM byte frame.

## Native parity boundary

`vam/native/src/quantified_theorem.rs` independently mirrors:

- identifier and binder validation;
- free-placeholder rejection;
- deterministic canonical serialization;
- exact-kind atomic specialization and 4096-byte input/output bounds;
- the permanently open proof status.

It is compiled directly by focused tests and is deliberately not registered in
the legacy native crate. This proves exact behavior only for the checked rows;
it does not establish semantic parity for arbitrary theorem languages.

`native_quantified_parity_boundary()` labels this result
`bounded-executable-parity` with `proof_grade=false`. A proof-grade claim stays
blocked until formal schema semantics, source-bound refinement theorems for both
implementations, and a toolchain-bound correspondence theorem exist.

## Optimized VAMD emission obstruction

Optimized `VAMD` frame emission is not soundly available in this isolated
slice: the native CLI has no integrated VAMD encoder. The policy therefore
returns `allowed=false` and names four gates before integration:

1. native VAMD opcode/argument encoder validation;
2. exact decode of emitted optimized IR;
3. Python/Rust optimized semantic-report parity;
4. malformed-frame and resource-limit regressions.

No VAM0-only emission path is relabeled as VAMD, and no decoded-IR report is
misrepresented as an emitted frame.

## Integration hooks

The Python modules are exported from `vam.src` for explicit bounded use:

- `visible_use_guard`, `optimizer_theorem_skeleton`, and
  `vamd_optimized_emission_policy`;
- `declare_quantified_theorem`, `canonical_quantified_instruction`, and
  `specialize_quantified_theorem`;
- the Rust module remains unwired until the native crate and CLI receive
  reviewed integration.

The root index, module memory, changelog, and roadmap are integrator-owned.

## Verification

Focused gates cover accepted/rejected visible uses, theorem-skeleton non-claim
fields, duplicate corpus names, the VAMD obstruction, symbolic declarations,
hostile/type-mismatched/oversized specialization, forged optimizer scan
boundaries, malformed instructions, deterministic canonical text, direct Rust
unit tests, and Python/Rust canonical/specialization parity. All files in this
slice currently remain at or below 300 LOC and therefore within the shared
1000-line target.
