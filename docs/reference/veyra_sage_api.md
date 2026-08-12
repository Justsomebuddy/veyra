# `veyra_sage` public API index

**Generated/verified:** 2026-07-29
**Source of truth:** `veyra_sage/all.py::__all__`
**Stability:** research-lab API. Names below are public for current notebooks, tests, and examples; package-extension stability is governed by `docs/69_package_boundary.md`.

## How to import

```python
from veyra_sage.all import VeyraSchoolCore, sage_certificate_suite
```

Do not deep-import non-public implementation helpers when writing notebooks or external examples.  Import through `veyra_sage.all` unless a document explicitly names a lower-level module.

## Domain tiers

| Tier | Domain | Role |
|---|---|---|
| T0 | certification/runtime | project health and Sage availability |
| T1 | school-core/proof-graph/notebooks | current stable research-lab surface |
| T2 | modes/balances/ratios/polynomials | algebraic parent/element experiments |
| T3 | language/geometry/essence/proof-discipline/calculus/trig/linear/stat/number/category/topology/likelihood seed labs | fast-moving kernel research wrappers |
| T4 | refutations/search/card examples/artifacts | negative-pressure and generated notebook tooling |

## Public symbols

The table is intentionally machine-readable: tests parse the first column and compare it with `veyra_sage.all.__all__`.

