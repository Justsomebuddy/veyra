# 143 — Bounded topological observer-gap theorem

## Claim boundary

This note records one finite separation theorem card, `THM-S7-001`. It is a
five-row exact computation, not a claim about all directed acyclic graphs, an
optimal observer, automated discovery, or superiority over classical methods.

## Declared observer classes

The **S7 degree-factor baseline class** contains exactly the deterministic
observers that factor through this complete signature:

1. number of labelled vertices;
2. number of directed edges;
3. the sorted multiset of `(in-degree, out-degree)` pairs.

Therefore two graphs with equal signatures are indistinguishable to every
observer in that declared factor class, including arbitrary deterministic
postprocessing of the signature.

The **S7 extended class** may additionally inspect the exact number of
topological orders (linear extensions). No claim is made that this extension is
minimal or generally preferable.

## Witness pair and finite family

Both base DAGs have four sources, four sinks, eight edges, source degree
`(0,2)` four times, and sink degree `(2,0)` four times.

- `cycle-incidence-8` connects the two layers as one alternating eight-cycle.
- `split-square-incidence-8` is the disjoint union of two `K₂,₂` incidence
  components.

Their declared baseline signatures are identical. Exact subset dynamic
programming gives respectively `1,088` and `1,120` topological orders.

Adjoining `t` distinct isolated vertices multiplies either count by
`(8+t)!/8!`, while adding the same `t` copies of degree `(0,0)` to both
signatures. The executable card checks only `t ∈ {0,1,2,3,4}`:

| `t` | cycle-incidence orders | split-square orders | baseline equal | separated |
|---:|---:|---:|:---:|:---:|
| 0 | 1,088 | 1,120 | yes | yes |
| 1 | 9,792 | 10,080 | yes | yes |
| 2 | 97,920 | 100,800 | yes | yes |
| 3 | 1,077,120 | 1,108,800 | yes | yes |
| 4 | 12,925,440 | 13,305,600 | yes | yes |

## Theorem card

**`THM-S7-001` — Degree-factor blindness under bounded isolated extension.**
For each checked `t`, the two named DAGs extended by `t` labelled isolates
have equal S7 baseline signatures and unequal exact topological-order counts.
Consequently exact topological-order count does not factor through the declared
baseline signature on this five-row corpus.

The proof artifact is executable exact enumeration over at most 12 labelled
vertices. It does not establish an all-`t` formal theorem, uniqueness,
minimality, or any universal observer limitation.

## Executable artifacts

- `src/core/observer/gap_topology.py`
- `src/core/certificates/observer_gap_topology.py`
- `tests/observer/test_observer_gap_topology.py`

Targeted check:

```bash
pytest -q tests/observer/test_observer_gap_topology.py
ruff check src/core/observer/gap_topology.py tests/observer/test_observer_gap_topology.py
```
