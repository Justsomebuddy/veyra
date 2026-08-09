"""Exact UTF-8 alphabet and deterministic captured Lean presentation."""

from __future__ import annotations

import inspect
import logging

from .common import exact_digest, exact_shape, reject, sha
from .digest import digest, frame, texts
from .types import FormalAlphabetPresentation, StreamAlphabetSource

logger = logging.getLogger(__name__)
ALPHABET_VERSION = "pomega1-alphabet-v1"
BRIDGE_THEOREM_IDS = (
    "THM_POMEGA1_012_alphabet_encode_roundtrip",
    "THM_POMEGA1_013_alphabet_decode_roundtrip",
    "THM_POMEGA1_014_alphabet_bijection",
    "THM_POMEGA1_015_alphabet_order",
)
TEMPLATE_ID = "veyra.pomega1.utf8-fin-template.v1"
TEMPLATE_FORMAT_VERSION = "lean-fin-string-table-format-v1"
GENERATOR_CLOSURE_SHA256 = "36ae6a52794894d1839d0b912ce558a0648a8c81ec2c7ef79da3e2d1a465e530"
TEMPLATE_DIGEST = GENERATOR_CLOSURE_SHA256


def _lean_literal(value: str) -> str:
    """Encode one Unicode scalar string into unambiguous Lean syntax."""
    logger.debug("_lean_literal entry chars=%d", len(value))
    out = ['"']
    for char in value:
        code = ord(char)
        if char in ('"', "\\"):
            out.append("\\" + char)
        elif char == "\n":
            out.append("\\n")
        elif char == "\r":
            out.append("\\r")
        elif char == "\t":
            out.append("\\t")
        elif code < 0x20 or code == 0x7F:
            out.append(f"\\x{code:02x}")
        elif 0x20 <= code <= 0x7E:
            out.append(char)
        else:
            out.append(char)
    out.append('"')
    result = "".join(out)
    logger.debug("_lean_literal exit bytes=%d", len(result.encode()))
    return result


def stream_alphabet_source(symbols: tuple[str, ...]) -> StreamAlphabetSource:
    """Capture 1..16 ordered, unique, nonempty, bounded UTF-8 symbols."""
    logger.debug("stream_alphabet_source entry")
    if type(symbols) is not tuple or not 1 <= len(symbols) <= 16:
        reject("alphabet-symbol-tuple-invalid")
    captured = []
    for symbol in symbols:
        if type(symbol) is not str:
            reject("alphabet-symbol-must-be-exact-string")
        try:
            raw = symbol.encode("utf-8", errors="strict")
        except UnicodeError:
            reject("alphabet-symbol-invalid-utf8")
        if not raw or len(raw) > 64:
            reject("alphabet-symbol-size-invalid")
        captured.append(symbol)
    if len(set(captured)) != len(captured):
        reject("alphabet-symbols-must-be-unique")
    values = tuple(captured)
    value = digest("veyra.pomega1.alphabet.v1", (
        ("version", ALPHABET_VERSION.encode()), *texts("symbol", values),
    ))
    result = StreamAlphabetSource(ALPHABET_VERSION, values, value)
    logger.debug("stream_alphabet_source exit symbols=%d", len(values))
    return result


def snapshot_alphabet(value: StreamAlphabetSource) -> StreamAlphabetSource:
    """Rebuild the exact immutable alphabet source."""
    logger.debug("snapshot_alphabet entry")
    exact_shape(value, StreamAlphabetSource, "stream-alphabet")
    try:
        if type(value.version) is not str:
            reject("stream-alphabet-version-type-invalid")
        expected = stream_alphabet_source(value.symbols)
        exact_digest(value.alphabet_digest, "alphabet-digest")
    except AttributeError:
        reject("stream-alphabet-missing-fields")
    if value != expected:
        reject("stream-alphabet-drift")
    logger.debug("snapshot_alphabet exit")
    return expected


def _instance_source(alphabet: StreamAlphabetSource) -> bytes:
    """Generate the sole ordered Fin-N/String bijection artifact."""
    logger.debug("_instance_source entry symbols=%d", len(alphabet.symbols))
    literals = ", ".join(_lean_literal(item) for item in alphabet.symbols)
    count = len(alphabet.symbols)
    chain = "\n  ".join(
        f'if s == {_lean_literal(item)} then some ⟨{index}, by decide⟩ else'
        for index, item in enumerate(alphabet.symbols)
    ) + "\n  none"
    print_rows = "".join(f"#print axioms {name}\n" for name in BRIDGE_THEOREM_IDS)
    encode_rows = " ∧ ".join(
        f"pomegaDecode (pomegaEncode ⟨{i}, by decide⟩) = some ⟨{i}, by decide⟩"
        for i in range(count)
    )
    decode_rows = " ∧ ".join(
        f"(pomegaDecode {_lean_literal(item)}).map pomegaEncode = some {_lean_literal(item)}"
        for item in alphabet.symbols
    )
    text = f'''set_option autoImplicit false
def pomegaAlphabet : List String := [{literals}]
def pomegaEncode (i : Fin {count}) : String := pomegaAlphabet.get i
def pomegaDecode (s : String) : Option (Fin {count}) :=
  {chain}
theorem {BRIDGE_THEOREM_IDS[0]} : forall i, pomegaDecode (pomegaEncode i) = some i := by decide
theorem {BRIDGE_THEOREM_IDS[1]} : ({decode_rows}) := by decide
theorem {BRIDGE_THEOREM_IDS[2]} : ({encode_rows}) ∧ ({decode_rows}) := by decide
theorem {BRIDGE_THEOREM_IDS[3]} : pomegaAlphabet = [{literals}] := by rfl
{print_rows}'''
    result = text.encode("utf-8")
    logger.debug("_instance_source exit bytes=%d", len(result))
    return result


