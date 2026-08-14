#!/usr/bin/env python3
"""Freshly compile and audit the manifest-bound experimental Lean sources."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any

from tqdm import tqdm

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
BASE_ROOT = ROOT / "proofs" / "lean"
RESEARCH_ROOT = ROOT / "experimental" / "research_lean"
MANIFEST_PATH = RESEARCH_ROOT / "manifest.json"
TMP_ROOT = ROOT / "data" / "tmp"
EXPECTED_SCHEMA = "veyra.research-lean-manifest.v1"
EXPECTED_STATUS = "INTERNAL_RESEARCH_CANDIDATE"
EXPECTED_BASE_COUNT = 48
EXPECTED_RESEARCH_COUNT = 8
EXPECTED_DECLARATION_COUNT = 65
EXPECTED_HEADLINE_COUNT = 33
MAX_JOBS = 16
MAX_SOURCE_BYTES = 1_000_000
MAX_MANIFEST_BYTES = 512_000
MAX_DIAGNOSTIC_BYTES = 65_536
COMPILE_TIMEOUT_SECONDS = 600
TOOLCHAIN_TIMEOUT_SECONDS = 30
IMPORT_PATTERN = re.compile(r"(?m)^\s*import\s+(.+?)\s*$")
DECLARATION_PATTERN = re.compile(
    r"(?m)^\s*(theorem|lemma)\s+([A-Za-z_][A-Za-z0-9_']*)\b"
)
FORBIDDEN_PATTERN = re.compile(
    r"\b(?:sorryAx|sorry|admit|axiom|postulate|constant|opaque|unsafe|extern|"
    r"implemented_by|run_tac|elab|macro|syntax|addDecl|axiomDecl)\b"
)
HEADLINE_NAME_PATTERN = re.compile(r"^RESEARCH_(?:[A-Z]+_)?T[0-9]{3}_")
HEADLINE_STATEMENT_PATTERN = re.compile(
    r"(?ms)^\s*(?:theorem|lemma)\s+([A-Za-z_][A-Za-z0-9_']*)\b(.*?)\s*:="
)
ALLOWED_EXTERNAL_IMPORT_ROOTS = frozenset({"Init", "Lean", "Std"})
VERSION_PATTERN = re.compile(
    r"^Lean \(version ([^,]+), [^,]+, commit ([0-9a-f]{40}), Release\)$"
)
AXIOM_ROW_PATTERN = re.compile(
    r"'Veyra\.([A-Za-z_][A-Za-z0-9_']*)' depends on axioms: \[([^\]]*)\]"
)
NO_AXIOM_ROW_PATTERN = re.compile(
    r"'Veyra\.([A-Za-z_][A-Za-z0-9_']*)' does not depend on any axioms"
)
CHECK_ROW_PATTERN = re.compile(
    r"(?m)^Veyra\.([A-Za-z_][A-Za-z0-9_']*)\s+.*?:"
)


@dataclass(frozen=True)
class SourceRecord:
    """One exact source row from the canonical manifest."""

    group: str
    path: str
    sha256: str
    imports: tuple[str, ...]
    declarations: tuple[str, ...]

    @property
    def stem(self) -> str:
        """Return the import stem bound by this source path."""
        logger.debug("research_lean.SourceRecord.stem entry path=%s", self.path)
        result = Path(self.path).stem
        logger.debug("research_lean.SourceRecord.stem exit stem=%s", result)
        return result


@dataclass(frozen=True)
class ResearchManifest:
    """Closed checker contract loaded from ``manifest.json``."""

    toolchain: str
    version: str
    commit: str
    base: tuple[SourceRecord, ...]
    research: tuple[SourceRecord, ...]
    headlines: tuple[str, ...]
    headline_claims: tuple[tuple[str, str, str, str], ...]
    axiom_closure: tuple[tuple[str, tuple[str, ...]], ...]
    source_roots: tuple[tuple[str, str], ...]
    proof_root: str
    manifest_sha256: str = ""

    @property
    def records(self) -> tuple[SourceRecord, ...]:
        """Return base then research rows in their canonical manifest order."""
        logger.debug("research_lean.ResearchManifest.records entry")
        result = (*self.base, *self.research)
        logger.debug("research_lean.ResearchManifest.records exit count=%d", len(result))
        return result

    @property
    def declarations(self) -> tuple[str, ...]:
        """Return the exact ordered research declaration inventory."""
        logger.debug("research_lean.ResearchManifest.declarations entry")
        result = tuple(name for row in self.research for name in row.declarations)
        logger.debug("research_lean.ResearchManifest.declarations exit count=%d", len(result))
        return result


@dataclass(frozen=True)
class CompileResult:
    """Bounded result for one Lean compiler invocation."""

    source: str
    returncode: int
    output: str
    elapsed: float


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse bounded checker arguments."""
    logger.debug("research_lean.parse_args entry argc=%d", len(argv))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, default=min(8, os.cpu_count() or 1))
    result = parser.parse_args(argv)
    if not 1 <= result.jobs <= MAX_JOBS:
        logger.error("research_lean.parse_args invalid jobs=%d", result.jobs)
        raise ValueError(f"jobs-must-be-1-through-{MAX_JOBS}")
    logger.debug("research_lean.parse_args exit jobs=%d", result.jobs)
    return result


