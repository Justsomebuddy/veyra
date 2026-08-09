"""Closed all-depth specification and symbolic family terms for P1-D3."""

from __future__ import annotations

import logging

from .common import exact_bytes, exact_digest, exact_identifier, exact_shape, reject
from .digest import digest, frame, spec_digest, term_digest
from .types import AllDepthFamilySpec, FamilyTerm
from ..infinity_prefix import (
    InfinityPrefixValidationError, PrefixAlphabet, snapshot_prefix_alphabet,
)
from ...ontology.doctrine import snapshot_observer_doctrine
from ...ontology.types import ObserverDoctrine
from ..productivity.types import PeriodicProgram
from ..productivity.validation import OUTPUT_ENCODING_ID, snapshot_periodic_program

logger = logging.getLogger(__name__)


def _alphabet_digest(symbols: tuple[str, ...]) -> str:
    logger.debug("_alphabet_digest entry symbols=%d", len(symbols))
    result = digest("veyra.p1d3.alphabet.v1", (("count", len(symbols).to_bytes(8, "big")),) + tuple(
        (f"symbol-{i}", symbol.encode()) for i, symbol in enumerate(symbols)
    ))
    logger.debug("_alphabet_digest exit")
    return result
SPEC_VERSION = "p1-d3-family-spec-v1"
TERM_VERSION = "p1-d3-family-term-v1"
NATURAL_INDEX_ID = "lean4.inductive-nat.v1"
STAGE_VALIDATOR_ID = "veyra.p1d3.periodic-finite-prefix.validator.v1"
RELATION_ID = "veyra.p1d3.finite-prefix.exact-equality.v1"
RESTRICTION_ID = "veyra.p1d3.finite-prefix.take.v1"
RELATION_LAW_IDS = (
    "p1-d3-prefix-equality-reflexive-v1", "p1-d3-prefix-equality-symmetric-v1",
    "p1-d3-prefix-equality-transitive-v1",
)
RESTRICTION_LAW_IDS = (
    "p1-d3-prefix-restriction-identity-v1",
    "p1-d3-prefix-restriction-composition-v1",
    "p1-d3-prefix-restriction-congruence-v1",
)
FAMILY_EQUIVALENCE_THEOREM_ID = "p1-d3-coordinatewise-equivalence-v1"
PERIODIC_CONSTRUCTOR_ID = "p1-d3-periodic-family-constructor-v1"
SUPPLIED_CONSTRUCTOR_ID = "p1-d3-supplied-symbolic-family-v1"
ORACLE_CONSTRUCTOR_ID = "p1-d3-oracle-symbolic-family-v1"
_ALLOWED_CONSTRUCTORS = (
    PERIODIC_CONSTRUCTOR_ID, SUPPLIED_CONSTRUCTOR_ID, ORACLE_CONSTRUCTOR_ID,
)


def all_depth_family_spec(
    doctrine: ObserverDoctrine, alphabet: PrefixAlphabet,
) -> AllDepthFamilySpec:
    """Build the exact finite-stage/equality/restriction specification."""
    logger.debug("all_depth_family_spec entry")
    doctrine = snapshot_observer_doctrine(doctrine)
    try:
        alphabet = snapshot_prefix_alphabet(alphabet)
    except (InfinityPrefixValidationError, UnicodeError):
        logger.error("all_depth_family_spec alphabet rejected")
        reject("invalid-d3-alphabet")
    value = spec_digest(
        SPEC_VERSION, doctrine.version, doctrine.fingerprint, _alphabet_digest(alphabet.symbols),
        NATURAL_INDEX_ID, OUTPUT_ENCODING_ID, STAGE_VALIDATOR_ID, RELATION_ID,
        RESTRICTION_ID, RELATION_LAW_IDS, RESTRICTION_LAW_IDS,
        FAMILY_EQUIVALENCE_THEOREM_ID,
    )
    result = AllDepthFamilySpec(
        SPEC_VERSION, doctrine.version, doctrine.fingerprint, alphabet,
        NATURAL_INDEX_ID, OUTPUT_ENCODING_ID, STAGE_VALIDATOR_ID, RELATION_ID,
        RESTRICTION_ID, tuple(RELATION_LAW_IDS), tuple(RESTRICTION_LAW_IDS),
        FAMILY_EQUIVALENCE_THEOREM_ID, value,
    )
    logger.debug("all_depth_family_spec exit")
    return result


