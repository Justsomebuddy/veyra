"""Public import surface for the Veyra Sage laboratory."""

from .balances import VeyraBalanceElement, VeyraBalanceParent, VeyraBalances
from .calculus import VeyraCalculusLab, build_calculus_depth_notebook, calculus_depth_lab_summary
from .card_examples import VeyraCardExample, build_all_executable_card_notebooks, build_executable_card_notebook, card_example_summary, card_examples, run_card_example
from .category_like import VeyraCategoryLab, build_category_like_notebook, category_like_lab_summary
from .certify import sage_certificate_suite
from .essence import VeyraEssenceLab, build_essence_core_notebook, essence_lab_summary
from .geometry_cards import VeyraGeometryTheoremLab, build_geometry_theorem_card_notebook, geometry_theorem_lab_summary
from .modes import SAGE_AVAILABLE, VeyraModeElement, VeyraModeParent, VeyraModes
from .notebooks import VeyraDomainNotebookSpec, VeyraNotebook, VeyraNotebookCell, available_notebook_domains, build_all_domain_notebooks, build_domain_theorem_notebook, build_school_proof_notebook, domain_notebook_spec
from .number_theory import VeyraNumberTheoryLab, build_number_theory_notebook, number_theory_lab_summary
from .notebook_artifacts import VeyraNotebookArtifact, current_notebook_artifacts, notebook_artifact_summary, write_current_notebook_artifacts
from .polynomials import VeyraPolynomialElement, VeyraPolynomialParent, VeyraPolynomials
from .proof_discipline import VeyraProofDisciplineLab, build_proof_discipline_notebook, proof_discipline_lab_summary
from .proofs import VeyraProofCheck, VeyraProofGraph, VeyraProofObject
from .ratios import VeyraRatioElement, VeyraRatioParent, VeyraRatios
from .refutation_search import VeyraSearchHit, VeyraSearchReport, build_all_refutation_search_notebooks, build_refutation_search_notebook, refutation_search, refutation_search_summary, run_search_candidate
from .refutations import VeyraRefutationExample, build_all_refutation_notebooks, build_refutation_notebook, refutation_examples, refutation_summary, run_refutation_example
from .language import VeyraLanguageLab, VeyraLanguageResult, VeyraLanguageTraceRow, build_language_lab_notebook, language_lab_summary
from .linear_algebra import VeyraLinearAlgebraLab, build_linear_algebra_seed_notebook, linear_algebra_seed_lab_summary
from .likelihood_geometry import VeyraLikelihoodGeometryLab, build_likelihood_geometry_notebook, likelihood_geometry_lab_summary
from .intrinsic_observer_echo import VeyraIntrinsicObserverEchoLab
from .intrinsic_vam import VeyraIntrinsicVamLab
from .observer_synthesis_v2 import VeyraObserverSynthesisV2Lab
from .observer_patch_gluing import G4ExhaustiveRow, VeyraObserverPatchGluingLab, exhaustive_g4_row
from .adaptive_research_line import AdaptiveRetryOracleRow, VeyraAdaptiveResearchLineLab, adaptive_retry_oracle
from .school import VeyraCurriculumNode, VeyraExportRow, VeyraSchoolCore, VeyraTheoremSpec
from .statistics_inference import VeyraStatisticsInferenceLab, build_statistics_inference_notebook, statistics_inference_lab_summary
from .topology_echo import VeyraTopologyLab, build_topology_echo_notebook, topology_echo_lab_summary
from .trigonometry import VeyraTrigonometryIdentityLab, build_trigonometry_identity_notebook, trigonometry_identity_lab_summary

__all__ = [
    "VeyraCalculusLab", "build_calculus_depth_notebook", "calculus_depth_lab_summary",
    "VeyraTrigonometryIdentityLab", "build_trigonometry_identity_notebook", "trigonometry_identity_lab_summary",
    "VeyraLinearAlgebraLab", "build_linear_algebra_seed_notebook", "linear_algebra_seed_lab_summary",
    "VeyraStatisticsInferenceLab", "build_statistics_inference_notebook", "statistics_inference_lab_summary",
    "VeyraLanguageLab", "VeyraLanguageResult", "VeyraLanguageTraceRow", "build_language_lab_notebook", "language_lab_summary",
    "VeyraGeometryTheoremLab", "build_geometry_theorem_card_notebook", "geometry_theorem_lab_summary",
    "VeyraEssenceLab", "build_essence_core_notebook", "essence_lab_summary",
    "VeyraProofDisciplineLab", "build_proof_discipline_notebook", "proof_discipline_lab_summary",
    "VeyraNumberTheoryLab", "build_number_theory_notebook", "number_theory_lab_summary",
    "VeyraCategoryLab", "build_category_like_notebook", "category_like_lab_summary",
    "VeyraTopologyLab", "build_topology_echo_notebook", "topology_echo_lab_summary",
    "VeyraLikelihoodGeometryLab", "build_likelihood_geometry_notebook", "likelihood_geometry_lab_summary",
    "VeyraIntrinsicObserverEchoLab", "VeyraIntrinsicVamLab", "VeyraObserverSynthesisV2Lab",
    "G4ExhaustiveRow", "VeyraObserverPatchGluingLab", "exhaustive_g4_row",
    "AdaptiveRetryOracleRow", "VeyraAdaptiveResearchLineLab", "adaptive_retry_oracle",
    "SAGE_AVAILABLE",
    "VeyraBalanceElement",
    "VeyraBalanceParent",
    "VeyraBalances",
    "VeyraCardExample",
    "VeyraModeElement",
    "VeyraModeParent",
    "VeyraModes",
    "VeyraDomainNotebookSpec",
    "VeyraNotebook",
    "VeyraNotebookArtifact",
    "VeyraNotebookCell",
    "VeyraPolynomialElement",
    "VeyraPolynomialParent",
    "VeyraPolynomials",
    "VeyraProofCheck",
    "VeyraProofGraph",
    "VeyraProofObject",
    "VeyraCurriculumNode",
    "VeyraExportRow",
    "VeyraRatioElement",
    "VeyraRatioParent",
    "VeyraRefutationExample",
    "VeyraSchoolCore",
    "VeyraSearchHit",
    "VeyraSearchReport",
    "VeyraTheoremSpec",
    "VeyraRatios",
    "available_notebook_domains",
    "build_all_executable_card_notebooks",
    "build_all_domain_notebooks",
    "build_domain_theorem_notebook",
    "build_executable_card_notebook",
    "build_all_refutation_notebooks",
    "build_all_refutation_search_notebooks",
    "build_refutation_notebook",
    "build_refutation_search_notebook",
    "build_school_proof_notebook",
    "card_example_summary",
    "card_examples",
    "domain_notebook_spec",
    "current_notebook_artifacts",
    "notebook_artifact_summary",
    "refutation_examples",
    "refutation_search",
    "refutation_search_summary",
    "refutation_summary",
    "run_card_example",
    "run_refutation_example",
    "run_search_candidate",
    "sage_certificate_suite",
    "write_current_notebook_artifacts",
]
