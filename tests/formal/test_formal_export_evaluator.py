"""Parity and public-identity regressions for the internal X8 evaluator split."""
import logging
import pickle

import src.core.formal_export_completion as completion
from src.core.formal_export_catalog import formal_export_specs
from src.core.formal_export_evaluator import evaluate_completion_row, find_prep_row

logger = logging.getLogger(__name__)


def test_evaluator_matches_completion_wrapper_and_preserves_class_identity():
    logger.debug("test_evaluator_matches_completion_wrapper_and_preserves_class_identity entry")
    spec = next(row for row in formal_export_specs() if row.theorem_id == "binomial-symmetry")
    wrapped = completion._completion_row(spec)
    direct = evaluate_completion_row(
        spec, completion.check_captured_lean_artifact, completion.FormalExportCompletionRow,
    )
    assert direct == wrapped
    assert type(direct) is completion.FormalExportCompletionRow
    assert type(direct).__module__ == "src.core.formal.completion"
    restored = pickle.loads(pickle.dumps(direct))
    assert restored == direct and type(restored) is completion.FormalExportCompletionRow
    assert find_prep_row(spec.theorem_id).theorem_id == spec.theorem_id
    assert tuple(direct.as_dict()) == (
        "theorem_id", "title", "source_hook", "backend", "proof_path", "lean_symbol",
        "artifact_sha256", "artifact_digest_status", "dependencies", "export_status",
        "lean_status", "formalized", "boundary",
    )
    logger.debug("test_evaluator_matches_completion_wrapper_and_preserves_class_identity exit")


def test_completion_wrapper_forwards_live_monkeypatched_checker(monkeypatch):
    logger.debug("test_completion_wrapper_forwards_live_monkeypatched_checker entry")
    spec = next(row for row in formal_export_specs() if row.theorem_id == "binomial-symmetry")
    calls: list[tuple[int, str]] = []

    def blocking_checker(payload, digest):
        logger.debug("blocking_checker entry bytes=%d digest=%s", len(payload), digest)
        calls.append((len(payload), digest))
        logger.debug("blocking_checker exit status=blocked")
        return "blocked"

    monkeypatch.setattr(completion, "check_captured_lean_artifact", blocking_checker)
    row = completion._completion_row(spec)
    assert calls == [(spec.proof_path.stat().st_size, spec.artifact_sha256)]
    assert row.artifact_digest_status == "matched"
    assert row.lean_status == row.export_status == "blocked"
    assert not row.formalized
    logger.debug("test_completion_wrapper_forwards_live_monkeypatched_checker exit")