def snapshot_family_spec(value: AllDepthFamilySpec) -> AllDepthFamilySpec:
    """Recompute a spec without accepting a doctrine fingerprint as a doctrine."""
    logger.debug("snapshot_family_spec entry")
    exact_shape(value, AllDepthFamilySpec, "all-depth-family-spec")
    try:
        alphabet = snapshot_prefix_alphabet(value.alphabet)
        scalar = (
            (value.version, SPEC_VERSION), (value.natural_index_id, NATURAL_INDEX_ID),
            (value.stage_encoding_id, OUTPUT_ENCODING_ID),
            (value.stage_validator_id, STAGE_VALIDATOR_ID), (value.relation_id, RELATION_ID),
            (value.restriction_id, RESTRICTION_ID),
            (value.family_equivalence_theorem_id, FAMILY_EQUIVALENCE_THEOREM_ID),
        )
        if any(type(actual) is not str or actual != expected for actual, expected in scalar):
            reject("family-spec-scalar-drift")
        exact_identifier(value.doctrine_version, "doctrine-version")
        exact_digest(value.doctrine_fingerprint, "doctrine-fingerprint")
        if (
            type(value.relation_law_ids) is not tuple
            or type(value.restriction_law_ids) is not tuple
            or any(type(item) is not str for item in value.relation_law_ids)
            or any(type(item) is not str for item in value.restriction_law_ids)
            or value.relation_law_ids != RELATION_LAW_IDS
            or value.restriction_law_ids != RESTRICTION_LAW_IDS
        ):
            reject("family-spec-law-drift")
        expected_digest = spec_digest(
            SPEC_VERSION, value.doctrine_version, value.doctrine_fingerprint,
            _alphabet_digest(alphabet.symbols), NATURAL_INDEX_ID, OUTPUT_ENCODING_ID,
            STAGE_VALIDATOR_ID, RELATION_ID, RESTRICTION_ID, RELATION_LAW_IDS,
            RESTRICTION_LAW_IDS, FAMILY_EQUIVALENCE_THEOREM_ID,
        )
        exact_digest(value.specification_digest, "specification-digest")
    except (AttributeError, InfinityPrefixValidationError, UnicodeError):
        reject("family-spec-missing-or-invalid-fields")
    if value.specification_digest != expected_digest:
        reject("family-spec-digest-drift")
    result = AllDepthFamilySpec(
        SPEC_VERSION, value.doctrine_version, value.doctrine_fingerprint, alphabet,
        NATURAL_INDEX_ID, OUTPUT_ENCODING_ID, STAGE_VALIDATOR_ID, RELATION_ID,
        RESTRICTION_ID, tuple(RELATION_LAW_IDS), tuple(RESTRICTION_LAW_IDS),
        FAMILY_EQUIVALENCE_THEOREM_ID, expected_digest,
    )
    logger.debug("snapshot_family_spec exit")
    return result


def periodic_family_term(spec: AllDepthFamilySpec, program: PeriodicProgram) -> FamilyTerm:
    """Bind syntax/program/spec only, excluding execution policy and proof ledger."""
    logger.debug("periodic_family_term entry")
    spec = snapshot_family_spec(spec)
    program = snapshot_periodic_program(program)
    if program.alphabet != spec.alphabet:
        reject("periodic-program-alphabet-spec-mismatch")
    syntax = frame("veyra.p1d3.periodic-term-syntax.v1", (
        ("constructor", PERIODIC_CONSTRUCTOR_ID.encode()),
        ("program", program.program_digest.encode()),
        ("stage-encoding", spec.stage_encoding_id.encode()),
    ))
    value = term_digest(
        TERM_VERSION, PERIODIC_CONSTRUCTOR_ID, program.program_digest,
        syntax, spec.specification_digest,
    )
    result = FamilyTerm(
        TERM_VERSION, PERIODIC_CONSTRUCTOR_ID, program, syntax,
        spec.specification_digest, value,
    )
    logger.debug("periodic_family_term exit")
    return result


def symbolic_family_term(
    spec: AllDepthFamilySpec, constructor_id: str, symbolic_term: bytes,
) -> FamilyTerm:
    """Capture an immutable symbolic supplied/oracle term, never a callable."""
    logger.debug("symbolic_family_term entry")
    spec = snapshot_family_spec(spec)
    constructor_id = exact_identifier(constructor_id, "constructor-id")
    if constructor_id not in (SUPPLIED_CONSTRUCTOR_ID, ORACLE_CONSTRUCTOR_ID):
        reject("unsupported-symbolic-family-constructor")
    symbolic = exact_bytes(symbolic_term, "symbolic-family-term")
    value = term_digest(TERM_VERSION, constructor_id, None, symbolic, spec.specification_digest)
    result = FamilyTerm(TERM_VERSION, constructor_id, None, symbolic, spec.specification_digest, value)
    logger.debug("symbolic_family_term exit")
    return result


def snapshot_family_term(value: FamilyTerm, spec: AllDepthFamilySpec) -> FamilyTerm:
    """Deep-rebuild a periodic or symbolic family term and identity."""
    logger.debug("snapshot_family_term entry")
    spec = snapshot_family_spec(spec)
    exact_shape(value, FamilyTerm, "family-term")
    try:
        if type(value.version) is not str or value.version != TERM_VERSION:
            reject("family-term-version-drift")
        if type(value.constructor_id) is not str or value.constructor_id not in _ALLOWED_CONSTRUCTORS:
            reject("family-term-constructor-drift")
        exact_digest(value.family_spec_digest, "family-spec-digest")
        if value.family_spec_digest != spec.specification_digest:
            reject("family-term-spec-transplant")
        exact_digest(value.family_term_digest, "family-term-digest")
        symbolic = exact_bytes(value.symbolic_term, "family-term-symbolic-bytes")
        if value.constructor_id == PERIODIC_CONSTRUCTOR_ID:
            if type(value.program) is not PeriodicProgram:
                reject("periodic-family-program-missing")
            expected = periodic_family_term(spec, value.program)
            if symbolic != expected.symbolic_term:
                reject("periodic-family-symbolic-term-drift")
        else:
            if value.program is not None:
                reject("symbolic-family-program-present")
            expected = symbolic_family_term(spec, value.constructor_id, value.symbolic_term)
    except AttributeError:
        reject("family-term-missing-fields")
    if value != expected:
        reject("family-term-drift")
    logger.debug("snapshot_family_term exit")
    return expected
