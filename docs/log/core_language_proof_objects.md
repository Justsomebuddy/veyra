# Veyra Core Language v0.3 — Proof Objects

**Status:** executable trace layer.
**Implementation:** `src/core/language/proof.py`.
**Tests:** `tests/language/test_core_language_proofs.py`.

## Purpose

v0.1 gave Veyra a language kernel. v0.2 made grammar errors locatable. v0.3
turns inference into explicit proof data: every checked step records its rule,
source span, input kinds, input statuses, output status, and obstruction.

This is the first bridge from “the interpreter says ready/blocked” to “the lab
can explain why, where, and by which rule”.

## New artifacts

| Artifact | Meaning |
|---|---|
| `VeyraProofStep` | one rule application with source span and status |
| `VeyraProofTrace` | full trace for a source expression |
| `VeyraProofSummary` | counts of ready/blocked/unknown proof steps |
| `trace_veyra_proof(src)` | parse + type/inference trace builder |
| `proof_summary(trace)` | compact status summary |

## Step schema

A proof step records:

- `rule` — e.g. `kind.nod`, `kind.echo`, `infer.echo`, `grammar.parse`;
- `span` — source range inherited from the spanned parser;
- `input_kinds` — child kinds used by the rule;
- `input_statuses` — child readiness states;
- `output_kind` — resulting kind;
- `output_status` — `ready`, `blocked`, or `unknown`;
- `obstruction` — explanation when blocked/unknown.

## Examples

```text
echo(nod:a,nod:b,observer:kind)
```

produces kind steps for both `nod` atoms, one observer atom, an `echo` relation,
and a final `infer.echo` step. Since both operands have kind `nod`, the final
status is `ready`.

```text
echo(nod:a,nod:b,observer:trace)
```

has the same grammar/type structure but final `infer.echo` is `blocked` because
`nod:a` and `nod:b` do not match under the full trace observer.

## Parse failures as traces

A malformed expression still becomes a proof trace with one blocked
`grammar.parse` step. That keeps failed fuzz cases and notebook mistakes inside
the same proof-object format.

## Verification

Targeted command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/language/test_core_language_proofs.py tests/language/test_core_language_spans.py tests/language/test_core_language.py tests/shadows/test_certify.py
```

Current verification: targeted `22 passed`; full suite `234 passed`; doctest 41/41; smoke ok; certificates 11/11; line hygiene 0 files >300.

## Next step

Use proof steps to drive generated mutation tests: mutate constructors,
observers, and labels, then require either a ready proof trace or a precise
blocked trace with source span and obstruction.
