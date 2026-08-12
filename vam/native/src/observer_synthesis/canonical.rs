//! Exact canonical observer encoding shared with Python R11.

use super::ast::{infer_observer_kind, ObserverExpr, SynthesisCoreError};
use super::diagnostics::event;
use super::hash::sha256_hex;

pub const OBSERVER_SCHEMA: &str = "veyra.observer-core.v2";
pub const MAX_OBSERVER_BYTES: usize = 65_536;

fn write_node(node: &ObserverExpr, out: &mut String) {
    match node {
        ObserverExpr::Input => out.push_str("{\"tag\":\"input\"}"),
        ObserverExpr::Apply { primitive, child } => {
            out.push_str("{\"child\":");
            write_node(child, out);
            out.push_str(",\"primitive\":\"");
            out.push_str(primitive.as_str());
            out.push_str("\",\"tag\":\"apply\"}");
        }
        ObserverExpr::Pair { left, right } => {
            out.push_str("{\"left\":");
            write_node(left, out);
            out.push_str(",\"right\":");
            write_node(right, out);
            out.push_str(",\"tag\":\"pair\"}");
        }
    }
}

pub fn canonical_observer_bytes(observer: &ObserverExpr) -> Result<Vec<u8>, SynthesisCoreError> {
    event("ENTRY", "canonical-observer-bytes");
    if let Err(error) = infer_observer_kind(observer) {
        event("REJECT", "canonical-observer-kind-validation");
        return Err(error);
    }
    let mut out = String::from("{\"observer\":");
    write_node(observer, &mut out);
    out.push_str(",\"schema\":\"");
    out.push_str(OBSERVER_SCHEMA);
    out.push_str("\"}");
    if out.len() > MAX_OBSERVER_BYTES {
        event("REJECT", "canonical-observer-byte-limit");
        return Err(SynthesisCoreError("observer-byte-limit"));
    }
    event("EXIT", "canonical-observer-bytes");
    Ok(out.into_bytes())
}

pub fn observer_digest(observer: &ObserverExpr) -> Result<String, SynthesisCoreError> {
    event("ENTRY", "observer-digest");
    let result = canonical_observer_bytes(observer).map(|bytes| sha256_hex(&bytes));
    event(
        if result.is_ok() { "EXIT" } else { "REJECT" },
        "observer-digest",
    );
    result
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::observer_synthesis::PrimitiveId;

    #[test]
    fn python_golden_bytes_and_digests_match() {
        let input = ObserverExpr::Input;
        assert_eq!(
            observer_digest(&input).unwrap(),
            "5eb21cbbf9ace8fb6c9264119177bf610a4c6f3dcaec5cad5820f8f2729542c4"
        );
        let crest = ObserverExpr::apply(PrimitiveId::Crest, input);
        assert_eq!(String::from_utf8(canonical_observer_bytes(&crest).unwrap()).unwrap(), "{\"observer\":{\"child\":{\"tag\":\"input\"},\"primitive\":\"crest\",\"tag\":\"apply\"},\"schema\":\"veyra.observer-core.v2\"}");
        assert_eq!(
            observer_digest(&crest).unwrap(),
            "7eb8dcdbd11c47eb2f8553c26ca2cd4f4a09027deccb2a2a69bee881f927e502"
        );
    }
}
