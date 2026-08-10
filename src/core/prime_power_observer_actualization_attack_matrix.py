"""Exact-reason 24-base hostile mutation matrix for isolated P3-N0."""

from __future__ import annotations

from dataclasses import dataclass, replace
import logging
from pathlib import Path
import tempfile
from unittest.mock import patch

from .observer_network import observer_network_judgment
from .padic_completion_prime import prime_source
from .prime_power_observer_actualization_attestation import ARTIFACT_PATH, ARTIFACT_SHA256
from .prime_power_observer_actualization_common import N0ValidationError, digest, indexed
from .prime_power_observer_actualization_formal import N0CompileOutcome, _capture_one
from .prime_power_observer_actualization_history import REQUIRED_ACCESS, _event, rehash_history
from .prime_power_observer_actualization_counterfactuals import counterfactual_histories
from .prime_power_observer_actualization_history_validation import (
    audit_counterfactual_pair, audit_history, validate_history,
)
from .prime_power_observer_actualization_pressure import (
    discrimination_candidate, refute_discrimination, refute_separator, separator_candidate,
)
from .prime_power_observer_actualization_open_types import N0GenealogyUnavailable
from .prime_power_observer_actualization_unavailable import (
    run_unavailable_bridge, unavailable_bridge_request, unavailable_n0_source,
)
from .prime_power_observer_actualization_result_validation import _bound_positive
from .prime_power_observer_actualization_runtime import prime_power_observer_actualization
from .prime_power_observer_actualization_sources import exact_n0_source
from .prime_power_observer_actualization_types import (
    BoundaryStatus, FailedBound, FormalFailureKind, N0AccessEdge, N0Event,
    N0FormalFailure, N0ResourceLimit, PremiseStatus,
)
from .paths import PROJECT_ROOT

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class AttackSubmission:
    base_id: str
    variant: str
    expected: str
    actual: str
    passed: bool


def _submission(base, variant, expected, passed):
    """Record one actually executed mutation with explicit state logging."""
    logger.debug("_submission entry base=%s variant=%s", base, variant)
    logger.debug("_submission state passed=%s", passed)
    actual = expected if passed else "unexpected-outcome"
    result = AttackSubmission(base, variant, expected, actual, bool(passed))
    logger.debug("_submission exit")
    return result


def _rejects(callable_, reason) -> bool:
    """Accept only the exact N0 exception class and exact reason string."""
    logger.debug("_rejects entry expected=%s", reason)
    try:
        callable_()
    except N0ValidationError as exc:
        result = type(exc) is N0ValidationError and str(exc) == reason
        logger.debug("_rejects exit matched=%s", result)
        return result
    except Exception as exc:
        logger.error("_rejects foreign exception type=%s", type(exc).__name__)
        return False
    logger.debug("_rejects exit matched=false")
    return False


def _source_drift(mutated) -> bool:
    """Require exact canonical source-drift rejection."""
    logger.debug("_source_drift entry")
    result = _rejects(lambda: prime_power_observer_actualization(mutated), "n0-source-drift")
    logger.debug("_source_drift exit result=%s", result)
    return result


def _foreign_edge(source, history, consumer, producer):
    """Construct a fully rehashed foreign-token edge for semantic pressure."""
    logger.debug("_foreign_edge entry")
    token = digest("veyra.p3n0.foreign-token.v2", (("local", history.historical_token_id.encode()),))
    value = digest("veyra.p3n0.access.v2", (
        ("consumer", consumer.encode()), ("producer", producer.encode()),
        ("token", token.encode()), ("lineage", source.lineage_id.encode()),
        ("scope", source.scope.scope_digest.encode()),
    ))
    result = N0AccessEdge(consumer, producer, token, source.lineage_id,
                          source.scope.scope_digest, value)
    logger.debug("_foreign_edge exit")
    return result


