# Theorem and Definition Registry

This index and its linked bounded modules form the self-contained publication
registry. This root file defines the status vocabulary, module map, and critical
release boundaries; no untracked or local history is required.

## Status vocabulary

| Status | Meaning |
|---|---|
| `AXIOM` | Declared premise of a named Veyra layer; not inferred from earlier rows. |
| `CONJECTURE` | Mathematical statement not established by the listed evidence. |
| `EXECUTABLE_EVIDENCE` | Finite computation/tests support only the stated bounded claim. |
| `FORMALLY_PROVED` | Lean checks the exact declaration in the listed source. |
| `FORMAL_CONSTRUCTION` | Lean checks a definition carrying all required proof fields. |
| `PUBLICLY_VALIDATED` | Public aliases, validation evidence, and a release-bundle certificate are present. |
| `INTERNAL_RESEARCH_CANDIDATE` | Formal or executable source exists, but public release evidence is intentionally absent. |
| `OPEN` | Required premises or evidence are not established. |

A formal theorem may still be conditional on its arguments and imported
premises. `FORMALLY_PROVED` never implies physical truth, observer-independent
objecthood, unrestricted infinity, or a stronger theorem than the exact Lean
type. `EXECUTABLE_EVIDENCE` is not silently promoted to formal proof.

## Registry modules

The registry is split into bounded public modules. Together these files are the
complete registry; no local history is required.

| Module | Contents |
|---|---|
| [Historical core](docs/reference/theorem-registry-core.md) | axioms, definitions, theorems, conjectures, and counterexamples through 1.3.0 |
| [Additions 1.4.0–2.2.0](docs/reference/theorem-registry-additions.md) | processed-artifact definitions and propositions |
| [Definitions 059–115](docs/reference/theorem-registry-definitions-059-115.md) | transformers, completion, geometry, registries, curriculum, and finite statistics |
| [Definitions 116–176](docs/reference/theorem-registry-definitions-116-176.md) | depth packs, Sage facades, Core Language, proof traces, and coverage |
| [Active registry from DEF-177](docs/reference/theorem-registry-active.md) | native resonance, formal bridges, observer doctrine, completion, and prime-power families |
| [Exact formal evidence](docs/reference/theorem-registry-formal-evidence.md) | every named Lean declaration with status, dependencies, and source location |

## Publication-critical status summary

- N3 and N4 are `FORMALLY_PROVED + PUBLICLY_VALIDATED`; their formal sources,
  public aliases, certificates, and release-bundle entry are present.
- N0, N6, and N6-W are `INTERNAL_RESEARCH_CANDIDATE`. Lean declarations in
  those families are research evidence, not public theorem releases.
- `PΩ1` and `PΩ2` assert completed carriers only relative to their explicit
  formation rules and assumption ledgers.
- Candidate, executable, validated, and formally proved are distinct statuses;
  none is silently promoted into another.
- DEF-710–716 adds a structural bridge/separation ledger and bounded G4
  quotient-conflict classification. Its exhaustive `n≤3`/Sage evidence and two
  digest-bound Lean helpers do not add registered theorem cards or imply a
  general sheaf/descent, novelty, nonexpressibility, or superiority result.
