from veyra_sage.all import VeyraSchoolCore, VeyraTheoremSpec


def test_veyra_school_core_summary_and_missing():
    school = VeyraSchoolCore()
    summary = school.summary()
    assert summary["theorem_specs"] == 19
    assert summary["curriculum_nodes"] == 11
    assert summary["curriculum_missing"] == 0
    assert summary["sage_rows"] == 19
    assert school.missing() == ()


def test_veyra_school_core_lookup_wrappers():
    school = VeyraSchoolCore()
    spec = school.theorem_spec("pythagorean-separation")
    node = school.curriculum_node("probability")
    assert isinstance(spec, VeyraTheoremSpec)
    assert spec.hook == "geometry.pythagorean"
    assert node.status == "covered"
    assert "probability-complement" in node.theorem_ids


def test_veyra_school_core_export_rows_are_json_ready():
    school = VeyraSchoolCore()
    rows = school.export_rows()
    dicts = school.export_dicts()
    assert len(rows) == 38
    assert len(dicts) == 38
    assert any(row.row_type == "theorem" and row.name == "binomial-symmetry" for row in rows)
    assert any(item["row_type"] == "curriculum" and item["hook"] == "statistics.variance_shift" for item in dicts)