def run_attack_matrix(source, positive) -> tuple[AttackSubmission, ...]:
    """Execute exact reasons, semantic rehashes, hard-first counters, and all base IDs."""
    logger.debug("run_attack_matrix entry")
    strict, opened = counterfactual_histories(source)
    out = []
    out.append(_submission("A01", "boolean-depth", "validation",
                           _rejects(lambda: exact_n0_source(n=True), "depth-exact-int-required")))
    out.append(_submission("A01", "negative-depth", "validation",
                           _rejects(lambda: exact_n0_source(n=-1), "depth-out-of-envelope")))
    mutations = (
        ("depth", FailedBound.DEPTH, replace(source, depth=2,
                                             policy=replace(source.policy, max_depth=1))),
        ("integer-bits", FailedBound.INTEGER_BITS, replace(
            source, depth=1, policy=replace(source.policy, max_integer_bits=1))),
        ("exponent", FailedBound.EXPONENT, replace(
            source, depth=1, policy=replace(source.policy, max_exponent=1))),
        ("modulus", FailedBound.MODULUS_BITS, replace(
            source, policy=replace(source.policy, max_modulus_bits=1))),
    )
    for name, bound, mutated in mutations:
        with (patch("src.core.prime_power_observer_actualization_runtime._snapshot_source") as snap,
              patch("src.core.prime_power_observer_actualization_runtime.capture_size_required") as cap):
            value = prime_power_observer_actualization(mutated)
        passed = type(value) is N0ResourceLimit and value.failed_bound is bound
        passed = passed and snap.call_count == 0 and cap.call_count == 0
        out.append(_submission("A02", name, f"resource:{bound.value}", passed))
    out.append(_submission("A03", "nonprime", "validation",
                           _rejects(lambda: exact_n0_source(p=4),
                                    "n0-raw-builder-rejected-PadicCompletionValidationError")))
    cross = replace(source.n1_packages[0], prime=prime_source(3))
    out.append(_submission("A03", "cross-prime", "validation", _source_drift(
        replace(source, n1_packages=(cross, *source.n1_packages[1:])))))
    row, arrow = source.bridge.rows[0], source.strict_package.raw_package.finite.arrows[0]
    coordinate = replace(row.finite_family.coordinates[0], residue=1)
    family = replace(row.finite_family,
                     coordinates=(coordinate, *row.finite_family.coordinates[1:]))
    out.append(_submission("A04", "wrong-coordinate", "validation", _source_drift(replace(
        source, bridge=replace(source.bridge, rows=(replace(row, finite_family=family),
                                                    *source.bridge.rows[1:]))))))
    finite = replace(source.strict_package.raw_package.finite,
                     arrows=(replace(arrow, rows=tuple(reversed(arrow.rows))),
                             *source.strict_package.raw_package.finite.arrows[1:]))
    out.append(_submission("A04", "reversed-table", "validation", _source_drift(replace(
        source, strict_package=replace(source.strict_package, raw_package=replace(
            source.strict_package.raw_package, finite=finite))))))
    forged = replace(strict.events[5], payload_digest="0" * 64)
    forged_history = replace(strict, events=(*strict.events[:5], forged, *strict.events[6:]))
    out.append(_submission("A04", "forged-event-unhashed", "validation",
                           _rejects(lambda: audit_history(source, forged_history),
                                    "n0-event-digest-drift")))
    rehashed = _event(forged.event_id, forged.kind, forged.parents, forged.token_id,
                      source, forged.payload_digest)
    rehashed_history = rehash_history(
        source, strict, events=(*strict.events[:5], rehashed, *strict.events[6:]),
    )
    network = observer_network_judgment(source.strict_package.network_source,
                                        source.strict_package.network_policy)
    n2 = positive.n2_results[0]
    selected = next(x for x in n2.finite_arrows
                    if (x.fine_depth, x.coarse_depth) == source.scope.arrow)
    out.append(_submission("A04", "forged-event-rehashed", "validation", _rejects(
        lambda: validate_history(source, rehashed_history, network, n2, selected),
        "n0-history-future-semantic-drift")))
    disc = discrimination_candidate(source, strict, ("integer:0", "integer:2"), (0, 0), True)
    out.append(_submission("A05", "false-discriminator", "refuted",
                           refute_discrimination(source, strict, disc) is PremiseStatus.REFUTED))
    unavailable_source = unavailable_n0_source(
        source.prime, source.depth, source.lineage_id, policy=source.policy,
    )
    request = unavailable_bridge_request(unavailable_source)
    unavailable = run_unavailable_bridge(request)
    out.append(_submission("A06", "runner-unavailable-bridge", "genealogy-open-no-token",
                           type(unavailable) is N0GenealogyUnavailable
                           and unavailable.genealogy is PremiseStatus.OPEN))
    foreign_row = replace(source.bridge.rows[1], family_id="foreign:F1")
    out.append(_submission("A07", "foreign-family-row", "validation", _source_drift(replace(
        source, bridge=replace(source.bridge, rows=(source.bridge.rows[0], foreign_row,
                                                    source.bridge.rows[2]))))))
    sep = separator_candidate(source, strict, (0, 2), True)
    out.append(_submission("A08", "false-fine-equality", "refuted",
                           refute_separator(source, strict, sep) is PremiseStatus.REFUTED))
    out.append(_submission("A09", "samples-for-theorem", "validation", _source_drift(
        replace(source, bridge=((0, 0), (1, 1))))))
    edges = tuple(edge for edge in strict.access_edges
                  if "identity-requery" not in (edge.consumer_id, edge.producer_id))
    no_identity = rehash_history(source, strict, access_edges=edges)
    audit = audit_history(source, no_identity)
    out.append(_submission("A10", "missing-identity", "persistence-open",
                           audit["persistence"] is PremiseStatus.OPEN))
    bad = discrimination_candidate(source, strict, ("integer:0", "integer:1"), (0, 0), True)
    out.append(_submission("A11", "digest-for-residue", "validation", _rejects(
        lambda: refute_discrimination(source, strict, bad),
        "n0-discrimination-typed-residue-drift")))
    out.append(_submission("A12", "prior-result-as-source", "validation", _rejects(
        lambda: prime_power_observer_actualization(positive), "n0-source-exact-type-required")))
    out.append(_submission("A13", "decorative-mode-e4", "validation", _rejects(
        lambda: _bound_positive(source, replace(positive, generic_e4_bridge="mode")),
        "n0-result-boundary-promotion-forbidden")))
    birth = strict.events[4]
    target = _event("target-pressure", "TARGET", birth.parents, None, source,
                    strict.events[0].payload_digest)
    causal_target_birth = _event(birth.event_id, birth.kind, (*birth.parents, target.event_id),
                                 None, source, birth.payload_digest)
    target_events = (*strict.events[:4], target, causal_target_birth, *strict.events[5:])
    target_history = rehash_history(source, strict, events=target_events)
    out.append(_submission("A14", "target-in-past-rehashed", "refuted",
                           audit_history(source, target_history)["target_independence"]
                           is PremiseStatus.REFUTED))
    earlier = _event("earlier-birth", birth.kind, birth.parents, None, source, birth.payload_digest)
    causal_birth = _event(birth.event_id, birth.kind, (*birth.parents, earlier.event_id), None,
                          source, birth.payload_digest)
    prior = rehash_history(source, strict, events=(
        *strict.events[:4], earlier, causal_birth, *strict.events[5:],
    ))
    out.append(_submission("A15", "same-pretoken-prior-birth-rehashed", "refuted",
                           audit_history(source, prior)["first_birth"] is PremiseStatus.REFUTED))
    circular = replace(source.prebirth_ledger,
                       imports=(*source.prebirth_ledger.imports, "N0_RESULT"))
    out.append(_submission("A16", "result-in-root", "validation",
                           _source_drift(replace(source, prebirth_ledger=circular))))
    event = strict.events[0]
    raw = N0Event(event.event_id, event.kind, event.parents, event.token_id,
                  "foreign-lineage", event.scope_digest, event.payload_digest, "")
    eid = digest("veyra.p3n0.event.v2", (
        ("id", raw.event_id.encode()), ("kind", raw.kind.encode()),
        *indexed("parent", raw.parents), ("token", (raw.token_id or "PRETOKEN").encode()),
        ("lineage", raw.lineage_id.encode()), ("scope", raw.scope_digest.encode()),
        ("payload", raw.payload_digest.encode()),
    ))
    foreign_event = replace(raw, event_digest=eid)
    foreign_history = rehash_history(
        source, strict, events=(foreign_event, *strict.events[1:]),
    )
    out.append(_submission("A17", "foreign-lineage-rehashed", "validation", _rejects(
        lambda: audit_history(source, foreign_history), "n0-history-prefix-semantic-drift")))
    missing_pair = ("reduction", "response-F0")
    missing_edges = tuple(edge for edge in strict.access_edges
                          if (edge.consumer_id, edge.producer_id) != missing_pair)
    missing = rehash_history(source, strict, access_edges=missing_edges)
    out.append(_submission("A18", "missing-response-access-rehashed", "open",
                           audit_history(source, missing)["post_birth_efficacy"]
                           is PremiseStatus.OPEN))
    replacement_edge = _foreign_edge(source, strict, *REQUIRED_ACCESS[-1])
    foreign_edges = tuple(replacement_edge if
                          (edge.consumer_id, edge.producer_id) == REQUIRED_ACCESS[-1] else edge
                          for edge in strict.access_edges)
    foreign = rehash_history(source, strict, access_edges=foreign_edges)
    out.append(_submission("A19", "foreign-token-edge-rehashed", "refuted",
                           audit_history(source, foreign)["post_birth_efficacy"]
                           is PremiseStatus.REFUTED))
    out.append(_submission("A20", "uncommitted-selector", "validation", _rejects(
        lambda: audit_history(source, replace(strict, selector="foreign")),
        "n0-history-envelope-invalid")))
    mutated_open = rehash_history(source, replace(opened, birth_core_digest="0" * 64))
    out.append(_submission("A21", "suffix-birth-mutation-rehashed", "refuted",
                           audit_counterfactual_pair(source, strict, mutated_open)
                           is PremiseStatus.REFUTED))
    root = PROJECT_ROOT
    out.append(_submission("A22", "path-escape", "validation", _rejects(
        lambda: _capture_one(root, "../escape.lean", ARTIFACT_SHA256, 1024),
        "n0-source-path-escape")))
    with tempfile.TemporaryDirectory(prefix="p3n0-a22-", dir=root / "data" / "tmp") as directory:
        link = Path(directory) / "source.lean"
        link.symlink_to(root / ARTIFACT_PATH)
        relative = link.relative_to(root).as_posix()
        out.append(_submission("A22", "symlink", "validation", _rejects(
            lambda: _capture_one(root, relative, ARTIFACT_SHA256, 1024 * 1024),
            "n0-source-not-regular-file")))
    out.append(_submission("A22", "sha-mismatch", "validation", _rejects(
        lambda: _capture_one(root, ARTIFACT_PATH, "0" * 64, 1024 * 1024),
        "n0-source-pinned-sha-mismatch")))
    operational = (FormalFailureKind.TIMEOUT, FormalFailureKind.OUTPUT_LIMIT,
                   FormalFailureKind.COMPILE_ERROR)
    for kind in operational:
        with patch("src.core.prime_power_observer_actualization_runtime.compile_sources",
                   return_value=N0CompileOutcome(kind, b"bounded", (), None)):
            failure = prime_power_observer_actualization(source)
        out.append(_submission("A23", kind.value, "formal-failure",
                               type(failure) is N0FormalFailure and failure.kind is kind))
    with (patch("src.core.prime_power_observer_actualization_runtime.compile_sources") as compile_,
          patch("src.core.prime_power_observer_actualization_runtime.continuity_holds",
                return_value=False)):
        compile_.return_value = N0CompileOutcome(None, b"", (0, 0, 0, 0),
                                                 positive.formal_attestation)
        failure = prime_power_observer_actualization(source)
    out.append(_submission("A23", "continuity-drift", "formal-failure",
                           type(failure) is N0FormalFailure
                           and failure.kind is FormalFailureKind.CONTINUITY_DRIFT))
    boundaries = (
        ("promotion", {"promotions": 1}, "n0-result-promotion-forbidden"),
        ("physical", {"physical_instantiation": "established"},
         "n0-result-boundary-promotion-forbidden"),
        ("consciousness", {"consciousness": "established"},
         "n0-result-boundary-promotion-forbidden"),
        ("generic-e4", {"generic_e4_bridge": BoundaryStatus.NOT_ESTABLISHED},
         "n0-result-boundary-promotion-forbidden"),
    )
    for name, fields, reason in boundaries:
        out.append(_submission("A24", name, "validation",
                               _rejects(lambda fields=fields: _bound_positive(
                                   source, replace(positive, **fields)), reason)))
    result = tuple(out)
    logger.debug("run_attack_matrix exit submissions=%d", len(result))
    return result
