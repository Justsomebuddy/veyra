"""Hostile static boundaries for the manifest-bound research Lean checker."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import logging
from pathlib import Path
import subprocess

import pytest

import scripts.check_research_lean as checker

logger = logging.getLogger(__name__)


class ProgressProbe:
    """Minimal deterministic progress receiver for scheduler tests."""

    def __init__(self) -> None:
        logger.debug("test_research_lean.ProgressProbe init")
        self.count = 0

    def update(self, amount: int) -> None:
        logger.debug("test_research_lean.ProgressProbe update amount=%d", amount)
        self.count += amount


def _raw_manifest() -> dict[str, object]:
    """Return a fresh mutable copy of the canonical manifest JSON."""
    logger.debug("test_research_lean._raw_manifest entry")
    result = json.loads(checker.MANIFEST_PATH.read_text(encoding="utf-8"))
    logger.debug("test_research_lean._raw_manifest exit keys=%d", len(result))
    return result


def _write_manifest(path: Path, payload: dict[str, object]) -> Path:
    """Write one bounded JSON mutation fixture."""
    logger.debug("test_research_lean._write_manifest entry path=%s", path)
    path.write_text(json.dumps(payload), encoding="utf-8")
    logger.debug("test_research_lean._write_manifest exit bytes=%d", path.stat().st_size)
    return path


def _minimal_manifest(record: checker.SourceRecord) -> checker.ResearchManifest:
    """Build a one-record manifest for isolated helper tests."""
    logger.debug("test_research_lean._minimal_manifest entry path=%s", record.path)
    result = checker.ResearchManifest(
        toolchain="leanprover/lean4:v4.30.0-rc2",
        version="4.30.0-rc2",
        commit="3dc1a088b6d2d8eafe25a7cd7ec7b58d731bd7cc",
        base=(),
        research=(record,),
        headlines=record.declarations,
        headline_claims=tuple(
            (name, ": True", "test scope", "test registry boundary")
            for name in record.declarations
        ),
        axiom_closure=tuple((name, ()) for name in record.declarations),
        source_roots=(),
        proof_root="",
    )
    logger.debug("test_research_lean._minimal_manifest exit")
    return result


def test_canonical_manifest_binds_exact_inventory_and_toolchain() -> None:
    """The checked candidate has one exact 53+8/65 identity."""
    logger.debug("test_research_lean canonical manifest entry")
    manifest = checker.load_manifest()
    assert len(manifest.base) == 53
    assert len(manifest.research) == 8
    assert len(manifest.declarations) == 65
    assert len(manifest.headlines) == 33
    assert len(manifest.headline_claims) == 33
    assert len(manifest.axiom_closure) == 65
    assert manifest.version == "4.30.0-rc2"
    assert manifest.commit == "3dc1a088b6d2d8eafe25a7cd7ec7b58d731bd7cc"
    assert "RESEARCH_T008_cross_product_reassociation" in manifest.declarations
    assert "RESEARCH_T008_independence_counts" not in manifest.declarations
    assert manifest.source_roots == checker.calculate_source_roots(manifest)
    assert manifest.proof_root == checker.calculate_proof_root(manifest)
    logger.debug("test_research_lean canonical manifest exit")


def test_canonical_inventory_and_import_graph_replay_without_lean() -> None:
    """Exact bytes, digests, imports, symbols, and the local DAG replay statically."""
    logger.debug("test_research_lean inventory replay entry")
    manifest = checker.load_manifest()
    payloads = checker.verify_inventory(manifest)
    graph = checker.local_graph(manifest)
    layers = checker.graph_layers(graph)
    flattened = tuple(path for layer in layers for path in layer)
    assert len(payloads) == 61
    assert set(flattened) == {row.path for row in manifest.records}
    positions = {path: index for index, path in enumerate(flattened)}
    assert all(
        positions[dependency] < positions[source]
        for source, dependencies in graph.items()
        for dependency in dependencies
    )
    logger.debug("test_research_lean inventory replay exit layers=%d", len(layers))


@pytest.mark.parametrize(
    "token",
    [
        "sorryAx", "sorry", "admit", "axiom", "postulate", "constant",
        "opaque", "unsafe", "extern", "implemented_by", "run_tac", "elab",
        "macro", "syntax", "addDecl", "axiomDecl",
    ],
)
def test_token_aware_preflight_rejects_forbidden_project_code(token: str) -> None:
    """Forbidden declarations/escapes are rejected after lexical stripping."""
    logger.debug("test_research_lean forbidden token entry token=%s", token)
    payload = f"theorem safe : True := by trivial\n{token} injected : True\n".encode()
    with pytest.raises(ValueError, match=f"research-lean-forbidden:{token}"):
        checker.parse_source(payload)
    logger.debug("test_research_lean forbidden token exit token=%s", token)


def test_token_aware_preflight_ignores_nested_comments_and_strings() -> None:
    """Policy words in prose cannot create false project declarations."""
    logger.debug("test_research_lean lexical prose entry")
    payload = b'''/- no axiom; /- sorry -/ still prose -/
def note : String := "unsafe axiom admit sorryAx"
theorem SAFE_T001 : True := by trivial
'''
    imports, declarations = checker.parse_source(payload)
    assert imports == ()
    assert declarations == ("SAFE_T001",)
    logger.debug("test_research_lean lexical prose exit")


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("missing-source", "research-manifest-source-count"),
        ("wrong-count", "research-manifest-declaration-count"),
        ("missing-axiom", "research-manifest-axioms"),
        ("duplicate-symbol", "research-manifest-declarations"),
        ("bad-toolchain-commit", "research-manifest-toolchain-commit"),
    ],
)
def test_manifest_rejects_hostile_inventory_mutations(
    tmp_path: Path,
    mutation: str,
    reason: str,
) -> None:
    """No missing source/symbol/closure or malformed toolchain row is accepted."""
    logger.debug("test_research_lean hostile manifest entry mutation=%s", mutation)
    raw = _raw_manifest()
    research = raw["research_sources"]
    assert type(research) is list
    if mutation == "missing-source":
        research.pop()
    elif mutation == "wrong-count":
        raw["declaration_count"] = 64
    elif mutation == "missing-axiom":
        closure = raw["axiom_closure"]
        assert type(closure) is dict
        closure.pop(next(iter(closure)))
    elif mutation == "duplicate-symbol":
        first = research[0]
        assert type(first) is dict and type(first["declarations"]) is list
        first["declarations"][1] = first["declarations"][0]
    else:
        toolchain = raw["toolchain"]
        assert type(toolchain) is dict
        toolchain["commit"] = "not-a-commit"
    with pytest.raises(ValueError, match=reason):
        checker.load_manifest(_write_manifest(tmp_path / "manifest.json", raw))
    logger.debug("test_research_lean hostile manifest exit mutation=%s", mutation)


def test_manifest_rejects_base_research_stem_collision(tmp_path: Path) -> None:
    """A research file cannot shadow a compiled base module by import stem."""
    logger.debug("test_research_lean stem collision entry")
    raw = _raw_manifest()
    base = raw["base_sources"]
    research = raw["research_sources"]
    assert type(base) is list and type(research) is list
    assert type(base[0]) is dict and type(research[0]) is dict
    colliding = Path(base[0]["path"]).name
    research[0]["path"] = f"experimental/research_lean/{colliding}"
    with pytest.raises(ValueError, match="research-manifest-source-collision"):
        checker.load_manifest(_write_manifest(tmp_path / "manifest.json", raw))
    logger.debug("test_research_lean stem collision exit")


def test_manifest_rejects_reduced_headline_ledger(tmp_path: Path) -> None:
    """The canonical 33-headline set cannot be reduced and self-reblessed."""
    logger.debug("test_research_lean reduced headline entry")
    raw = _raw_manifest()
    headlines = raw["headline_declarations"]
    claims = raw["headline_claims"]
    assert type(headlines) is list and type(claims) is dict
    claims.pop(headlines.pop())
    with pytest.raises(ValueError, match="research-manifest-headlines"):
        checker.load_manifest(_write_manifest(tmp_path / "manifest.json", raw))
    logger.debug("test_research_lean reduced headline exit")


def test_graph_rejects_cycles_and_unknown_dependencies() -> None:
    """The scheduler cannot treat blocked local imports as ready."""
    logger.debug("test_research_lean invalid graph entry")
    with pytest.raises(ValueError, match="research-lean-import-cycle"):
        checker.graph_layers({"a": ("b",), "b": ("a",)})
    with pytest.raises(ValueError, match="research-lean-import-unknown"):
        checker.graph_layers({"a": ("missing",)})
    logger.debug("test_research_lean invalid graph exit")


def test_import_policy_rejects_unreviewed_external_and_base_to_research() -> None:
    """Only pinned Lean/Std imports are external and stable sources stay one-way."""
    logger.debug("test_research_lean import policy entry")
    base = checker.SourceRecord(
        "base", "proofs/lean/Base.lean", "0" * 64, ("Research",), (),
    )
    research = checker.SourceRecord(
        "research", "experimental/research_lean/Research.lean", "1" * 64,
        ("ThirdParty.Unreviewed",), ("T",),
    )
    manifest = checker.ResearchManifest(
        "toolchain", "version", "0" * 40, (base,), (research,), ("T",),
        (("T", ": True", "scope", "boundary"),), (("T", ()),), (), "",
    )
    with pytest.raises(ValueError, match="research-lean-import-not-allowed"):
        checker.local_graph(replace(manifest, base=()))
    with pytest.raises(ValueError, match="research-lean-base-imports-research"):
        checker.local_graph(replace(manifest, research=(replace(research, imports=()),)))
    logger.debug("test_research_lean import policy exit")


def test_fresh_snapshot_uses_verified_bytes_not_later_original(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Compilation input is a private byte snapshot and rehash detects later drift."""
    logger.debug("test_research_lean fresh snapshot entry")
    relative = "experimental/research_lean/One.lean"
    original = tmp_path / relative
    original.parent.mkdir(parents=True)
    payload = b"theorem ONE : True := by trivial\n"
    original.write_bytes(payload)
    record = checker.SourceRecord(
        "research", relative, hashlib.sha256(payload).hexdigest(), (), ("ONE",),
    )
    manifest = _minimal_manifest(record)
    snapshot_root = tmp_path / "snapshot"
    snapshots = checker.snapshot_sources(
        manifest, {relative: payload}, snapshot_root,
    )
    original.write_text("theorem CHANGED : True := by trivial\n", encoding="utf-8")
    assert snapshots[relative].read_bytes() == payload
    monkeypatch.setattr(checker, "ROOT", tmp_path)
    monkeypatch.setattr(checker, "BASE_ROOT", tmp_path / "proofs/lean")
    monkeypatch.setattr(checker, "RESEARCH_ROOT", tmp_path / "experimental/research_lean")
    with pytest.raises(RuntimeError, match="research-lean-source-toctou"):
        checker.verify_original_rehash(manifest)
    logger.debug("test_research_lean fresh snapshot exit")


