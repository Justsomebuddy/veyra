# Native observer synthesis v5: proof-carrying discovery and strict custody

## Status and claim boundary

V5 is an append-only experimental layer over the frozen v1–v4 contracts. It
adds finite scientific calibration, a versioned observer language,
proof-carrying branch-and-bound, a stricter Linux worker, threshold-authenticated
replay, and a narrow abstract Lean model. It does not establish causal or
scientific discovery, universal optimality, a complete observer language,
trusted identity/time/source, executable attestation, or verification of Rust
by Lean.

Every `FOUND`, `EXHAUSTED`, observer gap, alternative count, and pruning claim
is relative to one exact task, grammar profile, catalog order, cost definition,
and resource limit. `CUTOFF` is never negative evidence.

## Versioned grammar and generated calibration

The v5 profile appends 2,048 typed observers over sixteen finite states after
the unchanged v1 registry root:

- affine bit-parity terms; and
- affine reflection-orbit terms.

Profile, catalog, candidate order, response tables, and extension receipt have
separate domain-separated roots. The earlier registry bytes and public APIs are
not rebound.

The deterministic synthetic family generates declared targets from
domain-separated generators rather than embedding winning answer tables. It
covers hidden affine structure, reflection symmetry, recovery through a
nonidentity affine permutation of represented states, and a
catalog-diagonalized negative control. The recovery task binds both that
represented-state permutation and its target classes; its recovered observer is
therefore genuinely distinct from the hidden-affine task rather than merely
carrying a different label. A held-out row, when present in the pinned family,
uses a separately declared generator domain and is excluded from calibration
selection. This is reproducible synthetic held-out calibration—not empirical
validation, statistical generalization, unknown-variable recovery in nature,
or novelty evidence.

## Proof-carrying branch-and-bound

The optimized engine searches candidates in the pinned monotone order
`(intrinsic cost, catalog ordinal)`. After the first minimum exact-partition
witness, every remaining row at the incumbent cost is still evaluated to count
same-cost alternatives. A suffix can be pruned only when its first declared
cost is strictly greater than the incumbent. The result binds:

- the admitted catalog and lower-bound digest;
- evaluated and pruned pair-disposition counts;
- incumbent and first-pruned lower bound;
- an admissibility flag and canonical prune-proof digest;
- winner ordinal/digest/cost, observer gap, same-cost alternatives, and
  representation/explanation/witness roots.

A separately implemented exhaustive path uses independent admission/counting
arithmetic and canonical-partition comparison. The proof verifier independently
reconstructs the winner-cost frontier, same-cost evaluations, and strictly
higher-cost pruned suffix from the request, represented task, and catalog; it
does not accept the producer's split as an assumption. Bounded differential
tests require the same terminal, winner, task/profile/catalog bindings, and a
fresh optimized proof replay. `EXHAUSTED` means every cost-admitted row in this
exact finite catalog was evaluated; it says nothing about other grammars.

The observer gap in this v5 surface is a declared catalog-cost gap from the
admitted cost floor. It is not a likelihood ratio, information-theoretic
quantity, causal effect, or population statistic.

## Strict Linux worker v5

The strict profile is Linux x86-64 only and fails closed unless the caller
provides both a writable delegated cgroup-v2 root and a rootfs mount base. Its
setup handshake requires the parent to attach the child to the exact cgroup
before the child promotes custody. The child then applies the inherited v2/v4
limits and constructs:

- fresh user, mount, network, IPC, and UTS namespaces;
- private mount propagation;
- a bounded `nosuid,nodev,noexec` tmpfs root;
- `pivot_root`, detached old root, and empty-root readback;
- the pinned seccomp allowlist; and
- exact CPU, memory, PID, and membership readback.

The parent independently rereads namespaces, no-new-privileges/seccomp,
mount/root state, cgroup controls and membership. It owns wall time, bounded
output, process-group custody, cgroup empty-leaf removal, and rootfs cleanup.
Only a fully verified private discovery-v5 receipt can construct an executed
VOR5 package, and its exact request/result bytes and roots must match the
package. Portable verification authenticates this receipt binding; it does not
revalidate the historical OS controls or provide executable attestation.

The conditional cgroup harness reports `PASSED` or explicit `UNAVAILABLE`.
`UNAVAILABLE` covers valid host capability/delegation failures: an ordinary
nondelegated system cgroup mount, required controller/subtree state that cannot
be read or enabled, and kernel/delegation refusal of fresh leaf or control
operations. It does not convert invalid limits, nonexistent or out-of-mount
roots, non-directory roots, mismatched control readback, or harness program
failures into availability results; those remain fail-closed errors.
Its abnormal cleanup rows cover immediate `SIGKILL` and `SIGSEGV`; the
`SIGKILL` row is not labeled or presented as a deadline/timeout experiment.
Configuration readback and cleanup do not prove workload-level CPU throttling,
intentional OOM behavior, PID exhaustion resistance, protection from a hostile
kernel, or remote attestation. On a host without delegated cgroup ownership the
success lane is not claimed.

## Threshold-authenticated autonomous replay

VOR5 signs a bounded canonical package containing:

- exact v5 request and result bytes and roots;
- the prune-proof root;
- bounded source and toolchain digest declarations;
- optional strict-worker receipt/policy and exact request/result roots; and
- the complete payload digest.

An external trust policy supplies at most sixteen Ed25519 public keys, inclusive
rotation-epoch windows, and a threshold. The epoch is a caller-selected
coordinate, not trusted wall time. Signatures are unique, sorted, bounded, and
verified before semantic decoding. The state-free verifier then decodes exact
canonical request/result bytes and freshly rebuilds the branch-and-bound proof.

`vam-observer-replay-v5 verify-threshold` reads one package from standard input
and takes only public trust-key specifications on its command line. Signing
keys are never accepted as command-line arguments by this verifier. Library
construction remains available for controlled producers.

Authentication proves possession of enough configured private keys over exact
bytes. It does not identify signers, establish trusted chronology, validate the
truth of manifest declarations, or turn executable evidence into a theorem.

## Lean boundary

`proofs/lean/VeyraObserverSynthesisV5.lean` provides four axiom-free conditional
results:

1. an admitted lower bound cannot hide a cheaper represented candidate;
2. a visited-or-admissibly-pruned cover establishes finite-catalog cost
   completeness;
3. an explicitly supplied transport with inverse and preservation laws retains
   the declared acceptance predicate; and
4. exact rejection of every row in a supplied finite list excludes an accepted
   row in that list.

The model assumes the lower-bound, cover, and transport laws. It does not prove
that the Rust ledger satisfies them, parse VOR5 bytes, verify Ed25519 or Linux
controls, establish concrete catalog completeness, or register a public
`THM_*` result.

## Focused verification

The maintained focused evidence comprises exact Rust 1.83/current formatting,
all-target checks and v5 integration tests; v3/v4 compatibility tests; the
pinned Lean source/inventory with axiom reports; focused Python documentation
and metadata tests; portable CI; hygiene, line-count, public-content, and diff
checks. The multi-hour aggregate `make verify` is intentionally outside this
wave unless separately requested.
