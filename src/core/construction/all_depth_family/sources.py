"""Exact AFIP source construction and replay for P1-D3."""

from __future__ import annotations

import logging

from .common import exact_digest, exact_shape, reject
from .digest import introduction_digest, source_digest as make_source_digest
from .formal import check_formal_source, snapshot_formal_source
from .hypotheses import (
    snapshot_oracle_hypothesis, snapshot_supplied_hypothesis,
)
from .ledger import require_periodic_ledger, snapshot_assumption_ledger
from .spec import periodic_family_term, snapshot_family_spec, snapshot_family_term
from .types import (
    AllDepthFamilySpec, AssumptionLedger, FamilyHypothesis, FamilyIntroductionSource,
    FormalFamilySource, IntroductionKind, OracleFamilyHypothesis, ProjectionCapability,
)
from ..productivity.digest import generator_digest as d1_generator_digest
from ..productivity.types import ProductiveProcessSource
from ..productivity.validation import snapshot_productive_source

logger = logging.getLogger(__name__)


def derived_family_source(
    spec: AllDepthFamilySpec, d1_source: ProductiveProcessSource,
    formal_source: FormalFamilySource, ledger: AssumptionLedger,
) -> FamilyIntroductionSource:
    """Replay raw D1/formal bytes and introduce one policy-independent family."""
    logger.debug("derived_family_source entry")
    spec = snapshot_family_spec(spec)
    d1_source = snapshot_productive_source(d1_source)
    ledger = require_periodic_ledger(ledger)
    formal_source = check_formal_source(formal_source)
    term = periodic_family_term(spec, d1_source.program)
    evidence = introduction_digest("periodic-derived", (
        ("spec", spec.specification_digest.encode()),
        ("generator", d1_source.generator_digest.encode()),
        ("formal", formal_source.formal_source_digest.encode()),
        ("ledger", ledger.ledger_digest.encode()),
    ))
    source_value = make_source_digest(
        IntroductionKind.PERIODIC_DERIVED.value, spec.specification_digest,
        term.family_term_digest, evidence, ProjectionCapability.PERIODIC_EXECUTABLE.value,
    )
    result = FamilyIntroductionSource(
        IntroductionKind.PERIODIC_DERIVED, spec, term, ledger,
        d1_source.generator_digest, formal_source, None, None, evidence, source_value,
        ProjectionCapability.PERIODIC_EXECUTABLE,
    )
    logger.debug("derived_family_source exit source=%s", source_value)
    return result


def supplied_family_source(
    spec: AllDepthFamilySpec, hypothesis: FamilyHypothesis, ledger: AssumptionLedger,
) -> FamilyIntroductionSource:
    """Admit an explicit symbolic family hypothesis as assumed only."""
    logger.debug("supplied_family_source entry")
    spec = snapshot_family_spec(spec)
    ledger = snapshot_assumption_ledger(ledger)
    hypothesis = snapshot_supplied_hypothesis(hypothesis, spec)
    if hypothesis.ledger != ledger:
        reject("supplied-hypothesis-ledger-transplant")
    evidence = introduction_digest("supplied", (
        ("spec", spec.specification_digest.encode()),
        ("hypothesis", hypothesis.hypothesis_digest.encode()),
        ("ledger", ledger.ledger_digest.encode()),
    ))
    source_value = make_source_digest(
        IntroductionKind.SUPPLIED.value, spec.specification_digest,
        hypothesis.term.family_term_digest, evidence, ProjectionCapability.SYMBOLIC_ONLY.value,
    )
    result = FamilyIntroductionSource(
        IntroductionKind.SUPPLIED, spec, hypothesis.term, ledger, None, None,
        hypothesis, hypothesis.hypothesis_digest, evidence, source_value,
        ProjectionCapability.SYMBOLIC_ONLY,
    )
    logger.debug("supplied_family_source exit")
    return result


