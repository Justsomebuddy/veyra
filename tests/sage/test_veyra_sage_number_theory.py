from veyra_sage.all import VeyraNumberTheoryLab, build_number_theory_notebook, number_theory_lab_summary


def test_number_theory_lab_summary_closes_x2():
    assert number_theory_lab_summary() == {"divisibility": 2, "blocked": 1, "prime_rows": 3, "rank_rows": 3, "factor_hits": 2, "fermat_rows": 7, "fermat_derived": 4, "fermat_units": 13, "checklist": 4}


def test_number_theory_lab_rows_are_json_ready():
    lab = VeyraNumberTheoryLab()
    divs = lab.divisibility_rows()
    primes = lab.prime_rows()
    ranks = lab.rank_factor_rows()
    fermat = lab.fermat_rows()
    assert divs[0]["status"] == "divides"
    assert divs[1]["obstruction"] == "length-obstruction"
    assert [row["status"] for row in primes] == ["variant", "blocked", "blocked"]
    assert [row["factor_status"] for row in ranks] == ["divides", "divides", "blocked"]
    assert [row["status"] for row in fermat] == ["derived", "derived", "derived", "derived", "blocked", "blocked", "blocked"]


def test_number_theory_notebook_is_executable_contract():
    notebook = build_number_theory_notebook()
    assert notebook.summary() == {"cells": 5, "markdown": 2, "code": 3}
    assert "VeyraNumberTheoryLab" in notebook.to_markdown()