def test_failed_layer_prevents_dependent_compilation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed prerequisite leaves later layers explicitly skipped."""
    logger.debug("test_research_lean failed layer entry")
    calls: list[str] = []

    def fake_compile(
        _command: list[str], logical_path: str, _source: Path,
        _output: Path, _environment: dict[str, str],
    ) -> checker.CompileResult:
        logger.debug("test_research_lean fake compile entry path=%s", logical_path)
        calls.append(logical_path)
        result = checker.CompileResult(logical_path, 1, "expected failure", 0.01)
        logger.debug("test_research_lean fake compile exit path=%s", logical_path)
        return result

    monkeypatch.setattr(checker, "compile_one", fake_compile)
    progress = ProgressProbe()
    passed, failed, skipped = checker.compile_layers(
        ["lean"], (("parent",), ("child",)),
        {"parent": tmp_path / "parent.lean", "child": tmp_path / "child.lean"},
        tmp_path, {}, 1, progress,
    )
    assert (passed, failed, skipped) == (0, 1, 1)
    assert calls == ["parent"]
    assert progress.count == 1
    logger.debug("test_research_lean failed layer exit")


def test_timeout_is_failure_and_dependents_remain_skipped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Compiler timeout is normalized as failure, never unavailable success."""
    logger.debug("test_research_lean timeout entry")

    def timed_out(
        _command: list[str], logical_path: str, _source: Path,
        _output: Path, _environment: dict[str, str],
    ) -> checker.CompileResult:
        logger.debug("test_research_lean timed_out entry path=%s", logical_path)
        logger.error("test_research_lean timed_out expected timeout path=%s", logical_path)
        raise subprocess.TimeoutExpired(["lean"], 1)

    monkeypatch.setattr(checker, "compile_one", timed_out)
    progress = ProgressProbe()
    result = checker.compile_layers(
        ["lean"], (("parent",), ("child",)),
        {"parent": tmp_path / "parent.lean", "child": tmp_path / "child.lean"},
        tmp_path, {}, 1, progress,
    )
    assert result == (0, 1, 1)
    assert progress.count == 1
    logger.debug("test_research_lean timeout exit")


