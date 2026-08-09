"""Atomic raw-shape/count/byte/work preflight before P3-N2 reconstruction."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from ...observer.network.preflight import hard_preflight, network_resource_policy
from ...observer.network.common import ObserverNetworkError
from ...padic.completion.types import PadicTowerDoctrine, PrimeSource
from ...padic.family_introduction.types import N1TheoremSource
from .common import exact_digest, exact_shape, reject
from .formal import capture_sources
from .sources import n2_ledger, n2_policy, theorem_source
from .types import (
    DepthNode, FailedBound, FamilyCoordinate, FiniteFamilySource,
    FiniteReductionSource, N2Ledger, N2Policy, N2TheoremSource,
    PrimePowerReductionPackage, ReductionArrowSource, ReductionRow,
)

logger = logging.getLogger(__name__)
HARD_DEPTHS = 32
HARD_FAMILIES = 1024
HARD_ARROWS = 1024
HARD_ROWS = 100_000
HARD_BYTES = 16 * 1024 * 1024


@dataclass(frozen=True)
class RawPreflightCharge:
    captured_bytes: int
    static_cost: int
    depths: int
    arrows: int
    table_rows: int
    family_rows: int


def _utf8_size(value, label: str) -> int:
    """Charge one exact bounded string without coercion."""
    logger.debug("_utf8_size entry label=%s", label)
    if type(value) is not str:
        reject(f"{label}-not-text")
    try:
        result = len(value.encode("utf-8"))
    except UnicodeError:
        reject(f"{label}-invalid-utf8")
    if result > 4096:
        reject(f"{label}-text-hard-limit")
    logger.debug("_utf8_size exit bytes=%d", result)
    return result


def _policy(raw) -> N2Policy:
    """Authenticate the small exact policy before any source reconstruction."""
    logger.debug("_policy entry")
    values = exact_shape(raw, N2Policy, "n2-raw-policy")
    names = ("max_captured_bytes", "max_static_cost", "max_depths", "max_arrows",
             "max_table_rows", "max_output_bytes", "timeout_seconds")
    caps = tuple(values[name] for name in names)
    expected = n2_policy(*caps)
    if raw != expected:
        reject("n2-raw-policy-drift")
    logger.debug("_policy exit")
    return expected


def raw_package_preflight(value, captured: tuple[bytes, ...]) -> tuple[N2Policy, RawPreflightCharge]:
    """Validate envelopes and charge all raw work before rebuilding any table."""
    logger.debug("raw_package_preflight entry")
    raw = exact_shape(value, PrimePowerReductionPackage, "n2-raw-package")
    exact_digest(raw["package_digest"], "n2-raw-package-digest")
    if (type(raw["prime"]) is not PrimeSource or type(raw["doctrine"]) is not PadicTowerDoctrine
            or type(raw["n1_theorem"]) is not N1TheoremSource):
        reject("n2-raw-base-source-types-invalid")
    if type(raw["theorem"]) is not N2TheoremSource or raw["theorem"] != theorem_source():
        reject("n2-raw-theorem-source-drift")
    if type(raw["ledger"]) is not N2Ledger or raw["ledger"] != n2_ledger():
        reject("n2-raw-ledger-drift")
    policy = _policy(raw["policy"])
    finite = exact_shape(raw["finite"], FiniteReductionSource, "n2-raw-finite")
    for name in ("prime_digest", "doctrine_digest", "source_digest"):
        exact_digest(finite[name], f"n2-raw-finite-{name}")
    text_bytes = sum(_utf8_size(finite[name], f"n2-raw-finite-{name}")
                     for name in ("version", "p3t_version"))
    containers = tuple(finite[name] for name in ("depths", "families", "arrows"))
    if any(type(item) is not tuple for item in containers):
        reject("n2-raw-finite-containers-invalid")
    depths, families, arrows = containers
    if not 1 <= len(depths) <= HARD_DEPTHS or not 1 <= len(families) <= HARD_FAMILIES:
        reject("n2-raw-depth-or-family-hard-limit")
    if len(arrows) > HARD_ARROWS:
        reject("n2-raw-arrow-hard-limit")
    if any(type(x) is not DepthNode for x in depths):
        reject("n2-raw-depth-node-type-invalid")
    if any(type(x) is not FiniteFamilySource for x in families):
        reject("n2-raw-family-type-invalid")
    if any(type(x) is not ReductionArrowSource for x in arrows):
        reject("n2-raw-arrow-type-invalid")
    family_rows = 0
    for family in families:
        rows = object.__getattribute__(family, "coordinates")
        if type(rows) is not tuple:
            reject("n2-raw-family-coordinate-container-invalid")
        family_rows += len(rows)
    table_rows = 0
    for arrow in arrows:
        rows = object.__getattribute__(arrow, "rows")
        if type(rows) is not tuple:
            reject("n2-raw-arrow-row-container-invalid")
        table_rows += len(rows)
    if family_rows + table_rows > HARD_ROWS:
        reject("n2-raw-row-hard-limit")
    prime_value = object.__getattribute__(raw["prime"], "p")
    if type(prime_value) is not int or not 2 <= prime_value <= HARD_ROWS:
        reject("n2-raw-prime-scalar-invalid")
    depth_values = []
    for node in depths:
        fields = exact_shape(node, DepthNode, "n2-raw-depth-node")
        if (type(fields["depth"]) is not int or not 0 <= fields["depth"] <= 64
                or type(fields["modulus"]) is not int):
            reject("n2-raw-depth-scalar-invalid")
        depth_values.append(fields["depth"])
        exact_digest(fields["node_digest"], "n2-raw-node-digest")
    reconstruction_rows = 0
    for fine in depth_values:
        modulus = pow(prime_value, fine + 1)
        if modulus > HARD_ROWS:
            reject("n2-raw-reconstruction-work-hard-limit")
        reconstruction_rows += modulus * sum(coarse <= fine for coarse in depth_values)
        if reconstruction_rows > HARD_ROWS:
            reject("n2-raw-reconstruction-work-hard-limit")
    for family in families:
        fields = exact_shape(family, FiniteFamilySource, "n2-raw-family")
        text_bytes += _utf8_size(fields["family_id"], "n2-raw-family-id")
        if type(fields["integer"]) is not int or fields["integer"].bit_length() > 4096:
            reject("n2-raw-family-integer-invalid")
        exact_digest(fields["family_digest"], "n2-raw-family-digest")
        if any(type(x) is not FamilyCoordinate for x in fields["coordinates"]):
            reject("n2-raw-coordinate-type-invalid")
    for arrow in arrows:
        fields = exact_shape(arrow, ReductionArrowSource, "n2-raw-arrow")
        exact_digest(fields["arrow_digest"], "n2-raw-arrow-digest")
        if any(type(x) is not ReductionRow for x in fields["rows"]):
            reject("n2-raw-reduction-row-type-invalid")
    if type(captured) is not tuple or len(captured) != 3 or any(type(x) is not bytes for x in captured):
        reject("n2-raw-captured-source-envelope-invalid")
    captured_bytes = sum(len(x) for x in captured)
    try:
        hard_preflight(finite["p3t_raw_source"], network_resource_policy())
    except ObserverNetworkError:
        logger.debug("raw_package_preflight rejected nested P3-T source", exc_info=True)
        reject("n2-raw-p3t-source-invalid")
    static = captured_bytes + text_bytes + 256 * (
        len(depths) + len(families) + len(arrows) + family_rows + table_rows
        + len(raw["ledger"].ordered_rows) + len(raw["ledger"].direct_edges)
    )
    if captured_bytes > HARD_BYTES or static > HARD_BYTES:
        reject("n2-raw-byte-or-work-hard-limit")
    charge = RawPreflightCharge(captured_bytes, static, len(depths), len(arrows),
                                table_rows, family_rows)
    logger.debug("raw_package_preflight exit static=%d rows=%d", static, table_rows)
    return policy, charge


def raw_package_preflight_and_capture(value):
    """Authenticate the raw theorem envelope, capture it, then charge all raw work."""
    logger.debug("raw_package_preflight_and_capture entry")
    raw = exact_shape(value, PrimePowerReductionPackage, "n2-raw-package-envelope")
    theorem = raw["theorem"]
    if type(theorem) is not N2TheoremSource or theorem != theorem_source():
        reject("n2-raw-theorem-source-drift")
    captured = capture_sources(value)
    policy, charge = raw_package_preflight(value, captured)
    logger.debug("raw_package_preflight_and_capture exit static=%d", charge.static_cost)
    return policy, charge, captured


def first_raw_policy_failure(policy: N2Policy, charge: RawPreflightCharge):
    """Select a typed refusal in fixed priority after complete raw charging."""
    logger.debug("first_raw_policy_failure entry")
    checks = (
        (FailedBound.CAPTURED_BYTES, charge.captured_bytes, policy.max_captured_bytes),
        (FailedBound.STATIC_COST, charge.static_cost, policy.max_static_cost),
        (FailedBound.DEPTHS, charge.depths, policy.max_depths),
        (FailedBound.ARROWS, charge.arrows, policy.max_arrows),
        (FailedBound.TABLE_ROWS, charge.table_rows, policy.max_table_rows),
    )
    result = next((item for item in checks if item[1] > item[2]), None)
    logger.debug("first_raw_policy_failure exit failed=%s",
                 None if result is None else result[0].value)
    return result
