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

Lane-local judgment tokens (`ESTABLISHED`, `REFUTED`, `ABSENT`, `QUALIFIED`, …)
and provenance classes (`FORMALLY_DERIVED`, `ASSUMED`; see
`docs/reference/notation-extended.md` and
`docs/reference/silence-status-map.md`) are orthogonal vocabularies, not rows of
this table: they carry no registry status, imply no promotion, and must not be
read as adjacent to `FORMALLY_PROVED`.

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
- PΩ1 and PΩ2 are likewise `FORMALLY_PROVED + PUBLICLY_VALIDATED`: root
  aliases (`POMEGA1_*`/`pomega1_*`, `POMEGA2_*`/`pomega2_*`), certificates,
  and release-bundle entries are present. Four PΩ1 bridge declarations
  (`THM_POMEGA1_012`–`015`) are runtime-generated and digest-pinned, not
  repository Lean files (see `proofs/lean/README.md`, "Generated bridge
  declarations"); the ledger-relative carrier boundary below is unchanged.
- N0, P3-OG, N6, and N6-W are `INTERNAL_RESEARCH_CANDIDATE`. Lean declarations
  in N0/N6/N6-W and executable P3-OG machine/raw-cycle first-return pressure
  rows are research evidence, not public theorem releases or a historical
  formation judgment.
- `PΩ1` and `PΩ2` assert completed carriers only relative to their explicit
  formation rules and assumption ledgers.
- Candidate, executable, validated, and formally proved are distinct statuses;
  none is silently promoted into another.
- DEF-710–716 adds a structural bridge/separation ledger and bounded G4
  quotient-conflict classification. Its exhaustive `n≤3`/Sage evidence and two
  digest-bound Lean helpers do not add registered theorem cards or imply a
  general sheaf/descent, novelty, nonexpressibility, or superiority result.
- DEF-717–723 records declared adaptive research lines and the exact
  independent-null retry inflation witness. Its Python/Sage arithmetic is
  executable counterpressure, not a registered theorem, verified adaptive
  policy, significance license, or population claim.

## Experimental research Lean appendix

The ten files under `experimental/research_lean/` contain 87 manifest-bound
declarations (41 headlines) with status `INTERNAL_RESEARCH_CANDIDATE`. They are
not stable registry IDs, do not change any X8 card, and do not promote
THM-001–003 from `CONJECTURE` or close W-001. The one-tact bridge is restricted
to the explicit singleton-generated path-word realization and exact R9 image;
it is not an AX-007 exhaustion theorem or a general Mode equivalence. The
native-number bridge only carries ready-mode tact count into stable THM-F002;
it is not prime infinitude, Fermat, a third theorem-derived layer, or R8
promotion. Exact observed axiom closures are in the candidate manifest; compilation is not
public validation or a native Veyra proof.
