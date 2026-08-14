"""Strict tagged JSON codec shared by R7 proof artifacts and bindings."""
from __future__ import annotations

from hashlib import sha256
import json
import logging
from typing import NoReturn

from .proof_core_types import (
    Bound, CoreProp, CoreTerm, CoreType, Equal, Forall, Implies, ProofContext,
    Pulse, Resonates, Silence, Stitch, Weave,
)

logger = logging.getLogger(__name__)


def _value(reason: str) -> NoReturn:
    logger.error("proof_core_codec value rejection reason=%s", reason)
    raise ValueError(reason)


def _type(reason: str) -> NoReturn:
    logger.error("proof_core_codec type rejection reason=%s", reason)
    raise TypeError(reason)


def _json_value(value: object) -> object:
    logger.debug("proof_core_codec._json_value entry type=%s", type(value).__name__)
    if value is None or type(value) in {bool, int, str}:
        result = value
    elif type(value) is list:
        result = [_json_value(item) for item in value]
    elif type(value) is dict and all(type(key) is str for key in value):
        result = {key: _json_value(value[key]) for key in sorted(value)}
    else:
        _type(f"noncanonical-json-type:{type(value).__name__}")
    logger.debug("proof_core_codec._json_value exit")
    return result


def canonical_json(value: object) -> str:
    """Encode tagged integers/strings/lists/objects; never use repr or floats.

    A tuple is not JSON data and is therefore rejected instead of being
    silently collapsed onto the same bytes as a list.  Trusted callers must
    choose their JSON shape explicitly before entering this boundary.
    """
    logger.debug("canonical_json entry type=%s", type(value).__name__)
    result = json.dumps(
        _json_value(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    )
    logger.debug("canonical_json exit bytes=%d", len(result.encode()))
    return result


def digest_data(value: object, domain: str) -> str:
    """Hash canonical data under an explicit textual domain separator."""
    logger.debug("digest_data entry domain=%r", domain)
    if type(domain) is not str or not domain:
        _value("invalid-digest-domain")
    payload = domain.encode() + b"\0" + canonical_json(value).encode()
    result = sha256(payload).hexdigest()
    logger.debug("digest_data exit result=%s", result)
    return result


def term_data(term: CoreTerm) -> dict[str, object]:
    """Return the canonical tagged data form of a term."""
    logger.debug("term_data entry term=%r", term)
    if type(term) is Bound:
        result = {"tag": "bound", "index": term.index}
    elif type(term) is Silence:
        result = {"tag": "silence"}
    elif type(term) is Pulse:
        result = {"tag": "pulse", "tail": term_data(term.tail)}
    elif type(term) is Stitch:
        result = {"tag": "stitch", "left": term_data(term.left), "right": term_data(term.right)}
    elif type(term) is Weave:
        result = {"tag": "weave", "left": term_data(term.left), "right": term_data(term.right)}
    else:
        _type(f"unknown-core-term:{type(term).__name__}")
    logger.debug("term_data exit tag=%s", result["tag"])
    return result


def prop_data(prop: CoreProp) -> dict[str, object]:
    """Return the canonical tagged data form of a proposition."""
    logger.debug("prop_data entry prop=%r", prop)
    if type(prop) is Equal:
        result = {"tag": "equal", "left": term_data(prop.left), "right": term_data(prop.right)}
    elif type(prop) is Implies:
        result = {"tag": "implies", "premise": prop_data(prop.premise), "conclusion": prop_data(prop.conclusion)}
    elif type(prop) is Forall:
        result = {"tag": "forall", "type": prop.binder_type.value, "body": prop_data(prop.body)}
    elif type(prop) is Resonates:
        result = {"tag": "resonates", "factor": term_data(prop.factor), "carrier": term_data(prop.carrier)}
    else:
        _type(f"unknown-core-prop:{type(prop).__name__}")
    logger.debug("prop_data exit tag=%s", result["tag"])
    return result


def context_data(context: ProofContext) -> dict[str, object]:
    """Return canonical tagged context data."""
    logger.debug("context_data entry context=%r", context)
    result = {
        "tag": "context",
        "types": [item.value for item in context.term_types],
        "assumptions": [prop_data(item) for item in context.assumptions],
    }
    logger.debug("context_data exit types=%d assumptions=%d", len(context.term_types), len(context.assumptions))
    return result


def load_canonical(text: str) -> object:
    """Decode a field only when re-encoding is byte-identical."""
    logger.debug("load_canonical entry type=%s", type(text).__name__)
    if type(text) is not str:
        _type("canonical-field-not-string")
    value = json.loads(text)
    if canonical_json(value) != text:
        _value("noncanonical-json")
    logger.debug("load_canonical exit type=%s", type(value).__name__)
    return value


def exact_keys(data: object, expected: set[str]) -> dict[str, object]:
    """Require a tagged object to contain exactly the declared keys."""
    logger.debug("exact_keys entry expected=%r", expected)
    if type(data) is not dict or set(data) != expected:
        _value("tagged-object-shape")
    logger.debug("exact_keys exit valid")
    return data


def term_from_data(data: object) -> CoreTerm:
    """Decode a strict tagged term."""
    logger.debug("term_from_data entry data=%r", data)
    if type(data) is not dict or type(data.get("tag")) is not str:
        _value("term-tag")
    tag = data["tag"]
    if tag == "bound":
        row = exact_keys(data, {"tag", "index"})
        result: CoreTerm = Bound(row["index"])
    elif tag == "silence":
        exact_keys(data, {"tag"})
        result = Silence()
    elif tag == "pulse":
        row = exact_keys(data, {"tag", "tail"})
        result = Pulse(term_from_data(row["tail"]))
    elif tag in {"stitch", "weave"}:
        row = exact_keys(data, {"tag", "left", "right"})
        pair = term_from_data(row["left"]), term_from_data(row["right"])
        result = Stitch(*pair) if tag == "stitch" else Weave(*pair)
    else:
        _value("unknown-term-tag")
    logger.debug("term_from_data exit result=%r", result)
    return result


def prop_from_data(data: object) -> CoreProp:
    """Decode a strict tagged proposition."""
    logger.debug("prop_from_data entry data=%r", data)
    if type(data) is not dict or type(data.get("tag")) is not str:
        _value("prop-tag")
    tag = data["tag"]
    if tag == "equal":
        row = exact_keys(data, {"tag", "left", "right"})
        result: CoreProp = Equal(term_from_data(row["left"]), term_from_data(row["right"]))
    elif tag == "implies":
        row = exact_keys(data, {"tag", "premise", "conclusion"})
        result = Implies(prop_from_data(row["premise"]), prop_from_data(row["conclusion"]))
    elif tag == "forall":
        row = exact_keys(data, {"tag", "type", "body"})
        result = Forall(CoreType(row["type"]), prop_from_data(row["body"]))
    elif tag == "resonates":
        row = exact_keys(data, {"tag", "factor", "carrier"})
        result = Resonates(term_from_data(row["factor"]), term_from_data(row["carrier"]))
    else:
        _value("unknown-prop-tag")
    logger.debug("prop_from_data exit result=%r", result)
    return result


def context_from_data(data: object) -> ProofContext:
    """Decode a strict tagged proof context."""
    logger.debug("context_from_data entry")
    row = exact_keys(data, {"tag", "types", "assumptions"})
    if row["tag"] != "context" or type(row["types"]) is not list or type(row["assumptions"]) is not list:
        _value("context-shape")
    result = ProofContext(
        tuple(CoreType(item) for item in row["types"]),
        tuple(prop_from_data(item) for item in row["assumptions"]),
    )
    logger.debug("context_from_data exit result=%r", result)
    return result
