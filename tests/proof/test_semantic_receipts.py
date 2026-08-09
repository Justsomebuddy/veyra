from dataclasses import replace

import pytest

from src.core.semantic_kernel import axiom_closure, evaluate_native, replay_receipts, verify_receipts


SOURCE = "mode(breath(tact(nod:a,nod:a)))"


def test_receipts_are_deterministic_replayable_and_axioms_are_rule_derived():
    first = evaluate_native(SOURCE)
    second = evaluate_native(SOURCE)
    assert first.receipts == second.receipts
    assert replay_receipts(SOURCE, first.receipts).ok
    assert axiom_closure(first.receipts) == ("AX-REZ", "AX-NOD", "AX-TACT", "AX-BREATH", "AX-MODE")
    assert first.axioms == axiom_closure(first.receipts)


def test_checker_rejects_conclusion_tampering():
    rows = evaluate_native(SOURCE).receipts
    damaged = rows[:-1] + (replace(rows[-1], conclusion='"tampered"'),)
    checked = verify_receipts(damaged)
    assert not checked.ok
    assert any(error.startswith("tampered:") for error in checked.errors)
    with pytest.raises(ValueError, match="invalid receipt graph"):
        axiom_closure(damaged)


def test_checker_rejects_dangling_and_unknown_rule_ids():
    rows = evaluate_native(SOURCE).receipts
    dangling = rows[:-1] + (replace(rows[-1], premise_ids=rows[-1].premise_ids + ("R-missing",)),)
    unknown = rows[:-1] + (replace(rows[-1], rule_id="SK-NOT-A-RULE"),)
    assert any(error.startswith("dangling:") for error in verify_receipts(dangling).errors)
    assert "unknown-rule:SK-NOT-A-RULE" in verify_receipts(unknown).errors


def test_checker_rejects_cycles_before_accepting_graph():
    rows = evaluate_native(SOURCE).receipts
    root = rows[-1]
    cyclic = rows[:-1] + (replace(root, premise_ids=root.premise_ids + (root.receipt_id,)),)
    checked = verify_receipts(cyclic)
    assert not checked.ok
    assert any(error.startswith("cycle:") for error in checked.errors)


def test_checker_rejects_disconnected_extra_receipts_and_axioms():
    rows = evaluate_native(SOURCE).receipts
    foreign = evaluate_native("echo(nod:x,nod:y,observer:kind)").receipts
    combined = rows + tuple(row for row in foreign if row.receipt_id not in {item.receipt_id for item in rows})
    checked = verify_receipts(combined)
    assert not checked.ok
    assert any(error.startswith("graph-roots:") or error == "disconnected-receipts" for error in checked.errors)
    with pytest.raises(ValueError, match="invalid receipt graph"):
        axiom_closure(combined)


def test_blocked_native_rules_keep_the_operation_and_obstruction_axioms():
    non_contiguous = evaluate_native("breath(tact(nod:a,nod:b),tact(nod:c,nod:a))")
    open_mode = evaluate_native("mode(breath(tact(nod:a,nod:b)))")
    assert {"AX-BREATH", "AX-OBSTRUCTION"} <= set(non_contiguous.axioms)
    assert {"AX-BREATH", "AX-MODE", "AX-OBSTRUCTION"} <= set(open_mode.axioms)
