"""Canonical source-derived semantics for P3-N0 post-birth events."""

from __future__ import annotations

import logging

from .common import digest, exact_hex, indexed, reject
from .types import N0Event, PreTokenKey, SuffixSelector

logger = logging.getLogger(__name__)
RESERVED_FUTURE_ROWS = (
    ("response-F0", "RESPONSE", ("birth",)),
    ("response-F1", "RESPONSE", ("response-F0",)),
    ("identity-requery", "IDENTITY_REQUERY", ("response-F1",)),
    ("reduction", "REDUCTION", ("identity-requery",)),
    ("selector", "SELECTOR", ("reduction",)),
    ("bridge-access", "BRIDGE_ACCESS", ("selector",)),
    ("package-access", "RAW_PACKAGE_ACCESS", ("bridge-access",)),
)
RESERVED_PREFIX_ROWS = (
    ("past-doctrine", "DOCTRINE", ()),
    ("past-scope", "SCOPE", ("past-doctrine",)),
    ("past-genealogy", "RAW_GENEALOGY", ("past-scope",)),
    ("past-discrimination", "DISCRIMINATION", ("past-genealogy",)),
)
PRESSURE_EXTRA_KINDS = {"TARGET", "ARITHMETIC_ROLE_BIRTH"}


def response_payload(source, family_id: str) -> str:
    """Bind one response payload to the exact source bridge coordinate."""
    logger.debug("response_payload entry family=%s", family_id)
    try:
        row = next(item for item in source.bridge.rows if item.family_id == family_id)
        coordinate = next(
            item for item in row.finite_family.coordinates if item.depth == source.depth
        )
    except StopIteration:
        logger.error("response_payload coordinate missing family=%s", family_id)
        reject("n0-history-response-coordinate-missing")
    result = digest("veyra.p3n0.response-payload.v2", (
        ("row", row.row_digest.encode()),
        ("coordinate", coordinate.coordinate_digest.encode()),
        ("residue", str(coordinate.residue).encode()),
    ))
    logger.debug("response_payload exit family=%s", family_id)
    return result


def reduction_payload(source) -> str:
    """Bind the reduction payload to every exact fine/coarse bridge row."""
    logger.debug("reduction_payload entry")
    rows, modulus = [], source.prime ** (source.depth + 1)
    for row in source.bridge.rows:
        coordinates = {item.depth: item for item in row.finite_family.coordinates}
        try:
            fine, coarse = coordinates[source.depth + 1], coordinates[source.depth]
        except KeyError:
            logger.error("reduction_payload coordinate missing")
            reject("n0-history-reduction-coordinate-missing")
        if fine.residue % modulus != coarse.residue:
            logger.error("reduction_payload row refuted")
            reject("n0-history-reduction-row-refuted")
        rows.append(f"{row.row_digest}:{fine.coordinate_digest}:{coarse.coordinate_digest}")
    result = digest("veyra.p3n0.reduction-payload.v2", indexed("row", rows))
    logger.debug("reduction_payload exit rows=%d", len(rows))
    return result


def canonical_pending_semantics(source, selector) -> dict[str, tuple[str, str]]:
    """Reconstruct exact kind/payload pairs for every pending future event."""
    logger.debug("canonical_pending_semantics entry")
    if type(selector) is not SuffixSelector:
        logger.error("canonical_pending_semantics selector invalid")
        reject("n0-future-selector-exact-enum-required")
    package = (
        source.strict_package
        if selector is SuffixSelector.STRICT_SUFFIX
        else source.open_package
    )
    f0 = response_payload(source, "integer:0")
    f1 = response_payload(source, "integer:1")
    payloads = {
        "response-F0": f0,
        "response-F1": f1,
        "identity-requery": digest("veyra.p3n0.identity-requery.v2", (
            ("F0", f0.encode()), ("F1", f1.encode()),
            ("depth", str(source.depth).encode()),
        )),
        "reduction": reduction_payload(source),
        "selector": digest("veyra.p3n0.selector.v2", (
            ("selector", selector.value.encode()),
            ("package", package.wrapper_digest.encode()),
        )),
        "bridge-access": source.bridge.bridge_digest,
        "package-access": package.wrapper_digest,
    }
    kinds = {
        "response-F0": "RESPONSE", "response-F1": "RESPONSE",
        "identity-requery": "IDENTITY_REQUERY", "reduction": "REDUCTION",
        "selector": "SELECTOR", "bridge-access": "BRIDGE_ACCESS",
        "package-access": "RAW_PACKAGE_ACCESS",
    }
    result = {name: (kinds[name], payload) for name, payload in payloads.items()}
    logger.debug("canonical_pending_semantics exit selector=%s", selector.value)
    return result


def canonical_event_row(source, event_id: str, kind: str, parents: tuple[str, ...],
                        token_id: str | None, payload_digest: str) -> N0Event:
    """Construct one complete trusted source-bound event row and its digest."""
    logger.debug("canonical_event_row entry id=%s", event_id)
    if token_id is not None:
        exact_hex(token_id, "n0-canonical-event-token")
    value = digest("veyra.p3n0.event.v2", (
        ("id", event_id.encode()), ("kind", kind.encode()), *indexed("parent", parents),
        ("token", (token_id or "PRETOKEN").encode()), ("lineage", source.lineage_id.encode()),
        ("scope", source.scope.scope_digest.encode()), ("payload", payload_digest.encode()),
    ))
    result = N0Event(event_id, kind, parents, token_id, source.lineage_id,
                     source.scope.scope_digest, payload_digest, value)
    logger.debug("canonical_event_row exit id=%s", event_id)
    return result


