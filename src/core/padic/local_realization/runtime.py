"""Hard-first raw replay for P3-N3 local realization and N4 scoped equality."""

from __future__ import annotations

import logging

from ..completion.runtime import padic_completion_judgment
from ..completion.types import PadicCompletionJudgment
from ..family_introduction.runtime import introduce_integer_residue_family
from ..family_introduction.types import N1FamilyJudgment
from .common import digest, exact_shape, reject, role_term_digest, sha
from .derivation import derive_n3_judgment, revalidate_n3_derivation
from .formal import capture_sources, compile_sources, continuity_holds
from .requests import n3_request, n4_request
from .preflight import raw_request_preflight
from .sources import (
    HARD_CAPTURED, HARD_STATIC, THEOREM_IDS, n3_dependency_union,
    n4_dependency_union,
)
from .types import (
    EqualityStatus, FailedBound, FormalFailureKind, N34FormalFailure,
    N34Refuted, N34ResourceLimit, N34Status,
    N3Request, N3Result, N34_NONCLAIMS, N4EqualityJudgment, N4Kind, N4Request,
    N4Result,
)

logger = logging.getLogger(__name__)


def _snapshot_n3(value: N3Request) -> N3Request:
    """Deeply reconstruct one exact raw N3 request."""
    logger.debug("_snapshot_n3 entry")
    raw = exact_shape(value, N3Request, "n3-request")
    try:
        expected = n3_request(raw["n1"], raw["pomega2"], raw["theorem"], raw["policy"])
    except (KeyError, AttributeError, TypeError):
        reject("n3-request-fields-invalid")
    if value != expected:
        reject("n3-request-drift")
    logger.debug("_snapshot_n3 exit")
    return expected


def _snapshot_n4(value: N4Request) -> N4Request:
    """Deeply reconstruct one exact raw N4 request."""
    logger.debug("_snapshot_n4 entry")
    raw = exact_shape(value, N4Request, "n4-request")
    try:
        expected = n4_request(raw["left_n1"], raw["right_n1"], raw["pomega2"],
            raw["all_depth"], raw["theorem"], raw["policy"])
    except (KeyError, AttributeError, TypeError):
        reject("n4-request-fields-invalid")
    if value != expected:
        reject("n4-request-drift")
    logger.debug("_snapshot_n4 exit")
    return expected


def _agreement(n1, pomega2) -> bool:
    """Check exact prime/doctrine/source endpoint agreement after snapshots."""
    logger.debug("_agreement entry")
    result = (n1.prime == pomega2.prime and n1.doctrine == pomega2.doctrine
        and n1.theorem_source.pomega2_artifact_path_id == pomega2.theorem_source.artifact_path_id
        and n1.theorem_source.pomega2_artifact_sha256 == pomega2.theorem_source.artifact_sha256
        and n1.doctrine.family_class_id == pomega2.doctrine.family_class_id
        and n1.doctrine.carrier_id == pomega2.doctrine.carrier_id)
    logger.debug("_agreement exit result=%s", result)
    return result


def _charge(request, captured: tuple[bytes, ...], ledger):
    """Atomically charge all captured bytes and full raw/minimal graph shapes."""
    logger.debug("_charge entry")
    raw_ledgers = ((request.n1.ledger, request.pomega2.ledger)
        if type(request) is N3Request else
        (request.left_n1.ledger, request.right_n1.ledger, request.pomega2.ledger))
    raw_rows = sum(len(x.ordered_rows) if hasattr(x, "ordered_rows") else len(x.rows)
                   for x in raw_ledgers)
    raw_edges = sum(len(x.direct_edges) if hasattr(x, "direct_edges") else
                    sum(len(row.direct_dependencies) for row in x.rows) for x in raw_ledgers)
    if type(request) is N4Request:
        raw_rows += len(request.all_depth.ordered_rows)
        raw_edges += sum(len(row.direct_dependencies) for row in request.all_depth.ordered_rows)
    rows = len(ledger.ordered_rows)
    edges = sum(len(x.direct_dependencies) for x in ledger.ordered_rows)
    captured_bytes = sum(len(x) for x in captured)
    static = captured_bytes + 256 * (raw_rows + rows) + 64 * (raw_edges + edges)
    if captured_bytes > HARD_CAPTURED or static > HARD_STATIC or rows > 256 or edges > 512:
        reject("hard-resource-envelope")
    result = (captured_bytes, static, rows, edges)
    logger.debug("_charge exit captured=%d static=%d rows=%d edges=%d", *result)
    return result


