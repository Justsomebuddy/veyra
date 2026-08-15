#!/usr/bin/env python3
"""Smoke-test the Veyra Sage laboratory with progress."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from veyra_sage.all import (  # noqa: E402
    SAGE_AVAILABLE,
    VeyraBalances,
    VeyraModes,
    build_all_executable_card_notebooks,
    build_all_domain_notebooks,
    build_all_refutation_notebooks,
    build_all_refutation_search_notebooks,
    build_school_proof_notebook,
    build_language_lab_notebook,
    build_calculus_depth_notebook,
    build_trigonometry_identity_notebook,
    build_linear_algebra_seed_notebook,
    build_statistics_inference_notebook,
    build_essence_core_notebook,
    build_proof_discipline_notebook,
    build_number_theory_notebook,
    build_category_like_notebook,
    build_topology_echo_notebook,
    build_likelihood_geometry_notebook,
    current_notebook_artifacts,
    notebook_artifact_summary,
    language_lab_summary,
    calculus_depth_lab_summary,
    trigonometry_identity_lab_summary,
    linear_algebra_seed_lab_summary,
    statistics_inference_lab_summary,
    essence_lab_summary,
    proof_discipline_lab_summary,
    number_theory_lab_summary,
    category_like_lab_summary,
    topology_echo_lab_summary,
    likelihood_geometry_lab_summary,
    card_example_summary,
    refutation_summary,
    refutation_search_summary,
    VeyraPolynomials,
    VeyraProofGraph,
    VeyraRatios,
    sage_certificate_suite,
    VeyraSchoolCore,
    VeyraCalculusLab,
    VeyraTrigonometryIdentityLab,
    VeyraLinearAlgebraLab,
    VeyraStatisticsInferenceLab,
    VeyraEssenceLab,
    VeyraProofDisciplineLab,
    VeyraNumberTheoryLab,
    VeyraCategoryLab,
    VeyraTopologyLab,
    VeyraLikelihoodGeometryLab,
    VeyraIntrinsicObserverEchoLab,
    VeyraIntrinsicVamLab,
)

logger = logging.getLogger("veyra.sage_smoke")


def stage(index: int, total: int, message: str) -> None:
    """Print visible progress stage."""
    logger.debug("stage entry index=%d total=%d message=%s", index, total, message)
    print(f"[{index}/{total}] {message}")
    logger.debug("stage exit")


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse the explicit real-Sage requirement."""
    logger.debug("parse_args entry argc=%d", len(argv))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-sage",
        action="store_true",
        help="fail instead of using the documented pure-Python fallback",
    )
    result = parser.parse_args(argv)
    logger.debug("parse_args exit require_sage=%s", result.require_sage)
    return result


