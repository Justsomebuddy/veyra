# Native observer synthesis v2: profiles, transport, custody, and replay

**Status:** bounded Rust implementation plus an abstract Lean research slice.  
**Public claim class:** finite executable calibration; the four Lean lemmas are
`INTERNAL_RESEARCH_CANDIDATE`, not a proof of the Rust implementation.

## 1. Immutable and extended grammars

The original `r14-tail-crest-pair-v1` profile remains immutable. Its legacy
entry point still returns the exact pinned catalog:

```text
strata       [1, 3, 8, 27, 104, 358, 1064]
candidates   1,565
bytes        488,550
max row      338 bytes
catalog      23408184aba5d55d283e4a9440e1859beaefa9d73a909d283057d59b527437cf
```

Old `Input`/`Tail`/`Crest`/`Pair` canonical bytes retain schema
`veyra.observer-core.v2`, so existing receipts do not change. The separately
identified `r14-tail-crest-parity-pair-v2` profile adds the total recurrence
primitive `Parity`. Expressions containing it use schema
`veyra.observer-core.v3`; its catalog is independently pinned at 230 rows,
52,154 bytes, and digest
`6aa5cc4e0f386083a8b0bf5a4845099e232ab1fd939fecaf6ad2e65cb88430cf`.
The legacy and parity profile digests are respectively
`c0c6b1706a73655c9438a7249d0bad2ea4ad9c6c39a8078d2d1f35b47209d63e`
and `9ffad357ca724932ffafee3b11e47c81f88dd73c3b7415e3fccebc1748eb089b`.

Profile and catalog identities define two closed languages. V2 does not claim
that `Parity` is canonical, minimal, scientifically explanatory, or complete.

## 2. Systematic representation family

The declared family is the exact Cartesian product of unary shifts `0..4` and
all 24 lexicographic permutations of four abstract states: 120 transforms.
Every transform has canonical bytes, a digest, and cost
`shift + inversion_count(permutation)`. That cost is a search convention, not
physical, statistical, or ontological distance. The complete ordered family is
pinned by digest
`dbba66299481323f4621af7a896fb8486e14199a9ce0e2cd1f7cbf8acee62bad`.

`survey_representation_family` evaluates one fixed catalog observer on all 120
encodings, groups transforms by the complete six-obligation satisfaction table, and
binds the class membership/order in a survey digest. For `Parity(Input)` on the
XOR partition, the survey obtains three exact obligation-result classes and 40/120
preserving transforms, bound by survey digest
`f1b3d0a5313a82ae4fb5490ec56b8180a8c14e5374778d345449c96e3e3c148b`.
This is exhaustive only for the declared family.

The six booleans record whether each obligation is satisfied; they are not a
quotient by full semantic outcomes or obstruction reasons. For this published
survey `Parity(Input)` is total, so that distinction does not alter the result.

## 3. Joint transform/observer synthesis

`synthesize_transform_and_observer` searches the finite product using the key:

```text
(joint cost, transform cost, observer cost,
 transform ordinal, observer ordinal)
```

Transform, candidate, pair-attempt, and six-relation evaluation-charge counters
are bound separately. Six units are atomically precharged per pair even if a
mismatch lets evaluation return early; the field is a safe upper-bound charge,
not a measurement of short-circuited runtime calls. A counter cutoff returns `INCOMPLETE`; `EXHAUSTED` is emitted
only after traversing the complete admitted product.

For the XOR task, legacy V1 exhausts all `120 × 1,565` pairs. Parity V2 finds
the first minimum-cost pair at joint cost 2: transform ordinal 1 (permutation
`[0,1,3,2]`, cost 1) and `Parity(Input)` (observer ordinal 2, cost 1), after 22
pair attempts and 132 precharged relation evaluations. Identity plus
`Parity(Input)` does not fit the declared XOR labeling; the transform is a real
part of this bounded witness, not presentation decoration.

## 4. Isolated worker and physical custody

`vam-observer-worker` accepts one bounded canonical binary request and runs the
fixed v2 evidence build in a child process. On Linux, the child establishes and
reads back `RLIMIT_CPU`, `RLIMIT_AS`, and `RLIMIT_CORE=0`; the parent owns a
separate process group, drains bounded stdout concurrently, enforces a wall
deadline, and kills/reaps the group on failure. Request and receipt frames bind
the configured physical ceilings and actual custody flags. The child emits only
an internal `CustodyPending` result; only its supervising parent can add the
wall-clock/process-group facts and mint a terminal `Ready` receipt. Direct child
invocation therefore cannot self-assert parent custody.

The default hard ceilings are 10 CPU seconds, 30 wall seconds, and 512 MiB of
address space. They accommodate contended shared runners and are resource
ceilings, not performance claims; callers may choose stricter admitted values.

The parent checks the exact v2 artifact size and pinned receipt-domain digest
before promotion without repeating synthesis outside the child's limits.
The executable path remains a caller-selected local trust input: this layer
does not attest executable bytes, and the child's RLIMIT readback is accepted
only within that stated local executable boundary.

The profile is deliberately named `LinuxRlimitV1`. It is **not** seccomp,
filesystem/network isolation, a namespace, a container, a VM, trusted time, or
remote custody. `Strict` and non-Linux physical custody fail closed instead of
being emulated. Protocol counters and OS ceilings remain distinct evidence.

## 5. Portable authenticated replay

The portable VORP package contains the exact worker request and receipt,
canonical payload/receipt digests, a caller-declared signer identifier, and an
HMAC-SHA256 tag under an externally supplied key. The key is never serialized,
persisted, or logged. Decoding is bounded and rejects partial, trailing,
oversized, noncanonical, or malformed frames. Validation freshly rebuilds the
bound native evidence; executable replay launches the worker again and requires
byte-exact receipt equality. The atomic v2 evidence payload is pinned at 1,941
bytes with receipt digest
`0202c63f78ff8db0ea590591d0f8c338dc566c7bcfe5cc99d0814962b64c88c5`.

HMAC provides shared-key integrity and key-possession authentication. It is not
a public-key signature, public verifiability, nonrepudiation, signer trust,
trusted chronology, source truth, or theorem evidence.

## 6. Lean boundary

`proofs/lean/VeyraObserverSynthesisReplay.lean` proves four abstract facts with
no axioms:

1. successful functional replay implies that rebuild returned the bound evidence;
2. functional replay is deterministic;
3. an explicitly supplied bijective encoding preserves the pulled-back target;
4. finite-catalog exhaustion is equivalent to absence of an accepting list member.

The module does not formalize Rust, canonical binary/JSON encoding, SHA-256,
HMAC, CEGIS, catalog completeness, process custody, or any concrete benchmark.

## Verification boundary

Focused gates cover Rust formatting/check/tests, pinned Lean compilation,
source/package inventory, documentation references, hostile protocol/replay
tests, portable package lanes, hygiene, and diff integrity. The multi-hour
`make verify` is intentionally outside this wave.
