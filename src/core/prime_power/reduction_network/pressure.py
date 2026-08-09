"""Twenty-three executed mutation and semantic probes for P3-N2."""

from __future__ import annotations

from dataclasses import replace
import logging

from ...observer.network.core import observer_network_judgment
from ...observer.network.validation import snapshot_network_source
from ...padic.completion.core import padic_tower_doctrine, prime_source
from .common import (
    PrimePowerReductionValidationError, digest, exact_digest, exact_shape,
    exact_text, reject,
)
from .runtime import _snapshot_package, prime_power_reduction_judgment
from .sources import finite_reduction_source, reduction_network_package
from .types import (
    DepthNode, FamilyCoordinate, FiniteFamilySource, FiniteReductionSource,
    FiniteRelation, N2FormalFailure, N2Open, N2PressureCandidate, N2PressureKind,
    N2Refutation, N2ResourceLimit, PrimePowerReductionJudgment,
    ReductionArrowSource, ReductionRow, ResultStatus,
)

logger = logging.getLogger(__name__)
ATTACK_LABELS = (
    "reversed-map", "forged-m>n", "foreign-prime", "caller-table",
    "bounded-composition", "omitted-triangle", "intersection-promotion",
    "preservation-to-reflection", "strict-without-separator", "collapsing-separator",
    "finite-to-all-family", "resource-changes-symbolic", "completion-judgment-premise",
    "prior-p3t-judgment", "bounded-paths-only", "carry-confusion", "chosen-lift-inverse",
    "transplanted-source", "digest-not-map-equality", "generic-p3c2-relabel",
    "comparison-proof-dependence", "failure-normalized", "unregistered-p2s-promotion",
)


def _rejected(package) -> bool:
    """Execute a malformed-package replay and require the local typed rejection."""
    logger.debug("_rejected entry")
    try:
        prime_power_reduction_judgment(package)
    except PrimePowerReductionValidationError:
        logger.debug("_rejected exit result=True")
        return True
    logger.debug("_rejected exit result=False")
    return False


def _claim_rejected(package, claim) -> bool:
    """Execute fresh result validation and require hostile-claim rejection."""
    logger.debug("_claim_rejected entry")
    from .validation import validate_prime_power_reduction_result

    try:
        validate_prime_power_reduction_result(package, claim)
    except PrimePowerReductionValidationError:
        logger.debug("_claim_rejected exit result=True")
        return True
    logger.debug("_claim_rejected exit result=False")
    return False


def _package_with(package, finite):
    """Bind an independently constructed finite source into the exact N2 envelope."""
    logger.debug("_package_with entry")
    result = reduction_network_package(package.prime, package.doctrine, finite,
        package.n1_theorem, package.theorem, package.ledger, package.policy)
    logger.debug("_package_with exit")
    return result