def _exact_dict(value: object, reason: str) -> dict[str, Any]:
    """Require an exact JSON object before nested access."""
    logger.debug("research_lean._exact_dict entry reason=%s", reason)
    if type(value) is not dict:
        logger.error("research_lean._exact_dict invalid reason=%s", reason)
        raise ValueError(reason)
    logger.debug("research_lean._exact_dict exit keys=%d", len(value))
    return value


def _exact_list(value: object, reason: str) -> list[Any]:
    """Require an exact JSON array before nested access."""
    logger.debug("research_lean._exact_list entry reason=%s", reason)
    if type(value) is not list:
        logger.error("research_lean._exact_list invalid reason=%s", reason)
        raise ValueError(reason)
    logger.debug("research_lean._exact_list exit items=%d", len(value))
    return value


def _exact_text(value: object, reason: str, maximum: int = 256) -> str:
    """Require one bounded nonempty text scalar."""
    logger.debug("research_lean._exact_text entry reason=%s", reason)
    if type(value) is not str or not value or len(value) > maximum:
        logger.error("research_lean._exact_text invalid reason=%s", reason)
        raise ValueError(reason)
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        logger.error("research_lean._exact_text unicode reason=%s", reason)
        raise ValueError(reason) from exc
    logger.debug("research_lean._exact_text exit length=%d", len(value))
    return value


def _exact_string_tuple(value: object, reason: str) -> tuple[str, ...]:
    """Require a bounded duplicate-free list of bounded strings."""
    logger.debug("research_lean._exact_string_tuple entry reason=%s", reason)
    rows = _exact_list(value, reason)
    if len(rows) > EXPECTED_DECLARATION_COUNT:
        logger.error("research_lean._exact_string_tuple oversized reason=%s", reason)
        raise ValueError(reason)
    result = tuple(_exact_text(row, reason) for row in rows)
    if len(result) != len(set(result)):
        logger.error("research_lean._exact_string_tuple duplicate reason=%s", reason)
        raise ValueError(reason)
    logger.debug("research_lean._exact_string_tuple exit count=%d", len(result))
    return result


def _source_record(value: object, group: str) -> SourceRecord:
    """Validate and construct one manifest source record."""
    logger.debug("research_lean._source_record entry group=%s", group)
    row = _exact_dict(value, "research-manifest-source-row")
    expected_keys = {"path", "sha256", "imports", "declarations"}
    if set(row) != expected_keys:
        logger.error("research_lean._source_record keys mismatch group=%s", group)
        raise ValueError("research-manifest-source-row")
    path = _exact_text(row["path"], "research-manifest-source-path", 512)
    pure = Path(path)
    expected_parent = "proofs/lean" if group == "base" else "experimental/research_lean"
    if (
        pure.is_absolute()
        or pure.as_posix() != path
        or ".." in pure.parts
        or pure.parent.as_posix() != expected_parent
        or pure.suffix != ".lean"
    ):
        logger.error("research_lean._source_record path invalid path=%r", path)
        raise ValueError("research-manifest-source-path")
    sha256 = _exact_text(row["sha256"], "research-manifest-source-digest", 64)
    if not re.fullmatch(r"[0-9a-f]{64}", sha256):
        logger.error("research_lean._source_record digest invalid path=%s", path)
        raise ValueError("research-manifest-source-digest")
    imports = _exact_string_tuple(row["imports"], "research-manifest-imports")
    declarations = _exact_string_tuple(
        row["declarations"], "research-manifest-declarations"
    )
    if group == "base" and declarations:
        logger.error("research_lean._source_record base declarations must be omitted")
        raise ValueError("research-manifest-base-declarations")
    result = SourceRecord(group, path, sha256, imports, declarations)
    logger.debug("research_lean._source_record exit path=%s", path)
    return result