def test_compiler_success_without_nonempty_object_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A zero compiler status cannot substitute for the promised fresh object."""
    logger.debug("test_research_lean missing object entry")
    source = tmp_path / "One.lean"
    source.write_text("theorem ONE : True := by trivial\n", encoding="utf-8")
    monkeypatch.setattr(
        checker.subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "", ""),
    )
    result = checker.compile_one(["lean"], "One.lean", source, tmp_path, {})
    assert result.returncode == 1
    assert "without a nonempty regular .olean" in result.output
    logger.debug("test_research_lean missing object exit")


def test_generated_audit_covers_every_declaration_exactly() -> None:
    """Every bound declaration receives one check and one axiom query."""
    logger.debug("test_research_lean generated audit entry")
    manifest = checker.load_manifest()
    source = checker.audit_source(manifest)
    for name in manifest.declarations:
        assert source.count(f"#check Veyra.{name}\n") == 1
        assert source.count(f"#print axioms Veyra.{name}\n") == 1
    assert source.count("#check Veyra.") == 65
    assert source.count("#print axioms Veyra.") == 65
    logger.debug("test_research_lean generated audit exit")


def test_axiom_parser_rejects_omissions_and_replays_exact_rows() -> None:
    """Missing check/closure output cannot masquerade as an empty dependency row."""
    logger.debug("test_research_lean axiom parser entry")
    output = "\n".join(
        (
            "Veyra.FIRST : True",
            "'Veyra.FIRST' does not depend on any axioms",
            "Veyra.SECOND (n : Nat) : True",
            "'Veyra.SECOND' depends on axioms: [propext, Quot.sound]",
        )
    )
    assert checker.parse_axiom_audit(output, ("FIRST", "SECOND")) == (
        ("FIRST", ()), ("SECOND", ("propext", "Quot.sound")),
    )
    with pytest.raises(ValueError, match="research-lean-axiom-audit-incomplete"):
        checker.parse_axiom_audit(output.splitlines()[0], ("FIRST",))
    with pytest.raises(ValueError, match="research-lean-axiom-audit-incomplete"):
        checker.parse_axiom_audit(output + "\n" + output, ("FIRST", "SECOND"))
    logger.debug("test_research_lean axiom parser exit")


def test_stale_persistent_object_cannot_mask_source_digest_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: the reproduced name-only stale-olean attack fails preflight."""
    logger.debug("test_research_lean stale object regression entry")
    base_root = tmp_path / "proofs/lean"
    research_root = tmp_path / "experimental/research_lean"
    base_root.mkdir(parents=True)
    research_root.mkdir(parents=True)
    valid = b"theorem ONE : True := by trivial\n"
    source = research_root / "One.lean"
    source.write_bytes(b"theorem ONE : True := by invalid_tactic\n")
    stale = tmp_path / "data/tmp/research-olean/One.olean"
    stale.parent.mkdir(parents=True)
    stale.write_bytes(b"previously accepted object")
    record = checker.SourceRecord(
        "research",
        "experimental/research_lean/One.lean",
        hashlib.sha256(valid).hexdigest(),
        (),
        ("ONE",),
    )
    monkeypatch.setattr(checker, "ROOT", tmp_path)
    monkeypatch.setattr(checker, "BASE_ROOT", base_root)
    monkeypatch.setattr(checker, "RESEARCH_ROOT", research_root)
    with pytest.raises(ValueError, match="research-lean-source-drift"):
        checker.verify_inventory(_minimal_manifest(record))
    assert stale.read_bytes() == b"previously accepted object"
    logger.debug("test_research_lean stale object regression exit")


