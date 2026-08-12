"""Canonical research-line construction and nonpromoting assessment."""

from __future__ import annotations

from dataclasses import replace
import logging
from typing import NoReturn

from ..service import (
    GOVERNED_EVALUATION_READY,
    GovernedEvaluationResult,
    validate_governed_evaluation_result,
)
from ...proof_core_codec import digest_data
from .types import (
    ASSESSMENT_BOUNDARY,
    LINEAGE_BOUNDARY,
    LINEAGE_SCHEMA,
    AdaptiveInferencePolicy,
    AdaptivePolicyStatus,
    AdaptiveValidityStatus,
    ExperimentDesignMode,
    ExperimentLineageNode,
    ExperimentResearchLine,
    FamilyRecordingStatus,
    LocalValidityStatus,
    PolicyClaimScope,
    ResearchLineAssessment,
    TerminalLocalStatus,
)

logger = logging.getLogger(__name__)

MAX_LINEAGE_NODES = 128
MAX_PARENT_NODES = 16
MAX_DATA_COMMITMENTS = 8
MAX_TEXT_BYTES = 512
_HEX = frozenset("0123456789abcdef")


class ResearchLineError(ValueError):
    """Stable fail-closed research-line validation error."""

    def __init__(self, reason: str) -> None:
        logger.error("ResearchLineError state=blocked reason=%s", reason)
        self.reason = reason
        super().__init__(reason)


def build_experiment_lineage_node(
    experiment_root: str,
    parent_nodes: tuple[str, ...],
    doctrine_root: str,
    grammar_root: str,
    baseline_root: str,
    decision_policy_root: str,
    data_commitment_roots: tuple[str, ...],
    prior_outcomes_visible_before_design: tuple[str, ...],
    design_mode: ExperimentDesignMode,
    adaptation_reason: str,
    terminal_local_status: TerminalLocalStatus,
    terminal_outcome_root: str,
) -> ExperimentLineageNode:
    """Build one canonical content-bound node without claiming historical truth."""
    logger.debug("build_experiment_lineage_node entry")
    roots = (
        experiment_root,
        doctrine_root,
        grammar_root,
        baseline_root,
        decision_policy_root,
        terminal_outcome_root,
    )
    if any(not _is_digest(root) for root in roots):
        _reject("node-root")
    parents = _canonical_digest_tuple(parent_nodes, MAX_PARENT_NODES, allow_empty=True, reason="parent-nodes")
    commitments = _canonical_digest_tuple(
        data_commitment_roots,
        MAX_DATA_COMMITMENTS,
        allow_empty=False,
        reason="data-commitments",
    )
    visible = _canonical_digest_tuple(
        prior_outcomes_visible_before_design,
        MAX_LINEAGE_NODES,
        allow_empty=True,
        reason="visible-prior-outcomes",
    )
    if type(design_mode) is not ExperimentDesignMode or type(terminal_local_status) is not TerminalLocalStatus:
        _reject("node-enum")
    _bounded_text(adaptation_reason, allow_empty=True, reason="adaptation-reason")
    if design_mode is ExperimentDesignMode.ISOLATED:
        if parents or visible or adaptation_reason:
            _reject("isolated-node-has-history")
    elif design_mode is ExperimentDesignMode.PREDECLARED_CONTINUATION:
        if not parents or visible or adaptation_reason:
            _reject("predeclared-node-shape")
    elif not parents or not visible or not adaptation_reason:
        _reject("adaptive-node-missing-history")
    draft = ExperimentLineageNode(
        experiment_root,
        parents,
        doctrine_root,
        grammar_root,
        baseline_root,
        decision_policy_root,
        commitments,
        visible,
        design_mode,
        adaptation_reason,
        terminal_local_status,
        terminal_outcome_root,
        "",
    )
    result = replace(draft, node_digest=digest_data(_node_data(draft), "veyra.observer-discovery.lineage-node.v1"))
    logger.debug("build_experiment_lineage_node exit digest=%s", result.node_digest[:12])
    return result


