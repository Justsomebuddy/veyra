import logging

from scripts.verify_g4_gluing import main

logger = logging.getLogger(__name__)


def test_verifier_reports_progress_and_zero_errors(capsys):
    logger.debug("test_verifier_reports_progress_and_zero_errors entry")
    assert main(["--max-nodes", "2"]) == 0
    output = capsys.readouterr().out
    assert "[1/3]" in output and "[2/3]" in output and "[3/3]" in output
    assert "processed=10/10 remaining=0" in output
    assert "[done] errors=0" in output
    logger.debug("test_verifier_reports_progress_and_zero_errors exit")
