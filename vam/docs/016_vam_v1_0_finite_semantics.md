# 016 — VAM v1.0 finite semantics and boundary hardening

VAM v1.0 turns the v0.9 parity slice into a sharper finite-semantics contract.
It is still a reference contract, not a speed claim and not a proof assistant.

## What changed

- `vam/src/theorem.py` now emits `VamFiniteTheoremCase` rows.
- `vam/src/shell.py` now emits a deterministic non-certificate shell carrier.
- `vam/src/fixtures.py` now covers current obstruction surfaces and malformed VAM0 decoder boundaries.
- `vam/src/optimizer.py` now has a conservative `compress-idempotent` pass.
- `tests/vam/test_vam_native_boundaries.py` checks native CLI frame/error JSON shape.
- `vam_reference_v1` now requires expanded fixture coverage, shell blocked-carrier behavior, and finite theorem-case transport.

## Finite theorem cases

A finite theorem carrier records:

- theorem id and original source;
- finite `forall` binders with concrete environment assignments;
- assumption and conclusion obligation rows;
- case status: `verified`, `blocked`, or `open`;
- trust boundary: `core.finite_obligation_check`.

`verified` means every executable finite Core obligation case transported as verified.
It does **not** mean VAM proved an unbounded theorem.

Unsupported quantifier shapes, missing assignments, or opaque semantics keep the theorem open or blocked.

## Shell/conjunction carrier

Supported finite shell shape:

```text
shell(echo(A,B,observer:o), echo(C,D,observer:p), ...)
```

VAM now records a root `Rez` shell-carrier label containing child rows and status:

- `transported` when every child echo lowered and no certificate claim exists;
- `blocked` when any child is unsupported, unknown, or obstructed.

No shell-level `CERT` is emitted.

## Optimizer compression normalization

The `compress-idempotent` pass may collapse:

```text
COMPRESS b, a, obs
COMPRESS c, b, obs
```

into an alias `c -> b` only when:

- all involved registers are single-definition;
- observer kind has an explicit idempotent contract;
- target/source/candidate contain no obstruction evidence;
- downstream uses stay inside the same observer context.

Otherwise the optimizer records a rejected audit row and preserves the program.

## Fixture and native boundary coverage

The fixture corpus now covers accepted echo, explicit obstructions, construction-type obstructions,
missing-register witnesses, nested compressed obstruction shadows, shell blocked/unsupported rows,
and optimizer surfaces.

Malformed VAM0 frames stop at decoder/CLI boundaries with stable JSON errors. Native success reports
keep the `vam0-ref-v1` shape.

## Non-claims

VAM v1.0 does not claim:

- dense opcode completeness;
- native optimizer parity;
- Rust speed advantage;
- GPU/FPGA readiness;
- theorem-prover semantics;
- full Core Language quantifier semantics.

Next work should define execution-error taxonomy, dense opcodes, richer theorem/shell objects, and a
native optimizer parity contract.