def test_toolchain_identity_requires_exact_version_and_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A matching version label cannot hide compiler-commit drift."""
    logger.debug("test_research_lean toolchain identity entry")
    manifest = checker.load_manifest()

    def found_elan(name: str) -> str:
        logger.debug("test_research_lean found_elan entry name=%s", name)
        logger.debug("test_research_lean found_elan exit")
        return "/elan"

    monkeypatch.setattr(checker.shutil, "which", found_elan)

    def completed(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        logger.debug("test_research_lean completed entry command=%r", command)
        result = subprocess.CompletedProcess(
            command,
            0,
            "Lean (version 4.30.0-rc2, test, commit " + "0" * 40 + ", Release)\n",
            "",
        )
        logger.debug("test_research_lean completed exit")
        return result

    monkeypatch.setattr(checker.subprocess, "run", completed)
    with pytest.raises(RuntimeError, match="research-lean-toolchain-mismatch"):
        checker.lean_command(manifest)
    logger.debug("test_research_lean toolchain identity exit")


def test_toolchain_identity_rejects_root_pin_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The root Elan pin and manifest cannot select different compilers."""
    logger.debug("test_research_lean root toolchain drift entry")
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.29.0\n")
    monkeypatch.setattr(checker, "ROOT", tmp_path)
    with pytest.raises(RuntimeError, match="research-lean-root-toolchain-mismatch"):
        checker.lean_command(checker.load_manifest())
    logger.debug("test_research_lean root toolchain drift exit")


