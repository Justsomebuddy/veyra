from src.core.proof_discipline import (
    primitive_model_notes,
    proof_discipline_checklist,
    proof_discipline_summary,
    proof_rule_coverage,
    proof_rule_coverage_summary,
    semantic_domain_coverage,
    stable_formal_export_rows,
)


def test_rule_coverage_records_rules_statuses_and_spans():
    rows = {row.rule: row for row in proof_rule_coverage()}
    assert rows["infer.echo"].ready >= 1
    assert rows["infer.echo"].blocked >= 1
    assert rows["infer.echo"].unknown >= 1
    assert rows["grammar.parse"].blocked == 1
    assert rows["kind.nod"].spans == rows["kind.nod"].count


def test_rule_coverage_summary_is_nontrivial():
    summary = proof_rule_coverage_summary()
    assert summary["rules"] >= 7
    assert summary["steps"] >= 28
    assert summary["blocked_rules"] >= 1
    assert summary["spans"] >= 20


def test_semantic_domain_coverage_names_school_shadows():
    rows = {row.domain: row for row in semantic_domain_coverage()}
    assert set(rows) == {"arithmetic", "geometry", "logic", "analysis", "topology", "probability", "statistics"}
    assert rows["arithmetic"].status == "ready"
    assert "length" in rows["arithmetic"].keys
    assert "boundary" in rows["geometry"].keys
    assert "status" in rows["logic"].keys
    assert "variation" in rows["analysis"].keys
    assert "deformation_class" in rows["topology"].keys
    assert "sample_space" in rows["probability"].keys
    assert "support_size" in rows["statistics"].keys
    assert all(row.certificate == "declared-shadow" and not row.missing_keys for row in rows.values())
    assert all(row.counter_status == "blocked" for row in rows.values())


def test_model_notes_cover_native_primitives():
    notes = {row.name: row for row in primitive_model_notes()}
    assert {"rez", "nod", "tact", "echo", "cycle-echo", "compression"} <= set(notes)
    assert all(row.status == "model-noted" and row.witness for row in notes.values())


def test_stable_formal_export_gate_is_theorem_card_only():
    rows = stable_formal_export_rows()
    assert len(rows) == 19
    assert all(row.export_status == "stable-card-only" for row in rows)
    assert all(row.hook != "pending" and row.dependencies for row in rows)


def test_proof_discipline_summary_and_checklist_close_sprint_f():
    summary = proof_discipline_summary()
    assert summary == {"rules": 7, "steps": 28, "blocked_rules": 3, "domains": 7, "domain_certs": 7, "models": 10, "exports": 19}
    assert proof_discipline_checklist() == (
        "rule/source-span coverage",
        "semantic shadow certificates",
        "primitive model/consistency notes",
        "stable-card formal-export gate",
    )