def _refusal(request, charge):
    """Return the first fixed-priority policy refusal."""
    logger.debug("_refusal entry")
    kinds = (FailedBound.CAPTURED_BYTES, FailedBound.STATIC_COST,
             FailedBound.LEDGER_ROWS, FailedBound.LEDGER_EDGES)
    caps = (request.policy.max_captured_bytes, request.policy.max_static_cost,
            request.policy.max_ledger_rows, request.policy.max_ledger_edges)
    result = next(((k, n, cap) for k, n, cap in zip(kinds, charge, caps, strict=True)
                   if n > cap), None)
    logger.debug("_refusal exit failed=%s", None if result is None else result[0].value)
    return result


def _resource(request, failure) -> N34ResourceLimit:
    """Construct a payload-free first-bound refusal."""
    logger.debug("_resource entry")
    kind, required, allowed = failure
    value = digest("veyra.p3n3n4.resource.v1", (("request", request.request_digest.encode()),
        ("bound", kind.value.encode()), ("required", str(required).encode()),
        ("allowed", str(allowed).encode())))
    result = N34ResourceLimit(N34Status.RESOURCE_LIMIT, kind, required, allowed,
                              request.request_digest, value)
    logger.debug("_resource exit")
    return result


def _refuted(request, reason: str) -> N34Refuted:
    """Construct one exact semantic mismatch result."""
    logger.debug("_refuted entry reason=%s", reason)
    value = digest("veyra.p3n3n4.refuted.v1", (("request", request.request_digest.encode()),
        ("reason", reason.encode())))
    result = N34Refuted(N34Status.REFUTED, reason, request.request_digest, value)
    logger.debug("_refuted exit")
    return result


def _failure(request, kind: FormalFailureKind, output: bytes, diagnostic: str) -> N34FormalFailure:
    """Construct one sanitized operational failure without semantic relabeling."""
    logger.debug("_failure entry kind=%s", kind.value)
    attempt = digest("veyra.p3n3n4.formal-attempt.v1", (
        ("request", request.request_digest.encode()), ("kind", kind.value.encode()),
        ("output", sha(output).encode())))
    result = N34FormalFailure(kind, request.request_digest, attempt, diagnostic)
    logger.debug("_failure exit")
    return result


def _replay_dependencies(request) -> tuple[tuple[N1FamilyJudgment, ...],
                                            PadicCompletionJudgment] | None:
    """Freshly replay complete raw N1/PΩ2 package ledgers, never old judgments."""
    logger.debug("_replay_dependencies entry")
    n1s = (request.n1,) if type(request) is N3Request else (request.left_n1, request.right_n1)
    n1_results = tuple(introduce_integer_residue_family(x) for x in n1s)
    p2_result = padic_completion_judgment(request.pomega2)
    if any(type(x) is not N1FamilyJudgment for x in n1_results) or type(p2_result) is not PadicCompletionJudgment:
        logger.error("_replay_dependencies dependency replay refused or failed")
        return None
    logger.debug("_replay_dependencies exit n1=%d", len(n1_results))
    return n1_results, p2_result


def _formal(request, captured, ledger):
    """Compile owned source and require exact closure plus source continuity."""
    logger.debug("_formal entry")
    outcome = compile_sources(request, captured)
    if outcome.kind is not None:
        return _failure(request, outcome.kind, outcome.output,
                        f"formal execution {outcome.kind.value}")
    if not continuity_holds(request, captured):
        return _failure(request, FormalFailureKind.CONTINUITY_DRIFT, outcome.output,
                        "formal source continuity drift")
    used = ((*THEOREM_IDS[:2], "p3n3Concrete") if type(request) is N3Request else
            (*THEOREM_IDS, *request.all_depth.theorem_ids, "p3n4Concrete"))
    rows = dict(outcome.axiom_rows)
    closure = tuple(sorted({axiom for name in used for axiom in rows.get(name, ())}))
    if any(name not in rows for name in used) or closure != ledger.theorem_axiom_closure:
        return _failure(request, FormalFailureKind.COMPILE_ERROR, outcome.output,
                        "compiler and minimal-ledger axiom closure mismatch")
    logger.debug("_formal exit rows=%d", len(outcome.axiom_rows))
    return outcome


def local_realization_judgment(raw_request: N3Request) -> N3Result:
    """Replay raw N1/PΩ2 and establish one exact local realization through THM007."""
    logger.debug("local_realization_judgment entry")
    _, precharge, refusal = raw_request_preflight(raw_request)
    if refusal is not None:
        return _resource(raw_request, refusal)
    request = _snapshot_n3(raw_request)
    ledger = n3_dependency_union(request.n1, request.pomega2)
    captured = capture_sources(request)
    charge = _charge(request, captured, ledger)
    if charge != (precharge.captured_bytes, precharge.static_cost,
                  precharge.ledger_rows, precharge.ledger_edges):
        reject("n3-preflight-charge-continuity-drift")
    refusal = _refusal(request, charge)
    if refusal is not None:
        return _resource(request, refusal)
    replay = _replay_dependencies(request)
    if replay is None:
        return _failure(request, FormalFailureKind.DEPENDENCY_REPLAY_FAILURE, b"",
                        "raw dependency replay did not establish")
    formal = _formal(request, captured, ledger)
    if type(formal) is N34FormalFailure:
        return formal
    if not _agreement(request.n1, request.pomega2):
        return _refuted(request, "n1-pomega2-endpoint-mismatch")
    result = derive_n3_judgment(request, replay[0][0], replay[1], ledger)
    logger.debug("local_realization_judgment exit")
    return result


