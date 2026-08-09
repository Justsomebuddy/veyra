"""Hard-first finite replay and symbolic judgment for P3-N2."""

from __future__ import annotations

import logging

from ...observer.network.core import observer_network_judgment, validate_observer_network_result
from ...padic.completion.doctrine import snapshot_doctrine
from ...padic.completion.prime import snapshot_prime
from ...padic.family_introduction.sources import snapshot_theorem as snapshot_n1
from .common import digest, exact_shape, reject, sha
from .formal import capture_sources, compile_sources, continuity_holds
from .link import consume_arithmetic_p3t
from .preflight import (
    first_raw_policy_failure, raw_package_preflight_and_capture,
)
from .sources import (
    AXIOM_ROWS, THEOREM_IDS, finite_reduction_source, n2_ledger, n2_policy,
    reduction_network_package, theorem_source,
)
from .types import (
    BoundaryStatus, DepthNode, FiniteArrowJudgment, FiniteRelation,
    FiniteReductionSource, FormalFailureKind, N2FormalFailure, N2_NONCLAIMS,
    N2ResourceLimit, PrimePowerReductionJudgment,
    PrimePowerReductionPackage, RelativeStatus, ResultStatus, SymbolicKind,
)

logger = logging.getLogger(__name__)


def _snapshot_package(value: PrimePowerReductionPackage) -> PrimePowerReductionPackage:
    """Deeply reconstruct all raw source identities before semantic replay."""
    logger.debug("_snapshot_package entry")
    raw = exact_shape(value, PrimePowerReductionPackage, "n2-package")
    if type(raw["finite"]) is not FiniteReductionSource:
        reject("n2-finite-exact-type-required")
    finite_raw = exact_shape(raw["finite"], FiniteReductionSource, "n2-finite")
    depths = finite_raw["depths"]
    if type(depths) is not tuple or not depths or len(depths) > 32:
        reject("n2-finite-depth-envelope-invalid")
    arrows, families = finite_raw["arrows"], finite_raw["families"]
    if (type(arrows) is not tuple or len(arrows) > 1024 or type(families) is not tuple
            or len(families) > 1024):
        reject("n2-finite-collection-envelope-invalid")
    if any(type(x) is not DepthNode for x in depths):
        reject("n2-depth-node-exact-type-required")
    try:
        depth_values = tuple(object.__getattribute__(x, "depth") for x in depths)
    except (AttributeError, TypeError):
        reject("n2-depth-node-malformed")
    p, d = snapshot_prime(raw["prime"]), snapshot_doctrine(raw["doctrine"])
    if any(type(x) is not int or not 0 <= x <= 64 for x in depth_values):
        reject("n2-depth-value-envelope-invalid")
    try:
        family_integers = tuple(object.__getattribute__(x, "integer") for x in families)
    except (AttributeError, TypeError):
        reject("n2-family-source-malformed")
    expected_finite = finite_reduction_source(p, d, depth_values, family_integers)
    if raw["finite"] != expected_finite:
        reject("n2-finite-source-drift")
    n1 = snapshot_n1(raw["n1_theorem"])
    if raw["theorem"] != theorem_source() or raw["ledger"] != n2_ledger():
        reject("n2-theorem-or-ledger-drift")
    policy = raw["policy"]
    try:
        caps = tuple(object.__getattribute__(policy, name) for name in (
            "max_captured_bytes", "max_static_cost", "max_depths", "max_arrows",
            "max_table_rows", "max_output_bytes", "timeout_seconds"))
    except AttributeError:
        reject("n2-policy-fields-missing")
    if type(policy) is not type(n2_policy()) or policy != n2_policy(*caps):
        reject("n2-policy-drift")
    expected = reduction_network_package(p, d, expected_finite, n1,
        raw["theorem"], raw["ledger"], policy)
    if value != expected:
        reject("n2-package-drift")
    logger.debug("_snapshot_package exit")
    return expected


def _resource(package, refusal) -> N2ResourceLimit:
    """Return a theorem-payload-free operational refusal."""
    logger.debug("_resource entry")
    kind, required, allowed = refusal
    value = digest("veyra.p3n2.resource.v1", (("package", package.package_digest.encode()),
        ("bound", kind.value.encode()), ("required", str(required).encode()),
        ("allowed", str(allowed).encode())))
    result = N2ResourceLimit(ResultStatus.RESOURCE_LIMIT, kind, required, allowed,
                             package.package_digest, value)
    logger.debug("_resource exit bound=%s", kind.value)
    return result


def _formal_failure(package, outcome, captured) -> N2FormalFailure:
    """Preserve operational failure kind instead of inventing semantic OPEN."""
    logger.debug("_formal_failure entry kind=%s", outcome.kind.value)
    value = digest("veyra.p3n2.formal-attempt.v1", (("package", package.package_digest.encode()),
        ("kind", outcome.kind.value.encode()), ("output", sha(outcome.output).encode()),
        *((f"source-{i}", sha(x).encode()) for i, x in enumerate(captured))))
    result = N2FormalFailure(outcome.kind, package.package_digest,
                             f"formal execution {outcome.kind.value}", value)
    logger.debug("_formal_failure exit")
    return result


