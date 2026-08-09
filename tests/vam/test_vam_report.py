import json

from vam.src.interpreter import execute
from vam.src.assembly import parse_vmasm
from vam.src.report import PROFILE, canonical_report


def _minimal_echo_program():
    return parse_vmasm('''
REZ %r1, "phase"
NOD %r2, %r1, "0"
NOD %r3, %r1, "1"
TACT %r4, %r2, %r3, "step"
BREATH %r5, %r4
MODE %r6, %r5
OBSERVER %r7, "length"
ECHO %r8, %r6, %r6, %r7
CERT %r9, "self-length", %r8, "finite report test"
''')


def test_canonical_report_minimal_echo_contains_expected_sections():
    program = _minimal_echo_program()
    state = execute(program)
    report = canonical_report(program, state)

    assert report["profile"] == PROFILE == "vam0-ref-v1"
    assert report["final_pc"] == len(program)
    assert report["instructions"][0] == {"pc": 0, "line": 2, "op": "REZ", "args": ["%r1", "phase"]}
    assert report["trace"][-1]["kind"] == "Certificate"
    assert report["registers"]["%r8"]["kind"] == "Echo"
    assert report["registers"]["%r8"]["data"]["passed"] is True
    assert report["certs"][0]["data"]["claim"] == "self-length"
    assert report["obstructions"] == []


def test_canonical_report_obstruction_case_records_obstruction_and_rejected_cert():
    program = parse_vmasm('''
REZ %r1, "phase"
BREATH %r2, %r1
CERT %r3, "bad-breath", %r2, "must fail"
''')
    state = execute(program)
    report = canonical_report(program, state)

    assert report["registers"]["%r2"]["kind"] == "Obstruction"
    assert report["registers"]["%r3"]["kind"] == "Certificate"
    assert report["registers"]["%r3"]["data"]["accepted"] is False
    assert report["certs"] == []
    assert report["obstructions"][0]["data"]["claim"] == "breath-requires-tacts"


def test_canonical_report_is_deterministic_for_repeated_execution():
    program = _minimal_echo_program()
    left = canonical_report(program, execute(program))
    right = canonical_report(program, execute(program))

    assert left == right
    assert json.dumps(left, sort_keys=True, separators=(",", ":")) == json.dumps(
        right, sort_keys=True, separators=(",", ":")
    )


def test_canonical_report_is_json_serializable_and_avoids_tuple_outputs():
    program = parse_vmasm('''
REZ %r1, "phase"
NOD %r2, %r1, "a"
NOD %r3, %r1, "b"
TACT %r4, %r2, %r3, "step"
BREATH %r5, %r4
MODE %r6, %r5
OBSERVER %r7, "boundary"
OBSERVE %r8, %r6, %r7
''')
    report = canonical_report(program, execute(program))
    encoded = json.dumps(report, sort_keys=True)
    decoded = json.loads(encoded)

    assert decoded == report
    assert decoded["registers"]["%r8"]["data"]["value"] == ["mode", ["breath", "phase:a", "phase:b"], "native-cycle"]
