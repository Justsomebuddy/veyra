import json

from src.core.compression import CompressionWeights
from src.core.modes import Mode
from src.core.tables import (
    approx_resonance_rows,
    compression_rows,
    counterexample_data,
    cyclic_weave_rows,
    language_coverage_rows,
    phase_resonance_rows,
    prime_variant_rows,
    spectrum_rows,
    span_diagnostic_rows,
    weighted_resonance_rows,
    write_csv,
    write_json,
    write_manifest,
)


def test_spectrum_and_compression_rows_have_expected_candidate():
    whole = Mode.from_word("abac")
    spectrum = spectrum_rows(whole, ("a", "b", "c"), 2, 2, 1)
    assert any(row["part"] == "ab" and row["obstruction"] == "bounded-defect" for row in spectrum)
    compression = compression_rows(whole, ("a", "b", "c"), 2, 2, 1, CompressionWeights(defect_weight=1.0))
    assert compression[0]["saving"] >= 1.0


def test_prime_and_counterexample_rows():
    prime_rows = prime_variant_rows(("a", "b"), 2, tact="a")
    assert any(row["mode"] == "aa" and row["numeric_prime"] for row in prime_rows)
    data = counterexample_data(("a", "b"), 2, 2)
    assert data["echo_splits"]
    assert data["stitch_commutators"]
    assert data["weave_incompatibilities"]


def test_phase_approx_and_cyclic_weave_rows():
    phase = phase_resonance_rows(Mode.from_word("ab"), ("a", "b"), 2)
    assert any(row["whole"] == "ba" and row["cyclic"] and not row["ordered"] for row in phase)
    approx = approx_resonance_rows(Mode.from_word("ab"), ("a", "b", "c"), 2, 1)
    assert any(row["whole"] == "ac" and row["obstruction"] == "bounded-defect" for row in approx)
    weighted = weighted_resonance_rows(Mode.from_word("ab"), ("a", "b", "c"), 2, 0.5, {("b", "c"): 0.25}, 1.0)
    assert any(row["whole"] == "ac" and row["resonates"] and row["obstruction"] == "weighted-defect" for row in weighted)
    weave = cyclic_weave_rows(("a", "b"), 2, {"a": Mode.from_word("x"), "b": Mode.from_word("yy")})
    assert any(row["driver"] == "ba" and row["cyclic_output"] == "xyy" for row in weave)


def test_core_language_table_rows():
    coverage = language_coverage_rows()
    assert len(coverage) == 11
    assert coverage[0] == {"family": "grammar", "cases": 4, "blocked": 4, "unknown": 0, "ready": 0, "unexpected": 0, "covered": True}
    assert sum(row["cases"] for row in coverage) == 54

    diagnostics = span_diagnostic_rows()
    assert len(diagnostics) == 7
    assert all(row["ok"] for row in diagnostics)
    assert any(row["name"] == "newline-close" and row["multiline"] for row in diagnostics)


def test_write_artifacts(tmp_path):
    csv_artifact = write_csv(tmp_path / "sample.csv", [{"a": 1}], ["a"])
    assert csv_artifact.rows == 1
    assert (tmp_path / "sample.csv").read_text().startswith("a")
    json_artifact = write_json(tmp_path / "sample.json", {"x": [1, 2]}, rows=2)
    assert json_artifact.rows == 2
    assert json.loads((tmp_path / "sample.json").read_text())["x"] == [1, 2]
    manifest = write_manifest(tmp_path / "manifest.json", {"p": 1}, [csv_artifact, json_artifact])
    assert manifest.rows == 2
