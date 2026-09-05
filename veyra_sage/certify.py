"""Sage-facing Veyra certificate helpers."""

from __future__ import annotations

import logging

from src.core.certify import certificate_suite, certificate_summary

from .balances import VeyraBalances
from .calculus import VeyraCalculusLab, build_calculus_depth_notebook, calculus_depth_lab_summary
from .category_like import VeyraCategoryLab, build_category_like_notebook, category_like_lab_summary
from .linear_algebra import VeyraLinearAlgebraLab, build_linear_algebra_seed_notebook, linear_algebra_seed_lab_summary
from .card_examples import build_all_executable_card_notebooks, card_example_summary
from .essence import VeyraEssenceLab, build_essence_core_notebook, essence_lab_summary
from .geometry_cards import VeyraGeometryTheoremLab, build_geometry_theorem_card_notebook, geometry_theorem_lab_summary
from .language import build_language_lab_notebook, language_lab_summary
from .likelihood_geometry import VeyraLikelihoodGeometryLab, build_likelihood_geometry_notebook, likelihood_geometry_lab_summary
from .intrinsic_observer_echo import _intrinsic_observer_echo_presentation
from .intrinsic_vam import _intrinsic_vam_presentation
from .observer_synthesis_v2 import _observer_synthesis_v2_from_core
from .modes import SAGE_AVAILABLE, VeyraModes
from .notebook_artifacts import current_notebook_artifacts, notebook_artifact_summary
from .notebooks import build_all_domain_notebooks, build_school_proof_notebook
from .number_theory import VeyraNumberTheoryLab, build_number_theory_notebook, number_theory_lab_summary
from .polynomials import VeyraPolynomials
from .proof_discipline import VeyraProofDisciplineLab, build_proof_discipline_notebook, proof_discipline_lab_summary
from .proofs import VeyraProofGraph
from .ratios import VeyraRatios
from .refutation_search import build_all_refutation_search_notebooks, refutation_search_summary
from .refutations import build_all_refutation_notebooks, refutation_summary
from .school import VeyraSchoolCore
from .statistics_inference import VeyraStatisticsInferenceLab, build_statistics_inference_notebook, statistics_inference_lab_summary
from .topology_echo import VeyraTopologyLab, build_topology_echo_notebook, topology_echo_lab_summary
from .trigonometry import VeyraTrigonometryIdentityLab, build_trigonometry_identity_notebook, trigonometry_identity_lab_summary

logger = logging.getLogger(__name__)


