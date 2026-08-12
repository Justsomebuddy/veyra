//! Exact canonical observer encoding shared with Python R11.

use super::ast::{infer_observer_kind, ObserverExpr, PrimitiveId, SynthesisCoreError};
use super::diagnostics::event;
use super::hash::sha256_hex;

pub const OBSERVER_SCHEMA: &str = "veyra.observer-core.v2";
pub const PARITY_OBSERVER_SCHEMA: &str = "veyra.observer-core.v3";
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

fn contains_parity(node: &ObserverExpr) -> bool {
    event("ENTRY", "observer-contains-parity");
    fn walk(node: &ObserverExpr) -> bool {
        match node {
            ObserverExpr::Input => false,
            ObserverExpr::Apply { primitive, child } => {
                *primitive == PrimitiveId::Parity || walk(child)
            }
            ObserverExpr::Pair { left, right } => walk(left) || walk(right),
        }
    }
    let result = walk(node);
    event("EXIT", "observer-contains-parity");
    result
}

/// Returns the schema selected by the observer itself. Old Tail/Crest/Pair
/// expressions remain on v2; only expressions containing Parity move to v3.
pub fn observer_canonical_schema(observer: &ObserverExpr) -> &'static str {
    event("ENTRY", "observer-canonical-schema");
    let result = if contains_parity(observer) {
        PARITY_OBSERVER_SCHEMA
    } else {
        OBSERVER_SCHEMA
    };
    event("EXIT", "observer-canonical-schema");
    result
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
    out.push_str(observer_canonical_schema(observer));
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

    #[test]
    fn parity_uses_a_new_schema_without_rebinding_legacy_bytes() {
        let parity = ObserverExpr::apply(PrimitiveId::Parity, ObserverExpr::Input);
        let encoded = String::from_utf8(canonical_observer_bytes(&parity).unwrap()).unwrap();
        assert_eq!(observer_canonical_schema(&parity), PARITY_OBSERVER_SCHEMA);
        assert!(encoded.contains("\"primitive\":\"parity\""));
        assert!(encoded.ends_with("\"schema\":\"veyra.observer-core.v3\"}"));
        assert_eq!(
            observer_canonical_schema(&ObserverExpr::Input),
            OBSERVER_SCHEMA
        );
    }
}
