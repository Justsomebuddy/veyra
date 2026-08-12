//! Derived finite bit-marginal evidence for the XOR negative control.

use super::ast::SynthesisCoreError;
use super::benchmark_suite::NativeEncodedState;
use super::diagnostics;
use super::hash::domain_sha256_hex;

const MARGINAL_SCHEMA: &str = "veyra.native-observer-benchmark.bit-marginals.v1";
const MARGINAL_DOMAIN: &str = "veyra.native-observer-benchmark.bit-marginals.v1.binding";

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeBitMarginalBalanceV1 {
    pub schema: &'static str,
    pub bit_order: [&'static str; 2],
    /// `[bit][bit_value][target_class]` over the four abstract states.
    pub counts: [[[usize; 2]; 2]; 2],
    pub balanced: bool,
    pub marginal_digest: String,
}

pub(super) fn marginal_json(balance: &NativeBitMarginalBalanceV1) -> String {
    diagnostics::event("MARGINAL_JSON_ENTER", "encoding derived marginal table");
    let result = format!(
        concat!(
            "{{\"balanced\":{},\"bit_order\":[\"{}\",\"{}\"],",
            "\"counts\":[[[{},{}],[{},{}]],[[{},{}],[{},{}]]],",
            "\"marginal_digest\":\"{}\",\"schema\":\"{}\"}}"
        ),
        balance.balanced,
        balance.bit_order[0],
        balance.bit_order[1],
        balance.counts[0][0][0],
        balance.counts[0][0][1],
        balance.counts[0][1][0],
        balance.counts[0][1][1],
        balance.counts[1][0][0],
        balance.counts[1][0][1],
        balance.counts[1][1][0],
        balance.counts[1][1][1],
        balance.marginal_digest,
        balance.schema,
    );
    diagnostics::event("MARGINAL_JSON_EXIT", "derived marginal table encoded");
    result
}

pub(super) fn derive_binary_marginals(
    states: &[NativeEncodedState],
) -> Result<NativeBitMarginalBalanceV1, SynthesisCoreError> {
    diagnostics::event("MARGINAL_DERIVE_ENTER", "deriving exact two-bit marginals");
    if states.len() != 4
        || states
            .iter()
            .enumerate()
            .any(|(ordinal, state)| state.abstract_id as usize != ordinal || state.target_class > 1)
    {
        diagnostics::event("MARGINAL_DERIVE_REJECT", "abstract state order is invalid");
        return Err(SynthesisCoreError("invalid-marginal-state-order"));
    }
    let mut counts = [[[0usize; 2]; 2]; 2];
    for state in states {
        let features = [state.feature_a, state.feature_b];
        if features.iter().any(|value| *value > 1) {
            diagnostics::event("MARGINAL_DERIVE_REJECT", "feature value is not binary");
            return Err(SynthesisCoreError("invalid-marginal-feature-value"));
        }
        for (bit, value) in features.into_iter().enumerate() {
            counts[bit][value as usize][state.target_class as usize] += 1;
        }
    }
    let balanced = counts
        .iter()
        .all(|bit| bit.iter().all(|row| *row == [1, 1]));
    let canonical = format!(
        concat!(
            "{{\"bit_order\":[\"feature_a\",\"feature_b\"],",
            "\"counts\":[[[{},{}],[{},{}]],[[{},{}],[{},{}]]],",
            "\"schema\":\"{}\"}}"
        ),
        counts[0][0][0],
        counts[0][0][1],
        counts[0][1][0],
        counts[0][1][1],
        counts[1][0][0],
        counts[1][0][1],
        counts[1][1][0],
        counts[1][1][1],
        MARGINAL_SCHEMA,
    );
    let result = NativeBitMarginalBalanceV1 {
        schema: MARGINAL_SCHEMA,
        bit_order: ["feature_a", "feature_b"],
        counts,
        balanced,
        marginal_digest: domain_sha256_hex(MARGINAL_DOMAIN, canonical.as_bytes()),
    };
    diagnostics::event("MARGINAL_DERIVE_EXIT", "exact two-bit marginals derived");
    Ok(result)
}