| Symbol | Domain | Kind | Owner module |
|---|---|---|---|
| `VeyraCalculusLab` | calculus-depth | class | `veyra_sage.calculus` |
| `build_calculus_depth_notebook` | calculus-depth | function | `veyra_sage.calculus` |
| `calculus_depth_lab_summary` | calculus-depth | function | `veyra_sage.calculus` |
| `VeyraTrigonometryIdentityLab` | trigonometry-identities | class | `veyra_sage.trigonometry` |
| `build_trigonometry_identity_notebook` | trigonometry-identities | function | `veyra_sage.trigonometry` |
| `trigonometry_identity_lab_summary` | trigonometry-identities | function | `veyra_sage.trigonometry` |
| `VeyraLinearAlgebraLab` | linear-algebra | class | `veyra_sage.linear_algebra` |
| `build_linear_algebra_seed_notebook` | linear-algebra | function | `veyra_sage.linear_algebra` |
| `linear_algebra_seed_lab_summary` | linear-algebra | function | `veyra_sage.linear_algebra` |
| `VeyraStatisticsInferenceLab` | statistics-inference | class | `veyra_sage.statistics_inference` |
| `build_statistics_inference_notebook` | statistics-inference | function | `veyra_sage.statistics_inference` |
| `statistics_inference_lab_summary` | statistics-inference | function | `veyra_sage.statistics_inference` |
| `VeyraLanguageLab` | core-language | class | `veyra_sage.language` |
| `VeyraLanguageResult` | core-language | class | `veyra_sage.language` |
| `VeyraLanguageTraceRow` | core-language | class | `veyra_sage.language` |
| `build_language_lab_notebook` | core-language | function | `veyra_sage.language` |
| `language_lab_summary` | core-language | function | `veyra_sage.language` |
| `VeyraGeometryTheoremLab` | geometry-theorem-cards | class | `veyra_sage.geometry_cards` |
| `build_geometry_theorem_card_notebook` | geometry-theorem-cards | function | `veyra_sage.geometry_cards` |
| `geometry_theorem_lab_summary` | geometry-theorem-cards | function | `veyra_sage.geometry_cards` |
| `VeyraEssenceLab` | essence-core | class | `veyra_sage.essence` |
| `build_essence_core_notebook` | essence-core | function | `veyra_sage.essence` |
| `essence_lab_summary` | essence-core | function | `veyra_sage.essence` |
| `VeyraProofDisciplineLab` | proof-discipline | class | `veyra_sage.proof_discipline` |
| `build_proof_discipline_notebook` | proof-discipline | function | `veyra_sage.proof_discipline` |
| `proof_discipline_lab_summary` | proof-discipline | function | `veyra_sage.proof_discipline` |
| `VeyraNumberTheoryLab` | native-number-theory | class | `veyra_sage.number_theory` |
| `build_number_theory_notebook` | native-number-theory | function | `veyra_sage.number_theory` |
| `number_theory_lab_summary` | native-number-theory | function | `veyra_sage.number_theory` |
| `VeyraCategoryLab` | category-like | class | `veyra_sage.category_like` |
| `build_category_like_notebook` | category-like | function | `veyra_sage.category_like` |
| `category_like_lab_summary` | category-like | function | `veyra_sage.category_like` |
| `VeyraTopologyLab` | topology-echo | class | `veyra_sage.topology_echo` |
| `build_topology_echo_notebook` | topology-echo | function | `veyra_sage.topology_echo` |
| `topology_echo_lab_summary` | topology-echo | function | `veyra_sage.topology_echo` |
| `VeyraLikelihoodGeometryLab` | likelihood-geometry | class | `veyra_sage.likelihood_geometry` |
| `build_likelihood_geometry_notebook` | likelihood-geometry | function | `veyra_sage.likelihood_geometry` |
| `likelihood_geometry_lab_summary` | likelihood-geometry | function | `veyra_sage.likelihood_geometry` |
| `VeyraIntrinsicObserverEchoLab` | intrinsic-observer-echo | class | `veyra_sage.intrinsic_observer_echo` |
| `VeyraIntrinsicVamLab` | intrinsic-vam | class | `veyra_sage.intrinsic_vam` |
| `VeyraObserverSynthesisV2Lab` | observer-synthesis-v2 | class | `veyra_sage.observer_synthesis_v2` |
| `G4ExhaustiveRow` | observer-patch-gluing | class | `veyra_sage.observer_patch_gluing` |
| `VeyraObserverPatchGluingLab` | observer-patch-gluing | class | `veyra_sage.observer_patch_gluing` |
| `exhaustive_g4_row` | observer-patch-gluing | function | `veyra_sage.observer_patch_gluing` |
| `AdaptiveRetryOracleRow` | adaptive-research-line | class | `veyra_sage.adaptive_research_line` |
| `VeyraAdaptiveResearchLineLab` | adaptive-research-line | class | `veyra_sage.adaptive_research_line` |
| `adaptive_retry_oracle` | adaptive-research-line | function | `veyra_sage.adaptive_research_line` |
| `SAGE_AVAILABLE` | runtime | constant | `veyra_sage.all` |
| `VeyraBalanceElement` | arithmetic-balances | class | `veyra_sage.balances` |
| `VeyraBalanceParent` | arithmetic-balances | class | `veyra_sage.balances` |
| `VeyraBalances` | arithmetic-balances | function | `veyra_sage.balances` |
| `VeyraCardExample` | theorem-card-examples | class | `veyra_sage.card_examples` |
| `VeyraModeElement` | modes | class | `veyra_sage.modes` |
| `VeyraModeParent` | modes | class | `veyra_sage.modes` |
| `VeyraModes` | modes | function | `veyra_sage.modes` |
| `VeyraDomainNotebookSpec` | notebooks | class | `veyra_sage.notebooks` |
| `VeyraNotebook` | notebooks | class | `veyra_sage.notebooks` |
| `VeyraNotebookArtifact` | notebook-artifacts | class | `veyra_sage.notebook_artifacts` |
| `VeyraNotebookCell` | notebooks | class | `veyra_sage.notebooks` |
| `VeyraPolynomialElement` | polynomials | class | `veyra_sage.polynomials` |
| `VeyraPolynomialParent` | polynomials | class | `veyra_sage.polynomials` |
| `VeyraPolynomials` | polynomials | function | `veyra_sage.polynomials` |
| `VeyraProofCheck` | proof-graph | class | `veyra_sage.proofs` |
| `VeyraProofGraph` | proof-graph | class | `veyra_sage.proofs` |
| `VeyraProofObject` | proof-graph | class | `veyra_sage.proofs` |
| `VeyraCurriculumNode` | school-core | class | `veyra_sage.school` |
| `VeyraExportRow` | school-core | class | `veyra_sage.school` |
| `VeyraRatioElement` | ratio-arithmetic | class | `veyra_sage.ratios` |
| `VeyraRatioParent` | ratio-arithmetic | class | `veyra_sage.ratios` |
| `VeyraRefutationExample` | refutations | class | `veyra_sage.refutations` |
| `VeyraSchoolCore` | school-core | class | `veyra_sage.school` |
| `VeyraSearchHit` | refutation-search | class | `veyra_sage.refutation_search` |
| `VeyraSearchReport` | refutation-search | class | `veyra_sage.refutation_search` |
| `VeyraTheoremSpec` | school-core | class | `veyra_sage.school` |
| `VeyraRatios` | ratio-arithmetic | function | `veyra_sage.ratios` |
| `available_notebook_domains` | notebooks | function | `veyra_sage.notebooks` |
| `build_all_executable_card_notebooks` | notebooks | function | `veyra_sage.card_examples` |
| `build_all_domain_notebooks` | notebooks | function | `veyra_sage.notebooks` |
| `build_domain_theorem_notebook` | notebooks | function | `veyra_sage.notebooks` |
| `build_executable_card_notebook` | notebooks | function | `veyra_sage.card_examples` |
| `build_all_refutation_notebooks` | notebooks | function | `veyra_sage.refutations` |
| `build_all_refutation_search_notebooks` | notebooks | function | `veyra_sage.refutation_search` |
| `build_refutation_notebook` | notebooks | function | `veyra_sage.refutations` |
| `build_refutation_search_notebook` | notebooks | function | `veyra_sage.refutation_search` |
| `build_school_proof_notebook` | notebooks | function | `veyra_sage.notebooks` |
| `card_example_summary` | theorem-card-examples | function | `veyra_sage.card_examples` |
| `card_examples` | theorem-card-examples | function | `veyra_sage.card_examples` |
| `domain_notebook_spec` | notebooks | function | `veyra_sage.notebooks` |
| `current_notebook_artifacts` | notebook-artifacts | function | `veyra_sage.notebook_artifacts` |
| `notebook_artifact_summary` | notebook-artifacts | function | `veyra_sage.notebook_artifacts` |
| `refutation_examples` | refutations | function | `veyra_sage.refutations` |
| `refutation_search` | refutation-search | function | `veyra_sage.refutation_search` |
| `refutation_search_summary` | refutation-search | function | `veyra_sage.refutation_search` |
| `refutation_summary` | refutations | function | `veyra_sage.refutations` |
| `run_card_example` | theorem-card-examples | function | `veyra_sage.card_examples` |
| `run_refutation_example` | refutations | function | `veyra_sage.refutations` |
| `run_search_candidate` | refutation-search | function | `veyra_sage.refutation_search` |
| `sage_certificate_suite` | certification | function | `veyra_sage.certify` |
| `write_current_notebook_artifacts` | notebook-artifacts | function | `veyra_sage.notebook_artifacts` |

## API count

- Public symbols: 99
- Governing tests: `tests/test_veyra_sage_api_index.py`
- Boundary document: `docs/69_package_boundary.md`

## Maintenance rule

Whenever `veyra_sage/all.py::__all__` changes, update this file in the same commit and run:

```bash
PYTHONPATH=. python3 -m pytest -q tests/test_veyra_sage_api_index.py
```
