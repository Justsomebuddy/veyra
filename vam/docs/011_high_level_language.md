# 011 — High-Level Veyra/VAM Language Sketch

> **Design-history status:** the one-echo seed in `vam/src/highlevel.py` and the
> bounded observer/process/claim subset in `vam/src/highlevel_v1.py` are
> implemented. The broader syntax below remains a proposal, not an active
> completion checklist.

## Purpose

This document sketches a future high-level source language for Veyra programs
that lower into VAM. A tiny v0.8 seed now exists for one echo body; the full language below remains a design target. The language is process-first: it describes how a
construction is made, which observer reads it, and which echo or obstruction is
claimed under that observer.

The language is not intended to replace `.vmasm`. It is a readable authoring
layer above the existing path:

```text
high-level Veyra source -> AST -> Core/VAM lowering -> VAM IR -> VAM0 -> VM
```

## Design constraints

- A process is primary; a value is a shadow of a process under an observer.
- Every theorem-like form must expose proof status or open obligations.
- Observers are explicit and named, never hidden global context.
- Obstructions are first-class outcomes, not exceptions to erase.
- Lowering must preserve source spans and no-overclaim metadata.
- The first parser should accept a small deterministic subset, not a clever DSL.

## Syntax layers

### Process declarations

A `process` names a construction recipe. Its body is ordered Veyra-native
construction steps.

```veyra
process one_edge {
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

Process declarations lower to ordinary VAM construction instructions. The
source language keeps human labels (`A`, `path`, `m`) while lowering allocates
registers.

### Observer declarations

An `observer` names what is visible about a process result. Observer families
are explicit so that multiple readings of the same process do not collapse into
one hidden notion of equality.

```veyra
observer length reads mode as natural_shadow
observer boundary reads breath as endpoint_pair
observer trace reads process as construction_trace
```

A later parser can support parameterized observer families:

```veyra
observer window(k: Nat) reads trace as bounded_trace
```

For v0, parameters should parse as metadata only unless lowering rules exist.

### Echo claims

An `echo` claim compares two process outputs under a chosen observer.

```veyra
process left_edge { ... yield mode_left }
process right_edge { ... yield mode_right }

claim same_length {
  echo left_edge with right_edge under length
  cert "same-length-demo"
}
```

The word `claim` is deliberate. It records an obligation and a requested
certificate; it does not imply a proof has been accepted.

### Obstruction claims

Obstructions are written symmetrically with echoes. They should lower to VAM
`OBSTRUCT` rows or to theorem obligations with blocked status.

```veyra
claim open_path_not_closed {
  obstruct closed_mode from open_path under boundary
  witness "endpoint mismatch"
}
```

The boundary text is carried into diagnostics; it is not a proof term.

### Theorem cards

A theorem card is a structured claim plus explicit status. It is a source-level
container for binders, assumptions, observers, obligations, and certificate
requests.

```veyra
theorem THM-HL-001 "length echo is observer-local" {
  forall p: process
  forall q: process
  observer o = length

  assume wellformed(p)
  assume wellformed(q)

  claim echo p with q under o

  status conjectural
  boundary "source card only; no proof accepted"
}
```

Allowed initial statuses:

- `verified`: only after a configured checker accepts all proof-critical
  obligations;
- `imported`: accepted under a named external trust boundary;
- `partial`: some obligations are discharged, some remain open;
- `conjectural`: recorded claim with no accepted proof;
- `invalid`: malformed or overclaiming card.

## Sample lowering to VAM

High-level source:

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

observer length reads mode as natural_shadow

claim edge_self_echo {
  echo edge_ab with edge_ab under length
  cert "edge-self-echo"
}
```

Possible VAM IR shape:

```text
REZ      r0, a
REZ      r1, b
NOD      r2, r0
NOD      r3, r1
TACT     r4, r2, r3
BREATH   r5, r4
MODE     r6, r5
OBSERVER r7, length
ECHO     r8, r6, r6, r7
CERT     edge-self-echo, r8
```