def canonical_pretoken(source, strict_past_digest: str) -> PreTokenKey:
    """Derive the one exact pre-token key from source-bound strict past."""
    logger.debug("canonical_pretoken entry")
    rho = digest("veyra.p3n0.rho-structural.v2", (
        ("version", b"rho-prime-power-coordinate-v2"),
        ("prime", str(source.prime).encode()), ("depth", str(source.depth).encode()),
        ("tower", source.n1_packages[0].doctrine.doctrine_digest.encode()),
    ))
    value = digest("veyra.p3n0.pretoken.v2", (
        ("lineage", source.lineage_id.encode()), ("rho", rho.encode()),
        ("doctrine", source.doctrine.doctrine_digest.encode()),
        ("scope", strict_past_digest.encode()),
        ("theorem", source.theorem_source.source_digest.encode()),
    ))
    result = PreTokenKey(
        source.lineage_id, rho, source.doctrine.doctrine_digest,
        strict_past_digest, value,
    )
    logger.debug("canonical_pretoken exit")
    return result


def canonical_strict_prefix(source):
    """Construct all five reserved prefix rows and their derived identities."""
    logger.debug("canonical_strict_prefix entry")
    genealogy = digest("veyra.p3n0.raw-genealogy.v2", (
        ("ledger", source.prebirth_ledger.ledger_digest.encode()),
        ("theorem", source.theorem_source.source_digest.encode()),
    ))
    payloads = {
        "past-doctrine": source.doctrine.doctrine_digest,
        "past-scope": source.scope.scope_digest,
        "past-genealogy": genealogy,
        "past-discrimination": source.bridge.bridge_digest,
    }
    past = tuple(
        canonical_event_row(source, event_id, kind, parents, None, payloads[event_id])
        for event_id, kind, parents in RESERVED_PREFIX_ROWS
    )
    strict_past = digest("veyra.p3n0.strict-past.v2", (
        *indexed("event", (item.event_digest for item in past)),
        ("ledger", source.prebirth_ledger.ledger_digest.encode()),
    ))
    key = canonical_pretoken(source, strict_past)
    birth = canonical_event_row(
        source, "birth", "ARITHMETIC_ROLE_BIRTH",
        ("past-genealogy", "past-discrimination"), None, key.key_digest,
    )
    core = digest("veyra.p3n0.birth-core.v2", (
        ("past", strict_past.encode()), ("birth", birth.event_digest.encode()),
        ("key", key.key_digest.encode()),
        ("theorem", source.theorem_source.source_digest.encode()),
    ))
    token = digest("veyra.p3n0.historical-token.v2", (
        ("lineage", source.lineage_id.encode()),
        ("rho", key.rho_structural_id.encode()),
        ("doctrine", source.doctrine.doctrine_digest.encode()),
        ("core", core.encode()),
    ))
    logger.debug("canonical_strict_prefix exit")
    return past, birth, strict_past, core, token


def validate_pressure_prefix(source, events) -> None:
    """Require canonical prefix rows, allowing only typed direct prebirth pressure extras."""
    logger.debug("validate_pressure_prefix entry")
    past, birth, _, _, _ = canonical_strict_prefix(source)
    birth_index = next((i for i, item in enumerate(events) if item.event_id == "birth"), -1)
    extras = events[4:birth_index] if birth_index >= 4 else ()
    if tuple(events[:4]) != past:
        logger.error("validate_pressure_prefix reserved past drift")
        reject("n0-history-prefix-semantic-drift")
    if any(
        item.kind not in PRESSURE_EXTRA_KINDS or item.token_id is not None
        or item.lineage_id != source.lineage_id
        or item.scope_digest != source.scope.scope_digest
        or item.parents != birth.parents
        or (item.kind == "ARITHMETIC_ROLE_BIRTH"
            and item.payload_digest != birth.payload_digest)
        for item in extras
    ):
        logger.error("validate_pressure_prefix extra drift")
        reject("n0-history-extra-pressure-event-invalid")
    expected_birth = canonical_event_row(
        source, birth.event_id, birth.kind,
        (*birth.parents, *(item.event_id for item in extras)),
        None, birth.payload_digest,
    )
    if birth_index != 4 + len(extras) or events[birth_index] != expected_birth:
        logger.error("validate_pressure_prefix birth drift")
        reject("n0-history-prefix-semantic-drift")
    extra_ids = {item.event_id for item in extras}
    if any(item.event_id not in extra_ids for item in events
           if item.event_id not in {
               *(row[0] for row in RESERVED_PREFIX_ROWS), "birth",
               *(row[0] for row in RESERVED_FUTURE_ROWS), "n2-selected",
           }):
        logger.error("validate_pressure_prefix misplaced extra")
        reject("n0-history-extra-pressure-event-invalid")
    logger.debug("validate_pressure_prefix exit extras=%d", len(extras))


def canonical_pending_event_rows(source, selector, token_id: str) -> dict[str, N0Event]:
    """Derive every complete reserved pending row from exact source semantics."""
    logger.debug("canonical_pending_event_rows entry")
    payloads = canonical_pending_semantics(source, selector)
    result = {
        event_id: canonical_event_row(
            source, event_id, kind, parents, token_id, payloads[event_id][1],
        )
        for event_id, kind, parents in RESERVED_FUTURE_ROWS
    }
    logger.debug("canonical_pending_event_rows exit rows=%d", len(result))
    return result
