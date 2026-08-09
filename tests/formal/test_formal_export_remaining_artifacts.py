"""Source-level checks for the final four fixed X8 Lean artifacts."""

import hashlib
import logging
from pathlib import Path

from src.core.formal_export_remaining_data import (
    ANALYSIS_ARTIFACT_SHA256,
    CYCLIC_ARTIFACT_SHA256,
    REMAINING_FORMAL_EXPORT_ROWS,
)
from src.core.paths import LEAN_DIR

logger = logging.getLogger(__name__)

IDS = ("sampled-continuity", "drift-stability", "area-additivity", "chord-symmetry")
SYMBOLS = (
    "THM_A004_sampled_continuity_double_0_five_points",
    "THM_A005_square_symmetric_drift_3_steps_1_2_3",
    "THM_A006_identity_midpoint_area_4_4_8",
    "THM_C002_chord_symmetry_12_0_3_9",
)


def test_remaining_metadata_has_exact_order_hooks_dependencies_and_boundaries():
    """Bind all four rows to their existing executable-card identities."""
    logger.debug("test_remaining_metadata_has_exact_order_hooks_dependencies_and_boundaries entry")
    assert tuple(row[0] for row in REMAINING_FORMAL_EXPORT_ROWS) == IDS
    assert tuple(row[5] for row in REMAINING_FORMAL_EXPORT_ROWS) == SYMBOLS
    assert tuple((row[2], row[3]) for row in REMAINING_FORMAL_EXPORT_ROWS) == (
        ("analysis.sampled_continuity", ("DEF-072", "DEF-073", "DEF-086")),
        ("analysis.drift_stability", ("DEF-074", "DEF-086")),
        ("analysis.area_additivity", ("DEF-075", "DEF-086")),
        ("trig.chord_symmetry", ("DEF-106", "DEF-108", "DEF-086")),
    )
    assert all("formalizes only" in row[7] and "no claim about general" in row[7] for row in REMAINING_FORMAL_EXPORT_ROWS)
    logger.debug("test_remaining_metadata_has_exact_order_hooks_dependencies_and_boundaries exit")


def test_remaining_metadata_pins_actual_whole_file_digests():
    """Keep A001-A006 and C001-C002 on their respective whole-file hashes."""
    logger.debug("test_remaining_metadata_pins_actual_whole_file_digests entry")
    algebra = (LEAN_DIR / "VeyraAlgebra.lean").read_bytes()
    cyclic = (LEAN_DIR / "VeyraCyclic.lean").read_bytes()
    assert hashlib.sha256(algebra).hexdigest() == ANALYSIS_ARTIFACT_SHA256
    assert hashlib.sha256(cyclic).hexdigest() == CYCLIC_ARTIFACT_SHA256
    assert tuple(row[6] for row in REMAINING_FORMAL_EXPORT_ROWS[:3]) == (ANALYSIS_ARTIFACT_SHA256,) * 3
    assert REMAINING_FORMAL_EXPORT_ROWS[3][6] == CYCLIC_ARTIFACT_SHA256
    logger.debug("test_remaining_metadata_pins_actual_whole_file_digests exit")


def test_analysis_artifact_states_only_the_three_fixed_fixtures():
    """Reject drift from the canonical finite continuity, drift, and area cards."""
    logger.debug("test_analysis_artifact_states_only_the_three_fixed_fixtures entry")
    text = (LEAN_DIR / "VeyraAlgebra.lean").read_text()
    literals = (
        "(-2 : Int) * 2 = -4", "(2 : Int) * 2 = 4", "(4 : Nat) * 5 = 20",
        "(4 : Int) * 4 - 2 * 2 = 6 * (2 * 1)",
        "(5 : Int) * 5 - 1 * 1 = 6 * (2 * 2)",
        "(6 : Int) * 6 - 0 * 0 = 6 * (2 * 3)",
        "(1 : Nat) + 3 + 5 + 7 = 16", "9 + 11 + 13 + 15 = 48",
        "1 + 3 + 5 + 7 + 9 + 11 + 13 + 15 = 64", "16 + 48 = 64",
    )
    assert all(literal in text for literal in literals)
    assert all(f"theorem {symbol} :" in text for symbol in SYMBOLS[:3])
    logger.debug("test_analysis_artifact_states_only_the_three_fixed_fixtures exit")


def test_cyclic_artifact_preserves_c001_and_pins_fixed_chord_mirror():
    """Preserve the original period theorem while adding only the 0/3/9 shell."""
    logger.debug("test_cyclic_artifact_preserves_c001_and_pins_fixed_chord_mirror entry")
    text = (LEAN_DIR / "VeyraCyclic.lean").read_text()
    assert "theorem THM_C001_cyclic_period (phase modulus : Nat)" in text
    assert f"theorem {SYMBOLS[3]} :" in text
    assert "Nat.min 3 (12 - 3) = 3" in text
    assert "Nat.min 9 (12 - 9) = 3" in text
    assert "4 * 3 * (12 - 3) = 108" in text
    assert "4 * (12 - 9) * (12 - (12 - 9)) = 108" in text
    assert "4 * 3 * (12 - 3) = 4 * (12 - 9) * (12 - (12 - 9))" in text
    assert text.count("108 * 4 = 3 * (12 * 12)") == 1
    logger.debug("test_cyclic_artifact_preserves_c001_and_pins_fixed_chord_mirror exit")


def test_new_declarations_are_closed_and_have_no_general_quantifiers():
    """Ensure each new theorem has no parameters, forall, or variable declaration."""
    logger.debug("test_new_declarations_are_closed_and_have_no_general_quantifiers entry")
    texts = {
        **{symbol: (LEAN_DIR / "VeyraAlgebra.lean").read_text() for symbol in SYMBOLS[:3]},
        SYMBOLS[3]: (LEAN_DIR / "VeyraCyclic.lean").read_text(),
    }
    for symbol, text in texts.items():
        start = text.index(f"theorem {symbol} :")
        end_candidates = [position for marker in ("\ntheorem ", "\n#check ", "\nend ") if (position := text.find(marker, start + 1)) >= 0]
        declaration = text[start:min(end_candidates)]
        assert "∀" not in declaration and "forall" not in declaration and "variable" not in declaration
    logger.debug("test_new_declarations_are_closed_and_have_no_general_quantifiers exit")
