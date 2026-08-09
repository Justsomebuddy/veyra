"""Hard-first pending/replay/outcome runtime for isolated P3-N0."""

from __future__ import annotations

import hashlib
import logging

from ...observer.network.core import observer_network_judgment
from ...padic.family_introduction.core import introduce_integer_residue_family
from ...padic.family_introduction.types import (
    N1EvidenceProvenance, N1EvidenceStatus, N1FamilyJudgment, N1FormalFailure,
    N1JudgmentKind, N1ResourceLimit,
)
from .attestation import validate_attestation
from .common import (
    N0ValidationError, digest, indexed, reject,
)
from .formal import (
    capture_size_required, capture_sources, compile_sources, continuity_holds,
)
from .history import (
    finalize_history, pending_histories, replay_evidence, rho_structural_id,
)
from .history_validation import (
    access_status, audit_counterfactual_pair, audit_history, validate_history,
)
from .outcomes import bound_postbirth_ledger
from .types import N0DoctrineOpen
from .preflight import hard_first
from .resource import nested_resource_bound
from .sources import exact_n0_source, n0_policy
from .types import (
    ActualizationStatus, BoundaryStatus, DoctrineAdmission, FailedBound,
    FormalFailureKind, N0FormalFailure, N0Premises,
    N0ResourceLimit, N0_NONCLAIMS, PremiseStatus,
    PrimePowerObserverActualizationJudgment, RoleStatus,
)
from ..reduction_network.core import prime_power_reduction_judgment
from ..reduction_network.types import (
    FiniteRelation, N2FormalFailure, N2ResourceLimit, PrimePowerReductionJudgment,
)

logger = logging.getLogger(__name__)


def _resource(source, bound, required, allowed, nested=None):
    """Return a payload-free outer refusal while retaining an exact native terminal."""
    logger.debug("_resource entry bound=%s", bound.value)
    run = digest("veyra.p3n0.run.v2", (("source", source.source_digest.encode()),))
    value = digest("veyra.p3n0.resource.v2", (
        ("source", source.source_digest.encode()), ("bound", bound.value.encode()),
        ("run", run.encode()), ("required", str(required).encode()),
        ("allowed", str(allowed).encode()),
        ("nested", b"none" if nested is None else repr(nested).encode()),
    ))
    result = N0ResourceLimit(bound, required, allowed, source.source_digest, run, nested, value)
    logger.debug("_resource exit")
    return result


def _formal_failure(source, kind, diagnostic, nested=None, payload=b""):
    """Preserve an operational failure instead of inventing semantic OPEN."""
    logger.debug("_formal_failure entry kind=%s", kind.value)
    run = digest("veyra.p3n0.run.v2", (("source", source.source_digest.encode()),))
    attempt = digest("veyra.p3n0.formal-attempt.v2", (
        ("source", source.source_digest.encode()), ("kind", kind.value.encode()),
        ("run", run.encode()),
        ("output-sha", hashlib.sha256(payload).hexdigest().encode()),
        ("nested", b"none" if nested is None else repr(nested).encode()),
    ))
    result = N0FormalFailure(kind, source.source_digest, run, nested, diagnostic[:256], attempt)
    logger.debug("_formal_failure exit")
    return result


def _snapshot_source(source):
    """Rebuild the complete canonical raw envelope only after hard preflight."""
    logger.debug("_snapshot_source entry")
    policy = source.policy
    caps = tuple(getattr(policy, name) for name in (
        "max_depth", "max_integer_bits", "max_exponent", "max_modulus_bits",
        "max_events", "max_parent_edges", "max_access_edges", "max_evaluations",
        "max_families", "max_finite_rows", "max_reductions", "max_assumptions",
        "max_ledger_bytes", "max_captured_bytes", "max_output_bytes", "timeout_seconds",
    ))
    if policy != n0_policy(*caps):
        reject("n0-policy-drift")
    try:
        expected = exact_n0_source(
            source.prime, source.depth, source.lineage_id, policy=policy,
            admitted=source.doctrine.admission is DoctrineAdmission.ADMITTED,
        )
    except N0ValidationError:
        raise
    except Exception as exc:
        logger.exception("_snapshot_source foreign rejection")
        reject(f"n0-raw-package-rejected-{type(exc).__name__}")
    if source != expected:
        reject("n0-source-drift")
    logger.debug("_snapshot_source exit")
    return expected


