# Veyra Magic M1

**Status:** bounded audit, not a superiority claim.  
**Implementation:** `src/core/surprise/veyra_magic.py`, `src/core/observer/synthesis.py`, `src/core/certificates/veyra_magic.py`.
**Certificate:** `veyra_magic_m1`.

## Thesis

The current magic of Veyra is not speed or a universal classical-impossibility theorem.

The current magic candidate is:

```text
observer synthesis: find the observer under which an object becomes simple,
explanatory, or blocked.
```

The candidate is now executable rather than only methodological. A typed finite
grammar enumerates observer ASTs by cost, fits without a holdout argument, locks
the winner plus evaluator/config semantics, and validates it on a payload-disjoint
split without reranking. Failures, noncanonical responses, nondeterminism,
ID/group/payload leakage, protocol substitution, and “not found in this budget”
are explicit obstructions.

The current parity witness synthesizes `histogram(xor-rows(input))` on an even
4-cube training pair and validates it on an odd 5-cube holdout. Proper-subset
marginal baselines are blind on both. The strength gate requires exact winner-AST
membership in the executable extended class. This is a bounded classical parity
result, not a universal synthesis algorithm.

## Audit rows

| Row | Name | Verdict | Evidence |
|---|---|---|---|
| `M1-OBSERVER-SYNTHESIS` | observer synthesis | strongest current magic candidate | real R5 train/holdout synthesis plus R6 scoped class certificate |
| `M2-OBSTRUCTION-AS-DATA` | obstruction ledger | active magic candidate | Q7 and coverage |
| `M3-HIDDEN-ORDER-PRESSURE` | hidden order pressure | active magic candidate | S3/S5/S6 |
| `M4-ANTI-MAGIC-GUARD` | anti-magic guard | truth maintenance | F5, Q3, F1/F3 |
| `M5-NO-ADVANTAGE-YET` | blocked advantage claim | blocked claim | gap audit and surprise docs |

## Non-claim boundary

This audit does not claim global superiority, speedup, quantum advantage, or universal classical impossibility. It says only that the most
promising Veyra-specific object is the executable calculus of observer switches
and obstruction logs.

## Verification

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. python3 -m pytest -q tests/surprise/test_veyra_magic.py tests/shadows/test_certify.py
the complete verification suite
```

Expected signal: `veyra_magic_m1` reports `validated`, winner
`histogram(xor-rows(input))`, scoped strength true, and `overclaims = 0`.
