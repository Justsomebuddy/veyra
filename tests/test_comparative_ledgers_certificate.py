import logging

import src.core as core
from src.core.certify_comparative_ledgers import certify_comparative_bridge_separation_ledgers

logger = logging.getLogger(__name__)


def test_comparative_ledgers_certificate_binds_exact_catalogs_and_no_promotion():
    logger.debug("test_comparative_ledgers_certificate_binds_exact_catalogs_and_no_promotion entry")
    result = certify_comparative_bridge_separation_ledgers()
    assert result.name == "comparative_bridge_separation_ledgers"
    assert result.passed and result.level == 1
    assert result.detail == "bridges=3 reduced=1 open=1 separations=1 strict=1 promotions=0"
    logger.debug("test_comparative_ledgers_certificate_binds_exact_catalogs_and_no_promotion exit")


def test_comparative_and_g4_classification_root_exports_are_collision_safe():
    logger.debug("test_comparative_and_g4_classification_root_exports_are_collision_safe entry")
    expected = {
        "ComparativeBridgeRow",
        "ComparativeBridgeStatus",
        "StructuralSeparationRow",
        "StructuralSeparationStatus",
        "comparative_bridge_rows",
        "structural_separation_rows",
        "ExactGluingClassification",
        "QuotientConflictGraph",
        "classify_exact_gluings",
        "quotient_conflict_graph",
    }
    assert len(core.__all__) == len(set(core.__all__))
    assert expected <= set(core.__all__)
    assert core.ComparativeBridgeStatus is not core.StructuralSeparationStatus
    logger.debug("test_comparative_and_g4_classification_root_exports_are_collision_safe exit")