def oracle_family_source(
    spec: AllDepthFamilySpec, hypothesis: OracleFamilyHypothesis, ledger: AssumptionLedger,
) -> FamilyIntroductionSource:
    """Admit a named total-oracle hypothesis without executing or upgrading it."""
    logger.debug("oracle_family_source entry")
    spec = snapshot_family_spec(spec)
    ledger = snapshot_assumption_ledger(ledger)
    hypothesis = snapshot_oracle_hypothesis(hypothesis, spec)
    if hypothesis.ledger != ledger:
        reject("oracle-hypothesis-ledger-transplant")
    evidence = introduction_digest("oracle", (
        ("spec", spec.specification_digest.encode()),
        ("hypothesis", hypothesis.hypothesis_digest.encode()),
        ("ledger", ledger.ledger_digest.encode()),
    ))
    source_value = make_source_digest(
        IntroductionKind.ORACLE.value, spec.specification_digest,
        hypothesis.term.family_term_digest, evidence, ProjectionCapability.ORACLE_INTERFACE.value,
    )
    result = FamilyIntroductionSource(
        IntroductionKind.ORACLE, spec, hypothesis.term, ledger, None, None,
        hypothesis, hypothesis.hypothesis_digest, evidence, source_value,
        ProjectionCapability.ORACLE_INTERFACE,
    )
    logger.debug("oracle_family_source exit")
    return result


def snapshot_family_source(value: FamilyIntroductionSource) -> FamilyIntroductionSource:
    """Deeply rebuild any positive source without compiling or oracle querying."""
    logger.debug("snapshot_family_source entry")
    exact_shape(value, FamilyIntroductionSource, "family-introduction-source")
    try:
        if type(value.kind) is not IntroductionKind or type(value.capability) is not ProjectionCapability:
            reject("source-kind-or-capability-must-be-exact")
        if value.generator_digest is not None:
            exact_digest(value.generator_digest, "generator-digest")
        if value.formal_source is not None and type(value.formal_source) is not FormalFamilySource:
            reject("formal-source-optional-lane-must-be-exact")
        if value.hypothesis is not None and type(value.hypothesis) not in (
            FamilyHypothesis, OracleFamilyHypothesis,
        ):
            reject("hypothesis-optional-lane-must-be-exact")
        if value.hypothesis_digest is not None:
            exact_digest(value.hypothesis_digest, "hypothesis-digest")
        exact_digest(value.introduction_evidence_digest, "introduction-evidence-digest")
        exact_digest(value.source_digest, "source-digest")
        spec = snapshot_family_spec(value.spec)
        term = snapshot_family_term(value.term, spec)
        ledger = snapshot_assumption_ledger(value.ledger)
        if value.kind is IntroductionKind.PERIODIC_DERIVED:
            expected = _snapshot_derived(value, spec, term, ledger)
        elif value.kind is IntroductionKind.SUPPLIED:
            expected = _snapshot_supplied(value, spec, ledger)
        else:
            expected = _snapshot_oracle(value, spec, ledger)
    except AttributeError:
        reject("family-introduction-source-missing-fields")
    if value != expected:
        reject("family-introduction-source-drift")
    logger.debug("snapshot_family_source exit kind=%s", value.kind.value)
    return expected

def _snapshot_derived(value, spec, term, ledger) -> FamilyIntroductionSource:
    logger.debug("_snapshot_derived entry")
    if (
        term.program is None or type(value.generator_digest) is not str
        or value.hypothesis is not None or value.hypothesis_digest is not None
        or type(value.formal_source) is not FormalFamilySource
        or value.capability is not ProjectionCapability.PERIODIC_EXECUTABLE
    ):
        reject("invalid-derived-source-shape")
    formal = snapshot_formal_source(value.formal_source)
    expected_generator = d1_generator_digest(
        term.program.program_digest, "p1-d1-periodic-modulo-total-v1",
        "p1-d1-prefix-restriction-v1", "veyra.p1d1.periodic-prefix-stage.v1",
    )
    exact_digest(value.generator_digest, "generator-digest")
    if value.generator_digest != expected_generator or ledger != require_periodic_ledger(ledger):
        reject("derived-generator-or-ledger-drift")
    evidence = introduction_digest("periodic-derived", (
        ("spec", spec.specification_digest.encode()), ("generator", expected_generator.encode()),
        ("formal", formal.formal_source_digest.encode()), ("ledger", ledger.ledger_digest.encode()),
    ))
    result = _assemble(
        value.kind, spec, term, ledger, expected_generator, formal, None, None,
        evidence, ProjectionCapability.PERIODIC_EXECUTABLE,
    )
    logger.debug("_snapshot_derived exit")
    return result


