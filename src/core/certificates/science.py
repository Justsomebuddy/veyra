"""Science-domain certificate helper."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..shadows.ratio import ratio_from_ints, ratio_shadow
from ..shadows.science_certificates import FlowEdge, anti_diffusion_obstruction_card, finite_conservation_row, finite_diffusion_row, finite_flow_balance_row, science_certificate_checklist
from ..shadows.model_diagnostics import anomaly_obstruction_card, baseline_model_observations, canonical_model_observations, compare_model_reports, model_diagnostics_checklist, model_fit_report

logger = logging.getLogger(__name__)


def certify_science_domain_certificates() -> Certificate:
    """Certify finite science-domain rows."""
    logger.debug("certify_science_domain_certificates entry")
    conservation = finite_conservation_row("two-cell-transfer", (ratio_from_ints(3), ratio_from_ints(1)), (ratio_from_ints(2), ratio_from_ints(2)))
    edges = (FlowEdge("source", "a", ratio_from_ints(3)), FlowEdge("a", "sink", ratio_from_ints(3)), FlowEdge("source", "b", ratio_from_ints(2)), FlowEdge("b", "sink", ratio_from_ints(2)))
    flow = finite_flow_balance_row("source-sink-network", edges, frozenset({"source", "sink"}))
    diffusion = finite_diffusion_row("two-cell-average", (ratio_from_ints(0), ratio_from_ints(1)), (ratio_from_ints(1, 2), ratio_from_ints(1, 2)))
    anti = anti_diffusion_obstruction_card()
    passed = ratio_shadow(conservation.before_total) == 4 and conservation.status == "conserved" and flow.status == "boundary-balanced" and ratio_shadow(diffusion.before_variation) == 1 and ratio_shadow(diffusion.after_variation) == 0 and anti.obstruction == "variation-growth" and len(science_certificate_checklist()) == 4
    detail = f"conserve={ratio_shadow(conservation.before_total)} flow={flow.status} diffusion={ratio_shadow(diffusion.after_variation)} anti={anti.obstruction}"
    result = Certificate("science_domain_certificates", "finite conservation, network flow, diffusion, obstruction certificates", passed, detail, 1)
    logger.debug("certify_science_domain_certificates exit result=%r", result)
    return result


def certify_model_diagnostics() -> Certificate:
    """Certify finite model residual diagnostics."""
    logger.debug("certify_model_diagnostics entry")
    candidate = model_fit_report("candidate", canonical_model_observations(), ratio_from_ints(1, 2))
    baseline = model_fit_report("baseline", baseline_model_observations(), ratio_from_ints(2))
    comparison = compare_model_reports("candidate-vs-baseline", candidate, baseline)
    anomaly = anomaly_obstruction_card()
    passed = ratio_shadow(candidate.total_absolute_error) == ratio_shadow(ratio_from_ints(1, 2)) and ratio_shadow(candidate.max_absolute_error) == ratio_shadow(ratio_from_ints(1, 4)) and candidate.status == "fit" and comparison.status == "improved" and ratio_shadow(baseline.total_absolute_error) == ratio_shadow(ratio_from_ints(5, 2)) and anomaly.obstruction == "residual-outlier" and len(model_diagnostics_checklist()) == 4
    detail = f"fit={ratio_shadow(candidate.total_absolute_error)} baseline={ratio_shadow(baseline.total_absolute_error)} anomaly={anomaly.obstruction}"
    result = Certificate("model_diagnostics", "finite residual, fit, baseline comparison, anomaly obstruction certificates", passed, detail, 1)
    logger.debug("certify_model_diagnostics exit result=%r", result)
    return result
