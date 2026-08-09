"""True row-free P3-N0 genealogy-unavailable source and request lane."""

from __future__ import annotations

import logging

from ...padic.completion.prime import prime_source
from .attestation import (
    n0_theorem_source, validate_theorem_source,
)
from .common import (
    N0ValidationError, digest, exact_hex, exact_int, exact_shape, exact_text, reject,
)
from .types import (
    N0GenealogyUnavailable, N0UnavailableBridgeRequest, N0UnavailableSource,
)
from .sources import n0_policy, observer_doctrine
from .types import (
    ActualizationStatus, N0Policy, PremiseStatus, RoleStatus,
    UnavailableFamilyFiniteBridgeEvidence,
)

logger = logging.getLogger(__name__)


def unavailable_bridge_evidence(reason="raw-family-bridge-unavailable"):
    """Return exact evidence of missing family-to-finite bridge genealogy."""
    logger.debug("unavailable_bridge_evidence entry")
    reason = exact_text(reason, "n0-unavailable-bridge-reason")
    value = digest("veyra.p3n0.unavailable-bridge.v2", (("reason", reason.encode()),))
    result = UnavailableFamilyFiniteBridgeEvidence("p3n0-unavailable-bridge-v2", reason, value)
    logger.debug("unavailable_bridge_evidence exit")
    return result


def unavailable_bridge_status(evidence) -> PremiseStatus:
    """Classify exact absence as genealogy OPEN, never as doctrine rejection."""
    logger.debug("unavailable_bridge_status entry")
    raw = exact_shape(evidence, UnavailableFamilyFiniteBridgeEvidence,
                      "n0-unavailable-bridge-evidence")
    exact_text(raw["version"], "n0-unavailable-version", maximum=64)
    exact_text(raw["reason"], "n0-unavailable-reason")
    exact_hex(raw["evidence_digest"], "n0-unavailable-evidence")
    if evidence != unavailable_bridge_evidence(raw["reason"]):
        reject("n0-unavailable-bridge-drift")
    logger.debug("unavailable_bridge_status exit status=open")
    return PremiseStatus.OPEN


def unavailable_n0_source(p=2, n=0, lineage_id="n0-lineage-alpha", *, policy=None,
                          admitted=True, reason="raw-family-bridge-unavailable"):
    """Build a source whose digest binds absence evidence without any positive bridge."""
    logger.debug("unavailable_n0_source entry p=%r n=%r", p, n)
    p = exact_int(p, "prime", minimum=2, maximum=65521)
    n = exact_int(n, "depth", maximum=64)
    lineage_id = exact_text(lineage_id, "lineage")
    if type(admitted) is not bool or not admitted:
        reject("n0-unavailable-source-requires-admitted-doctrine")
    selected = n0_policy() if policy is None else policy
    if type(selected) is not N0Policy:
        reject("n0-unavailable-policy-exact-type-required")
    caps = tuple(getattr(selected, name) for name in (
        "max_depth", "max_integer_bits", "max_exponent", "max_modulus_bits",
        "max_events", "max_parent_edges", "max_access_edges", "max_evaluations",
        "max_families", "max_finite_rows", "max_reductions", "max_assumptions",
        "max_ledger_bytes", "max_captured_bytes", "max_output_bytes", "timeout_seconds",
    ))
    if selected != n0_policy(*caps):
        reject("n0-unavailable-policy-drift")
    try:
        prime_source(p)
    except N0ValidationError:
        raise
    except Exception as exc:
        logger.exception("unavailable_n0_source prime rejection")
        reject(f"n0-unavailable-prime-rejected-{type(exc).__name__}")
    evidence = unavailable_bridge_evidence(reason)
    doctrine, theorem = observer_doctrine(admitted), n0_theorem_source()
    value = digest("veyra.p3n0.unavailable-source.v1", (
        ("p", str(p).encode()), ("n", str(n).encode()), ("lineage", lineage_id.encode()),
        ("doctrine", doctrine.doctrine_digest.encode()),
        ("policy", selected.policy_digest.encode()),
        ("theorem", theorem.source_digest.encode()),
        ("bridge-evidence", evidence.evidence_digest.encode()),
    ))
    result = N0UnavailableSource(
        p, n, lineage_id, doctrine, selected, theorem, evidence, value,
    )
    logger.debug("unavailable_n0_source exit")
    return result


