import pytest

from veyra_sage import number_theory_oracle as module
from veyra_sage.all import NumberTheoryOracleRow, VeyraNumberTheoryOracleLab, number_theory_oracle_rows, number_theory_oracle_summary

EXPECTED_LANES = ("fermat-lyndon", "gauss-mobius", "primitive-root", "commutation", "padic-domain", "fermat-phase", "break-locus-gcd")


def test_oracle_fails_closed_without_sage(monkeypatch):
    def unavailable():
        raise RuntimeError(module.SAGE_REQUIRED_REASON)

    monkeypatch.setattr(module, "_sage", unavailable)
    summary = number_theory_oracle_summary()
    assert summary["status"] == "unavailable"
    assert summary["reason"] == module.SAGE_REQUIRED_REASON
    assert summary["rows"] == [] and summary["checked"] == 0
    with pytest.raises(RuntimeError, match=module.SAGE_REQUIRED_REASON):
        number_theory_oracle_rows()


def test_row_is_json_ready_and_never_passes_on_empty_or_mismatch():
    passed = NumberTheoryOracleRow("x", 3, 0, "d", True).as_dict()
    assert passed == {"lane": "x", "checked": 3, "mismatches": 0, "detail": "d", "sage_crosscheck_passed": True}
    assert not module._row("x", 0, 0, "d").sage_crosscheck_passed
    assert not module._row("x", 3, 1, "d").sage_crosscheck_passed


def test_real_sage_oracle_lanes_all_witnessed():
    pytest.importorskip("sage.all")
    summary = VeyraNumberTheoryOracleLab().summary()
    assert summary["status"] == "witnessed"
    assert summary["backend"] == "python+real-sage"
    assert summary["mismatches"] == 0
    assert tuple(row["lane"] for row in summary["rows"]) == EXPECTED_LANES
    assert all(row["sage_crosscheck_passed"] for row in summary["rows"])
    checked = {row["lane"]: row["checked"] for row in summary["rows"]}
    assert checked["primitive-root"] == sum(3**length for length in range(1, 8))
    assert checked["commutation"] == 63 * 63
    assert checked["break-locus-gcd"] == 90 + 20 + 15 + 70 + 420 + 1
    assert checked["fermat-phase"] == 6 + 4


def test_real_sage_break_locus_gcd_form_matches_witness():
    sage = pytest.importorskip("sage.all")
    from src.core.break_locus import refutation_witness

    word, alphabet = refutation_witness()
    locus = module._gcd_form_locus(sage, tuple(word), tuple(alphabet))
    assert locus == ((("a", "b"), ("b", "c")), (("a", "c"), ("b", "c")))
    projections = {pair: [x for x in word if x in pair] for pair in (("a", "b"), ("a", "c"), ("b", "c"))}
    exponents = {pair: len(proj) // int(sage.Word(proj).primitive_length()) for pair, proj in projections.items()}
    assert exponents == {("a", "b"): 2, ("a", "c"): 3, ("b", "c"): 1}