def test_final_rehash_rejects_late_extra_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A late extra Lean path cannot escape the final inventory boundary."""
    logger.debug("test_research_lean late inventory drift entry")
    research_root = tmp_path / "experimental/research_lean"
    base_root = tmp_path / "proofs/lean"
    research_root.mkdir(parents=True)
    base_root.mkdir(parents=True)
    payload = b"theorem ONE : True := by trivial\n"
    source = research_root / "One.lean"
    source.write_bytes(payload)
    record = checker.SourceRecord(
        "research", "experimental/research_lean/One.lean",
        hashlib.sha256(payload).hexdigest(), (), ("ONE",),
    )
    monkeypatch.setattr(checker, "ROOT", tmp_path)
    monkeypatch.setattr(checker, "BASE_ROOT", base_root)
    monkeypatch.setattr(checker, "RESEARCH_ROOT", research_root)
    (research_root / "Late.lean").write_bytes(b"axiom LATE : True\n")
    with pytest.raises(RuntimeError, match="research-lean-source-toctou"):
        checker.verify_original_rehash(_minimal_manifest(record))
    logger.debug("test_research_lean late inventory drift exit")


def test_checker_has_no_persistent_correctness_cache() -> None:
    """Only a fresh TemporaryDirectory may hold snapshots and object files."""
    logger.debug("test_research_lean no persistent cache entry")
    source = Path(checker.__file__).read_text(encoding="utf-8")
    assert "TemporaryDirectory" in source
    assert "research-olean" not in source
    assert "OLEAN_ROOT" not in source
    logger.debug("test_research_lean no persistent cache exit")
