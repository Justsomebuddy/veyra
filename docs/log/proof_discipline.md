# Veyra Proof Discipline Layer

**Date:** 2026-06-03
**Status:** Sprint F closed as executable coverage layer.
**Implementation:** `src/core/registry/proof_discipline.py`, `veyra_sage/proof_discipline.py`.
**Certificate:** `proof_discipline` in `src/core/certify.py`.

## What this closes

Proof discipline is the anti-self-deception layer.  It does not prove all Veyra mathematics.  It proves that the current kernel can expose:

- proof-step coverage by rule name;
- source-span coverage for checked steps;
- semantic-domain coverage for arithmetic, geometry, logic, analysis, topology, probability, and statistics shadows;
- model/consistency notes for primitive families;
- formal-prover export gates only for stable theorem cards.

This is **governance/QA**, not ontology. Tests, certificates, fuzzing, coverage,
reproducibility, and counterexample pressure regulate trust in claims; they do
not make those claims facts about reality. P0's canonical ontology/semantics/
epistemology split is in `../concepts/positive_ontology_p0.md`, and the standing
non-claim gate remains `../concepts/foundational_gap_audit.md`.
The strict philosophical P1 contract now has bounded level-1 slices through
P1-A2/B/C1/C2/D1/D2/E1. C2's evidence under registry `86` justifies only exact declared finite-catalog confluence. D2's ordered five-row certificate and named Lean basis justify exactly two evidence insufficiencies
and three countermodels—not generator nonexistence, D3 all-depth introduction,
completion, or PΩ. Immutable I1-77 verification does not cover this later tree.

## Executable rows

| Row family | Function | Current signal |
|---|---|---|
| Rule coverage | `proof_rule_coverage()` | 7 rules, 28 steps |
| Rule summary | `proof_rule_coverage_summary()` | 3 blocked-rule families |
| Semantic domains | `semantic_domain_coverage()` | 7 declared domains, 7 certificates |
| Primitive models | `primitive_model_notes()` | 10 primitive families |
| Stable exports | `stable_formal_export_rows()` | 19 stable theorem cards |
| Sprint summary | `proof_discipline_summary()` | `{rules:7, steps:28, domains:7, domain_certs:7, models:10, exports:19}` |

## Rule/span coverage

The default source set deliberately includes ready, blocked, unknown, shell, and parse-failure cases:

```text
echo(nod:a,nod:b,observer:kind)      # ready
echo(nod:a,nod:b,observer:trace)     # blocked
echo(nod:a,nod:b,observer:alien)     # unknown
shell(echo(...kind),echo(...trace))  # composed blocked shell
echo(nod:a,nod:b,observer:kind       # grammar.parse failure
```

This makes `grammar.parse`, `kind.*`, `infer.echo`, and `infer.shell` visible as named coverage rows instead of hidden interpreter behavior.

## Semantic-domain coverage

Human school domains remain shadows, not native truth. A row is accepted only when its required observer keys are present and the shared trace-mismatch counterexample remains blocked.

| Domain | Required shadow keys |
|---|---|
| arithmetic | `length` |
| geometry | `boundary` |
| logic | `status` |
| analysis | `length`, `variation` |
| topology | `component_count`, `deformation_class` |
| probability | `sample_space`, `sample_size` |
| statistics | `sample_size`, `support_size` |

See `docs/log/semantic_shadow_certificates.md` for the X1 certificate rule.

## Primitive model notes

Current model notes cover: `rez`, `nod`, `tact`, `breath/mode`, `echo`, `obstruction`, `shadow`, `cycle-echo`, `balance/ratio`, and `compression`.

Each note has:

- native primitive name;
- intended model;
- consistency condition;
- executable witness;
- status `model-noted`.

## Formal-prover export gate

`stable_formal_export_rows()` only emits theorem specs with:

1. non-`pending` Sage hook;
2. no missing dependencies;
3. status `stable-card-only`.

Current count is 19 rows. X7 mirrors them into `formal_export_prep_x7`; X8 promotes all nineteen finite cards and leaves 0 prep-ready, with no general continuity/derivative/integration/chord/trigonometry/geometry/statistics/probability/measure/combinatorics theorem.

## Sage-facing lab

```python
from veyra_sage.all import VeyraProofDisciplineLab

lab = VeyraProofDisciplineLab()
lab.summary()
lab.rule_coverage_rows()
lab.semantic_domain_rows()
lab.primitive_model_rows()
lab.stable_export_rows()
```

`build_proof_discipline_notebook()` provides an in-memory notebook smoke artifact for the same layer.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/proof/test_proof_discipline.py tests/sage/test_veyra_sage_proof_discipline.py tests/shadows/test_certify.py tests/kernel/test_essence_core.py tests/sage/test_veyra_sage.py
python3 scripts/certify_veyra.py
python3 scripts/sage_smoke.py
```

Expected signals after Sprint F:

- full test suite: 304 passing tests;
- certificates: 20/20 passing at Sprint F baseline;
- Sage smoke: `sage_proof_discipline_passed=True`;
- Essence/Core: 13 ready layers at Sprint F baseline; later calculus-depth raises this to 14.

## Next

Sprint F is closed.  Continue with Sprint C and D: real `.ipynb` artifacts, coverage/diagnostic tables, public `veyra_sage/` API index, and updated school-to-11 coverage map.