def required_n2_attacks(package, result, refusal) -> tuple[tuple[str, bool], ...]:
    """Execute every mandatory attack rather than checking descriptive flags."""
    logger.debug("required_n2_attacks entry")
    if type(result) is not PrimePowerReductionJudgment:
        return tuple((label, False) for label in ATTACK_LABELS)
    arrows = package.finite.arrows
    source_arrow = arrows[1]
    reversed_arrow = replace(source_arrow, fine_depth=source_arrow.coarse_depth,
                             coarse_depth=source_arrow.fine_depth)
    reversed_source = replace(package.finite, arrows=(arrows[0], reversed_arrow, *arrows[2:]))
    reversed_rejected = _rejected(replace(package, finite=reversed_source))
    impossible_arrow = replace(source_arrow, coarse_depth=source_arrow.fine_depth + 1)
    impossible_source = replace(package.finite,
        arrows=(arrows[0], impossible_arrow, *arrows[2:]))
    impossible_rejected = _rejected(replace(package, finite=impossible_source))

    foreign = prime_source(3)
    foreign_finite = finite_reduction_source(foreign, package.doctrine,
        tuple(x.depth for x in package.finite.depths))
    foreign_bound = (foreign_finite.p3t_raw_source.network_digest
                     != package.finite.p3t_raw_source.network_digest)
    foreign_transplant = _rejected(replace(package, prime=foreign))

    bad_row = replace(source_arrow.rows[0], target_residue=1)
    bad_arrow = replace(source_arrow, rows=(bad_row, *source_arrow.rows[1:]))
    table_source = replace(package.finite, arrows=(arrows[0], bad_arrow, *arrows[2:]))
    table_rejected = _rejected(replace(package, finite=table_source))
    direct = arrows[3]
    bad_direct = replace(direct, rows=(replace(direct.rows[0], target_residue=1),
                                      *direct.rows[1:]))
    composition_source = replace(package.finite,
        arrows=(*arrows[:3], bad_direct, *arrows[4:]))
    composition_rejected = _rejected(replace(package, finite=composition_source))

    p3t = package.finite.p3t_raw_source
    no_triangle = replace(p3t, triangles=())
    omitted_rejected = _rejected(replace(package,
        finite=replace(package.finite, p3t_raw_source=no_triangle)))
    partial_triangle = replace(p3t.triangles[0], indirect_edge_ids=("reduce-2-to-1",))
    partial_source = replace(p3t, triangles=(partial_triangle,))
    partial_rejected = _rejected(replace(package,
        finite=replace(package.finite, p3t_raw_source=partial_source)))

    reflected = replace(result.finite_arrows[1], preservation=False)
    reflection_rejected = _claim_rejected(package, replace(result,
        finite_arrows=(result.finite_arrows[0], reflected, *result.finite_arrows[2:])))
    depths = tuple(x.depth for x in package.finite.depths)
    sparse = _package_with(package, finite_reduction_source(package.prime,
        package.doctrine, depths, (0,)))
    sparse_result = prime_power_reduction_judgment(sparse)
    collapse_integer = package.prime.p ** (depths[-1] + 1)
    collapsing = _package_with(package, finite_reduction_source(package.prime,
        package.doctrine, depths, (0, collapse_integer)))
    collapsing_result = prime_power_reduction_judgment(collapsing)
    sparse_open = [x for x in sparse_result.finite_arrows if x.fine_depth > x.coarse_depth]
    collapse_open = [x for x in collapsing_result.finite_arrows if x.fine_depth > x.coarse_depth]
    fake_strict = replace(sparse_result.finite_arrows[1],
        relation=FiniteRelation.STRICT_REFINEMENT_ON_EXACT_FINITE_SCOPE,
        separator_family_ids=("family-0", "family-0"))
    promotion_rejected = _claim_rejected(sparse, replace(sparse_result,
        finite_arrows=(sparse_result.finite_arrows[0], fake_strict,
                       *sparse_result.finite_arrows[2:])))

    prior = observer_network_judgment(p3t)
    prior_rejected = _rejected(replace(package,
        finite=replace(package.finite, p3t_raw_source=prior)))
    coordinate = package.finite.families[0].coordinates[-1]
    bad_coordinate = replace(coordinate, residue=coordinate.residue + 1)
    bad_family = replace(package.finite.families[0],
        coordinates=(*package.finite.families[0].coordinates[:-1], bad_coordinate))
    carry_rejected = _rejected(replace(package, finite=replace(package.finite,
        families=(bad_family, *package.finite.families[1:]))))
    transplant = replace(package.theorem, artifact_sha256="0" * 64)
    transplant_rejected = _rejected(replace(package, theorem=transplant))
    bad_translation = replace(p3t.translations[0], translation_digest="0" * 64)
    map_digest_rejected = _rejected(replace(package, finite=replace(package.finite,
        p3t_raw_source=replace(p3t, translations=(bad_translation, *p3t.translations[1:])))))

    path_direct = tuple(x.target_residue for x in arrows[3].rows)
    first = {x.source_residue: x.target_residue for x in arrows[4].rows}
    second = {x.source_residue: x.target_residue for x in arrows[1].rows}
    path_composed = tuple(second[first[x]] for x in range(len(path_direct)))
    wrong_path_detected = path_direct == path_composed and tuple(
        (x + 1) % package.prime.p for x in path_composed) != path_direct
    inverse_claim_rejected = _claim_rejected(package, replace(result,
        nonclaims=tuple(x for x in result.nonclaims if x != "coarse-to-fine-inverse")))
    p3c2_rejected = _claim_rejected(package, replace(result, p3c2_status_consumed=True))
    proof_rejected = _claim_rejected(package, replace(result,
        theorem_ids=(result.theorem_ids[1], result.theorem_ids[0], *result.theorem_ids[2:])))
    failure_separated = (type(refusal) is N2ResourceLimit
        and refusal.status is ResultStatus.RESOURCE_LIMIT and table_rejected)
    promotion_count_rejected = _claim_rejected(package, replace(result, promotions=1))
    checks = (
        reversed_rejected, impossible_rejected, foreign_bound and foreign_transplant,
        table_rejected, composition_rejected, omitted_rejected, partial_rejected,
        reflection_rejected,
        bool(sparse_open) and all(x.relation is FiniteRelation.OPEN for x in sparse_open),
        bool(collapse_open) and all(x.relation is FiniteRelation.OPEN for x in collapse_open),
        promotion_rejected, type(refusal) is N2ResourceLimit and result.promotions == 0,
        _rejected(replace(package, n1_theorem=package.theorem)), prior_rejected,
        wrong_path_detected, carry_rejected, inverse_claim_rejected, transplant_rejected,
        map_digest_rejected, p3c2_rejected, proof_rejected, failure_separated,
        promotion_count_rejected,
    )
    rows = tuple(zip(ATTACK_LABELS, checks, strict=True))
    logger.debug("required_n2_attacks exit passed=%d", sum(ok for _, ok in rows))
    return rows

