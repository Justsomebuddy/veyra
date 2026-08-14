# Same-Doctrine All-Status P1-A Realization Transport V2

**Date:** 2026-08-14  
**Status:** bounded executable research contract; no theorem promotion  
**Version/schema:** `p1-r16-p1a-observation-transport-v2`,
`veyra.p1-r16.p1a-realization-transport-receipt.v2`  
**Design:** [RFC 169](169_p1a_all_status_transport_rfc.md)

## 1. Implemented boundary

`src.core.p1a_realization_transport_v2` is a separate, non-root-exported
sibling. It accepts one exact doctrine and `ObserverSourceBinding`, a freshly
reconstructed `STRONG` P1-A judgment, two independently replayed R16 endpoint
witnesses, and one exact v1 realization-context transport receipt. It neither
changes nor reinterprets v1.

The constructor is:

```python
p1a_realization_transport_v2(
    doctrine,
    binding,
    source_context,
    target_context,
    source_witness,
    target_witness,
    context_transport,
    *,
    transport_id,
    p1a_morphism_id,
    fine_observer_id,
    coarse_observer_id,
    projection,
)
```

`verify_p1a_realization_transport_v2(...)` takes the same authoritative inputs
plus a supplied receipt and requires exact equality with a wholly reconstructed
receipt. Exact-type validation rejects subclasses and malformed sibling DTOs.

## 2. Complete observation action

For `Ready(value)`, v2 delegates to the current validated
`translate_response(...)` structural projection and canonicalizes the complete
result.

For `Blocked(obstructions)`, v2 maps every P1-A `LEFT|RIGHT` step to the matching
R11 pair-path step, keeps only obstructions with that complete prefix, strips
exactly the prefix, and preserves code, suffix, order, and multiplicity. Empty
projection is byte-preserving identity. If a nonempty projection keeps nothing,
the selected branch value is unknowable; the action is undefined and the whole
arrow is rejected rather than inventing `Ready` or relabeling `Blocked`.

Each endpoint is freshly observed for every state. The reconstructed
transported-fine bytes must exactly equal independently replayed coarse bytes.
Tag-only and digest-only matches are insufficient.

## 3. Six-payload square

For every v1 graph edge `x -> f(x)`, one commuting row retains canonical bytes
and digests for:

1. source fine;
2. source transported fine;
3. source coarse;
4. target fine;
5. target transported fine; and
6. target coarse.

Both vertical equalities are reconstructed from the P1-A action. Both
horizontal fine/coarse equalities and exact recurrence commitments are bound to
fresh verification of the embedded v1 receipt. Every row is classified only as
`READY_COMMUTES_EXACT` or `BLOCKED_COMMUTES_EXACT`; mixed-status or undefined
rows reject the receipt.

## 4. Partition laws

Source and target fine, transported, and coarse partitions are normalized from
complete canonical payload bytes, not status tags or caller labels. At each
endpoint, transported equals coarse and the raw-fine partition must refine it
through a reconstructed `fine_to_coarse_class_map`.

The v1 graph separately enforces both horizontal pullbacks. The target law is
built over the complete target carrier, including states outside a
non-surjective graph image. No endpoint-local class ordinal or representative
is transported as semantic data.

## 5. Identity and composition

`identity_p1a_realization_transport_v2(...)` uses the validated v1 identity and
empty P1-A projection, so complete ready and blocked bytes are preserved.

`compose_p1a_realization_transport_v2(...)` freshly verifies both children,
requires the first coarse observer to equal the second fine observer, composes
the v1 state graph, concatenates the structural projection paths, and rebuilds
the direct source-to-target receipt from authoritative endpoints. It never
splices child rows. Focused tests compare direct and composed full-payload
results, including nested blocked-path projection.

These finite executable laws do not define a category, functor, natural
transformation, or theorem.

## 6. Integrity, resources, and logs

The transport binds the exact doctrine and source-membership roots, complete
fresh strong-judgment root, validated translation root, endpoint context and
witness roots, v1 morphism and receipt roots, policies, version, and fixed
scope. Rows and endpoint partition laws have separate framed,
domain-separated roots, and the receipt binds their ordered roots plus schema
and scope.

Sibling-specific ceilings are:

| Resource | Ceiling |
|---|---:|
| commuting rows | 256 |
| one canonical retained payload | 262,144 bytes |
| transported payloads at one endpoint | 8 MiB |
| all six retained streams | 32 MiB |
| expanded sibling DTO nodes | 65,536 |
| sibling nonpayload text | 1 MiB |

Existing endpoint limits, v1's independent precharge, 128-byte P1-A IDs,
128-step projection, and R11 obstruction limits remain in force. Validation
charges the 32 MiB six-stream total before row/receipt construction and combines
the shallow sibling graph with all decoded payload nodes under the single
65,536-node ceiling. The 1 MiB counter covers every sibling UTF-8 scalar,
status, policy, kind, path selector, and digest field, but not canonical payload
bytes already governed by the payload/stream caps. Each string is bounded
before encoding.

Validation uses fixed bounded reason codes. The sibling has a local exact
Ready/Blocked encoder and wraps every public authoritative replay in a transient
thread-local logging boundary. Sibling and safe lower records retain fixed
control-flow markers, counts, status names, and short digest prefixes; the
reachable repr/full-root-bearing lower loggers retain only
logger/function/level routing metadata. The redactor is installed before any
pre-existing target-logger filter and removed at call exit without reordering
those filters; the process record factory is never changed. Recurrence and
proposition values, response values, obstruction paths, complete payload bytes,
and full digests are never logged by a public v2 call.

## 7. Public surface

The sibling package exports the exact DTO/enums/error plus:

- `p1a_realization_transport_v2`;
- `verify_p1a_realization_transport_v2`;
- `identity_p1a_realization_transport_v2`;
- `compose_p1a_realization_transport_v2`; and
- `p1a_realization_transport_v2_scope_boundary`.

`src.core.__init__` remains unchanged. The existing
`src.core.realization_transport` facade, v1 DTOs, schemas, digest bytes, and
behavior remain separate and compatibility-pinned.

## 8. Nonclaims

This implementation is finite, same-doctrine, locally replayed evidence only.
It adds no cross-doctrine conversion, vertical closure or cost law, covariant
pushforward, generic R16 descent, category, functor, naturality, formal proof,
certificate, authentication, custody, chronology, performance claim, observer
formation/admission, role, history, birth/token, efficacy, lifecycle
implication, theorem-card entry, or status promotion.

## 9. Evidence map

- package: [`src/core/p1a_realization_transport_v2/`](../src/core/p1a_realization_transport_v2/)
- normal laws: [`test_p1a_realization_transport_v2.py`](../tests/test_p1a_realization_transport_v2.py)
- hostile validation/resources:
  [`test_p1a_realization_transport_v2_adversarial.py`](../tests/test_p1a_realization_transport_v2_adversarial.py)
- frozen cap edges and binding anti-splice:
  [`test_p1a_realization_transport_v2_limits.py`](../tests/test_p1a_realization_transport_v2_limits.py)
- v1/API compatibility:
  [`test_p1a_realization_transport_v2_compat.py`](../tests/test_p1a_realization_transport_v2_compat.py)
- unchanged horizontal v1:
  [document 167](167_realization_context_transport.md)
