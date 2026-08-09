import json
import shutil
import subprocess
from pathlib import Path

import pytest

from vam.src import encode_vmbc
from vam.src.model import Instruction
from src.core.paths import PROJECT_ROOT


ROOT = PROJECT_ROOT
NATIVE = ROOT / "vam" / "native"


def cargo_bin():
    found = shutil.which("cargo")
    if found:
        return found
    fallback = Path.home() / ".cargo" / "bin" / "cargo"
    if fallback.exists():
        return str(fallback)
    pytest.skip("cargo/rust unavailable")


def run_inspect(path: Path):
    return subprocess.run(
        [cargo_bin(), "run", "--quiet", "--manifest-path", str(NATIVE / "Cargo.toml"), "--", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_vam_native_accepts_python_vam0_oracle(tmp_path):
    program = [
        Instruction("REZ", ("%r1", "phase"), 1),
        Instruction("NOD", ("%r2", "%r1", "0"), 2),
        Instruction("CERT", ("%r3", "claim", "%r2", "native scaffold"), 3),
    ]
    blob = encode_vmbc(program)
    sample = tmp_path / "sample.vam0"
    sample.write_bytes(blob)

    result = run_inspect(sample)
    assert result.returncode == 0, result.stderr + result.stdout
    report = json.loads(result.stdout)
    assert report["ok"] is True
    assert report["profile"] == "vam0-ref-v1"
    assert report["frame"]["magic"] == "VAM0"
    assert report["frame"]["version"] == 1
    assert report["instruction_count"] == 3
    assert report["ops"] == ["REZ", "NOD", "CERT"]
    assert report["instructions"][1]["args"][1] == {"t": "reg", "v": 1}


def test_vam_native_rejects_crc_mismatch(tmp_path):
    blob = bytearray(encode_vmbc([Instruction("REZ", ("%r1", "phase"), 1)]))
    blob[-1] ^= 1
    sample = tmp_path / "bad_crc.vam0"
    sample.write_bytes(blob)

    result = run_inspect(sample)
    assert result.returncode != 0
    report = json.loads(result.stdout)
    assert report["ok"] is False
    assert report["error"]["kind"] == "crc32"


@pytest.mark.parametrize(
    ("mutate", "kind"),
    [
        (lambda b: b.__setitem__(slice(0, 4), b"NOPE"), "magic"),
        (lambda b: b.__setitem__(slice(4, 6), (2).to_bytes(2, "big")), "version"),
        (lambda b: b.__setitem__(slice(6, 10), (999).to_bytes(4, "big")), "length"),
    ],
)
def test_vam_native_rejects_bad_header_fields(tmp_path, mutate, kind):
    blob = bytearray(encode_vmbc([Instruction("REZ", ("%r1", "phase"), 1)]))
    mutate(blob)
    sample = tmp_path / f"bad_{kind}.vam0"
    sample.write_bytes(blob)

    result = run_inspect(sample)
    assert result.returncode != 0
    report = json.loads(result.stdout)
    assert report["ok"] is False
    assert report["error"]["kind"] == kind
