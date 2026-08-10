# VAM Compression Optimizer Extension Plan

> **Historical plan:** the bounded optimizer and native parity slices described
> here were subsequently implemented through the versioned contracts recorded
> in `018_native_optimizer_parity_contract.md` and `../native/README.md`.
> Unchecked roadmap language below is not an active release checklist.

## Purpose

Extend the conservative VAM optimizer with compression-specific rewrites while
preserving the current executable contract:

```text
Core source / .vmasm -> IR -> VAM0 -> IR -> optimizer -> interpreter -> certificate
```

The optimizer must remain an auditable semantics-preserving pass, not a heuristic
compression searcher. Every accepted rewrite needs a local reason, and every
unsafe candidate needs a rejection row.

## Current baseline

Implemented optimizer behavior is intentionally small:

- `observer-alias`: remove duplicate `OBSERVER` declarations with the same kind
  and rewrite later uses to the canonical register.
- `dead-shadow`: remove unused `OBSERVE` and `COMPRESS` outputs only when the
  interpreted output is not an `Obstruction`.
- `CERT`, `ECHO`, and `OBSTRUCT` are treated as side-effect/evidence boundaries.

Compression-specific optimization starts from that baseline and must not weaken
obstruction preservation.

## Roadmap phases

### Phase 1 — Compression normal form metadata

Add internal metadata helpers before adding rewrites:

1. classify each `COMPRESS dst, obj, obs` by:
   - source object register,
   - observer register and observer kind,
   - interpreted result kind,
   - whether the result feeds `ECHO`, `CERT`, `OBSTRUCT`, or another `COMPRESS`;
2. compute use/definition information after alias rewriting;
3. record candidate fingerprints in `OptimizationRow.detail` without changing
   behavior yet.

Deliverable: a no-op analysis pass whose report rows can explain what would be
considered compressible.

### Phase 2 — Safe local rewrites

Only enable rewrites that are locally checkable and interpreter-equivalent.
Initial candidates:

1. **Duplicate compression aliasing**
   - Pattern: two `COMPRESS` rows over the same canonical object and canonical
     observer.
   - Rewrite: keep the first destination, alias later destinations to it.
   - Guard: both rows must have single definitions and the first result must not
     be an `Obstruction`.

2. **Compression-after-observer-alias canonicalization**
   - Pattern: `COMPRESS` uses an observer register that has already been aliased
     by `observer-alias`.
   - Rewrite: rewrite the observer argument to the canonical observer register.
   - Guard: no semantic row is removed; only register spelling changes.

3. **Unused successful compression pruning**
   - Pattern: current `dead-shadow` case for unused `COMPRESS` rows.
   - Rewrite: keep as-is but split its audit label into `dead-compress` so tests
     can distinguish compression pruning from generic observation pruning.
   - Guard: interpreted output kind is not `Obstruction`.

4. **Idempotent compression collapse**
   - Pattern: `COMPRESS b, a, obs` followed by `COMPRESS c, b, obs` with the
     same canonical observer.
   - Rewrite: alias `c` to `b` only if a certificate check proves the second
     compression produces the same observable fields as the first.
   - Guard: disabled until the certificate checker can compare observations
     under the same observer kind.

## Rejection rules

A candidate rewrite must be rejected, with an explicit rejected row, when any of
these conditions holds:

- the candidate row or a row it would erase produces an `Obstruction`;
- the destination feeds `ECHO`, `CERT`, `OBSTRUCT`, or any future proof/evidence
  opcode in a way not covered by the rewrite rule;
- the destination has multiple definitions or the source register is redefined;
- observer kinds differ after canonicalization;
- interpreted object kind differs before and after the rewrite;
- object fields relevant to the active observer differ before and after the
  rewrite;
- pass ordering would make the explanation ambiguous;
- the optimizer cannot build a certificate comparison because an input register
  is missing, malformed, or produced by an unknown opcode.

Rejected rows are not failures. They are evidence that the optimizer found a
candidate and deliberately preserved semantics.

## Certificate checks

Each accepted compression rewrite should pass a certificate boundary stricter
than the current structural audit row:

1. execute the original candidate slice and the rewritten slice;
2. compare destination object kind;
3. compare observer-visible fields for the active observer kind;
4. require identical `Echo` acceptance if the destination reaches an `ECHO`;
5. require identical `CERT.accepted` values and claim labels if the destination
   reaches a `CERT`;
6. require identical obstruction presence, claim, and witness if an obstruction
   is reachable;
7. emit a stable audit detail string naming the rule, source registers,
   canonical registers, and certificate comparison result.

For Phase 2, whole-program execute-and-compare is acceptable. Later phases may
replace it with smaller slices, but only after tests prove equivalence.

## Test plan

Add tests before enabling each rewrite:

- duplicate successful compression aliases to the first destination;
- duplicate compression is rejected when either result is an obstruction;
- canonical observer aliases are reflected inside compression arguments;
- compression feeding `ECHO` preserves echo acceptance;
- compression feeding `CERT` preserves certificate acceptance and claim text;
- compression feeding `OBSTRUCT` is never removed or aliased away;
- unknown or malformed compression candidates produce rejected rows, not crashes;
- pass ordering is deterministic across repeated optimizer runs;
- VAM0 round-trip plus optimizer produces the same certificates as direct IR;
- Core lowering examples keep the same `vam_reference_v1` certificate status.

Recommended commands:

```bash
PYTHONPATH=. pytest tests/test_vam_reference.py -q
PYTHONPATH=. pytest tests/test_certify.py tests/test_core_language.py -q
```

Add a focused `test_vam_optimizer_compression.py` once the first compression
rewrite lands, keeping examples small and auditable.

## Non-goals for this extension

- no global optimality claim;
- no lossy compression;
- no native backend-specific rewrite;
- no rewrite that depends on wall-clock timing, random choice, or hash iteration
  order;
- no erasure of failed constructions, counterexamples, or obstruction witnesses.

## Implementation checklist

1. add no-op compression candidate analysis;
2. add tests for rejected obstruction candidates;
3. implement duplicate compression aliasing behind certificate checks;
4. split audit labels for compression-specific dead pruning;
5. add Core/VAM0 certificate regression tests;
6. update this plan only when a new compression rule is accepted or rejected by
   design.
