from pathlib import Path

from veyra_sage import all as veyra_api


API_DOC = Path("docs/reference/veyra_sage_api.md")


def _documented_symbols() -> tuple[str, ...]:
    symbols = []
    in_table = False
    for line in API_DOC.read_text().splitlines():
        if line.startswith("| Symbol |"):
            in_table = True
            continue
        if not in_table or line.startswith("|---"):
            continue
        if not line.startswith("| `"):
            if symbols:
                break
            continue
        symbol = line.split("|", 2)[1].strip().strip("`")
        symbols.append(symbol)
    return tuple(symbols)


def test_veyra_sage_api_index_matches_public_all():
    documented = _documented_symbols()
    assert documented == tuple(veyra_api.__all__)
    assert len(documented) == 96


def test_veyra_sage_api_index_records_boundary_and_domains():
    text = API_DOC.read_text()
    assert "docs/69_package_boundary.md" in text
    assert "core-language" in text
    assert "proof-discipline" in text
    assert "native-number-theory" in text
    assert "category-like" in text
    assert "topology-echo" in text
    assert "likelihood-geometry" in text
    assert "refutation-search" in text
    assert "sage_certificate_suite" in text
    assert "VeyraIntrinsicVamLab" in text
    assert "VeyraIntrinsicObserverEchoLab" in text
    assert "VeyraObserverSynthesisV2Lab" in text
    assert "VeyraObserverPatchGluingLab" in text