def _finite_arrows(package) -> tuple[FiniteArrowJudgment, ...]:
    """Replay total arithmetic maps, squares, preservation, and exact separators."""
    logger.debug("_finite_arrows entry")
    by_integer = {f.integer: f for f in package.finite.families}
    result = []
    for arrow in package.finite.arrows:
        source_modulus = package.prime.p ** (arrow.fine_depth + 1)
        target_modulus = package.prime.p ** (arrow.coarse_depth + 1)
        total = tuple((r.source_residue, r.target_residue) for r in arrow.rows) == tuple(
            (x, x % target_modulus) for x in range(source_modulus))
        coordinates = {f.family_id: {x.depth: x.residue for x in f.coordinates}
                       for f in package.finite.families}
        square = all(coordinates[f.family_id][arrow.fine_depth] % target_modulus
                     == coordinates[f.family_id][arrow.coarse_depth]
                     for f in package.finite.families)
        preserving = all((coordinates[a.family_id][arrow.fine_depth]
                          == coordinates[b.family_id][arrow.fine_depth])
                         <= (coordinates[a.family_id][arrow.coarse_depth]
                             == coordinates[b.family_id][arrow.coarse_depth])
                         for a in package.finite.families for b in package.finite.families)
        separator = None
        if arrow.fine_depth == arrow.coarse_depth:
            relation = FiniteRelation.TRANSLATION_ISOMORPHIC_ON_EXACT_FINITE_SCOPE
        else:
            witness = package.prime.p ** (arrow.coarse_depth + 1)
            left, right = by_integer.get(0), by_integer.get(witness)
            witnessed = left is not None and right is not None and (
                coordinates[left.family_id][arrow.coarse_depth]
                == coordinates[right.family_id][arrow.coarse_depth]) and (
                coordinates[left.family_id][arrow.fine_depth]
                != coordinates[right.family_id][arrow.fine_depth])
            relation = (FiniteRelation.STRICT_REFINEMENT_ON_EXACT_FINITE_SCOPE
                        if witnessed else FiniteRelation.OPEN)
            if witnessed:
                separator = (left.family_id, right.family_id)
        if not (total and square and preserving):
            reject("arithmetic-derived-valid-source-internal-mismatch")
        jd = digest("veyra.p3n2.finite-arrow-judgment.v1", (("arrow", arrow.arrow_digest.encode()),
            ("relation", relation.value.encode()), ("separator", str(separator).encode())))
        result.append(FiniteArrowJudgment(arrow.fine_depth, arrow.coarse_depth, total,
            square, preserving, relation, separator, arrow.arrow_digest, jd))
    by_endpoints = {(x.fine_depth, x.coarse_depth): x for x in package.finite.arrows}
    depths = tuple(x.depth for x in package.finite.depths)
    for fine in depths:
        for middle in depths:
            for coarse in depths:
                if not coarse <= middle <= fine:
                    continue
                direct = by_endpoints[(fine, coarse)].rows
                first = by_endpoints[(fine, middle)].rows
                second = by_endpoints[(middle, coarse)].rows
                second_map = {x.source_residue: x.target_residue for x in second}
                composed = tuple(second_map[x.target_residue] for x in first)
                if composed != tuple(x.target_residue for x in direct):
                    reject("finite-arithmetic-composition-refuted")
    logger.debug("_finite_arrows exit count=%d", len(result))
    return tuple(result)


def prime_power_reduction_judgment(raw_package):
    """Replay raw P3-T/P1, arithmetic N2-F, and private all-depth N2-S sources."""
    logger.debug("prime_power_reduction_judgment entry")
    _, raw_charge, captured = raw_package_preflight_and_capture(raw_package)
    refusal = first_raw_policy_failure(raw_package.policy, raw_charge)
    if refusal is not None:
        return _resource(raw_package, refusal)
    package = _snapshot_package(raw_package)
    if capture_sources(package) != captured:
        reject("n2-captured-source-continuity-drift")
    p3t = observer_network_judgment(package.finite.p3t_raw_source)
    validate_observer_network_result(package.finite.p3t_raw_source, p3t)
    if p3t.promotions != 0:
        reject("p3t-replay-promotions-nonzero")
    arrows = _finite_arrows(package)
    p3t_consumption = consume_arithmetic_p3t(package, p3t, arrows)
    outcome = compile_sources(captured, package.policy.timeout_seconds,
                              package.policy.max_output_bytes)
    if outcome.kind is not None:
        return _formal_failure(package, outcome, captured)
    if outcome.axiom_rows != AXIOM_ROWS or not continuity_holds(package, captured):
        broken = type(outcome)(FormalFailureKind.CONTINUITY_DRIFT, outcome.output,
            outcome.return_codes, (), outcome.attestation_digest, outcome.phase_receipts)
        return _formal_failure(package, broken, captured)
    yes = RelativeStatus.ESTABLISHED_RELATIVE_TO_LEDGER
    jd = digest("veyra.p3n2.judgment.v1", (("package", package.package_digest.encode()),
        ("p3t", p3t_consumption.encode()), ("theorem", package.theorem.source_digest.encode()),
        ("ledger", package.ledger.ledger_digest.encode()),
        *((f"arrow-{i}", x.judgment_digest.encode()) for i, x in enumerate(arrows)),
        *((f"nonclaim-{i}", x.encode()) for i, x in enumerate(N2_NONCLAIMS))))
    result = PrimePowerReductionJudgment(yes, yes,
        SymbolicKind.THIN_REDUCTION_PATH_COHERENT_RELATIVE_TO_TOWER, arrows,
        package.finite.p3t_raw_source.network_digest, p3t_consumption,
        package.theorem.source_digest, package.ledger.ledger_digest,
        yes, yes, yes, yes, BoundaryStatus.NOT_CLAIMED, False, False, 0,
        THEOREM_IDS, AXIOM_ROWS, N2_NONCLAIMS, jd)
    logger.debug("prime_power_reduction_judgment exit")
    return result
