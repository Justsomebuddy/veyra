from scripts.verify_adaptive_retry import main, parse_args


def test_parse_args_and_default_oracle(capsys) -> None:
    args = parse_args(["--attempts", "20", "--alpha-numerator", "1", "--alpha-denominator", "20"])
    assert (args.attempts, args.alpha_numerator, args.alpha_denominator) == (20, 1, 20)
    assert main([]) == 0
    output = capsys.readouterr().out
    assert "processed=20/20" in output
    assert "errors=0" in output


def test_invalid_cli_parameters_fail_closed(capsys) -> None:
    assert main(["--attempts", "0"]) == 2
    assert "errors=1" in capsys.readouterr().err