def build_experiment_research_line(
    nodes: tuple[ExperimentLineageNode, ...],
) -> ExperimentResearchLine:
    """Validate and canonicalize one bounded declared experiment DAG."""
    logger.debug("build_experiment_research_line entry")
    if type(nodes) is not tuple or not 1 <= len(nodes) <= MAX_LINEAGE_NODES:
        _reject("lineage-node-count")
    checked = tuple(_validate_node(node) for node in nodes)
    if len({node.node_digest for node in checked}) != len(checked):
        _reject("duplicate-node")
    if len({node.experiment_root for node in checked}) != len(checked):
        _reject("duplicate-experiment-root")
    by_digest = {node.node_digest: node for node in checked}
    if any(parent not in by_digest for node in checked for parent in node.parent_nodes):
        _reject("unknown-parent")
    canonical = _canonical_topological_order(by_digest)
    ancestors: dict[str, frozenset[str]] = {}
    for node in canonical:
        inherited = frozenset(
            parent
            for direct in node.parent_nodes
            for parent in (direct, *ancestors[direct])
        )
        ancestors[node.node_digest] = inherited
        allowed_outcomes = {by_digest[digest].terminal_outcome_root for digest in inherited}
        if not set(node.prior_outcomes_visible_before_design) <= allowed_outcomes:
            _reject("visible-outcome-not-ancestor")
    draft = ExperimentResearchLine(LINEAGE_SCHEMA, canonical, "", LINEAGE_BOUNDARY)
    result = replace(
        draft,
        lineage_digest=digest_data(_lineage_data(draft), "veyra.observer-discovery.research-line.v1"),
    )
    logger.debug("build_experiment_research_line exit nodes=%d", len(result.nodes))
    return result


def validate_experiment_research_line(value: object) -> bool:
    """Replay every node, edge, ancestry disclosure, order, and digest."""
    logger.debug("validate_experiment_research_line entry type=%s", type(value).__name__)
    try:
        valid = (
            type(value) is ExperimentResearchLine
            and value.schema_version == LINEAGE_SCHEMA
            and value.boundary == LINEAGE_BOUNDARY
            and build_experiment_research_line(value.nodes) == value
        )
    except (AttributeError, OverflowError, ResearchLineError, TypeError, ValueError):
        logger.error("validate_experiment_research_line rejected")
        valid = False
    logger.debug("validate_experiment_research_line exit valid=%s", valid)
    return valid


def adaptive_inference_policy(
    policy_id: str,
    policy_family: str,
    evidence_root: str,
    claim_scope: PolicyClaimScope,
) -> AdaptiveInferencePolicy:
    """Capture a named pluggable policy without asserting that it is sound here."""
    logger.debug("adaptive_inference_policy entry")
    _bounded_text(policy_id, allow_empty=False, reason="policy-id")
    _bounded_text(policy_family, allow_empty=False, reason="policy-family")
    if evidence_root and not _is_digest(evidence_root):
        _reject("policy-root")
    if type(claim_scope) is not PolicyClaimScope:
        _reject("policy-scope")
    if claim_scope is PolicyClaimScope.EXPLORATORY_ONLY and evidence_root:
        _reject("exploratory-policy-evidence")
    policy_root = digest_data(
        {
            "policy_id": policy_id,
            "policy_family": policy_family,
            "evidence_root": evidence_root,
            "claim_scope": claim_scope.value,
        },
        "veyra.observer-discovery.adaptive-policy-declaration.v1",
    )
    result = AdaptiveInferencePolicy(policy_id, policy_family, policy_root, evidence_root, claim_scope)
    logger.debug("adaptive_inference_policy exit scope=%s", claim_scope.value)
    return result