def _check_template() -> None:
    """Authenticate generator, literal helper, theorem IDs, and format constants."""
    logger.debug("_check_template entry")
    try:
        payload = frame("veyra.pomega1.generator-closure.v1", (
            ("instance-source", inspect.getsource(_instance_source).encode("utf-8")),
            ("literal-source", inspect.getsource(_lean_literal).encode("utf-8")),
            ("template-id", TEMPLATE_ID.encode()),
            ("format-version", TEMPLATE_FORMAT_VERSION.encode()),
            *texts("bridge-theorem", BRIDGE_THEOREM_IDS),
        ))
    except (OSError, TypeError) as exc:
        logger.error("_check_template unavailable error=%s", exc)
        reject("alphabet-template-unavailable")
    if sha(payload) != GENERATOR_CLOSURE_SHA256:
        reject("alphabet-template-drift")
    logger.debug("_check_template exit")


def formal_alphabet_presentation(
    alphabet: StreamAlphabetSource, generic_source_digest: str,
) -> FormalAlphabetPresentation:
    """Bind exact order, tables, inhabitant, template, and captured instance bytes."""
    logger.debug("formal_alphabet_presentation entry")
    alphabet = snapshot_alphabet(alphabet)
    generic_source_digest = exact_digest(generic_source_digest, "generic-source-digest")
    _check_template()
    source = _instance_source(alphabet)
    source_sha = sha(source)
    inverse = tuple((symbol, index) for index, symbol in enumerate(alphabet.symbols))
    value = digest("veyra.pomega1.alphabet-presentation.v1", (
        ("alphabet", alphabet.alphabet_digest.encode()),
        ("cardinality", len(alphabet.symbols).to_bytes(4, "big")),
        ("instance-sha", source_sha.encode()), *texts("symbol", alphabet.symbols),
        *texts("theorem", BRIDGE_THEOREM_IDS), ("generic", generic_source_digest.encode()),
        ("template", TEMPLATE_DIGEST.encode()),
    ))
    result = FormalAlphabetPresentation(
        alphabet.alphabet_digest, len(alphabet.symbols), source, source_sha,
        alphabet.symbols, inverse, 0, alphabet.symbols[0], BRIDGE_THEOREM_IDS,
        generic_source_digest, TEMPLATE_DIGEST, value,
    )
    logger.debug("formal_alphabet_presentation exit")
    return result


def snapshot_presentation(
    value: FormalAlphabetPresentation, alphabet: StreamAlphabetSource,
    generic_source_digest: str,
) -> FormalAlphabetPresentation:
    """Reject same-cardinality, reordered, mutable, or forged presentations."""
    logger.debug("snapshot_presentation entry")
    exact_shape(value, FormalAlphabetPresentation, "alphabet-presentation")
    try:
        if type(value.generated_instance_bytes) is not bytes:
            reject("generated-instance-must-be-bytes")
        if len(value.generated_instance_bytes) > 2 * 1024 * 1024:
            reject("generated-instance-hard-size-invalid")
        if any(type(item) is not int for item in (
            value.cardinality, value.inhabitant_index,
        )):
            reject("alphabet-presentation-integer-type-invalid")
        if not 1 <= value.cardinality <= 16:
            reject("alphabet-presentation-cardinality-invalid")
        if type(value.index_to_symbol) is not tuple or len(value.index_to_symbol) != value.cardinality:
            reject("alphabet-presentation-forward-table-length-invalid")
        if type(value.symbol_to_index) is not tuple or len(value.symbol_to_index) != value.cardinality:
            reject("alphabet-presentation-inverse-table-length-invalid")
        if type(value.theorem_ids) is not tuple or len(value.theorem_ids) != 4:
            reject("alphabet-presentation-theorem-table-length-invalid")
        if type(value.inhabitant_symbol) is not str:
            reject("alphabet-presentation-inhabitant-type-invalid")
        if any(
            type(item) is not str for item in value.index_to_symbol
        ):
            reject("alphabet-presentation-forward-table-invalid")
        if any(
            type(row) is not tuple or len(row) != 2
            or type(row[0]) is not str or type(row[1]) is not int
            for row in value.symbol_to_index
        ):
            reject("alphabet-presentation-inverse-table-invalid")
        if any(type(item) is not str for item in value.theorem_ids):
            reject("alphabet-presentation-theorem-table-invalid")
        for name in ("alphabet_digest", "generic_source_digest", "template_digest"):
            exact_digest(getattr(value, name), name.replace("_", "-"))
        exact_digest(value.generated_instance_sha256, "generated-instance-sha")
        exact_digest(value.presentation_digest, "presentation-digest")
        expected = formal_alphabet_presentation(alphabet, generic_source_digest)
    except AttributeError:
        reject("alphabet-presentation-missing-fields")
    if value != expected:
        reject("alphabet-presentation-drift")
    logger.debug("snapshot_presentation exit")
    return expected