PRESSURE_VERSION = "p3n2-pressure-v1"
OPEN_REASON = "missing-admissible-symbolic-theorem-source"
def _exact_root(value: int, exponent: int) -> int:
    """Recover an exact positive integer root without floating point."""
    logger.debug("_exact_root entry bits=%d exponent=%d", value.bit_length(), exponent)
    low, high = 1, 1 << ((value.bit_length() + exponent - 1) // exponent)
    while low <= high:
        middle = (low + high) // 2
        power = pow(middle, exponent)
        if power == value:
            logger.debug("_exact_root exit root=%d", middle)
            return middle
        if power < value:
            low = middle + 1
        else:
            high = middle - 1
    reject("n2-finite-first-modulus-not-exact-prime-power")
def _snapshot_admissible_finite(value) -> tuple[object, object, FiniteReductionSource]:
    """Freshly rebuild a finite arithmetic source without symbolic evidence."""
    logger.debug("_snapshot_admissible_finite entry")
    raw = exact_shape(value, FiniteReductionSource, "n2-open-finite")
    exact_text(raw["version"], "n2-open-version")
    exact_text(raw["p3t_version"], "n2-open-p3t-version")
    for name in ("prime_digest", "doctrine_digest", "source_digest"):
        exact_digest(raw[name], f"n2-open-{name}")
    depths, families, arrows = raw["depths"], raw["families"], raw["arrows"]
    if (type(depths) is not tuple or not 1 <= len(depths) <= 32
            or type(families) is not tuple or not 1 <= len(families) <= 1024
            or type(arrows) is not tuple or len(arrows) > 1024):
        reject("n2-open-finite-envelope-invalid")
    if (any(type(x) is not DepthNode for x in depths)
            or any(type(x) is not FiniteFamilySource for x in families)
            or any(type(x) is not ReductionArrowSource for x in arrows)):
        reject("n2-open-finite-member-type-invalid")
    family_rows = tuple(object.__getattribute__(x, "coordinates") for x in families)
    arrow_rows = tuple(object.__getattribute__(x, "rows") for x in arrows)
    if any(type(x) is not tuple for x in (*family_rows, *arrow_rows)):
        reject("n2-open-finite-nested-container-invalid")
    nested = sum(map(len, family_rows)) + sum(map(len, arrow_rows))
    if nested > 100_000:
        reject("n2-open-finite-row-hard-limit")
    for node in depths:
        item = exact_shape(node, DepthNode, "n2-open-depth")
        if (type(item["depth"]) is not int or not 0 <= item["depth"] <= 64
                or type(item["modulus"]) is not int or item["modulus"] < 2
                or item["modulus"].bit_length() > 4096):
            reject("n2-open-depth-value-invalid")
        exact_digest(item["node_digest"], "n2-open-node-digest")
    for family in families:
        item = exact_shape(family, FiniteFamilySource, "n2-open-family")
        exact_text(item["family_id"], "n2-open-family-id")
        if (type(item["integer"]) is not int or item["integer"].bit_length() > 4096
                or type(item["coordinates"]) is not tuple
                or any(type(x) is not FamilyCoordinate for x in item["coordinates"])):
            reject("n2-open-family-value-invalid")
        exact_digest(item["family_digest"], "n2-open-family-digest")
        for coordinate in item["coordinates"]:
            row = exact_shape(coordinate, FamilyCoordinate, "n2-open-coordinate")
            if type(row["depth"]) is not int or type(row["residue"]) is not int:
                reject("n2-open-coordinate-value-invalid")
            exact_digest(row["coordinate_digest"], "n2-open-coordinate-digest")
    for arrow in arrows:
        item = exact_shape(arrow, ReductionArrowSource, "n2-open-arrow")
        if (type(item["fine_depth"]) is not int or type(item["coarse_depth"]) is not int
                or type(item["rows"]) is not tuple
                or any(type(x) is not ReductionRow for x in item["rows"])):
            reject("n2-open-arrow-value-invalid")
        exact_digest(item["arrow_digest"], "n2-open-arrow-digest")
        for reduction in item["rows"]:
            row = exact_shape(reduction, ReductionRow, "n2-open-reduction-row")
            if type(row["source_residue"]) is not int or type(row["target_residue"]) is not int:
                reject("n2-open-reduction-row-value-invalid")
            exact_digest(row["row_digest"], "n2-open-reduction-row-digest")
    first = depths[0]
    p = prime_source(_exact_root(first.modulus, first.depth + 1))
    doctrine = padic_tower_doctrine()
    safe_network = snapshot_network_source(raw["p3t_raw_source"])
    expected = finite_reduction_source(
        p, doctrine, tuple(x.depth for x in depths), tuple(x.integer for x in families),
    )
    if (raw["prime_digest"] != p.source_digest
            or raw["doctrine_digest"] != doctrine.doctrine_digest
            or safe_network != expected.p3t_raw_source or value != expected):
        reject("n2-open-finite-source-drift")
    logger.debug("_snapshot_admissible_finite exit source=%s", expected.source_digest)
    return p, doctrine, expected
def _candidate_digest(kind, finite_digest, family_id, path, source, claimed) -> str:
    """Commit one exact finite counterclaim."""
    logger.debug("_candidate_digest entry kind=%s", kind.value)
    result = digest("veyra.p3n2.pressure-candidate.v1", (
        ("version", PRESSURE_VERSION.encode()), ("kind", kind.value.encode()),
        ("finite", finite_digest.encode()), ("family", str(family_id).encode()),
        *((f"depth-{i}", str(depth).encode()) for i, depth in enumerate(path)),
        ("source", str(source).encode()), ("claimed", str(claimed).encode()),
    ))
    logger.debug("_candidate_digest exit")
    return result
def square_pressure_candidate(raw_finite, family_id: str, fine_depth: int,
                              coarse_depth: int, claimed_target_residue: int):
    """Construct a typed square counterclaim from one admissible finite family."""
    logger.debug("square_pressure_candidate entry")
    _, _, finite = _snapshot_admissible_finite(raw_finite)
    if type(family_id) is not str:
        reject("n2-square-family-id-invalid")
    family = next((x for x in finite.families if x.family_id == family_id), None)
    if family is None:
        reject("n2-square-family-not-declared")
    coordinates = {x.depth: x.residue for x in family.coordinates}
    if (type(fine_depth) is not int or type(coarse_depth) is not int
            or coarse_depth > fine_depth or fine_depth not in coordinates
            or coarse_depth not in coordinates or type(claimed_target_residue) is not int):
        reject("n2-square-endpoints-invalid")
    target_modulus = next(x.modulus for x in finite.depths if x.depth == coarse_depth)
    if not 0 <= claimed_target_residue < target_modulus:
        reject("n2-square-claimed-residue-out-of-range")
    source = coordinates[fine_depth]
    path = (fine_depth, coarse_depth)
    value = _candidate_digest(N2PressureKind.WRONG_SQUARE, finite.source_digest,
                              family_id, path, source, claimed_target_residue)
    result = N2PressureCandidate(PRESSURE_VERSION, N2PressureKind.WRONG_SQUARE,
        finite.source_digest, family_id, path, source, claimed_target_residue, value)
    logger.debug("square_pressure_candidate exit")
    return result
def path_pressure_candidate(raw_finite, path_depths: tuple[int, ...],
                            source_residue: int, claimed_target_residue: int):
    """Construct a typed composable-path counterclaim on the declared tower."""
    logger.debug("path_pressure_candidate entry")
    _, _, finite = _snapshot_admissible_finite(raw_finite)
    declared = {x.depth for x in finite.depths}
    if (type(path_depths) is not tuple or not 2 <= len(path_depths) <= 32
            or any(type(x) is not int or x not in declared for x in path_depths)
            or any(b > a for a, b in zip(path_depths, path_depths[1:]))
            or type(source_residue) is not int or type(claimed_target_residue) is not int):
        reject("n2-path-candidate-invalid")
    source_modulus = next(x.modulus for x in finite.depths if x.depth == path_depths[0])
    target_modulus = next(x.modulus for x in finite.depths if x.depth == path_depths[-1])
    if (not 0 <= source_residue < source_modulus
            or not 0 <= claimed_target_residue < target_modulus):
        reject("n2-path-residue-out-of-range")
    value = _candidate_digest(N2PressureKind.WRONG_PATH, finite.source_digest,
                              None, path_depths, source_residue, claimed_target_residue)
    result = N2PressureCandidate(PRESSURE_VERSION, N2PressureKind.WRONG_PATH,
        finite.source_digest, None, path_depths, source_residue,
        claimed_target_residue, value)
    logger.debug("path_pressure_candidate exit")
    return result
def _snapshot_candidate(package, value, required_kind) -> N2PressureCandidate:
    """Authenticate a candidate only after the package resource lane has run."""
    logger.debug("_snapshot_candidate entry kind=%s", required_kind.value)
    raw = exact_shape(value, N2PressureCandidate, "n2-pressure-candidate")
    if (raw["version"] != PRESSURE_VERSION or type(raw["kind"]) is not N2PressureKind
            or raw["kind"] is not required_kind
            or raw["finite_source_digest"] != package.finite.source_digest):
        reject("n2-pressure-candidate-binding-invalid")
    path = raw["path_depths"]
    declared = {x.depth for x in package.finite.depths}
    if (type(path) is not tuple or not 2 <= len(path) <= 32
            or any(type(x) is not int or x not in declared for x in path)
            or any(b > a for a, b in zip(path, path[1:]))
            or type(raw["source_residue"]) is not int
            or type(raw["claimed_target_residue"]) is not int):
        reject("n2-pressure-candidate-shape-invalid")
    if required_kind is N2PressureKind.WRONG_SQUARE:
        if type(raw["family_id"]) is not str or len(path) != 2:
            reject("n2-square-candidate-shape-invalid")
        exact_text(raw["family_id"], "n2-square-candidate-family")
    elif raw["family_id"] is not None:
        reject("n2-path-family-id-must-be-none")
    target_modulus = next(x.modulus for x in package.finite.depths if x.depth == path[-1])
    source_modulus = next(x.modulus for x in package.finite.depths if x.depth == path[0])
    if (not 0 <= raw["source_residue"] < source_modulus
            or not 0 <= raw["claimed_target_residue"] < target_modulus):
        reject("n2-pressure-residue-out-of-range")
    expected_digest = _candidate_digest(required_kind, raw["finite_source_digest"],
        raw["family_id"], path, raw["source_residue"], raw["claimed_target_residue"])
    exact_digest(raw["candidate_digest"], "n2-pressure-candidate-digest")
    if raw["candidate_digest"] != expected_digest:
        reject("n2-pressure-candidate-digest-mismatch")
    logger.debug("_snapshot_candidate exit")
    return N2PressureCandidate(**raw)
def _refute(raw_package, raw_candidate, required_kind):
    """Give policy refusal precedence, then derive one arithmetic mismatch."""
    logger.debug("_refute entry kind=%s",
                 "dispatch" if required_kind is None else required_kind.value)
    baseline = prime_power_reduction_judgment(raw_package)
    if type(baseline) in (N2ResourceLimit, N2FormalFailure):
        logger.debug("_refute exit operational=%s", type(baseline).__name__)
        return baseline
    if type(baseline) is not PrimePowerReductionJudgment:
        reject("n2-pressure-base-result-invalid")
    package = _snapshot_package(raw_package)
    if required_kind is None:
        kind = exact_shape(raw_candidate, N2PressureCandidate,
                           "n2-pressure-candidate-dispatch")["kind"]
        if type(kind) is not N2PressureKind:
            reject("n2-pressure-candidate-kind-invalid")
        required_kind = kind
    candidate = _snapshot_candidate(package, raw_candidate, required_kind)
    path = candidate.path_depths
    current = candidate.source_residue
    witness_rows = []
    if required_kind is N2PressureKind.WRONG_SQUARE:
        family = next((x for x in package.finite.families
                       if x.family_id == candidate.family_id), None)
        if family is None:
            reject("n2-square-family-not-declared")
        coordinates = {x.depth: x for x in family.coordinates}
        target_modulus = next(
            x.modulus for x in package.finite.depths if x.depth == path[-1]
        )
        if (candidate.source_residue != coordinates[path[0]].residue
                or candidate.source_residue % target_modulus
                != coordinates[path[-1]].residue):
            reject("n2-square-candidate-not-admissible")
        witness_rows.extend((family.family_digest, coordinates[path[0]].coordinate_digest,
                             coordinates[path[-1]].coordinate_digest))
    by_endpoints = {(x.fine_depth, x.coarse_depth): x for x in package.finite.arrows}
    for fine, coarse in zip(path, path[1:]):
        arrow = by_endpoints.get((fine, coarse))
        if arrow is None:
            reject("n2-pressure-path-arrow-missing")
        row = arrow.rows[current]
        if row.source_residue != current:
            reject("n2-pressure-path-row-index-mismatch")
        current = row.target_residue
        witness_rows.extend((arrow.arrow_digest, row.row_digest))
    if current == candidate.claimed_target_residue:
        reject("n2-pressure-candidate-does-not-witness-mismatch")
    witness = digest("veyra.p3n2.pressure-witness.v1", tuple(
        (f"row-{i}", value.encode()) for i, value in enumerate(witness_rows)))
    value = digest("veyra.p3n2.refutation.v1", (
        ("package", package.package_digest.encode()),
        ("candidate", candidate.candidate_digest.encode()),
        ("witness", witness.encode()), ("expected", str(current).encode()),
        ("claimed", str(candidate.claimed_target_residue).encode()),
    ))
    result = N2Refutation(ResultStatus.REFUTED, required_kind, candidate.family_id,
        path, candidate.source_residue, current, candidate.claimed_target_residue,
        package.finite.source_digest, package.package_digest, candidate.candidate_digest,
        witness, value)
    logger.debug("_refute exit expected=%d claimed=%d", current,
                 candidate.claimed_target_residue)
    return result
def refute_pressure_candidate(raw_package, raw_candidate):
    """Dispatch either exact pressure kind after policy refusal precedence."""
    logger.debug("refute_pressure_candidate entry")
    result = _refute(raw_package, raw_candidate, None)
    logger.debug("refute_pressure_candidate exit type=%s", type(result).__name__)
    return result
def refute_wrong_square_candidate(raw_package, raw_candidate):
    """Refute a valid wrong family/reduction square, preserving resource refusal."""
    logger.debug("refute_wrong_square_candidate entry")
    result = _refute(raw_package, raw_candidate, N2PressureKind.WRONG_SQUARE)
    logger.debug("refute_wrong_square_candidate exit type=%s", type(result).__name__)
    return result
def refute_wrong_path_candidate(raw_package, raw_candidate):
    """Refute a valid wrong composable-path value, preserving resource refusal."""
    logger.debug("refute_wrong_path_candidate entry")
    result = _refute(raw_package, raw_candidate, N2PressureKind.WRONG_PATH)
    logger.debug("refute_wrong_path_candidate exit type=%s", type(result).__name__)
    return result


def report_missing_symbolic_evidence(raw_finite) -> N2Open:
    """Classify one freshly rebuilt finite source with absent theorem evidence OPEN."""
    logger.debug("report_missing_symbolic_evidence entry")
    p, doctrine, finite = _snapshot_admissible_finite(raw_finite)
    value = digest("veyra.p3n2.open.v2", (
        ("prime", p.source_digest.encode()), ("doctrine", doctrine.doctrine_digest.encode()),
        ("source", finite.source_digest.encode()),
        ("p3t", finite.p3t_raw_source.network_digest.encode()), ("reason", OPEN_REASON.encode()),
    ))
    result = N2Open(ResultStatus.OPEN, OPEN_REASON, p.source_digest,
        doctrine.doctrine_digest, finite.source_digest,
        finite.p3t_raw_source.network_digest, value)
    logger.debug("report_missing_symbolic_evidence exit")
    return result