def assess_research_line(
    lineage: ExperimentResearchLine,
    terminal_node: str,
    *,
    governed_results: tuple[GovernedEvaluationResult, ...] = (),
    policy: AdaptiveInferencePolicy | None = None,
) -> ResearchLineAssessment:
    """Separate local replay, declared family history, and adaptive validity."""
    logger.debug("assess_research_line entry")
    if not validate_experiment_research_line(lineage) or not _is_digest(terminal_node):
        _reject("assessment-lineage")
    by_digest = {node.node_digest: node for node in lineage.nodes}
    if terminal_node not in by_digest:
        _reject("assessment-terminal")
    if any(terminal_node in node.parent_nodes for node in lineage.nodes):
        _reject("assessment-terminal-not-leaf")
    if type(governed_results) is not tuple or len(governed_results) > MAX_LINEAGE_NODES:
        _reject("assessment-results")
    valid_results: dict[str, GovernedEvaluationResult] = {}
    for result in governed_results:
        if not validate_governed_evaluation_result(result):
            _reject("invalid-governed-result")
        if result.result_digest in valid_results:
            _reject("duplicate-governed-result")
        valid_results[result.result_digest] = result
    terminal = by_digest[terminal_node]
    governed = valid_results.get(terminal.experiment_root)
    local = (
        LocalValidityStatus.ESTABLISHED
        if governed is not None
        and governed.status == GOVERNED_EVALUATION_READY
        and terminal.terminal_local_status is TerminalLocalStatus.LOCALLY_VALID
        and terminal.terminal_outcome_root == governed.terminal_ledger.outcome_digest
        else LocalValidityStatus.NOT_ESTABLISHED
    )
    checked_policy = _validate_policy(policy)
    has_family = len(lineage.nodes) > 1
    claims: tuple[str, ...]
    if not has_family:
        adaptive = AdaptiveValidityStatus.ISOLATED_LOCAL_ONLY
        policy_status = AdaptivePolicyStatus.NOT_REQUIRED_FOR_ISOLATED_LOCAL_RESULT
        claims = ("isolated-local-result-only",)
    else:
        if checked_policy is None:
            adaptive = AdaptiveValidityStatus.NOT_ESTABLISHED
            policy_status = AdaptivePolicyStatus.ABSENT
            claims = ("locally-valid-if-replayed", "family-recorded-relative-to-declared-lineage")
        elif checked_policy.claim_scope is PolicyClaimScope.EXPLORATORY_ONLY:
            adaptive = AdaptiveValidityStatus.EXPLORATORY_NO_INFERENCE_CLAIMED
            policy_status = AdaptivePolicyStatus.EXPLORATORY_ONLY
            claims = ("exploratory-family", "no-significance-or-population-claim")
        else:
            adaptive = AdaptiveValidityStatus.NOT_ESTABLISHED
            policy_status = AdaptivePolicyStatus.DECLARED_UNVERIFIED
            claims = ("named-family-policy-declared", "adaptive-validity-not-established")
    draft = ResearchLineAssessment(
        terminal_node,
        local,
        FamilyRecordingStatus.RECORDED_RELATIVE_TO_DECLARATION,
        adaptive,
        policy_status,
        "" if checked_policy is None else checked_policy.policy_id,
        "" if checked_policy is None else checked_policy.policy_family,
        "" if checked_policy is None else checked_policy.policy_root,
        "" if checked_policy is None else checked_policy.evidence_root,
        False,
        False,
        claims,
        "",
        ASSESSMENT_BOUNDARY,
    )
    result = replace(
        draft,
        assessment_digest=digest_data(_assessment_data(draft), "veyra.observer-discovery.lineage-assessment.v1"),
    )
    logger.debug("assess_research_line exit adaptive=%s", adaptive.value)
    return result


def validate_research_line_assessment(
    assessment: object,
    lineage: ExperimentResearchLine,
    *,
    governed_results: tuple[GovernedEvaluationResult, ...] = (),
    policy: AdaptiveInferencePolicy | None = None,
) -> bool:
    """Replay one assessment from its exact lineage, local results, and policy."""
    logger.debug("validate_research_line_assessment entry type=%s", type(assessment).__name__)
    try:
        valid = (
            type(assessment) is ResearchLineAssessment
            and assess_research_line(
                lineage,
                assessment.terminal_node,
                governed_results=governed_results,
                policy=policy,
            )
            == assessment
        )
    except (AttributeError, OverflowError, ResearchLineError, TypeError, ValueError):
        logger.error("validate_research_line_assessment rejected")
        valid = False
    logger.debug("validate_research_line_assessment exit valid=%s", valid)
    return valid


def _validate_node(node: object) -> ExperimentLineageNode:
    logger.debug("_validate_node entry type=%s", type(node).__name__)
    if type(node) is not ExperimentLineageNode:
        _reject("node-type")
    rebuilt = build_experiment_lineage_node(
        node.experiment_root,
        node.parent_nodes,
        node.doctrine_root,
        node.grammar_root,
        node.baseline_root,
        node.decision_policy_root,
        node.data_commitment_roots,
        node.prior_outcomes_visible_before_design,
        node.design_mode,
        node.adaptation_reason,
        node.terminal_local_status,
        node.terminal_outcome_root,
    )
    if rebuilt != node:
        _reject("node-digest")
    logger.debug("_validate_node exit")
    return rebuilt