def load_manifest(path: Path = MANIFEST_PATH) -> ResearchManifest:
    """Load the bounded canonical research manifest without trusting nesting."""
    logger.debug("research_lean.load_manifest entry path=%s", path)
    if path.is_symlink() or not path.is_file():
        logger.error("research_lean.load_manifest missing or symlink path=%s", path)
        raise ValueError("research-manifest-path")
    payload = path.read_bytes()
    if not payload or len(payload) > MAX_MANIFEST_BYTES:
        logger.error("research_lean.load_manifest invalid size=%d", len(payload))
        raise ValueError("research-manifest-size")
    try:
        raw = json.loads(payload.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        logger.error("research_lean.load_manifest decode failed error=%s", exc)
        raise ValueError("research-manifest-json") from exc
    root = _exact_dict(raw, "research-manifest-root")
    expected_keys = {
        "schema", "status", "toolchain", "base_sources", "research_sources",
        "declaration_count", "headline_declarations", "headline_claims",
        "axiom_closure", "source_roots", "proof_root",
    }
    if set(root) != expected_keys:
        logger.error("research_lean.load_manifest root keys mismatch")
        raise ValueError("research-manifest-root")
    if root["schema"] != EXPECTED_SCHEMA or root["status"] != EXPECTED_STATUS:
        logger.error("research_lean.load_manifest schema/status mismatch")
        raise ValueError("research-manifest-identity")
    toolchain = _exact_dict(root["toolchain"], "research-manifest-toolchain")
    if set(toolchain) != {"name", "version", "commit"}:
        logger.error("research_lean.load_manifest toolchain keys mismatch")
        raise ValueError("research-manifest-toolchain")
    base_rows = _exact_list(root["base_sources"], "research-manifest-base")
    research_rows = _exact_list(
        root["research_sources"], "research-manifest-research"
    )
    if len(base_rows) != EXPECTED_BASE_COUNT or len(research_rows) != EXPECTED_RESEARCH_COUNT:
        logger.error(
            "research_lean.load_manifest source count mismatch base=%d research=%d",
            len(base_rows), len(research_rows),
        )
        raise ValueError("research-manifest-source-count")
    base = tuple(_source_record(row, "base") for row in base_rows)
    research = tuple(_source_record(row, "research") for row in research_rows)
    declarations = tuple(name for row in research for name in row.declarations)
    if (
        type(root["declaration_count"]) is not int
        or root["declaration_count"] != EXPECTED_DECLARATION_COUNT
        or len(declarations) != EXPECTED_DECLARATION_COUNT
        or len(set(declarations)) != EXPECTED_DECLARATION_COUNT
    ):
        logger.error("research_lean.load_manifest declaration inventory mismatch")
        raise ValueError("research-manifest-declaration-count")
    headlines = _exact_string_tuple(
        root["headline_declarations"], "research-manifest-headlines"
    )
    expected_headlines = tuple(
        name for name in declarations if HEADLINE_NAME_PATTERN.match(name)
    )
    if len(headlines) != EXPECTED_HEADLINE_COUNT or headlines != expected_headlines:
        logger.error("research_lean.load_manifest headline mismatch")
        raise ValueError("research-manifest-headlines")
    claims_raw = _exact_dict(root["headline_claims"], "research-manifest-claims")
    if set(claims_raw) != set(headlines):
        logger.error("research_lean.load_manifest claim row mismatch")
        raise ValueError("research-manifest-claims")
    headline_claims: list[tuple[str, str, str, str]] = []
    for name in headlines:
        claim = _exact_dict(claims_raw[name], "research-manifest-claim-row")
        if set(claim) != {"statement", "scope", "registry_relation"}:
            logger.error("research_lean.load_manifest claim keys mismatch name=%s", name)
            raise ValueError("research-manifest-claim-row")
        headline_claims.append(
            (
                name,
                _exact_text(claim["statement"], "research-manifest-claim-statement", 4096),
                _exact_text(claim["scope"], "research-manifest-claim-scope", 512),
                _exact_text(
                    claim["registry_relation"],
                    "research-manifest-claim-registry",
                    512,
                ),
            )
        )
    closure_raw = _exact_dict(root["axiom_closure"], "research-manifest-axioms")
    if set(closure_raw) != set(declarations):
        logger.error("research_lean.load_manifest axiom row mismatch")
        raise ValueError("research-manifest-axioms")
    closure = tuple(
        (
            declaration,
            _exact_string_tuple(
                closure_raw[declaration], "research-manifest-axiom-row"
            ),
        )
        for declaration in declarations
    )
    roots_raw = _exact_dict(root["source_roots"], "research-manifest-source-roots")
    if set(roots_raw) != {"base", "research"}:
        logger.error("research_lean.load_manifest source root keys mismatch")
        raise ValueError("research-manifest-source-roots")
    source_roots = tuple(
        (group, _exact_text(roots_raw[group], "research-manifest-source-root", 64))
        for group in ("base", "research")
    )
    proof_root = _exact_text(root["proof_root"], "research-manifest-proof-root", 64)
    if any(not re.fullmatch(r"[0-9a-f]{64}", digest) for _, digest in source_roots) or not re.fullmatch(
        r"[0-9a-f]{64}", proof_root
    ):
        logger.error("research_lean.load_manifest malformed aggregate root")
        raise ValueError("research-manifest-aggregate-root")
    paths = tuple(row.path for row in (*base, *research))
    stems = tuple(row.stem for row in (*base, *research))
    if len(paths) != len(set(paths)) or len(stems) != len(set(stems)):
        logger.error("research_lean.load_manifest duplicate path/stem")
        raise ValueError("research-manifest-source-collision")
    result = ResearchManifest(
        _exact_text(toolchain["name"], "research-manifest-toolchain-name"),
        _exact_text(toolchain["version"], "research-manifest-toolchain-version"),
        _exact_text(toolchain["commit"], "research-manifest-toolchain-commit"),
        base,
        research,
        headlines,
        tuple(headline_claims),
        closure,
        source_roots,
        proof_root,
        sha256_bytes(payload),
    )
    if not re.fullmatch(r"[0-9a-f]{40}", result.commit):
        logger.error("research_lean.load_manifest invalid toolchain commit")
        raise ValueError("research-manifest-toolchain-commit")
    if result.source_roots != calculate_source_roots(result):
        logger.error("research_lean.load_manifest aggregate source root mismatch")
        raise ValueError("research-manifest-source-root-drift")
    if result.proof_root != calculate_proof_root(result):
        logger.error("research_lean.load_manifest proof root mismatch")
        raise ValueError("research-manifest-proof-root-drift")
    logger.debug("research_lean.load_manifest exit records=%d", len(result.records))
    return result


def strip_lean_noncode(source: str) -> str:
    """Replace nested comments and strings while preserving line boundaries."""
    logger.debug("research_lean.strip_lean_noncode entry chars=%d", len(source))
    output: list[str] = []
    index = 0
    block_depth = 0
    in_string = False
    escaped = False
    while index < len(source):
        current = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if block_depth:
            if current == "/" and following == "-":
                block_depth += 1
                output.extend((" ", " "))
                index += 2
            elif current == "-" and following == "/":
                block_depth -= 1
                output.extend((" ", " "))
                index += 2
            else:
                output.append("\n" if current == "\n" else " ")
                index += 1
            continue
        if in_string:
            output.append("\n" if current == "\n" else " ")
            if escaped:
                escaped = False
            elif current == "\\":
                escaped = True
            elif current == '"':
                in_string = False
            index += 1
            continue
        if current == "-" and following == "-":
            while index < len(source) and source[index] != "\n":
                output.append(" ")
                index += 1
            continue
        if current == "/" and following == "-":
            block_depth = 1
            output.extend((" ", " "))
            index += 2
            continue
        if current == '"':
            in_string = True
            output.append(" ")
            index += 1
            continue
        output.append(current)
        index += 1
    if block_depth or in_string:
        logger.error(
            "research_lean.strip_lean_noncode unterminated block=%d string=%s",
            block_depth, in_string,
        )
        raise ValueError("research-lean-unterminated-lexeme")
    result = "".join(output)
    logger.debug("research_lean.strip_lean_noncode exit chars=%d", len(result))
    return result


def parse_source(payload: bytes) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Parse exact imports/declarations and reject forbidden project code."""
    logger.debug("research_lean.parse_source entry bytes=%d", len(payload))
    if not payload or len(payload) > MAX_SOURCE_BYTES:
        logger.error("research_lean.parse_source invalid size=%d", len(payload))
        raise ValueError("research-lean-source-size")
    try:
        source = payload.decode("utf-8")
    except UnicodeError as exc:
        logger.error("research_lean.parse_source invalid unicode")
        raise ValueError("research-lean-source-unicode") from exc
    code = strip_lean_noncode(source)
    forbidden = FORBIDDEN_PATTERN.search(code)
    if forbidden:
        logger.error("research_lean.parse_source forbidden token=%s", forbidden.group(0))
        raise ValueError(f"research-lean-forbidden:{forbidden.group(0)}")
    imports = tuple(
        name
        for row in IMPORT_PATTERN.findall(code)
        for name in row.split()
    )
    declarations = tuple(match[1] for match in DECLARATION_PATTERN.findall(code))
    if len(imports) != len(set(imports)) or len(declarations) != len(set(declarations)):
        logger.error("research_lean.parse_source duplicate import/declaration")
        raise ValueError("research-lean-source-duplicate")
    logger.debug("research_lean.parse_source exit imports=%d declarations=%d", len(imports), len(declarations))
    return imports, declarations


def headline_statements(payload: bytes) -> dict[str, str]:
    """Return normalized literal signatures for theorem/lemma declarations."""
    logger.debug("research_lean.headline_statements entry bytes=%d", len(payload))
    try:
        code = strip_lean_noncode(payload.decode("utf-8"))
    except UnicodeError as exc:
        logger.error("research_lean.headline_statements invalid unicode")
        raise ValueError("research-lean-source-unicode") from exc
    result = {
        name: " ".join(signature.split())
        for name, signature in HEADLINE_STATEMENT_PATTERN.findall(code)
    }
    logger.debug("research_lean.headline_statements exit count=%d", len(result))
    return result


def sha256_bytes(payload: bytes) -> str:
    """Return one lowercase SHA-256 digest."""
    logger.debug("research_lean.sha256_bytes entry bytes=%d", len(payload))
    result = hashlib.sha256(payload).hexdigest()
    logger.debug("research_lean.sha256_bytes exit digest=%s", result[:12])
    return result


def _domain_root(domain: str, rows: tuple[str, ...]) -> str:
    """Hash length-delimited rows under one explicit manifest domain."""
    logger.debug("research_lean._domain_root entry domain=%s rows=%d", domain, len(rows))
    digest = hashlib.sha256()
    for value in (domain, *rows):
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    result = digest.hexdigest()
    logger.debug("research_lean._domain_root exit digest=%s", result[:12])
    return result


def calculate_source_roots(
    manifest: ResearchManifest,
) -> tuple[tuple[str, str], ...]:
    """Calculate ordered, domain-separated roots for base and research bytes."""
    logger.debug("research_lean.calculate_source_roots entry")
    result = tuple(
        (
            group,
            _domain_root(
                f"veyra.research-lean.sources.v1:{group}",
                tuple(f"{row.path}\0{row.sha256}" for row in records),
            ),
        )
        for group, records in (("base", manifest.base), ("research", manifest.research))
    )
    logger.debug("research_lean.calculate_source_roots exit")
    return result


def calculate_proof_root(manifest: ResearchManifest) -> str:
    """Calculate the domain-separated aggregate claim/closure evidence root."""
    logger.debug("research_lean.calculate_proof_root entry")
    roots = dict(calculate_source_roots(manifest))
    claims = {name: (statement, scope, registry) for name, statement, scope, registry in manifest.headline_claims}
    closures = dict(manifest.axiom_closure)
    rows = (
        f"toolchain\0{manifest.toolchain}\0{manifest.version}\0{manifest.commit}",
        f"base\0{roots['base']}",
        f"research\0{roots['research']}",
        *(
            "claim\0"
            + name
            + "\0"
            + "\0".join(claims[name])
            for name in manifest.headlines
        ),
        *(f"axioms\0{name}\0{','.join(closures[name])}" for name in manifest.declarations),
    )
    result = _domain_root("veyra.research-lean.proof.v1", tuple(rows))
    logger.debug("research_lean.calculate_proof_root exit digest=%s", result[:12])
    return result


def verify_inventory(manifest: ResearchManifest) -> dict[str, bytes]:
    """Verify exact paths, bytes, digests, imports, and declaration inventory."""
    logger.debug("research_lean.verify_inventory entry records=%d", len(manifest.records))
    actual_paths = {
        path.relative_to(ROOT).as_posix()
        for source_root in (BASE_ROOT, RESEARCH_ROOT)
        for path in source_root.glob("*.lean")
        if path.is_file() and not path.is_symlink()
    }
    expected_paths = {row.path for row in manifest.records}
    if actual_paths != expected_paths:
        logger.error(
            "research_lean.verify_inventory path drift missing=%s extra=%s",
            sorted(expected_paths - actual_paths), sorted(actual_paths - expected_paths),
        )
        raise ValueError("research-lean-source-inventory-drift")
    payloads: dict[str, bytes] = {}
    observed_headlines: dict[str, str] = {}
    for row in manifest.records:
        path = ROOT / row.path
        if path.is_symlink() or not path.is_file():
            logger.error("research_lean.verify_inventory invalid path=%s", row.path)
            raise ValueError("research-lean-source-path")
        payload = path.read_bytes()
        imports, declarations = parse_source(payload)
        if (
            sha256_bytes(payload) != row.sha256
            or imports != row.imports
            or (row.group == "research" and declarations != row.declarations)
        ):
            logger.error("research_lean.verify_inventory row drift path=%s", row.path)
            raise ValueError("research-lean-source-drift")
        payloads[row.path] = payload
        if row.group == "research":
            observed_headlines.update(headline_statements(payload))
    expected_statements = {
        name: statement
        for name, statement, _scope, _registry in manifest.headline_claims
    }
    if {name: observed_headlines.get(name) for name in manifest.headlines} != expected_statements:
        logger.error("research_lean.verify_inventory headline statement drift")
        raise ValueError("research-lean-headline-statement-drift")
    logger.debug("research_lean.verify_inventory exit payloads=%d", len(payloads))
    return payloads


def local_graph(manifest: ResearchManifest) -> dict[str, tuple[str, ...]]:
    """Build the exact local import DAG from manifest rows."""
    logger.debug("research_lean.local_graph entry")
    by_stem = {row.stem: row.path for row in manifest.records}
    by_group = {row.stem: row.group for row in manifest.records}
    result: dict[str, tuple[str, ...]] = {}
    for row in manifest.records:
        unknown = tuple(name for name in row.imports if name not in by_stem)
        if any(name.split(".", 1)[0] not in ALLOWED_EXTERNAL_IMPORT_ROOTS for name in unknown):
            logger.error("research_lean.local_graph external import rejected path=%s", row.path)
            raise ValueError("research-lean-import-not-allowed")
        if row.group == "base" and any(by_group.get(name) == "research" for name in row.imports):
            logger.error("research_lean.local_graph base imports research path=%s", row.path)
            raise ValueError("research-lean-base-imports-research")
        result[row.path] = tuple(by_stem[name] for name in row.imports if name in by_stem)
    logger.debug("research_lean.local_graph exit nodes=%d", len(result))
    return result


def graph_layers(graph: dict[str, tuple[str, ...]]) -> tuple[tuple[str, ...], ...]:
    """Partition a complete local import DAG into deterministic layers."""
    logger.debug("research_lean.graph_layers entry nodes=%d", len(graph))
    if any(dependency not in graph for dependencies in graph.values() for dependency in dependencies):
        logger.error("research_lean.graph_layers unknown dependency")
        raise ValueError("research-lean-import-unknown")
    remaining = set(graph)
    completed: set[str] = set()
    rows: list[tuple[str, ...]] = []
    while remaining:
        layer = tuple(sorted(node for node in remaining if set(graph[node]) <= completed))
        if not layer:
            logger.error("research_lean.graph_layers cycle")
            raise ValueError("research-lean-import-cycle")
        rows.append(layer)
        completed.update(layer)
        remaining.difference_update(layer)
    result = tuple(rows)
    logger.debug("research_lean.graph_layers exit layers=%d", len(result))
    return result


def lean_command(manifest: ResearchManifest) -> list[str]:
    """Resolve Lean and verify the root pin, version, and compiler commit."""
    logger.debug("research_lean.lean_command entry toolchain=%s", manifest.toolchain)
    toolchain_path = ROOT / "lean-toolchain"
    if toolchain_path.is_symlink() or not toolchain_path.is_file() or toolchain_path.read_bytes() != (manifest.toolchain + "\n").encode():
        logger.error("research_lean.lean_command root toolchain pin mismatch")
        raise RuntimeError("research-lean-root-toolchain-mismatch")
    lean = shutil.which("lean")
    if lean is None:
        logger.error("research_lean.lean_command Lean unavailable")
        raise RuntimeError("lean-not-found")
    command = [lean]
    process = subprocess.run(
        [*command, "--version"],
        capture_output=True,
        text=True,
        check=False,
        timeout=TOOLCHAIN_TIMEOUT_SECONDS,
    )
    output = (process.stdout + process.stderr).strip()
    match = VERSION_PATTERN.fullmatch(output)
    if (
        process.returncode
        or match is None
        or match.group(1) != manifest.version
        or match.group(2) != manifest.commit
    ):
        logger.error("research_lean.lean_command identity mismatch output=%r", output)
        raise RuntimeError("research-lean-toolchain-mismatch")
    logger.debug("research_lean.lean_command exit commit=%s", manifest.commit[:12])
    return command


def snapshot_sources(
    manifest: ResearchManifest,
    payloads: dict[str, bytes],
    snapshot_root: Path,
) -> dict[str, Path]:
    """Write the already verified bytes into a fresh private snapshot."""
    logger.debug("research_lean.snapshot_sources entry records=%d", len(manifest.records))
    result: dict[str, Path] = {}
    for row in manifest.records:
        destination = snapshot_root / row.path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payloads[row.path])
        if sha256_bytes(destination.read_bytes()) != row.sha256:
            logger.error("research_lean.snapshot_sources write drift path=%s", row.path)
            raise RuntimeError("research-lean-snapshot-drift")
        result[row.path] = destination
    logger.debug("research_lean.snapshot_sources exit files=%d", len(result))
    return result


def compile_one(
    command: list[str],
    logical_path: str,
    source: Path,
    output_root: Path,
    environment: dict[str, str],
) -> CompileResult:
    """Compile one snapshotted source with bounded output and time."""
    logger.debug("research_lean.compile_one entry source=%s", logical_path)
    started = time.perf_counter()
    output_path = output_root / f"{source.stem}.olean"
    process = subprocess.run(
        [*command, "-DwarningAsError=true", "-o", str(output_path), str(source)],
        cwd=source.parent,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=COMPILE_TIMEOUT_SECONDS,
    )
    elapsed = time.perf_counter() - started
    diagnostics = (process.stdout + process.stderr)[-MAX_DIAGNOSTIC_BYTES:]
    returncode = process.returncode
    if not returncode and (
        output_path.is_symlink() or not output_path.is_file() or output_path.stat().st_size == 0
    ):
        logger.error("research_lean.compile_one missing object source=%s", logical_path)
        returncode = 1
        diagnostics += "\ncompiler returned success without a nonempty regular .olean"
    result = CompileResult(logical_path, returncode, diagnostics, elapsed)
    if result.returncode:
        logger.error("research_lean.compile_one failed source=%s", logical_path)
    logger.debug(
        "research_lean.compile_one exit source=%s rc=%d elapsed=%.3f",
        logical_path, result.returncode, elapsed,
    )
    return result


def compile_layers(
    command: list[str],
    layers: tuple[tuple[str, ...], ...],
    snapshots: dict[str, Path],
    output_root: Path,
    environment: dict[str, str],
    jobs: int,
    progress: tqdm[Any],
) -> tuple[int, int, int]:
    """Compile dependency layers and stop before every dependent of a failure."""
    logger.debug("research_lean.compile_layers entry layers=%d jobs=%d", len(layers), jobs)
    passed = failed = 0
    total = sum(len(layer) for layer in layers)
    for layer in layers:
        layer_failed = False
        with ThreadPoolExecutor(max_workers=min(jobs, len(layer))) as executor:
            futures = {
                executor.submit(
                    compile_one,
                    command,
                    logical_path,
                    snapshots[logical_path],
                    output_root,
                    environment,
                ): logical_path
                for logical_path in layer
            }
            for future in as_completed(futures):
                logical_path = futures[future]
                try:
                    result = future.result()
                except (OSError, UnicodeError, subprocess.TimeoutExpired) as exc:
                    logger.error(
                        "research_lean.compile_layers blocked source=%s error=%s",
                        logical_path, exc,
                    )
                    print(f"\n[fail] {logical_path}: {exc}", file=sys.stderr)
                    failed += 1
                    layer_failed = True
                else:
                    if result.returncode:
                        print(f"\n[fail] {result.source}\n{result.output}", file=sys.stderr)
                        failed += 1
                        layer_failed = True
                    else:
                        passed += 1
                progress.update(1)
        if layer_failed:
            break
    skipped = total - passed - failed
    logger.debug(
        "research_lean.compile_layers exit passed=%d failed=%d skipped=%d",
        passed, failed, skipped,
    )
    return passed, failed, skipped


def audit_source(manifest: ResearchManifest) -> str:
    """Generate exact ``#check`` and ``#print axioms`` rows for all declarations."""
    logger.debug("research_lean.audit_source entry declarations=%d", len(manifest.declarations))
    imports = "\n".join(f"import {row.stem}" for row in manifest.research)
    checks = "\n".join(
        f"#check Veyra.{name}\n#print axioms Veyra.{name}"
        for name in manifest.declarations
    )
    result = f"{imports}\n\n{checks}\n"
    logger.debug("research_lean.audit_source exit chars=%d", len(result))
    return result


def parse_axiom_audit(
    output: str,
    declarations: tuple[str, ...],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Parse exact compiler ``#check``/axiom rows without accepting omissions."""
    logger.debug("research_lean.parse_axiom_audit entry chars=%d", len(output))
    expected = set(declarations)
    checked_rows = CHECK_ROW_PATTERN.findall(output)
    dependency_rows = AXIOM_ROW_PATTERN.findall(output)
    empty_rows = NO_AXIOM_ROW_PATTERN.findall(output)
    axiom_names = tuple(name for name, _values in dependency_rows) + tuple(empty_rows)
    rows: dict[str, tuple[str, ...]] = {
        name: tuple(item.strip() for item in values.split(",") if item.strip())
        for name, values in dependency_rows
    }
    rows.update({name: () for name in empty_rows})
    if (
        len(checked_rows) != len(declarations)
        or set(checked_rows) != expected
        or len(axiom_names) != len(declarations)
        or set(axiom_names) != expected
        or set(rows) != expected
    ):
        logger.error(
            "research_lean.parse_axiom_audit incomplete checks=%d axioms=%d expected=%d",
            len(checked_rows), len(axiom_names), len(expected),
        )
        raise ValueError("research-lean-axiom-audit-incomplete")
    result = tuple((name, rows[name]) for name in declarations)
    logger.debug("research_lean.parse_axiom_audit exit rows=%d", len(result))
    return result


def compile_audit(
    command: list[str],
    manifest: ResearchManifest,
    snapshot_root: Path,
    output_root: Path,
    environment: dict[str, str],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Compile and parse the generated exact declaration/axiom audit."""
    logger.debug("research_lean.compile_audit entry")
    source = snapshot_root / "experimental/research_lean/VeyraResearchAudit.lean"
    source.write_text(audit_source(manifest), encoding="utf-8")
    started = time.perf_counter()
    process = subprocess.run(
        [
            *command,
            "-DwarningAsError=true",
            "-o",
            str(output_root / "VeyraResearchAudit.olean"),
            str(source),
        ],
        cwd=source.parent,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=COMPILE_TIMEOUT_SECONDS,
    )
    output = process.stdout + process.stderr
    audit_object = output_root / "VeyraResearchAudit.olean"
    if process.returncode or audit_object.is_symlink() or not audit_object.is_file() or audit_object.stat().st_size == 0:
        logger.error("research_lean.compile_audit compile failed")
        print(output[-MAX_DIAGNOSTIC_BYTES:], file=sys.stderr)
        raise RuntimeError("research-lean-axiom-audit-failed")
    result = parse_axiom_audit(output, manifest.declarations)
    logger.debug(
        "research_lean.compile_audit exit rows=%d elapsed=%.3f",
        len(result), time.perf_counter() - started,
    )
    return result


def verify_original_rehash(manifest: ResearchManifest) -> None:
    """Rehash every original source after compilation to close the read window."""
    logger.debug("research_lean.verify_original_rehash entry records=%d", len(manifest.records))
    try:
        verify_inventory(manifest)
    except ValueError as exc:
        logger.error("research_lean.verify_original_rehash source drift error=%s", exc)
        raise RuntimeError("research-lean-source-toctou") from exc
    if (
        not manifest.manifest_sha256
        or MANIFEST_PATH.is_symlink()
        or not MANIFEST_PATH.is_file()
        or sha256_bytes(MANIFEST_PATH.read_bytes()) != manifest.manifest_sha256
    ):
        logger.error("research_lean.verify_original_rehash manifest drift")
        raise RuntimeError("research-lean-manifest-toctou")
    toolchain_path = ROOT / "lean-toolchain"
    if toolchain_path.is_symlink() or not toolchain_path.is_file() or toolchain_path.read_bytes() != (manifest.toolchain + "\n").encode():
        logger.error("research_lean.verify_original_rehash root toolchain drift")
        raise RuntimeError("research-lean-toolchain-toctou")
    logger.debug("research_lean.verify_original_rehash exit")


def run(argv: list[str]) -> int:
    """Execute the fresh manifest, compile, closure, and TOCTOU gates."""
    logger.debug("research_lean.run entry argc=%d", len(argv))
    args = parse_args(argv)
    started = time.perf_counter()
    print("[1/6] Loading exact research manifest", flush=True)
    manifest = load_manifest()
    print("[2/6] Verifying 48 base + 8 research source rows", flush=True)
    payloads = verify_inventory(manifest)
    layers = graph_layers(local_graph(manifest))
    print(
        f"[3/6] Resolving Lean {manifest.version} commit {manifest.commit[:12]}",
        flush=True,
    )
    command = lean_command(manifest)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    passed = failed = skipped = 0
    with tempfile.TemporaryDirectory(prefix="research-lean-", dir=TMP_ROOT) as directory:
        scratch = Path(directory)
        snapshot_root = scratch / "snapshot"
        output_root = scratch / "olean"
        output_root.mkdir(parents=True)
        snapshots = snapshot_sources(manifest, payloads, snapshot_root)
        environment = os.environ.copy()
        environment["LEAN_PATH"] = os.pathsep.join(
            (
                str(output_root),
                str(snapshot_root / "proofs/lean"),
                str(snapshot_root / "experimental/research_lean"),
            )
        )
        print(
            f"[4/6] Fresh-compiling 56 sources in {len(layers)} layers "
            f"with {args.jobs} workers",
            flush=True,
        )
        with tqdm(total=len(manifest.records), desc="Research Lean", unit="source") as progress:
            passed, failed, skipped = compile_layers(
                command,
                layers,
                snapshots,
                output_root,
                environment,
                args.jobs,
                progress,
            )
        if failed or skipped:
            elapsed = time.perf_counter() - started
            print(
                f"[done] passed={passed} failed={failed} skipped={skipped} "
                f"closure=not-run elapsed={elapsed:.2f}s",
                flush=True,
            )
            logger.debug("research_lean.run exit rc=1 compile failure")
            return 1
        print("[5/6] Checking all 65 declarations and exact axiom closure", flush=True)
        observed_closure = compile_audit(
            command, manifest, snapshot_root, output_root, environment,
        )
        if observed_closure != manifest.axiom_closure:
            logger.error("research_lean.run axiom closure drift")
            expected = dict(manifest.axiom_closure)
            observed = dict(observed_closure)
            for name in manifest.declarations:
                if expected[name] != observed[name]:
                    print(
                        f"[fail] axiom-closure {name}: expected={expected[name]} "
                        f"observed={observed[name]}",
                        file=sys.stderr,
                    )
            raise RuntimeError("research-lean-axiom-closure-drift")
        print("[6/6] Rehashing original sources after trusted snapshot replay", flush=True)
        verify_original_rehash(manifest)
    elapsed = time.perf_counter() - started
    roots = dict(manifest.source_roots)
    print(
        f"[evidence] manifest_sha256={manifest.manifest_sha256} "
        f"base_root={roots['base']} research_root={roots['research']} "
        f"proof_root={manifest.proof_root}", flush=True,
    )
    print(
        f"[done] passed={passed} failed=0 skipped=0 declarations=65 "
        f"axiom_rows=65 elapsed={elapsed:.2f}s "
        f"speed={passed / elapsed if elapsed else 0:.2f} source/s",
        flush=True,
    )
    logger.debug("research_lean.run exit rc=0")
    return 0


def main() -> None:
    """CLI boundary with stable blocked/failure status."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logger.debug("research_lean.main entry")
    try:
        result = run(sys.argv[1:])
    except (
        OSError,
        RuntimeError,
        UnicodeError,
        ValueError,
        subprocess.TimeoutExpired,
    ) as exc:
        logger.error("research_lean.main blocked error=%s", exc)
        print(f"[blocked] {exc}", file=sys.stderr)
        result = 2
    logger.debug("research_lean.main exit rc=%d", result)
    raise SystemExit(result)


if __name__ == "__main__":
    main()
