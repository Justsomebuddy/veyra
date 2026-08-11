# Native observer-synthesis core

**Status:** bounded Rust parity implementation, not a backend promotion.  
**Implementation:** `vam/native/src/observer_synthesis/`.  
**Oracle:** Python R11 and R14.1/R14.3b modules remain authoritative.

## Scope

The native crate now contains a closed finite observer synthesizer rather than
only an executor for caller-supplied `OBSERVER` instructions. Its first scope is
deliberately restricted to:

1. the R11 `Input | Apply(Tail|Crest) | Pair` AST and response-kind rules;
2. byte-exact canonical observer identities;
3. the exact R14.1 cost-six/depth-four ordered grammar;
4. finite unary-recurrence observation and echo;
5. monotone counter precharges; and
6. deterministic train-only R14.3b CEGIS with a native-domain-separated
   counter-only trace binding.

It does not modify `vam0-ref-v1`, VAM0/VAMD/VAMI decoding, optimizer behavior,
Python certificate paths, or default backend selection.

## Exact grammar parity

The native dynamic program constructs candidates by exact constructor cost,
derives their response kind, and sorts each stratum by `(depth,
canonical_bytes)`. Both orders of every product are retained. The default
constructor verifies these Python-bound pins:

```text
strata             1 / 3 / 8 / 27 / 104 / 358 / 1064
candidates         1565
canonical bytes    488550
maximum row bytes  338
catalog digest     23408184aba5d55d283e4a9440e1859beaefa9d73a909d283057d59b527437cf
```

The canonical writer is explicit and dependency-free. It neither relies on
map iteration nor serializes Rust debug output. Its SHA-256 implementation is
covered by standard empty/`abc` vectors and the Python observer/catalog roots.

## Native semantics and CEGIS

The recurrence domain is the finite closed `Silence`/unary-`Pulse` fragment.
`Tail(Silence)` returns a typed obstruction, `Crest` returns the native
silent/pulse mark, ordered pairs preserve response order, and blocked results
never become echo.

The training algorithm precharges the complete catalog, activates the first
training case, scans candidates in fixed ordinal order, adds the first failing
unused training case as a counterexample, and locks the first candidate that
satisfies every active obligation. The exact default calibration is:

```text
events        SEED / COUNTEREXAMPLE / WINNER
ordinals      0 / 0 / 1
winner        Crest(Input)
traversed     2
evaluations   6
trace digest  44507b59459a501a286d2a259f3ebd16d986e8c28f718fa38cd103cc74aeaa95
```

The native trace intentionally does not reuse the Python R14.3b digest. The
Python receipt binds a five-second wall limit and 512 MiB process-address-space
limit enforced by its worker boundary; this in-process Rust library currently
enforces only deterministic counters. Its limits record therefore binds
`wall_clock_enforced=false` and `process_as_enforced=false` under a distinct
schema. Equal catalog/winner identities do not imply equal execution custody.

Terminal states remain disjoint: `Found`, `Exhausted`, `Incomplete`, and
`Invalid`. A counter cutoff cannot become exhaustion, and an impossible
training obligation returns exhaustion only after all 1,565 candidates have
been evaluated.

Native diagnostics are opt-in through `VEYRA_NATIVE_DEBUG`. They expose only
bounded static lifecycle, rejection, cutoff, and terminal-state labels on
stderr; recurrence values, observer payloads, canonical bytes, and digests are
never logged. Normal library use remains silent.

## Present boundary

This slice intentionally omits:

- R14.4-R14.6 equal-resource trials, baselines, receipts, and aggregate suite;
- a cache authority or isolated worker/process supervisor;
- wall-clock and address-space enforcement inside the library;
- holdout, unseen, and adversarial split execution;
- statistical observer discovery and Phase-II/III governance;
- a CLI or Python-to-Rust production dispatch;
- a whole-correctness proof, certificate registration, theorem promotion,
  general completeness/minimality, novelty, superiority, or speed claim.

Those omissions prevent a silent claim that a matching finite calibration has
already replaced the hardened Python protocol. A future worker integration
must fail closed on any Python/Rust mismatch and must be reviewed separately.

## Verification

Focused native verification is:

```bash
cargo fmt --manifest-path vam/native/Cargo.toml --all -- --check
cargo test --manifest-path vam/native/Cargo.toml --locked
```

The unit suite binds SHA-256 vectors, canonical observer roots, all catalog
pins, R11 obstruction paths, monotone sticky budgets, deterministic default
replay, cutoff-to-incomplete behavior, exact exhaustion, and invalid inputs.