def main(argv: list[str] | None = None) -> int:
    """Run Sage lab smoke."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    logger.debug("main entry")
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.require_sage and not SAGE_AVAILABLE:
        logger.error("real SageMath required but unavailable")
        print("[done] errors=1 error=real-sage-required", file=sys.stderr)
        return 2
    stage(1, 4, "Constructing Veyra Sage parent")
    parent = VeyraModes("abc")
    part = parent("ab")
    shifted = parent("baba")
    whole = parent("abac")
    print(f"sage_available={SAGE_AVAILABLE} parent={parent}")

    stage(2, 4, "Checking Veyra methods")
    ratios = VeyraRatios("τ")
    half = ratios(1, 2)
    third = ratios(1, 3)
    print(f"cyclic={part.cyclic_resonates(shifted)} weighted={part.weighted_resonates(whole, 0.5)}")
    balances = VeyraBalances("τ")
    print(f"balance_sum={(balances(3) + balances(-2)).net_length()}")
    print(f"ratio_sum={(half + third).shadow()} ratio_product={(half * third).shadow()}")
    polynomials = VeyraPolynomials("τ", "x")
    product = polynomials([1, 1]) * polynomials([-1, 1])
    print(f"poly_coeffs={product.coefficient_shadows()} poly_at_3={product.evaluate(3).shadow()}")

    stage(3, 4, "Checking school-core facade")
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
    artifact_summary = notebook_artifact_summary(current_notebook_artifacts())
    print(f"school_summary={school.summary()} export_rows={len(school.export_rows())}")
    print(f"proof_graph={graph.summary()} path={graph.curriculum_path('arithmetic-ratios', 'statistics')}")
    print(f"notebook={notebook.summary()} ipynb={notebook.to_ipynb_dict()['nbformat']}")
    print(f"domain_notebooks={len(domain_notebooks)} domains={tuple(domain_notebooks)}")
    print(f"card_examples={card_example_summary()} card_notebooks={len(card_notebooks)}")
    print(f"refutations={refutation_summary()} refutation_notebooks={len(refutation_notebooks)}")
    print(f"refutation_search={refutation_search_summary()} search_notebooks={len(search_notebooks)}")
    print(f"language_lab={language_lab_summary()} language_notebook={language_notebook.summary()}")
    print(
        f"calculus_depth={calculus_depth_lab_summary()} notebook={calculus_notebook.summary()} cards={len(calculus.card_rows())}"
    )
    print(
        f"trigonometry_identities={trigonometry_identity_lab_summary()} notebook={trig_notebook.summary()} cards={len(trig.card_rows())}"
    )
    print(
        f"linear_algebra_seed={linear_algebra_seed_lab_summary()} notebook={linear_notebook.summary()} cards={len(linear.card_rows())}"
    )
    print(
        f"statistics_inference={statistics_inference_lab_summary()} notebook={stats_notebook.summary()} hypotheses={len(stats.hypothesis_rows())}"
    )
    print(
        f"essence_core={essence_lab_summary()} essence_notebook={essence_notebook.summary()} axioms={len(essence.axiom_rows())}"
    )
    print(
        f"proof_discipline={proof_discipline_lab_summary()} notebook={discipline_notebook.summary()} exports={len(discipline.stable_export_rows())}"
    )
    print(
        f"number_theory={number_theory_lab_summary()} notebook={number_notebook.summary()} ranks={len(number.rank_factor_rows())}"
    )
    print(
        f"category_like={category_like_lab_summary()} notebook={category_notebook.summary()} universal={len(category.universal_rows())}"
    )
    print(
        f"topology_echo={topology_echo_lab_summary()} notebook={topology_notebook.summary()} obstructions={len(topology.obstruction_rows())}"
    )
    print(
        f"likelihood_geometry={likelihood_geometry_lab_summary()} notebook={likelihood_notebook.summary()} residuals={len(likelihood.residual_rows())}"
    )
    print(f"notebook_artifacts={artifact_summary}")

    stage(4, 4, "Running certificates")
    summary = sage_certificate_suite()
    intrinsic_vam = summary["sage_intrinsic_vam_summary"]
    intrinsic_observer_echo = summary["sage_intrinsic_observer_echo_summary"]
    print(f"intrinsic_vam={intrinsic_vam} facade={VeyraIntrinsicVamLab.__name__}")
    print(f"intrinsic_observer_echo={intrinsic_observer_echo} facade={VeyraIntrinsicObserverEchoLab.__name__}")
    ok = (
        summary["failed"] == []
        and summary["sage_parent_passed"]
        and summary["sage_balance_passed"]
        and summary["sage_ratio_passed"]
        and summary["sage_polynomial_passed"]
        and summary["sage_school_passed"]
        and summary["sage_proof_graph_passed"]
        and summary["sage_notebook_passed"]
        and summary["sage_domain_notebooks_passed"]
        and summary["sage_card_examples_passed"]
        and summary["sage_refutations_passed"]
        and summary["sage_refutation_search_passed"]
        and summary["sage_language_passed"]
        and summary["sage_calculus_depth_passed"]
        and summary["sage_trigonometry_identities_passed"]
        and summary["sage_linear_algebra_seed_passed"]
        and summary["sage_statistics_inference_passed"]
        and summary["sage_essence_passed"]
        and summary["sage_proof_discipline_passed"]
        and summary["sage_number_theory_passed"]
        and summary["sage_category_like_passed"]
        and summary["sage_topology_echo_passed"]
        and summary["sage_likelihood_geometry_passed"]
        and summary["sage_notebook_artifacts_passed"]
        and summary["sage_intrinsic_vam_passed"]
        and summary["sage_intrinsic_observer_echo_passed"]
        and intrinsic_vam["presentation_only"] is True
        and intrinsic_vam["evidence_accepted"] is False
        and intrinsic_vam["promotion_ready"] is False
        and intrinsic_vam["taxonomy_changed"] is False
        and intrinsic_observer_echo["contract_promoted"] is True
        and intrinsic_observer_echo["presentation_only"] is True
        and intrinsic_observer_echo["evidence_accepted"] is False
    )
    print(f"summary={summary}")
    print(f"[done] errors={0 if ok else 1}")
    logger.debug("main exit ok=%s", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