def scoped_carrier_equality_judgment(raw_request: N4Request) -> N4Result:
    """Use owned all-depth evidence and THM009 for ledger-relative carrier equality."""
    logger.debug("scoped_carrier_equality_judgment entry")
    _, precharge, refusal = raw_request_preflight(raw_request)
    if refusal is not None:
        return _resource(raw_request, refusal)
    request = _snapshot_n4(raw_request)
    ledger = n4_dependency_union(request.left_n1, request.right_n1,
                                 request.pomega2, request.all_depth)
    captured = capture_sources(request)
    charge = _charge(request, captured, ledger)
    if charge != (precharge.captured_bytes, precharge.static_cost,
                  precharge.ledger_rows, precharge.ledger_edges):
        reject("n4-preflight-charge-continuity-drift")
    refusal = _refusal(request, charge)
    if refusal is not None:
        return _resource(request, refusal)
    replay = _replay_dependencies(request)
    if replay is None:
        return _failure(request, FormalFailureKind.DEPENDENCY_REPLAY_FAILURE, b"",
                        "raw dependency replay did not establish")
    formal = _formal(request, captured, ledger)
    if type(formal) is N34FormalFailure:
        return formal
    if not (_agreement(request.left_n1, request.pomega2)
            and _agreement(request.right_n1, request.pomega2)):
        return _refuted(request, "n4-package-endpoint-mismatch")
    role_requests = (n3_request(request.left_n1, request.pomega2,
        request.theorem, request.policy), n3_request(request.right_n1,
        request.pomega2, request.theorem, request.policy))
    role_ledgers = (n3_dependency_union(request.left_n1, request.pomega2),
                    n3_dependency_union(request.right_n1, request.pomega2))
    role_n3 = tuple(derive_n3_judgment(role_request, n1_replay, replay[1], role_ledger)
        for role_request, n1_replay, role_ledger in
        zip(role_requests, replay[0], role_ledgers, strict=True))
    role_n3 = tuple(revalidate_n3_derivation(
        role_request, n1_replay, replay[1], role_ledger, value)
        for role_request, n1_replay, role_ledger, value in
        zip(role_requests, replay[0], role_ledgers, role_n3, strict=True))
    terms = tuple(role_term_digest(value.realized_term_digest, role)
                  for value, role in zip(role_n3, ("left", "right"), strict=True))
    identities = (role_n3[0].family_term_digest, role_n3[1].family_term_digest,
                  *terms, role_n3[0].pomega2_package_digest,
                  role_n3[1].pomega2_package_digest)
    expected = (request.all_depth.left_family_source_digest,
                request.all_depth.right_family_source_digest,
                request.all_depth.left_realized_term_digest,
                request.all_depth.right_realized_term_digest,
                request.pomega2.package_digest, request.pomega2.package_digest)
    if identities != expected:
        return _refuted(request, "all-depth-premise-role-n3-identity-mismatch")
    evidence = digest("veyra.p3n4.equality-evidence.v1", (("left", terms[0].encode()),
        ("right", terms[1].encode()), ("premise", request.all_depth.source_digest.encode()),
        ("thm009", request.pomega2.theorem_source.theorem_ids[8].encode()),
        ("ledger", ledger.ledger_digest.encode())))
    judgment = digest("veyra.p3n4.judgment.v1", (("request", request.request_digest.encode()),
        ("evidence", evidence.encode()), ("ledger", ledger.ledger_digest.encode())))
    if len({*terms, request.all_depth.source_digest, evidence, judgment}) != 5:
        raise RuntimeError("internal N4 digest-domain collision")
    result = N4EqualityJudgment(N34Status.ESTABLISHED,
        N4Kind.SCOPED_CARRIER_EQUALITY_ESTABLISHED_RELATIVE_TO_LEDGER,
        EqualityStatus.ESTABLISHED_RELATIVE_TO_LEDGER, *terms,
        request.all_depth.source_digest, request.theorem.source_digest,
        ledger.ledger_digest, evidence, 0, N34_NONCLAIMS, judgment)
    logger.debug("scoped_carrier_equality_judgment exit")
    return result