Lowering notes:

- `process edge_ab` lowers once to a register-producing block.
- `yield m` identifies the block output register (`r6`).
- `observer length` lowers to `OBSERVER r7, length`.
- `echo edge_ab with edge_ab under length` reuses the process output twice.
- `cert` emits a certificate request; acceptance is decided by the VM result,
  not by parser trust.

## Non-proof-assistant boundary

This high-level language is not a proof assistant.

It may:

- describe theorem cards and proof obligations;
- lower finite executable constructions to VAM;
- preserve source spans, statuses, assumptions, and trust boundaries;
- request certificates from the reference VM or an external checker;
- reject overclaiming syntax before execution.

It must not:

- infer a proof from a theorem-shaped block;
- treat a successful parse as theorem verification;
- hide external trust as internal proof;
- solve quantifiers, induction, or equality reasoning automatically;
- erase unresolved symbols, missing witnesses, or open obligations;
- advertise Veyra/VAM as a complete formal foundation because this syntax
  exists.

The first honest success criterion is: source cards lower to auditable VAM data
and diagnostics without changing their evidence status.

## Implemented v0.8 seed

`vam/src/highlevel.py` currently accepts only:

```text
process NAME { echo(EXPR,EXPR) under OBSERVER }
claim NAME := echo(EXPR,EXPR) under OBSERVER
```

It lowers to Core `echo(...)` and then to VAM IR. Theorem-like syntax returns a diagnostic and proves nothing.

## Staged parser plan

### Stage 0 — Lexical skeleton

- Implement a line/brace tokenizer with comments and string literals.
- Preserve byte offsets, line numbers, and column numbers.
- Reject tabs/indent ambiguity only if it affects spans.
- Produce stable error messages for unclosed blocks and strings.

### Stage 1 — Concrete AST

Parse only:

- `process NAME { ... }`;
- construction steps: `rez`, `nod`, `tact`, `breath`, `mode`, `yield`;
- `observer NAME reads KIND as SHADOW_KIND`;
- `claim NAME { echo ...; obstruct ...; cert ...; witness ... }`.

Do not parse theorem binders yet. Unknown statements should become structured
errors, not opaque accepted nodes.

### Stage 2 — Name and kind checks

- Resolve process, local variable, observer, and claim names.
- Check simple kind transitions (`rez -> nod -> tact -> breath -> mode`).
- Emit diagnostics for duplicate names, missing yields, and observer-kind
  mismatches.
- Keep all checks deterministic and side-effect free.

### Stage 3 — VAM lowering

- Lower construction AST to VAM IR register blocks.
- Lower observers to `OBSERVER` instructions.
- Lower echo/obstruction claims to `ECHO`/`OBSTRUCT` plus optional `CERT`.
- Attach source-span metadata to each generated instruction or diagnostic.
- Round-trip through `VAM0` before claiming parser acceptance.

### Stage 4 — Theorem-card surface

Add theorem syntax after process/claim lowering is stable:

- `theorem ID "title" { ... }`;
- `forall`, `exists`, `assume`, `claim`, `status`, `boundary`;
- obligation generation matching `007_theorem_lowering_plan.md`.

The theorem parser should initially produce theorem data plus obligations, not
proof checking.

### Stage 5 — Golden fixtures and no-overclaim tests

- Parse minimal process/observer/claim examples.
- Verify generated VAM IR matches golden text.
- Verify source spans survive lowering diagnostics.
- Verify missing proofs stay `conjectural` or `partial`.
- Verify imported proofs name a trust boundary.
- Verify invalid overclaim cards cannot lower as `verified`.

## Open questions

- Should process bodies allow reusable sub-process calls in v0, or only inline
  construction steps?
- Should observer declarations live in modules, or inside theorem cards for
  maximum locality?
- How much Core Language syntax should be accepted directly before theorem
  lowering is implemented?
- Should `.veyra` be the source extension, or should VAM use a distinct
  `.vamhl` extension until the language stabilizes?