def validate_unavailable_source(source) -> N0UnavailableSource:
    """Validate the exact row-free source and freshly reconstruct its digest."""
    logger.debug("validate_unavailable_source entry")
    raw = exact_shape(source, N0UnavailableSource, "n0-unavailable-source")
    exact_int(raw["prime"], "n0-unavailable-prime", minimum=2, maximum=65521)
    exact_int(raw["depth"], "n0-unavailable-depth", maximum=64)
    exact_text(raw["lineage_id"], "n0-unavailable-lineage")
    if type(raw["policy"]) is not N0Policy:
        reject("n0-unavailable-policy-exact-type-required")
    from .types import (
        DoctrineAdmission, PrimePowerObserverDoctrine,
    )
    if type(raw["doctrine"]) is not PrimePowerObserverDoctrine:
        reject("n0-unavailable-doctrine-exact-type-required")
    validate_theorem_source(raw["theorem_source"])
    unavailable_bridge_status(raw["bridge_evidence"])
    exact_hex(raw["source_digest"], "n0-unavailable-source-digest")
    if raw["doctrine"].admission is not DoctrineAdmission.ADMITTED:
        reject("n0-unavailable-source-requires-admitted-doctrine")
    expected = unavailable_n0_source(
        raw["prime"], raw["depth"], raw["lineage_id"], policy=raw["policy"],
        admitted=True, reason=raw["bridge_evidence"].reason,
    )
    if source != expected:
        reject("n0-unavailable-source-drift")
    logger.debug("validate_unavailable_source exit")
    return source


def unavailable_bridge_request(source, reason=None):
    """Bind a true unavailable source and its evidence into one replayable request."""
    logger.debug("unavailable_bridge_request entry")
    source = validate_unavailable_source(source)
    chosen = source.bridge_evidence.reason if reason is None else exact_text(
        reason, "n0-unavailable-request-reason",
    )
    if chosen != source.bridge_evidence.reason:
        reject("n0-unavailable-request-reason-drift")
    value = digest("veyra.p3n0.unavailable-request.v3", (
        ("source", source.source_digest.encode()),
        ("evidence", source.bridge_evidence.evidence_digest.encode()),
        ("reason", chosen.encode()),
    ))
    result = N0UnavailableBridgeRequest(
        source, chosen, source.bridge_evidence.evidence_digest, value,
    )
    logger.debug("unavailable_bridge_request exit")
    return result


def validate_unavailable_request(request) -> N0UnavailableBridgeRequest:
    """Freshly replay an exact unavailable request without a positive bridge builder."""
    logger.debug("validate_unavailable_request entry")
    raw = exact_shape(request, N0UnavailableBridgeRequest, "n0-unavailable-request")
    exact_text(raw["reason"], "n0-unavailable-request-reason")
    exact_hex(raw["evidence_digest"], "n0-unavailable-request-evidence")
    exact_hex(raw["request_digest"], "n0-unavailable-request-digest")
    expected = unavailable_bridge_request(raw["source"], raw["reason"])
    if request != expected:
        reject("n0-unavailable-request-drift")
    logger.debug("validate_unavailable_request exit")
    return request


def run_unavailable_bridge(request):
    """Return only genealogy-unavailable OPEN, with no birth, token, N1, or N2 evidence."""
    logger.debug("run_unavailable_bridge entry")
    request = validate_unavailable_request(request)
    source = request.source
    if unavailable_bridge_status(source.bridge_evidence) is not PremiseStatus.OPEN:
        reject("n0-unavailable-status-drift")
    run = digest("veyra.p3n0.unavailable-run.v3", (
        ("source", source.source_digest.encode()),
        ("request", request.request_digest.encode()),
    ))
    result_digest = digest("veyra.p3n0.genealogy-unavailable.v1", (
        ("run", run.encode()), ("evidence", request.evidence_digest.encode()),
    ))
    result = N0GenealogyUnavailable(
        source.source_digest, request.request_digest, run, request.evidence_digest,
        PremiseStatus.OPEN, RoleStatus.OPEN, ActualizationStatus.OPEN, result_digest,
    )
    logger.debug("run_unavailable_bridge exit status=open")
    return result
