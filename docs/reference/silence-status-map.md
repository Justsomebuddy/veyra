# Silence-Status Map — one normative correspondence

**Date:** 2026-08-27
**Status:** governance/QA reference (P0 level 4); adds no ontology. The two
doctrine-level additions it records — scoped positive exclusion and the
`ABSENT` homonym resolution — are registered in
`../102_foundational_gap_audit.md` (amendment A3, non-claim 7).

## Why this file exists

Docs 149, 150, 154, 155, 156, and 158 each publish a typed-silence table.
They drifted: tokens were renamed (`RESOURCE_LIMITED` → `RESOURCE_REFUSAL`,
`UNRESOLVED_IN_SYSTEM` → `UNRESOLVED_IN_D` → `UNRESOLVED_IN_DOCTRINE`),
`INCONSISTENT` was demoted from a peer silence row (149 §9) to a separately
certified meta-status (154), and — most dangerously — the token `ABSENT`
acquired two incompatible meanings: **missing evidence** in doc 150
(“absent translation evidence stays `ABSENT`/OPEN”) and **checked exclusion**
in docs 155/156 (“Only checked absence can support a negative phenomenon
claim”; “`ABSENT` — excluded in the stated scope”). Reading one as the other
is the coercion `ignorance → absence`, the first refusal of
`../149_positive_ontology_p0.md`. This file is the single normative
correspondence; the source documents keep their published letter and carry
pointer notes to this map.

## Normative table

The 154 vocabulary is the normative spine (richest, latest reviewed). “—”
means the document has no counterpart row; a document without a row for a
class must not be read as denying the class.

| Normative (154) | 149 §9 | 150 | 155 | 156 | 158 `Obs_D` outcome | Meaning; evidence bar |
|---|---|---|---|---|---|---|
| `RESPONSE_SILENT` | response-silent | — | — | — | `ResponseSilent(mark)` | admitted observer ran, returned its silent value; may itself be positive evidence |
| `INTRINSIC_SILENT` | intrinsic-silent | — | — | — | — | the process is the native silence form |
| `OPERATIONALLY_ABSENT` | operationally-absent | — | — | — | — | no event in an exact finite window; **never** exclusion |
| `EXCLUDED_IN_D_S` | *(deliberately none)* | — | `ABSENT` | `ABSENT` | — | a positive proof excludes it in doctrine `D`, scope `S`; requires checked exclusion evidence; addition registered by 102-A3 non-claim 7 |
| `BLIND_IN_O_S` | — | — | `OBSERVER_BLIND` | `BLIND` | — | observer `O` cannot distinguish the candidates on `S`; a visibility limit, not a fact about the candidates |
| `DOMAIN_BLOCKED` | domain-blocked | — | `OPERATION_UNDEFINED` | `UNDEFINED` | `DomainBlocked(detail)` | operation/interpretation undefined on this input |
| `OBSTRUCTED` | *(first-class obstruction objects)* | — | `OBSTRUCTED` | `OBSTRUCTED` | `Obstructed(detail)` | a named mathematical incompatibility is witnessed |
| `UNOBSERVED` | unobserved | — | `NO_ATTEMPT` | — | — | no admitted observation was requested or performed |
| `EPISTEMICALLY_OPEN` | epistemically-open | `ABSENT`/OPEN *(evidence-absence sense)* | `UNKNOWN` | `UNKNOWN`, `OPEN` | — | neither support nor refutation currently available |
| `RESOURCE_REFUSAL` | resource-limited | — | *(execution tag)* | `RESOURCE` | `ResourceLimited(limit)` | evaluation stopped before semantic judgment |
| `UNRESOLVED_IN_D` | unresolved-in-system | — | `UNRESOLVED_IN_DOCTRINE` | `UNRESOLVED` | — | `D` has no deciding rule; formal independence remains unproved |
| `DIVERGENT` | divergent | — | `NONRETURN`, `DIVERGED` | — | — | execution exceeds its declared termination contract |
| *(meta)* `INCONSISTENT_D` | inconsistent *(peer row; demotion recorded)* | — | — | — | — | separately certified doctrine-level meta-status; never an ordinary positive judgment |

`Ready(response)` in 158 is the success outcome and has no row here. Doc 158
deliberately has no absence or exclusion constructor.

## Binding rules

1. **No coercion.** No token in any table converts to another, to falsity,
   to occurrence, or to nonexistence without an explicit certified rule
   (155’s rule, adopted map-wide).
2. **Evidence-absence never becomes exclusion.** `EPISTEMICALLY_OPEN`,
   `UNOBSERVED`, `OPERATIONALLY_ABSENT`, and `RESOURCE_REFUSAL` license no
   `EXCLUDED_IN_D_S`; only checked exclusion does.
3. **The bare token `ABSENT` is deprecated in future documents.** New text
   must write `EXCLUDED_IN_D_S` (checked exclusion) or
   `EPISTEMICALLY_OPEN`/`UNOBSERVED` (missing evidence). Published documents
   keep their letter; their pointer notes disambiguate.
4. **Extension procedure.** Adding, renaming, or re-partitioning any silence
   row anywhere requires updating this map and appending a
   `102_foundational_gap_audit.md` amendment row in the same change.
5. **Level boundary.** This map is bookkeeping over published vocabularies;
   it introduces no primitive, no judgment semantics, and no promotion.
