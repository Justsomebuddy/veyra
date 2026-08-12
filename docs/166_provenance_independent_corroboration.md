# Provenance-independent corroboration diagnostic

## 1. Question and boundary

Issue #3 separates two questions that are easy to conflate:

1. did several admitted observers agree on one bound claim and scope; and
2. did those observers reach that agreement through distinct decisive support
   routes?

`src.core.observer_provenance` answers only the second question, while retaining
the first as an externally validator-bound input. It does not rerun the
agreement checker and cannot weaken or strengthen an existing scoped agreement
or `objective-in(...)` judgment.

The diagnostic is finite and policy-relative. It is not statistical
independence, causal independence, source truth, complete provenance
disclosure, observer-free truth, or a P2 promotion.

## 2. Typed finite provenance DAG

A `ProvenanceNode` has one exact digest, canonical parents, and one role:

| Role | Meaning in this diagnostic |
|---|---|
| `SHARED_BASIS` | a declared common method, vocabulary, or public basis that may be shared |
| `DECISIVE_SOURCE` | a data/source ancestor whose sharing defeats route independence |
| `DECISIVE_CONTROL` | a control, selection, or decision ancestor whose sharing also defeats route independence |

An `ObserverSupportRoute` binds a distinct observer token to one DAG endpoint.
The bounded graph accepts at most 256 nodes and 64 observers, rejects duplicate
tokens and nodes, missing parents/endpoints, noncanonical parent order, cycles,
wrong exact types, and digest drift.

`ancestry_complete=True` is a declaration about the supplied finite DAG, not an
attestation of reality. With `False`, absence of a shared decisive ancestor
remains `OPEN`; a concrete shared decisive ancestor still yields `REFUTED`.

## 3. External agreement binding

`ScopedAgreementBinding` commits:

- the exact sorted observer family;
- claim, scope, and doctrine roots;
- the agreement receipt and its validator root;
- `ESTABLISHED` or `NOT_ESTABLISHED` agreement status.

The diagnostic verifies the binding's canonical shape and digest and requires
its observer family to equal the DAG route family. Validator identity and trust
remain external.

The output keeps three orthogonal fields:

```text
multi_observer_agreement
provenance_independence = ESTABLISHED | REFUTED | OPEN
independent_corroboration = ESTABLISHED | NOT_ESTABLISHED
```

Independent corroboration is established only when scoped agreement is
established, every observer route contains decisive support, and decisive
ancestry separation is established. A basis-only route therefore remains
`OPEN` even if the submitted DAG is declared complete.

## 4. Clone consensus

The issue's adversarial fixture has two distinct observer endpoints that both
descend from one decisive source root. The exact result is:

```text
multi_observer_agreement = ESTABLISHED
provenance_independence = REFUTED
independent_corroboration = NOT_ESTABLISHED
```

Agreement is preserved. Token multiplicity is not mistaken for root
multiplicity. A companion positive fixture permits a shared `SHARED_BASIS`
while requiring disjoint decisive source/control ancestry.

## 5. Composition and P2 relationship

Claim composition continues to produce only `MULTIPLE_LOCAL_RECEIPTS`.
Composition provenance roots are retained data, not an automatic proof of this
diagnostic. No direct conversion to
`claim_composition.CorroborationStatus.INDEPENDENT_CORROBORATION` exists.

Likewise, the diagnostic creates no P2 rule, claim descriptor, theorem,
certificate, objectivity verdict, or public-wording upgrade. Any future adapter
must separately bind the exact agreement validator, provenance policy, DAG,
scope, and intended conclusion.

## 6. Executable evidence

`tests/test_observer_provenance.py` covers clone consensus, allowed shared
basis, disjoint decisive routes, incomplete ancestry, shared decisive control,
missing agreement, cycles, dangling parents, foreign observer-family bindings,
and assessment drift. These are bounded implementation tests, not proof of a
universal epistemology.
