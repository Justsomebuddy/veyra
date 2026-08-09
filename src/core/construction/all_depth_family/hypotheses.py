"""Immutable supplied and oracle hypothesis packages for P1-D3."""

from __future__ import annotations

import logging

from .common import exact_digest, exact_identifier, exact_shape, reject
from .digest import hypothesis_digest
from .ledger import snapshot_assumption_ledger
from .spec import (
    ORACLE_CONSTRUCTOR_ID, SUPPLIED_CONSTRUCTOR_ID, snapshot_family_spec,
    snapshot_family_term,
)
from .types import (
    AllDepthFamilySpec, AssumptionLedger, FamilyHypothesis, FamilyTerm,
    OracleFamilyHypothesis,
)

logger = logging.getLogger(__name__)
HYPOTHESIS_VERSION = "p1-d3-hypothesis-v1"
SUPPLIED_COORDINATE_LAW_ID = "p1-d3.hypothesis.total-coordinates.v1"
SUPPLIED_COMPATIBILITY_LAW_ID = "p1-d3.hypothesis.compatible-restrictions.v1"
ORACLE_TOTALITY_HYPOTHESIS_ID = "p1-d3.oracle.totality-hypothesis.v1"
ORACLE_PURITY_HYPOTHESIS_ID = "p1-d3.oracle.purity-hypothesis.v1"
ORACLE_STABILITY_HYPOTHESIS_ID = "p1-d3.oracle.stability-hypothesis.v1"


def supplied_family_hypothesis(
    spec: AllDepthFamilySpec, term: FamilyTerm, hypothesis_id: str,
    coordinate_law_id: str, compatibility_law_id: str, ledger: AssumptionLedger,
) -> FamilyHypothesis:
    """Bind one explicit extensional-family assumption and its laws."""
    logger.debug("supplied_family_hypothesis entry")
    spec = snapshot_family_spec(spec)
    term = snapshot_family_term(term, spec)
    ledger = snapshot_assumption_ledger(ledger)
    if term.program is not None or term.constructor_id != SUPPLIED_CONSTRUCTOR_ID:
        reject("supplied-hypothesis-requires-supplied-symbolic-term")
    values = tuple(exact_identifier(value, field) for value, field in (
        (hypothesis_id, "hypothesis-id"), (coordinate_law_id, "coordinate-law-id"),
        (compatibility_law_id, "compatibility-law-id"),
    ))
    if values[1:] != (SUPPLIED_COORDINATE_LAW_ID, SUPPLIED_COMPATIBILITY_LAW_ID):
        reject("supplied-hypothesis-law-statement-drift")
    if not set(values).issubset(ledger.closure):
        reject("supplied-hypothesis-not-closed-in-ledger")
    value = hypothesis_digest("supplied", (
        ("id", values[0].encode()), ("term", term.family_term_digest.encode()),
        ("coordinate-law", values[1].encode()), ("compatibility-law", values[2].encode()),
        ("ledger", ledger.ledger_digest.encode()),
    ))
    result = FamilyHypothesis(
        HYPOTHESIS_VERSION, values[0], term, values[1], values[2], ledger, value,
    )
    logger.debug("supplied_family_hypothesis exit")
    return result


def snapshot_supplied_hypothesis(
    value: FamilyHypothesis, spec: AllDepthFamilySpec,
) -> FamilyHypothesis:
    """Deeply rebuild one supplied hypothesis and reject transplant."""
    logger.debug("snapshot_supplied_hypothesis entry")
    exact_shape(value, FamilyHypothesis, "family-hypothesis")
    try:
        if type(value.version) is not str or value.version != HYPOTHESIS_VERSION:
            reject("family-hypothesis-version-drift")
        expected = supplied_family_hypothesis(
            spec, value.term, value.hypothesis_id, value.coordinate_law_id,
            value.compatibility_law_id, value.ledger,
        )
        exact_digest(value.hypothesis_digest, "hypothesis-digest")
    except AttributeError:
        reject("family-hypothesis-missing-fields")
    if value != expected:
        reject("family-hypothesis-drift")
    logger.debug("snapshot_supplied_hypothesis exit")
    return expected


def oracle_family_hypothesis(
    spec: AllDepthFamilySpec, term: FamilyTerm, hypothesis_id: str,
    oracle_interface_id: str, totality_hypothesis_id: str, purity_hypothesis_id: str,
    stability_hypothesis_id: str, trust_identity: str, ledger: AssumptionLedger,
) -> OracleFamilyHypothesis:
    """Bind an explicit total-oracle assumption without querying an oracle."""
    logger.debug("oracle_family_hypothesis entry")
    spec = snapshot_family_spec(spec)
    term = snapshot_family_term(term, spec)
    ledger = snapshot_assumption_ledger(ledger)
    if term.program is not None or term.constructor_id != ORACLE_CONSTRUCTOR_ID:
        reject("oracle-hypothesis-requires-oracle-symbolic-term")
    rows = tuple(exact_identifier(value, field) for value, field in (
        (hypothesis_id, "hypothesis-id"), (oracle_interface_id, "oracle-interface-id"),
        (totality_hypothesis_id, "totality-hypothesis-id"),
        (purity_hypothesis_id, "purity-hypothesis-id"),
        (stability_hypothesis_id, "stability-hypothesis-id"),
        (trust_identity, "trust-identity"),
    ))
    if rows[2:5] != (
        ORACLE_TOTALITY_HYPOTHESIS_ID, ORACLE_PURITY_HYPOTHESIS_ID,
        ORACLE_STABILITY_HYPOTHESIS_ID,
    ):
        reject("oracle-hypothesis-law-statement-drift")
    if not set(rows).issubset(ledger.closure):
        reject("oracle-hypothesis-not-closed-in-ledger")
    value = hypothesis_digest("oracle", (
        ("id", rows[0].encode()), ("term", term.family_term_digest.encode()),
        ("interface", rows[1].encode()), ("totality", rows[2].encode()),
        ("purity", rows[3].encode()), ("stability", rows[4].encode()),
        ("trust", rows[5].encode()), ("ledger", ledger.ledger_digest.encode()),
    ))
    result = OracleFamilyHypothesis(HYPOTHESIS_VERSION, rows[0], term, *rows[1:], ledger, value)
    logger.debug("oracle_family_hypothesis exit")
    return result


def snapshot_oracle_hypothesis(
    value: OracleFamilyHypothesis, spec: AllDepthFamilySpec,
) -> OracleFamilyHypothesis:
    """Rebuild explicit totality/purity/stability/trust bindings."""
    logger.debug("snapshot_oracle_hypothesis entry")
    exact_shape(value, OracleFamilyHypothesis, "oracle-family-hypothesis")
    try:
        if type(value.version) is not str or value.version != HYPOTHESIS_VERSION:
            reject("oracle-hypothesis-version-drift")
        expected = oracle_family_hypothesis(
            spec, value.term, value.hypothesis_id, value.oracle_interface_id,
            value.totality_hypothesis_id, value.purity_hypothesis_id,
            value.stability_hypothesis_id, value.trust_identity, value.ledger,
        )
        exact_digest(value.hypothesis_digest, "hypothesis-digest")
    except AttributeError:
        reject("oracle-hypothesis-missing-fields")
    if value != expected:
        reject("oracle-hypothesis-drift")
    logger.debug("snapshot_oracle_hypothesis exit")
    return expected
