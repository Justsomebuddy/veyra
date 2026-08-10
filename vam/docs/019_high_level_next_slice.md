# 019 — High-Level Language Next Slice

> **Partially implemented design record:** `vam/src/highlevel_v1.py` implements
> observer aliases plus one conservative process/claim block. The broader
> theorem-card, reusable declaration, and module surface below remains future
> work and is not a proof-strength claim.

## Purpose

Record the design target around the bounded HL-1 helper that followed the
one-echo seed in `vam/src/highlevel.py`.

Implemented behavior is authoritative in `vam/src/highlevel_v1.py` and its
tests; unimplemented sections below remain proposals under this evidence boundary:

```text
parse/lower/transport != proof
theorem-shaped source != verified theorem
successful echo execution != complete mathematics
```

## Current audit

The implemented seed accepts only:

```text
process NAME { echo(EXPR,EXPR) under OBSERVER }
claim NAME := echo(EXPR,EXPR) under OBSERVER
```

It lowers both forms to one Core expression:

```text
echo(LEFT,RIGHT,observer:NAME)
```

Then it calls `compile_source_with_diagnostics()`, which can emit VAM IR and an
optional `CERT` for the finite Core echo. The seed already has useful
guardrails:

- theorem-like `theorem`/`lemma` input is rejected with
  `hl.unsupported_theorem`;
- diagnostics carry the no-overclaim note
  `high-level seed lowering is syntax transport only; it proves no theorem`;
- unsupported Core lowering failures are wrapped as high-level diagnostics;
- observer names are constrained to bare names or `observer:NAME`, then the
  Core/VAM compiler enforces the supported observer set.

Main gaps for the next slice:

- no durable observer declaration table;
- no process body with named construction steps and `yield`;
- no reusable process names in claims;
- no theorem-card carrier shape for open claims or proof-object references;
- no explicit unsupported-form matrix for future users and tests.

## Proposed slice name

Call the next slice **HL-1 finite carrier slice**.

HL-1 is intentionally small:

1. observer declarations;
2. straight-line finite process blocks;
3. block-form echo claims over process names;
4. theorem cards as open/proof-object carriers only;
5. deterministic diagnostics for everything else.

## Accepted source surface

### 1. Observer declarations

```veyra
observer length reads mode as natural_shadow
observer boundary reads breath as endpoint_pair
observer trace reads process as construction_trace
```

Required behavior:

- record `name`, `reads_kind`, `shadow_kind`, and source span;
- reject duplicate observer names in the same module;
- lower only names supported by the current compiler:
  `kind`, `label`, `length`, `trace`, `boundary`;
- declarations for unsupported observer names may be parsed as metadata, but
  any claim using them must fail with an explicit unsupported-observer
  diagnostic before VAM execution;
- parameterized observers remain unsupported in HL-1.

Observer declarations do not prove that the observer is semantically complete.
They only bind a high-level name to a visible VAM observer label.

### 2. Straight-line process blocks

```veyra
process edge_ab {
  rez a
  rez b
  nod A from a
  nod B from b
  tact e from A -> B
  breath path from e
  mode m from path
  yield m
}
```

Required behavior:

- parse one named process block into a finite step graph;
- allow only these statements in HL-1:
  - `rez NAME`
  - `nod NAME from RESIDUE`
  - `tact NAME from LEFT -> RIGHT`
  - `breath NAME from SOURCE`
  - `mode NAME from SOURCE`
  - `yield NAME`
- require exactly one `yield`;
- reject duplicate local names;
- reject references to unknown locals;
- reject cycles by construction: statements may reference only earlier names;
- reject empty process bodies;
- preserve source spans for every statement and reference.

Lowering target:

```text
process block -> one finite Core expression rooted at yield
```

For the example above, the Core shape is equivalent to:

```text
mode(breath(tact(nod(rez:a),nod(rez:b))))
```

The exact printed Core form may follow existing Core normalization, but golden
tests should compare stable normalized text, not handwritten whitespace.

### 3. Block-form echo claims

```veyra
claim edge_self_echo {
  echo edge_ab with edge_ab under length
  cert "edge-self-echo"
}
```

Required behavior:

- resolve both process names;
- resolve the observer name through the observer declaration table or the
  built-in supported observer set;
- lower to Core `echo(LEFT_EXPR,RIGHT_EXPR,observer:NAME)`;
- pass the existing `claim` name and `boundary` text into
  `compile_source_with_diagnostics()`;
- emit `CERT` only for the finite executable echo, exactly as current Core
  lowering does;
- keep certificate text scoped to this finite echo, not to any theorem card.

Optional in HL-1:

- `cert` line may be absent, compiling with `certify=False`;
- a `boundary "..."` line may override the default high-level boundary string.

Not in HL-1:

- multiple echo lines in one claim;
- obstruction claims as executable forms;
- process calls with arguments;
- imports/modules.

## Theorem cards as carriers

HL-1 may parse theorem cards, but only as records carrying open obligations or
opaque proof-object references.

Example open card:

```veyra
theorem THM-HL-001 "edge self echo is visible under length" {
  claim edge_self_echo
  status open
  boundary "high-level theorem card only; no proof accepted"
}
```

Example proof-object carrier:

```veyra
theorem THM-HL-002 "external note about edge echo" {
  claim edge_self_echo
  proof_object "lean4:Some.Module.edge_echo"
  status imported
  boundary "external Lean reference; not checked by VAM HL-1"
}
```

Required behavior:

- parse `id`, optional quoted title, referenced claim names, `status`,
  `boundary`, and optional `proof_object`;
- produce a theorem-carrier object or JSON-like record, not VAM proof
  acceptance;
- default missing status to `open`;
- default missing proof object to a `proof.missing` obligation;
- require a non-empty `boundary` for `imported` or proof-object-bearing cards;
- set every generated obligation row with `accepted_certificate = false`;
- never emit a VAM `CERT` because of a theorem card.

Allowed HL-1 card statuses:

- `open`: no proof accepted;
- `conjectural`: claim recorded with no proof accepted;
- `partial`: proof object or notes exist, but obligations remain open;
- `imported`: external reference exists and names an explicit trust boundary;
- `invalid`: parser or no-overclaim validation rejected the card.

`verified` is not an accepted user-written status in HL-1. If a user writes it,
the parser must return a diagnostic such as:

```text
hl.unsupported_verified_status:
  verified theorem cards require a configured checker; HL-1 carries only open,
  partial, conjectural, imported, or invalid records
```

Future verifier integration may map checked finite Core obligations into
`VamTheoremRecord.proof_status = "verified"`, but the high-level parser alone
must never do so.

## Unsupported forms matrix

HL-1 should reject or carry as open metadata:

| Form | HL-1 result |
| --- | --- |
| `theorem ... status verified` | diagnostic, no lowering |
| `lemma ...` | diagnostic alias to unsupported theorem-like form |
| `forall`, `exists`, induction, recursion | parse only as unsupported/open metadata if kept at all |
| parameterized observers | diagnostic |
| multiple yields | diagnostic |
| process arguments or process calls | diagnostic |
| branch/loop/control flow | diagnostic |
| obstruction claims | diagnostic or theorem-card open obligation, no VAM `OBSTRUCT` yet |
| custom observer not in supported set | declaration may parse; use in claim fails |
| external proof without `boundary` | diagnostic |
| imported proof treated as internal proof | diagnostic/no-overclaim failure |
| native speed, optimizer completeness, GPU/FPGA claims | out of language scope |

## Lowering pipeline

Recommended implementation order:

1. tokenize blocks while preserving byte offsets, line, and column;
2. parse declarations into a small AST:
   `ObserverDecl`, `ProcessDecl`, `ClaimDecl`, `TheoremCard`;
3. build symbol tables for observers, processes, and claims;
4. lower process yields to Core expressions;
5. lower echo claims through the existing diagnostic Core compiler;
6. serialize theorem cards as transport-only records with obligations;
7. add no-overclaim validation as a final pass.

The no-overclaim pass should run even if parsing succeeded. It should downgrade
or reject cards that imply proof strength not supplied by an actual checker.

## Minimal acceptance tests

Suggested tests for the eventual implementation:

- observer declaration plus process block plus echo claim compiles to VAM IR;
- duplicate observer/process/local names produce stable diagnostics;
- process with missing or multiple `yield` is rejected;
- claim under unsupported observer fails before VAM execution;
- theorem card with `status open` serializes with open obligations and no
  accepted certificate;
- theorem card with `proof_object` but no `boundary` is rejected;
- theorem card with `status verified` is rejected in HL-1;
- current one-line `claim NAME := echo(...) under OBSERVER` remains supported
  until a deprecation decision is explicit.

## Boundary notes

HL-1 extends authoring syntax, not mathematical strength.

It may honestly claim:

- a high-level process was parsed;
- a finite process block lowered to a Core expression;
- a finite echo claim compiled/executed under a named observer;
- a theorem card was transported with explicit open/imported/partial status.

It must not claim:

- theorem verification from parsing;
- proof completeness from a proof-object string;
- global equality from one observer-local echo;
- obstruction completeness before obstruction syntax is implemented;
- native/backend/optimizer completeness from high-level syntax.
