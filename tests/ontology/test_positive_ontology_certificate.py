"""Certificate, public-surface, and boundary regressions for P0."""

import logging
from pathlib import Path

import src.core as core
from src.core.certify_positive_ontology import certify_positive_ontology_p0
from src.core.paths import PROJECT_ROOT

logger = logging.getLogger(__name__)


def test_positive_ontology_certificate_is_level_one_and_nonmetaphysical():
    logger.debug("test_positive_ontology_certificate_is_level_one_and_nonmetaphysical entry")
    result = certify_positive_ontology_p0()
    assert result.name == "positive_ontology_p0"
    assert result.level == 1 and result.passed
    assert result.method == (
        "provisional bounded fixed-family pressure; no completed admission or translation"
    )
    assert result.detail == (
        "provisional-bounded-fixed-family=crest+tail persistence=echo "
        "family-extension=split pairwise/global=True/False infinity=2+3-boundaries "
        "no-completed-admission-or-translation"
    )
    logger.debug("test_positive_ontology_certificate_is_level_one_and_nonmetaphysical exit")


def test_positive_ontology_public_surface_exports_typed_judgments():
    logger.debug("test_positive_ontology_public_surface_exports_typed_judgments entry")
    expected = {
        "InternalObserver", "ObserverDoctrine", "OntologyStage", "ContinuationWitness",
        "OntologyPresentation", "RunJudgment", "ObserverSupportJudgment",
        "PersistenceJudgment", "FamilyExtensionJudgment", "PresentationCommitment",
        "DiagramCoherenceJudgment",
        "InfinityJudgment", "OntologyFacetReport", "FacetStatus",
        "internal_observer", "ontology_stage", "continuation_witness",
        "ontology_presentation", "observer_support_judgment", "persistence_judgment",
        "family_extension_judgment", "diagram_coherence_judgment",
        "bounded_window_judgment", "local_extension_judgment",
        "nonfinite_infinity_boundary", "ontology_facet_report",
        "metalanguage_boundary", "positive_ontology_checklist",
        "SilenceBoundaryJudgment", "silence_boundary_judgment",
        "observer_doctrine", "p0_observer_doctrine", "presentation_commitment",
    }
    assert expected <= set(core.__all__)
    for name in expected:
        assert getattr(core, name) is not None
    logger.debug("test_positive_ontology_public_surface_exports_typed_judgments exit")


def test_positive_ontology_logic_never_compares_representatives_as_identity():
    logger.debug("test_positive_ontology_logic_never_compares_representatives_as_identity entry")
    text = (PROJECT_ROOT / "src/core/ontology/core.py").read_text(encoding="utf-8")
    assert "representative ==" not in text
    assert "representative !=" not in text
    assert "lower.representative ==" not in text
    assert "upper.representative ==" not in text
    assert "canonical observer bytes" in str(core.metalanguage_boundary().metatheory_identity)
    logger.debug("test_positive_ontology_logic_never_compares_representatives_as_identity exit")