def _replay_n1(source):
    """Freshly establish and bridge all three exact N1 families."""
    logger.debug("_replay_n1 entry")
    results, rows = [], {row.package_digest: row for row in source.bridge.rows}
    for package in source.n1_packages:
        result = introduce_integer_residue_family(package)
        if type(result) in (N1ResourceLimit, N1FormalFailure):
            logger.debug("_replay_n1 terminal=%s", type(result).__name__)
            return tuple(results), result
        if (type(result) is not N1FamilyJudgment
                or result.kind is not N1JudgmentKind.ALL_DEPTH_FAMILY
                or result.status is not N1EvidenceStatus.ESTABLISHED
                or result.provenance is not N1EvidenceProvenance.FORMALLY_DERIVED
                or result.coordinate_totality is not N1EvidenceStatus.ESTABLISHED
                or result.all_reductions_compatible is not N1EvidenceStatus.ESTABLISHED
                or result.prime_digest != package.prime.source_digest
                or result.integer_digest != package.integer.source_digest
                or result.doctrine_digest != package.doctrine.doctrine_digest
                or result.theorem_source_digest != package.theorem_source.source_digest
                or result.package_digest != package.package_digest
                or result.ledger_digest != package.ledger.ledger_digest):
            reject("n0-n1-positive-contract-drift")
        row = rows.get(package.package_digest)
        if row is None or row.family_term_digest != result.family_term_digest:
            reject("n0-family-bridge-term-binding-drift")
        by_depth = {item.depth: item.residue for item in row.finite_family.coordinates}
        if any(by_depth.get(depth) != package.integer.z % source.prime ** (depth + 1)
               for depth in source.scope.depths):
            reject("n0-family-bridge-coordinate-drift")
        results.append(result)
    logger.debug("_replay_n1 exit count=%d", len(results))
    return tuple(results), None


def _replay_n2(source):
    """Freshly run both P3-T siblings and both N2-F packages before any outcome event."""
    logger.debug("_replay_n2 entry")
    results, networks, arrows = [], [], []
    lanes = (
        (source.strict_package, FiniteRelation.STRICT_REFINEMENT_ON_EXACT_FINITE_SCOPE),
        (source.open_package, FiniteRelation.OPEN),
    )
    for wrapper, expected_relation in lanes:
        if wrapper.network_source != wrapper.raw_package.finite.p3t_raw_source:
            reject("n0-n2f-network-binding-drift")
        network = observer_network_judgment(wrapper.network_source, wrapper.network_policy)
        if network.source_digest != wrapper.network_source.network_digest or network.promotions != 0:
            reject("n0-p3t-replay-contract-drift")
        result = prime_power_reduction_judgment(wrapper.raw_package)
        if type(result) in (N2ResourceLimit, N2FormalFailure):
            logger.debug("_replay_n2 terminal=%s", type(result).__name__)
            return tuple(results), tuple(networks), tuple(arrows), result
        if (type(result) is not PrimePowerReductionJudgment or result.promotions != 0
                or result.p3t_source_digest != wrapper.network_source.network_digest
                or result.theorem_source_digest != wrapper.raw_package.theorem.source_digest
                or result.ledger_digest != wrapper.raw_package.ledger.ledger_digest):
            reject("n0-n2-positive-contract-drift")
        arrow = next((item for item in result.finite_arrows
                      if (item.fine_depth, item.coarse_depth) == source.scope.arrow), None)
        if arrow is None or arrow.relation is not expected_relation:
            reject("n0-n2f-expected-arrow-drift")
        results.append(result)
        networks.append(network)
        arrows.append(arrow)
    logger.debug("_replay_n2 exit count=%d", len(results))
    return tuple(results), tuple(networks), tuple(arrows), None


def _doctrine_open(source, n1_results, attestation):
    """Return OPEN without constructing birth, token, suffix, or N2 outcome."""
    logger.debug("_doctrine_open entry")
    run = digest("veyra.p3n0.nonadmitted-run.v2", (
        ("source", source.source_digest.encode()),
        ("attestation", attestation.attestation_digest.encode()),
        *indexed("n1", (item.judgment_digest for item in n1_results)),
    ))
    result_digest = digest("veyra.p3n0.nonadmitted-open.v2", (
        ("run", run.encode()), ("doctrine", source.doctrine.doctrine_digest.encode()),
    ))
    result = N0DoctrineOpen(
        source.source_digest, run, source.doctrine.doctrine_digest,
        PremiseStatus.ESTABLISHED, RoleStatus.OPEN, ActualizationStatus.OPEN, result_digest,
    )
    logger.debug("_doctrine_open exit")
    return result


def _terminal_nested(source, terminal):
    """Map a native N1/N2 terminal without exposing sibling partial evidence."""
    logger.debug("_terminal_nested entry type=%s", type(terminal).__name__)
    if type(terminal) is N1ResourceLimit:
        result = _resource(source, nested_resource_bound(terminal),
                           terminal.required_value, terminal.allowed_value, terminal)
    elif type(terminal) is N2ResourceLimit:
        result = _resource(source, nested_resource_bound(terminal),
                           terminal.required, terminal.allowed, terminal)
    else:
        result = _formal_failure(source, FormalFailureKind(terminal.kind.value),
                                 terminal.diagnostic, terminal)
    logger.debug("_terminal_nested exit")
    return result


