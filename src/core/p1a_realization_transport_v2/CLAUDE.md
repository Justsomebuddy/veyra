# P1-A Realization Transport V2 Module

## Purpose

This additive, non-root-exported sibling implements RFC 169 for one exact P1
doctrine and source binding. It combines a freshly reconstructed `STRONG` P1-A
response projection with an independently verified v1 realization-context
transport, then rebuilds every source/target `Ready|Blocked` observation.

## Contract

- `Ready` delegates to the validated P1-A response projection.
- `Blocked` retains only obstructions below the complete structural projection
  prefix, strips exactly that prefix, and preserves code, suffix, order, and
  multiplicity. A nonempty projection that retains no obstruction is undefined
  and rejects the whole arrow.
- Both endpoints are independently replayed for every state. The transported
  fine payload must equal fresh coarse bytes at each endpoint, and mapped
  source/target fine and coarse payloads must commute horizontally.
- Endpoint partitions are normalized from full payload bytes. Transported and
  coarse partitions are equal; the raw-fine partition must refine them through
  an explicit class map. Target-only states remain represented.
- The embedded v1 receipt is freshly verified and binds the exact total state
  graph. V1 DTOs, digests, facade exports, and behavior remain unchanged.
- Identity and composition construct direct fresh receipts; child rows are
  never spliced or treated as authoritative.

## Resource boundary

- 256 sibling rows;
- 262,144 bytes per retained canonical payload;
- 8 MiB transported-payload aggregate per endpoint;
- 32 MiB across all six retained sibling streams;
- 65,536 expanded sibling DTO nodes; and
- 1 MiB nonpayload sibling text.

Existing endpoint, P1-A projection/obstruction, and embedded-v1 bounds remain
independently authoritative. The six-stream charge precedes row/receipt
construction; the node ceiling combines shallow DTO and decoded JSON nodes;
the UTF-8 text ceiling covers all sibling scalars but excludes separately
bounded canonical payload bytes. Logs contain only fixed reason codes, counts,
statuses, and short digest prefixes—not recurrence, response, or obstruction
payloads. The local observation encoder avoids repr-bearing codecs, and a
thread-local public-call boundary reduces every authoritative lower-layer log
that can carry repr/full roots to fixed logger/function/level metadata. It
installs before pre-existing target-logger filters, removes itself at call exit
without reordering those filters, and never replaces the process record factory
or changes lower modules.

## Nonclaims

No cross-doctrine transport, vertical closure/cost law, category, functor,
naturality, theorem, certificate, formation, role, chronology, history token,
efficacy, lifecycle implication, or promotion is created.

## Files

- `types.py`: exact immutable sibling DTOs and enums.
- `digest.py`: framed domain-separated roots.
- `observation.py`: exact all-status response action.
- `log_boundary.py`: thread-local authoritative lower-log redaction.
- `partitions.py`: byte partitions and vertical refinement maps.
- `validation.py`: exact-type, canonical-byte, root, and resource snapshots.
- `runtime.py`: fresh endpoint replay, construction, and verification.
- `composition.py`: fresh identity and composition builders.
- `public.py`: narrow sibling facade and explicit scope boundary.

## Version

Sibling contract v2 (`p1-r16-p1a-observation-transport-v2`); implementation
revision 2.0.1. Shallow exact/resource preflight precedes comparisons, copying,
JSON decoding, or child dereference; public builders normalize lower failures
to the sibling validation error.