def sage_certificate_suite() -> dict[str, object]:
    """Run core certificates plus Sage parent smoke."""
    logger.debug("sage_certificate_suite entry")
    parent = VeyraModes("abc")
    part = parent("ab")
    shifted = parent("baba")
    whole = parent("abac")
    balances = VeyraBalances("τ")
    ratios = VeyraRatios("τ")
    polys = VeyraPolynomials("τ", "x")
    school = VeyraSchoolCore()
    graph = VeyraProofGraph()
    notebook = build_school_proof_notebook()
    domain_notebooks = build_all_domain_notebooks()
    card_notebooks = build_all_executable_card_notebooks()
    refutation_notebooks = build_all_refutation_notebooks()
    search_notebooks = build_all_refutation_search_notebooks()
    language_notebook = build_language_lab_notebook()
    calculus = VeyraCalculusLab()
    calculus_notebook = build_calculus_depth_notebook()
    trig = VeyraTrigonometryIdentityLab()
    trig_notebook = build_trigonometry_identity_notebook()
    linear = VeyraLinearAlgebraLab()
    linear_notebook = build_linear_algebra_seed_notebook()
    stats = VeyraStatisticsInferenceLab()
    stats_notebook = build_statistics_inference_notebook()
    geometry = VeyraGeometryTheoremLab()
    geometry_notebook = build_geometry_theorem_card_notebook()
    essence = VeyraEssenceLab()
    essence_notebook = build_essence_core_notebook()
    discipline = VeyraProofDisciplineLab()
    discipline_notebook = build_proof_discipline_notebook()
    number = VeyraNumberTheoryLab()
    number_notebook = build_number_theory_notebook()
    category = VeyraCategoryLab()
    category_notebook = build_category_like_notebook()
    topology = VeyraTopologyLab()
    topology_notebook = build_topology_echo_notebook()
    likelihood = VeyraLikelihoodGeometryLab()
    likelihood_notebook = build_likelihood_geometry_notebook()
    notebook_artifacts = current_notebook_artifacts()
    balance_total = balances(3) + balances(-2)
    half = ratios(1, 2)
    third = ratios(1, 3)
    product = polys([1, 1]) * polys([-1, 1])
    core = certificate_suite()
    intrinsic_matches = tuple(
        item for item in core if item.name == "intrinsic_vam_r12"
    )
    if len(intrinsic_matches) != 1:
        logger.error(
            "sage_certificate_suite intrinsic_vam_r12 count=%d",
            len(intrinsic_matches),
        )
        raise RuntimeError("core certificate suite requires one intrinsic_vam_r12")
    intrinsic_certificate = intrinsic_matches[0]
    intrinsic_vam_summary = _intrinsic_vam_presentation(intrinsic_certificate)
    intrinsic_vam_passed = (
        intrinsic_vam_summary["passed"] is True
        and intrinsic_vam_summary["theorems"] == 9
        and intrinsic_vam_summary["lanes"] == 4
        and intrinsic_vam_summary["vami_frames"] == 4
        and intrinsic_vam_summary["presentation_only"] is True
        and intrinsic_vam_summary["evidence_accepted"] is False
        and intrinsic_vam_summary["promotion_ready"] is False
        and intrinsic_vam_summary["taxonomy_changed"] is False
        and intrinsic_vam_summary["proof_complete"] is False
    )
    observer_matches = tuple(
        item for item in core if item.name == "intrinsic_observer_echo_r13"
    )
    if len(observer_matches) != 1:
        logger.error(
            "sage_certificate_suite intrinsic_observer_echo_r13 count=%d",
            len(observer_matches),
        )
        raise RuntimeError(
            "core certificate suite requires one intrinsic_observer_echo_r13",
        )
    observer_echo_summary = _intrinsic_observer_echo_presentation(
        observer_matches[0],
    )
    observer_echo_passed = (
        observer_echo_summary["passed"] is True
        and observer_echo_summary["theorem"] == "THM-R13-003"
        and observer_echo_summary["formal_theorems"] == 5
        and observer_echo_summary["executable_rows"] == 3
        and observer_echo_summary["contract_promoted"] is True
        and observer_echo_summary["theorem_derived_layers"] == 2
        and observer_echo_summary["presentation_only"] is True
        and observer_echo_summary["evidence_accepted"] is False
        and observer_echo_summary["proof_complete"] is False
    )
    synthesis_summary = _observer_synthesis_v2_from_core(core)
    synthesis_passed = (
        synthesis_summary["passed"] is True
        and synthesis_summary["finite_audit"] is True
        and synthesis_summary["subjects"] == 5
        and synthesis_summary["cases"] == 10
        and synthesis_summary["receipt_rows"] == 10
        and synthesis_summary["presentation_only"] is True
        and synthesis_summary["semantic_replay"] is False
        and synthesis_summary["evidence_accepted"] is False
        and synthesis_summary["promotion_ready"] is False
        and synthesis_summary["taxonomy_changed"] is False
        and synthesis_summary["proof_complete"] is False
    )
    sage_passed = part.cyclic_resonates(shifted) and part.weighted_resonates(whole, 0.5)
    balance_passed = balance_total.net_length() == 1 and balance_total.opposite().net_length() == -1
    ratio_passed = (half + third).shadow().numerator == 5 and (half * third).shadow().denominator == 6
    polynomial_passed = product.coefficient_shadows() == [-1, 0, 1] and product.evaluate(3).shadow() == 8
    school_summary = school.summary()
    school_passed = school_summary["theorem_specs"] == 19 and school_summary["curriculum_missing"] == 0 and school_summary["sage_rows"] == 19
    proof_graph_summary = graph.summary()
    proof_graph_passed = proof_graph_summary["theorem_specs"] == 19 and proof_graph_summary["definition_edges"] > 0 and bool(graph.curriculum_path("arithmetic-ratios", "statistics"))
    notebook_summary = notebook.summary()
    notebook_passed = notebook_summary == {"cells": 8, "markdown": 4, "code": 4} and notebook.to_ipynb_dict()["nbformat"] == 4
    domain_notebook_summary = {"domains": len(domain_notebooks), "cells": sum(item.summary()["cells"] for item in domain_notebooks.values())}
    domain_notebooks_passed = domain_notebook_summary == {"domains": 7, "cells": 56} and "geometry" in domain_notebooks
    card_summary = card_example_summary()
    card_notebooks_summary = {"domains": len(card_notebooks), "cells": sum(item.summary()["cells"] for item in card_notebooks.values()), **card_summary}
    card_examples_passed = card_summary == {"examples": 19, "ready": 19, "domains": 7} and card_notebooks_summary["cells"] == 56
    ref_summary = refutation_summary()
    refutation_notebooks_summary = {"domains": len(refutation_notebooks), "cells": sum(item.summary()["cells"] for item in refutation_notebooks.values()), **ref_summary}
    refutations_passed = ref_summary == {"examples": 7, "blocked": 7, "domains": 7, "mutations": 3} and refutation_notebooks_summary["cells"] == 56
    search_summary = refutation_search_summary()
    search_notebooks_summary = {"domains": len(search_notebooks), "cells": sum(item.summary()["cells"] for item in search_notebooks.values()), **search_summary}
    refutation_search_passed = search_summary == {"domains": 7, "tried": 10, "blocked": 7} and search_notebooks_summary["cells"] == 42
    language_summary = language_lab_summary()
    language_notebook_summary = language_notebook.summary()
    calculus_summary = calculus_depth_lab_summary()
    calculus_notebook_summary = calculus_notebook.summary()
    trig_summary = trigonometry_identity_lab_summary()
    trig_notebook_summary = trig_notebook.summary()
    linear_summary = linear_algebra_seed_lab_summary()
    linear_notebook_summary = linear_notebook.summary()
    stats_summary = statistics_inference_lab_summary()
    stats_notebook_summary = stats_notebook.summary()
    geometry_summary = geometry_theorem_lab_summary()
    geometry_notebook_summary = geometry_notebook.summary()
    language_passed = language_summary == {"domain": "logic", "ready_status": "ready", "blocked_status": "blocked", "mutation_cases": 10, "mutation_unexpected": 0, "family_cases": 20, "family_unexpected": 0, "property_cases": 24, "property_unexpected": 0, "property_shrunk": 24, "coverage_cases": 54, "coverage_missed": 0, "span_diag_cases": 7, "span_diag_missed": 0} and language_notebook_summary == {"cells": 6, "markdown": 2, "code": 4}
    calculus_passed = calculus_summary == {"checklist": 4, "cards": 3, "linearization_ready": True, "integral_ready": True} and calculus_notebook_summary == {"cells": 5, "markdown": 2, "code": 3} and calculus.linearization_row()["slope"] == "6"
    trig_passed = trig_summary == {"checklist": 4, "cards": 4, "all_coherent": True, "unit_ready": True} and trig_notebook_summary == {"cells": 5, "markdown": 2, "code": 3} and len(trig.phase_rows()) == 2
    linear_passed = linear_summary == {"checklist": 4, "cards": 2, "action_ready": True, "determinant_ready": True} and linear_notebook_summary == {"cells": 5, "markdown": 2, "code": 3} and linear.action_row()["det"] == "6"
    stats_passed = stats_summary == {"checklist": 4, "hypothesis_cards": 2, "family_ready": True, "interval_ready": True, "uncertainty": "3/64"} and stats_notebook_summary == {"cells": 5, "markdown": 2, "code": 3} and stats.family_row()["p"] == "3/4"
    geometry_passed = geometry_summary == {"cards": 5, "ready": 5, "visual_scenes": 3, "stable_exports": 5, "package_stable": False} and geometry_notebook_summary == {"cells": 6, "markdown": 2, "code": 4} and len(geometry.stable_export_rows()) == 5
    essence_summary = essence_lab_summary()
    essence_notebook_summary = essence_notebook.summary()
    essence_passed = essence_summary == {"axioms": 9, "layers": 36, "executable_layers": 36, "missing": 0, "checklist": 6, "core_ready": True, "execution_ready": True, "proof_complete": False, "theorem_derived": 2, "witness_only": 4, "shadow": 25, "meta": 5} and essence_notebook_summary == {"cells": 5, "markdown": 2, "code": 3} and len(essence.axiom_rows()) == 9 and len(essence.layer_rows()) == 36
    discipline_summary = proof_discipline_lab_summary()
    discipline_notebook_summary = discipline_notebook.summary()
    discipline_passed = discipline_summary == {"rules": 7, "steps": 28, "blocked_rules": 3, "domains": 7, "domain_certs": 7, "models": 10, "exports": 19} and discipline_notebook_summary == {"cells": 5, "markdown": 2, "code": 3} and len(discipline.stable_export_rows()) == 19
    number_summary = number_theory_lab_summary()
    number_notebook_summary = number_notebook.summary()
    number_passed = number_summary == {"divisibility": 2, "blocked": 1, "prime_rows": 3, "rank_rows": 3, "factor_hits": 2, "fermat_rows": 7, "fermat_derived": 4, "fermat_units": 21, "checklist": 4} and number_notebook_summary == {"cells": 5, "markdown": 2, "code": 3} and len(number.rank_factor_rows()) == 3 and len(number.fermat_rows()) == 7
    category_summary = category_like_lab_summary()
    category_notebook_summary = category_notebook.summary()
    category_passed = category_summary == {"objects": 4, "morphisms": 4, "closed": 4, "invariants": 2, "broken": 1, "universal": 3, "blocked": 1, "checklist": 4} and category_notebook_summary == {"cells": 5, "markdown": 2, "code": 3} and category.universal_rows()[-1]["status"] == "blocked"
    topology_summary = topology_echo_lab_summary()
    topology_notebook_summary = topology_notebook.summary()
    topology_passed = topology_summary == {"shapes": 4, "invariants": 4, "invariant_hits": 4, "obstructions": 2, "blocked": 2, "checklist": 4} and topology_notebook_summary == {"cells": 5, "markdown": 2, "code": 3} and topology.obstruction_rows()[-1]["obstruction"] == "cycle-collapse"
    likelihood_summary = likelihood_geometry_lab_summary()
    likelihood_notebook_summary = likelihood_notebook.summary()
    likelihood_passed = likelihood_summary == {"likelihood_points": 3, "segments": 2, "rising_segments": 2, "residual_certificates": 2, "fit_domains": 1, "blocked_domains": 1, "checklist": 4} and likelihood_notebook_summary == {"cells": 5, "markdown": 2, "code": 3} and likelihood.residual_rows()[-1]["obstruction"] == "residual-outlier"
    artifact_summary = notebook_artifact_summary(notebook_artifacts)
    artifact_passed = artifact_summary == {"notebooks": 41, "families": 5, "cells": 280, "markdown": 133, "code": 147}
    result = certificate_summary(core) | {
        "sage_available": SAGE_AVAILABLE,
        "sage_parent_passed": sage_passed,
        "sage_balance_passed": balance_passed,
        "sage_ratio_passed": ratio_passed,
        "sage_polynomial_passed": polynomial_passed,
        "sage_school_passed": school_passed,
        "sage_school_summary": school_summary,
        "sage_proof_graph_passed": proof_graph_passed,
        "sage_proof_graph_summary": proof_graph_summary,
        "sage_notebook_passed": notebook_passed,
        "sage_notebook_summary": notebook_summary,
        "sage_domain_notebooks_passed": domain_notebooks_passed,
        "sage_domain_notebook_summary": domain_notebook_summary,
        "sage_card_examples_passed": card_examples_passed,
        "sage_card_examples_summary": card_notebooks_summary,
        "sage_refutations_passed": refutations_passed,
        "sage_refutations_summary": refutation_notebooks_summary,
        "sage_refutation_search_passed": refutation_search_passed,
        "sage_refutation_search_summary": search_notebooks_summary,
        "sage_language_passed": language_passed,
        "sage_language_summary": language_summary,
        "sage_language_notebook_summary": language_notebook_summary,
        "sage_calculus_depth_passed": calculus_passed,
        "sage_calculus_depth_summary": calculus_summary,
        "sage_calculus_depth_notebook_summary": calculus_notebook_summary,
        "sage_trigonometry_identities_passed": trig_passed,
        "sage_trigonometry_identities_summary": trig_summary,
        "sage_trigonometry_identities_notebook_summary": trig_notebook_summary,
        "sage_linear_algebra_seed_passed": linear_passed,
        "sage_linear_algebra_seed_summary": linear_summary,
        "sage_linear_algebra_seed_notebook_summary": linear_notebook_summary,
        "sage_statistics_inference_passed": stats_passed,
        "sage_statistics_inference_summary": stats_summary,
        "sage_statistics_inference_notebook_summary": stats_notebook_summary,
        "sage_geometry_theorem_cards_passed": geometry_passed,
        "sage_geometry_theorem_cards_summary": geometry_summary,
        "sage_geometry_theorem_cards_notebook_summary": geometry_notebook_summary,
        "sage_essence_passed": essence_passed,
        "sage_essence_summary": essence_summary,
        "sage_essence_notebook_summary": essence_notebook_summary,
        "sage_proof_discipline_passed": discipline_passed,
        "sage_proof_discipline_summary": discipline_summary,
        "sage_proof_discipline_notebook_summary": discipline_notebook_summary,
        "sage_number_theory_passed": number_passed,
        "sage_number_theory_summary": number_summary,
        "sage_number_theory_notebook_summary": number_notebook_summary,
        "sage_category_like_passed": category_passed,
        "sage_category_like_summary": category_summary,
        "sage_category_like_notebook_summary": category_notebook_summary,
        "sage_topology_echo_passed": topology_passed,
        "sage_topology_echo_summary": topology_summary,
        "sage_topology_echo_notebook_summary": topology_notebook_summary,
        "sage_likelihood_geometry_passed": likelihood_passed,
        "sage_likelihood_geometry_summary": likelihood_summary,
        "sage_likelihood_geometry_notebook_summary": likelihood_notebook_summary,
        "sage_notebook_artifacts_passed": artifact_passed,
        "sage_notebook_artifacts_summary": artifact_summary,
        "sage_intrinsic_vam_passed": intrinsic_vam_passed,
        "sage_intrinsic_vam_summary": intrinsic_vam_summary,
        "sage_intrinsic_observer_echo_passed": observer_echo_passed,
        "sage_intrinsic_observer_echo_summary": observer_echo_summary,
        "sage_observer_synthesis_v2_passed": synthesis_passed,
        "sage_observer_synthesis_v2_summary": synthesis_summary,
        "sage_parent": repr(parent),
    }
    logger.debug("sage_certificate_suite exit result=%r", result)
    return result