def _canonical_topological_order(
    by_digest: dict[str, ExperimentLineageNode],
) -> tuple[ExperimentLineageNode, ...]:
    logger.debug("_canonical_topological_order entry nodes=%d", len(by_digest))
    remaining = set(by_digest)
    completed: set[str] = set()
    ordered: list[ExperimentLineageNode] = []
    while remaining:
        available = sorted(
            (digest for digest in remaining if set(by_digest[digest].parent_nodes) <= completed)
        )
        if not available:
            _reject("lineage-cycle")
        for digest in available:
            ordered.append(by_digest[digest])
            completed.add(digest)
            remaining.remove(digest)
    result = tuple(ordered)
    logger.debug("_canonical_topological_order exit")
    return result


def _validate_policy(policy: AdaptiveInferencePolicy | None) -> AdaptiveInferencePolicy | None:
    logger.debug("_validate_policy entry type=%s", type(policy).__name__)
    if policy is None:
        return None
    if type(policy) is not AdaptiveInferencePolicy:
        _reject("policy-type")
    result = adaptive_inference_policy(
        policy.policy_id,
        policy.policy_family,
        policy.evidence_root,
        policy.claim_scope,
    )
    if result != policy:
        _reject("policy-shape")
    logger.debug("_validate_policy exit")
    return result


def _canonical_digest_tuple(
    value: object,
    limit: int,
    *,
    allow_empty: bool,
    reason: str,
) -> tuple[str, ...]:
    logger.debug("_canonical_digest_tuple entry reason=%s", reason)
    if (
        type(value) is not tuple
        or len(value) > limit
        or (not allow_empty and not value)
        or any(not _is_digest(item) for item in value)
        or tuple(sorted(set(value))) != value
    ):
        _reject(reason)
    logger.debug("_canonical_digest_tuple exit count=%d", len(value))
    return value


def _bounded_text(value: object, *, allow_empty: bool, reason: str) -> str:
    logger.debug("_bounded_text entry reason=%s", reason)
    if type(value) is not str or (not allow_empty and not value):
        _reject(reason)
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError as exc:
        logger.error("_bounded_text encoding rejected reason=%s", reason)
        raise ResearchLineError(reason) from exc
    if size > MAX_TEXT_BYTES:
        _reject(reason)
    logger.debug("_bounded_text exit bytes=%d", size)
    return value


def _is_digest(value: object) -> bool:
    return type(value) is str and len(value) == 64 and all(character in _HEX for character in value)


def _node_data(node: ExperimentLineageNode) -> dict[str, object]:
    return {
        "experiment_root": node.experiment_root,
        "parent_nodes": list(node.parent_nodes),
        "doctrine_root": node.doctrine_root,
        "grammar_root": node.grammar_root,
        "baseline_root": node.baseline_root,
        "decision_policy_root": node.decision_policy_root,
        "data_commitment_roots": list(node.data_commitment_roots),
        "prior_outcomes_visible_before_design": list(node.prior_outcomes_visible_before_design),
        "design_mode": node.design_mode.value,
        "adaptation_reason": node.adaptation_reason,
        "terminal_local_status": node.terminal_local_status.value,
        "terminal_outcome_root": node.terminal_outcome_root,
    }


def _lineage_data(lineage: ExperimentResearchLine) -> dict[str, object]:
    return {
        "schema_version": lineage.schema_version,
        "nodes": [{**_node_data(node), "node_digest": node.node_digest} for node in lineage.nodes],
        "boundary": lineage.boundary,
    }


def _assessment_data(assessment: ResearchLineAssessment) -> dict[str, object]:
    return {
        "terminal_node": assessment.terminal_node,
        "local_validity": assessment.local_validity.value,
        "family_recording": assessment.family_recording.value,
        "adaptive_validity": assessment.adaptive_validity.value,
        "policy_status": assessment.policy_status.value,
        "policy_id": assessment.policy_id,
        "policy_family": assessment.policy_family,
        "policy_root": assessment.policy_root,
        "policy_evidence_root": assessment.policy_evidence_root,
        "significance_wording_allowed": assessment.significance_wording_allowed,
        "population_wording_allowed": assessment.population_wording_allowed,
        "allowed_claims": list(assessment.allowed_claims),
        "boundary": assessment.boundary,
    }


def _reject(reason: str) -> NoReturn:
    raise ResearchLineError(reason)