def prime_power_observer_actualization(raw_source):
    """Execute A-HAP with outcome creation strictly after fresh P3-T/N2 replay."""
    logger.debug("prime_power_observer_actualization entry")
    refusal = hard_first(raw_source)
    if refusal is not None:
        result = _resource(raw_source, *refusal)
        logger.debug("prime_power_observer_actualization terminal preflight-resource")
        return result
    source = _snapshot_source(raw_source)
    required = capture_size_required(source)
    if required > source.policy.max_captured_bytes:
        result = _resource(source, FailedBound.CAPTURED_BYTES, required,
                           source.policy.max_captured_bytes)
        logger.debug("prime_power_observer_actualization terminal preopen-resource")
        return result
    captured = capture_sources(source)
    formal = compile_sources(captured, source.policy.timeout_seconds, source.policy.max_output_bytes)
    if formal.kind is not None:
        result = _formal_failure(source, formal.kind, f"formal {formal.kind.value}",
                                 payload=formal.output)
        logger.debug("prime_power_observer_actualization terminal formal=%s", formal.kind.value)
        return result
    if formal.attestation is None:
        reject("n0-formal-success-attestation-missing")
    attestation = validate_attestation(source.theorem_source, formal.attestation)
    if not continuity_holds(source, captured):
        result = _formal_failure(source, FormalFailureKind.CONTINUITY_DRIFT,
                                 "post-capture continuity drift")
        logger.debug("prime_power_observer_actualization terminal capture-drift")
        return result
    n1_results, terminal = _replay_n1(source)
    if terminal is not None:
        result = _terminal_nested(source, terminal)
        logger.debug("prime_power_observer_actualization terminal n1")
        return result
    if source.doctrine.admission is DoctrineAdmission.NOT_ADMITTED:
        result = _doctrine_open(source, n1_results, attestation)
        logger.debug("prime_power_observer_actualization terminal doctrine-open")
        return result
    pending = pending_histories(source)
    n2_results, networks, arrows, terminal = _replay_n2(source)
    if terminal is not None:
        result = _terminal_nested(source, terminal)
        logger.debug("prime_power_observer_actualization terminal n2")
        return result
    histories = tuple(finalize_history(source, pending[i], replay_evidence(
        source, pending[i], networks[i], n2_results[i], arrows[i],
    )) for i in range(2))
    for i, history in enumerate(histories):
        validate_history(source, history, networks[i], n2_results[i], arrows[i])
    strict, opened = histories
    audits = (*audit_history(source, strict).values(), *audit_history(source, opened).values())
    if (access_status(source, strict) != "established"
            or access_status(source, opened) != "established"
            or audit_counterfactual_pair(source, strict, opened) is not PremiseStatus.ESTABLISHED
            or any(item is not PremiseStatus.ESTABLISHED for item in audits)):
        reject("n0-canonical-history-audit-drift")
    if not continuity_holds(source, captured):
        result = _formal_failure(source, FormalFailureKind.CONTINUITY_DRIFT,
                                 "post-replay continuity drift")
        logger.debug("prime_power_observer_actualization terminal replay-drift")
        return result
    established = PremiseStatus.ESTABLISHED
    premises = N0Premises(*(established for _ in range(7)))
    run = digest("veyra.p3n0.run.v2", (("source", source.source_digest.encode()),))
    bound = bound_postbirth_ledger(strict, opened)
    judgment = digest("veyra.p3n0.judgment.v2", (
        ("source", source.source_digest.encode()), ("run", run.encode()),
        ("strict-history", strict.history_digest.encode()),
        ("open-history", opened.history_digest.encode()),
        ("strict-outcome", strict.outcome_digest.encode()),
        ("open-outcome", opened.outcome_digest.encode()),
        ("strict-efficacy", strict.efficacy_digest.encode()),
        ("open-efficacy", opened.efficacy_digest.encode()),
        ("bound-ledger", bound.ledger_digest.encode()),
        ("attestation", attestation.attestation_digest.encode()),
        *indexed("n1", (x.judgment_digest for x in n1_results)),
        *indexed("n2", (x.judgment_digest for x in n2_results)),
    ))
    result = PrimePowerObserverActualizationJudgment(
        premises, RoleStatus.ESTABLISHED_RELATIVE_TO_DOCTRINE,
        ActualizationStatus.ESTABLISHED_RELATIVE_TO_FINITE_ARITHMETIC_HISTORY,
        FiniteRelation.STRICT_REFINEMENT_ON_EXACT_FINITE_SCOPE.value,
        FiniteRelation.OPEN.value, run, rho_structural_id(source), source.scope.scope_digest,
        strict.birth_core_digest, strict.historical_token_id,
        strict.history_digest, opened.history_digest,
        strict.outcome_digest, opened.outcome_digest,
        strict.efficacy_digest, opened.efficacy_digest, bound, attestation,
        n1_results, n2_results, BoundaryStatus.OPEN, BoundaryStatus.NOT_ESTABLISHED,
        BoundaryStatus.NOT_CLAIMED, BoundaryStatus.NOT_CLAIMED, 0, N0_NONCLAIMS, judgment,
    )
    logger.debug("prime_power_observer_actualization exit")
    return result