def _snapshot_supplied(value, spec, ledger) -> FamilyIntroductionSource:
    logger.debug("_snapshot_supplied entry")
    if (
        value.generator_digest is not None or value.formal_source is not None
        or type(value.hypothesis) is not FamilyHypothesis
        or type(value.hypothesis_digest) is not str
        or value.capability is not ProjectionCapability.SYMBOLIC_ONLY
    ):
        reject("invalid-supplied-source-shape")
    exact_digest(value.hypothesis_digest, "hypothesis-digest")
    hypothesis = snapshot_supplied_hypothesis(value.hypothesis, spec)
    if hypothesis.ledger != ledger:
        reject("supplied-hypothesis-ledger-transplant")
    evidence = introduction_digest("supplied", (
        ("spec", spec.specification_digest.encode()),
        ("hypothesis", hypothesis.hypothesis_digest.encode()),
        ("ledger", ledger.ledger_digest.encode()),
    ))
    if value.hypothesis_digest != hypothesis.hypothesis_digest:
        reject("supplied-hypothesis-digest-drift")
    result = _assemble(
        value.kind, spec, hypothesis.term, ledger, None, None, hypothesis,
        hypothesis.hypothesis_digest, evidence, ProjectionCapability.SYMBOLIC_ONLY,
    )
    logger.debug("_snapshot_supplied exit")
    return result


def _snapshot_oracle(value, spec, ledger) -> FamilyIntroductionSource:
    logger.debug("_snapshot_oracle entry")
    if (
        value.generator_digest is not None or value.formal_source is not None
        or type(value.hypothesis) is not OracleFamilyHypothesis
        or type(value.hypothesis_digest) is not str
        or value.capability is not ProjectionCapability.ORACLE_INTERFACE
    ):
        reject("invalid-oracle-source-shape")
    exact_digest(value.hypothesis_digest, "hypothesis-digest")
    hypothesis = snapshot_oracle_hypothesis(value.hypothesis, spec)
    if hypothesis.ledger != ledger:
        reject("oracle-hypothesis-ledger-transplant")
    evidence = introduction_digest("oracle", (
        ("spec", spec.specification_digest.encode()),
        ("hypothesis", hypothesis.hypothesis_digest.encode()),
        ("ledger", ledger.ledger_digest.encode()),
    ))
    if value.hypothesis_digest != hypothesis.hypothesis_digest:
        reject("oracle-hypothesis-digest-drift")
    result = _assemble(
        value.kind, spec, hypothesis.term, ledger, None, None, hypothesis,
        hypothesis.hypothesis_digest, evidence, ProjectionCapability.ORACLE_INTERFACE,
    )
    logger.debug("_snapshot_oracle exit")
    return result


def _assemble(kind, spec, term, ledger, generator, formal, hypothesis, hypothesis_digest,
              evidence, capability) -> FamilyIntroductionSource:
    logger.debug("_assemble entry kind=%s", kind.value)
    source_value = make_source_digest(
        kind.value, spec.specification_digest, term.family_term_digest,
        evidence, capability.value,
    )
    result = FamilyIntroductionSource(
        kind, spec, term, ledger, generator, formal, hypothesis, hypothesis_digest,
        evidence, source_value, capability,
    )
    logger.debug("_assemble exit")
    return result
