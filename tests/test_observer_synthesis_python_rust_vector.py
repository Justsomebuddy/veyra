"""Shared identity-vector checks for the bounded Python/Rust observer scope."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.core.observer_synthesis_v2_cegis import fit_observer_cegis_v2
from src.core.observer_synthesis_v2_corpus import DEFAULT_CASES
from src.core.observer_synthesis_v2_grammar import enumerate_observer_grammar_v2
from src.core.proof_core_codec import canonical_json

logger = logging.getLogger(__name__)
VECTOR_PATH = Path(__file__).with_name("fixtures") / "observer_synthesis_python_rust_v1.json"
VECTOR_SCHEMA = "veyra.observer-synthesis.python-rust-vector.v1"


def test_python_matches_shared_rust_observer_identity_vector() -> None:
    """Python reproduces the exact catalog and winner identities consumed by Rust."""
    logger.debug("test_python_matches_shared_rust_observer_identity_vector entry")
    text = VECTOR_PATH.read_text(encoding="utf-8").rstrip("\n")
    vector = json.loads(text)
    assert canonical_json(vector) == text
    assert vector["schema"] == VECTOR_SCHEMA

    catalog = enumerate_observer_grammar_v2()
    report = fit_observer_cegis_v2(catalog, DEFAULT_CASES[:2])
    assert report.winner is not None
    assert vector["candidate_count"] == len(catalog.candidates)
    assert vector["canonical_bytes"] == catalog.canonical_bytes
    assert vector["catalog_digest"] == catalog.catalog_digest
    assert vector["winner"] == {
        "canonical": report.winner.canonical.decode("utf-8"),
        "cost": report.winner.cost,
        "depth": report.winner.depth,
        "digest": report.winner.digest,
        "ordinal": report.winner.ordinal,
    }
    logger.debug("test_python_matches_shared_rust_observer_identity_vector exit")
