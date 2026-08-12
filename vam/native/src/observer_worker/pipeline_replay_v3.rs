//! Canonical VOR2 codec and authenticated replay for observer pipeline v3.

use ed25519_dalek::SigningKey;

use crate::observer_synthesis::{
    run_observer_synthesis_pipeline_v3, FiniteDomainV1, JointSynthesisLimits,
    NamedObserverBaselineV1, NativePartitionTaskId, ObserverGapPolicyV1, ObserverGapRequestV1,
    ObserverGapStatusV1, ObserverGrammarProfileId, ObserverSynthesisPipelineRequestV3,
    ObserverSynthesisPipelineResultV3, PipelineStageV3, PipelineStatusV3,
    TransportInformationClassV1, TransportOpV1, TransportTermV1, MAX_TRANSPORT_DEPTH,
    MAX_TRANSPORT_NODES,
};

use super::event;
use super::replay_v2::{
    build_ed25519_payload_bundle_v2, build_hmac_payload_bundle_v2, ReplayBundleV2,
    ReplayPayloadKindV2, ReplayTrustPolicyV2, ReplayV2Error,
};

pub const MAX_PIPELINE_REQUEST_V3_BYTES: usize = 4 * 1024;
pub const MAX_PIPELINE_RESULT_V3_BYTES: usize = 24 * 1024;
const REQUEST_MAGIC: &[u8; 4] = b"VPR3";
const RESULT_MAGIC: &[u8; 4] = b"VPS3";
const VERSION: u16 = 1;

struct Encoder {
    bytes: Vec<u8>,
}

impl Encoder {
    fn new(magic: &[u8; 4]) -> Self {
        event("pipeline-replay-v3", "encoder-new");
        let mut bytes = magic.to_vec();
        bytes.extend_from_slice(&VERSION.to_be_bytes());
        Self { bytes }
    }
    fn u8(&mut self, value: u8) {
        event("pipeline-replay-v3", "encode-u8");
        self.bytes.push(value);
    }
    fn u16(&mut self, value: usize) -> Result<(), ReplayV2Error> {
        event("pipeline-replay-v3", "encode-u16");
        self.bytes.extend_from_slice(
            &u16::try_from(value)
                .map_err(|_| ReplayV2Error("pipeline-v3 u16 overflow"))?
                .to_be_bytes(),
        );
        Ok(())
    }
    fn u32(&mut self, value: usize) -> Result<(), ReplayV2Error> {
        event("pipeline-replay-v3", "encode-u32");
        self.bytes.extend_from_slice(
            &u32::try_from(value)
                .map_err(|_| ReplayV2Error("pipeline-v3 u32 overflow"))?
                .to_be_bytes(),
        );
        Ok(())
    }
    fn i32(&mut self, value: i32) {
        event("pipeline-replay-v3", "encode-i32");
        self.bytes.extend_from_slice(&value.to_be_bytes());
    }
    fn text(&mut self, value: &str) -> Result<(), ReplayV2Error> {
        event("pipeline-replay-v3", "encode-text-enter");
        self.u16(value.len())?;
        self.bytes.extend_from_slice(value.as_bytes());
        event("pipeline-replay-v3", "encode-text-exit");
        Ok(())
    }
    fn optional_text(&mut self, value: Option<&str>) -> Result<(), ReplayV2Error> {
        event("pipeline-replay-v3", "encode-optional-text-enter");
        match value {
            Some(text) => {
                self.u8(1);
                self.text(text)?;
            }
            None => self.u8(0),
        }
        event("pipeline-replay-v3", "encode-optional-text-exit");
        Ok(())
    }
}

struct Decoder<'a> {
    bytes: &'a [u8],
    offset: usize,
}

impl<'a> Decoder<'a> {
    fn new(bytes: &'a [u8], magic: &[u8; 4], maximum: usize) -> Result<Self, ReplayV2Error> {
        event("pipeline-replay-v3", "decoder-new-enter");
        if bytes.len() > maximum || bytes.get(..4) != Some(magic) {
            return Err(ReplayV2Error("invalid pipeline-v3 frame"));
        }
        let mut result = Self { bytes, offset: 4 };
        if result.u16()? != VERSION {
            return Err(ReplayV2Error("unsupported pipeline-v3 frame version"));
        }
        event("pipeline-replay-v3", "decoder-new-exit");
        Ok(result)
    }
    fn take(&mut self, count: usize) -> Result<&'a [u8], ReplayV2Error> {
        event("pipeline-replay-v3", "decode-take");
        let end = self
            .offset
            .checked_add(count)
            .ok_or(ReplayV2Error("pipeline-v3 offset overflow"))?;
        let result = self
            .bytes
            .get(self.offset..end)
            .ok_or(ReplayV2Error("truncated pipeline-v3 field"))?;
        self.offset = end;
        Ok(result)
    }
    fn u8(&mut self) -> Result<u8, ReplayV2Error> {
        event("pipeline-replay-v3", "decode-u8");
        Ok(self.take(1)?[0])
    }
    fn u16(&mut self) -> Result<u16, ReplayV2Error> {
        event("pipeline-replay-v3", "decode-u16");
        let mut bytes = [0; 2];
        bytes.copy_from_slice(self.take(2)?);
        Ok(u16::from_be_bytes(bytes))
    }
    fn u32(&mut self) -> Result<u32, ReplayV2Error> {
        event("pipeline-replay-v3", "decode-u32");
        let mut bytes = [0; 4];
        bytes.copy_from_slice(self.take(4)?);
        Ok(u32::from_be_bytes(bytes))
    }
    fn i32(&mut self) -> Result<i32, ReplayV2Error> {
        event("pipeline-replay-v3", "decode-i32");
        let mut bytes = [0; 4];
        bytes.copy_from_slice(self.take(4)?);
        Ok(i32::from_be_bytes(bytes))
    }
    fn boolean(&mut self) -> Result<bool, ReplayV2Error> {
        event("pipeline-replay-v3", "decode-boolean");
        match self.u8()? {
            0 => Ok(false),
            1 => Ok(true),
            _ => Err(ReplayV2Error("non-canonical pipeline-v3 boolean")),
        }
    }
    fn text(&mut self, maximum: usize) -> Result<String, ReplayV2Error> {
        event("pipeline-replay-v3", "decode-text-enter");
        let length = self.u16()? as usize;
        if length > maximum {
            return Err(ReplayV2Error("pipeline-v3 text exceeds bound"));
        }
        let result = std::str::from_utf8(self.take(length)?)
            .map_err(|_| ReplayV2Error("pipeline-v3 text is not UTF-8"))?
            .to_owned();
        event("pipeline-replay-v3", "decode-text-exit");
        Ok(result)
    }
    fn finish(self) -> Result<(), ReplayV2Error> {
        event("pipeline-replay-v3", "decode-finish");
        if self.offset == self.bytes.len() {
            Ok(())
        } else {
            Err(ReplayV2Error("trailing bytes in pipeline-v3 frame"))
        }
    }
}

fn encode_op(encoder: &mut Encoder, op: &TransportOpV1) -> Result<(), ReplayV2Error> {
    event("pipeline-replay-v3", "encode-op-enter");
    match op {
        TransportOpV1::Identity => encoder.u8(1),
        TransportOpV1::Relabel(rows) => {
            encoder.u8(2);
            encode_rows(encoder, rows)?;
        }
        TransportOpV1::ShiftEmbed(shift) => {
            encoder.u8(3);
            encoder.u16(*shift as usize)?;
        }
        TransportOpV1::Project(rows) => {
            encoder.u8(4);
            encode_rows(encoder, rows)?;
        }
        TransportOpV1::Group(rows) => {
            encoder.u8(5);
            encode_rows(encoder, rows)?;
        }
        TransportOpV1::CanonicalEncode(rows) => {
            encoder.u8(6);
            encode_rows(encoder, rows)?;
        }
        TransportOpV1::Compose(_) => {
            return Err(ReplayV2Error("nested composition requires term codec"));
        }
    }
    event("pipeline-replay-v3", "encode-op-exit");
    Ok(())
}

fn encode_term(
    encoder: &mut Encoder,
    term: &TransportTermV1,
    depth: u16,
    nodes: &mut u16,
) -> Result<(), ReplayV2Error> {
    event("pipeline-replay-v3", "encode-term-enter");
    if depth >= MAX_TRANSPORT_DEPTH || *nodes >= MAX_TRANSPORT_NODES {
        return Err(ReplayV2Error("pipeline-v3 transport tree exceeds bound"));
    }
    *nodes += 1;
    encoder.text(term.source.id())?;
    encoder.u16(term.source.cardinality() as usize)?;
    encoder.text(term.target.id())?;
    encoder.u16(term.target.cardinality() as usize)?;
    match &term.op {
        TransportOpV1::Compose(children) => {
            if children.len() < 2 || children.len() > MAX_TRANSPORT_NODES as usize {
                return Err(ReplayV2Error("invalid pipeline-v3 composition arity"));
            }
            encoder.u8(7);
            encoder.u16(children.len())?;
            for child in children {
                encode_term(encoder, child, depth + 1, nodes)?;
            }
        }
        op => encode_op(encoder, op)?,
    }
    event("pipeline-replay-v3", "encode-term-exit");
    Ok(())
}

fn decode_term(
    decoder: &mut Decoder<'_>,
    depth: u16,
    nodes: &mut u16,
) -> Result<TransportTermV1, ReplayV2Error> {
    event("pipeline-replay-v3", "decode-term-enter");
    if depth >= MAX_TRANSPORT_DEPTH || *nodes >= MAX_TRANSPORT_NODES {
        return Err(ReplayV2Error("pipeline-v3 transport tree exceeds bound"));
    }
    *nodes += 1;
    let source = FiniteDomainV1::new(&decoder.text(128)?, decoder.u16()?)
        .map_err(|_| ReplayV2Error("invalid pipeline-v3 source domain"))?;
    let target = FiniteDomainV1::new(&decoder.text(128)?, decoder.u16()?)
        .map_err(|_| ReplayV2Error("invalid pipeline-v3 target domain"))?;
    let op = match decoder.u8()? {
        1 => TransportOpV1::Identity,
        2 => TransportOpV1::Relabel(decode_rows(decoder)?),
        3 => TransportOpV1::ShiftEmbed(decoder.u16()?),
        4 => TransportOpV1::Project(decode_rows(decoder)?),
        5 => TransportOpV1::Group(decode_rows(decoder)?),
        6 => TransportOpV1::CanonicalEncode(decode_rows(decoder)?),
        7 => {
            let count = decoder.u16()? as usize;
            if count < 2 || count > MAX_TRANSPORT_NODES as usize {
                return Err(ReplayV2Error("invalid pipeline-v3 composition arity"));
            }
            let mut children = Vec::with_capacity(count);
            for _ in 0..count {
                children.push(decode_term(decoder, depth + 1, nodes)?);
            }
            TransportOpV1::Compose(children)
        }
        _ => return Err(ReplayV2Error("unknown pipeline-v3 transport operation")),
    };
    event("pipeline-replay-v3", "decode-term-exit");
    Ok(TransportTermV1 { source, target, op })
}

fn encode_rows(encoder: &mut Encoder, rows: &[u16]) -> Result<(), ReplayV2Error> {
    event("pipeline-replay-v3", "encode-rows-enter");
    if rows.is_empty() || rows.len() > 256 {
        return Err(ReplayV2Error("invalid pipeline-v3 transport row count"));
    }
    encoder.u16(rows.len())?;
    for value in rows {
        encoder.u16(*value as usize)?;
    }
    event("pipeline-replay-v3", "encode-rows-exit");
    Ok(())
}

fn decode_rows(decoder: &mut Decoder<'_>) -> Result<Vec<u16>, ReplayV2Error> {
    event("pipeline-replay-v3", "decode-rows-enter");
    let count = decoder.u16()? as usize;
    if count == 0 || count > 256 {
        return Err(ReplayV2Error("invalid pipeline-v3 transport row count"));
    }
    let mut result = Vec::with_capacity(count);
    for _ in 0..count {
        result.push(decoder.u16()?);
    }
    event("pipeline-replay-v3", "decode-rows-exit");
    Ok(result)
}

pub fn encode_observer_pipeline_request_v3(
    request: &ObserverSynthesisPipelineRequestV3,
) -> Result<Vec<u8>, ReplayV2Error> {
    event("pipeline-replay-v3", "encode-request-enter");
    if request.gap_request.baselines.is_empty() || request.gap_request.baselines.len() > 16 {
        return Err(ReplayV2Error("invalid pipeline-v3 baseline count"));
    }
    if request
        .gap_request
        .baselines
        .iter()
        .any(|baseline| baseline.name.len() > 64)
    {
        return Err(ReplayV2Error("pipeline-v3 baseline name exceeds bound"));
    }
    if request.transports.is_empty() || request.transports.len() > 16 {
        return Err(ReplayV2Error("invalid pipeline-v3 transport count"));
    }
    let mut encoder = Encoder::new(REQUEST_MAGIC);
    encoder.u8(match request.gap_request.task_id {
        NativePartitionTaskId::OneVsThree => 1,
        NativePartitionTaskId::XorParity => 2,
    });
    encoder.u8(match request.gap_request.grammar_profile_id {
        ObserverGrammarProfileId::LegacyV1 => 1,
        ObserverGrammarProfileId::ParityV2 => 2,
    });
    let limits = request.gap_request.joint_limits;
    encoder.u32(limits.transform_limit)?;
    encoder.u32(limits.candidate_limit)?;
    encoder.u32(limits.relation_evaluation_limit)?;
    encoder.u16(request.gap_request.baselines.len())?;
    for baseline in &request.gap_request.baselines {
        encoder.text(&baseline.name)?;
        encoder.u32(baseline.observer_ordinal)?;
    }
    let policy = request.gap_request.policy;
    encoder.i32(policy.minimum_fit_gain);
    encoder.i32(policy.minimum_class_saving_gain);
    encoder.i32(policy.maximum_cost_delta);
    encoder.u8(u8::from(policy.permit_information_loss));
    encoder.u32(request.gap_request.information_loss_penalty as usize)?;
    encoder.u16(request.transports.len())?;
    for term in &request.transports {
        let mut nodes = 0;
        encode_term(&mut encoder, term, 0, &mut nodes)?;
    }
    if encoder.bytes.len() > MAX_PIPELINE_REQUEST_V3_BYTES {
        return Err(ReplayV2Error("pipeline-v3 request exceeds bound"));
    }
    event("pipeline-replay-v3", "encode-request-exit");
    Ok(encoder.bytes)
}

pub fn decode_observer_pipeline_request_v3(
    bytes: &[u8],
) -> Result<ObserverSynthesisPipelineRequestV3, ReplayV2Error> {
    event("pipeline-replay-v3", "decode-request-enter");
    let mut decoder = Decoder::new(bytes, REQUEST_MAGIC, MAX_PIPELINE_REQUEST_V3_BYTES)?;
    let task_id = match decoder.u8()? {
        1 => NativePartitionTaskId::OneVsThree,
        2 => NativePartitionTaskId::XorParity,
        _ => return Err(ReplayV2Error("unknown pipeline-v3 task")),
    };
    let grammar_profile_id = match decoder.u8()? {
        1 => ObserverGrammarProfileId::LegacyV1,
        2 => ObserverGrammarProfileId::ParityV2,
        _ => return Err(ReplayV2Error("unknown pipeline-v3 grammar profile")),
    };
    let joint_limits = JointSynthesisLimits {
        transform_limit: decoder.u32()? as usize,
        candidate_limit: decoder.u32()? as usize,
        relation_evaluation_limit: decoder.u32()? as usize,
    };
    let baseline_count = decoder.u16()? as usize;
    if baseline_count == 0 || baseline_count > 16 {
        return Err(ReplayV2Error("invalid pipeline-v3 baseline count"));
    }
    let mut baselines = Vec::with_capacity(baseline_count);
    for _ in 0..baseline_count {
        baselines.push(NamedObserverBaselineV1 {
            name: decoder.text(64)?,
            observer_ordinal: decoder.u32()? as usize,
        });
    }
    let policy = ObserverGapPolicyV1 {
        minimum_fit_gain: decoder.i32()?,
        minimum_class_saving_gain: decoder.i32()?,
        maximum_cost_delta: decoder.i32()?,
        permit_information_loss: decoder.boolean()?,
    };
    let information_loss_penalty = decoder.u32()?;
    let transport_count = decoder.u16()? as usize;
    if transport_count == 0 || transport_count > 16 {
        return Err(ReplayV2Error("invalid pipeline-v3 transport count"));
    }
    let mut transports = Vec::with_capacity(transport_count);
    for _ in 0..transport_count {
        let mut nodes = 0;
        transports.push(decode_term(&mut decoder, 0, &mut nodes)?);
    }
    decoder.finish()?;
    let result = ObserverSynthesisPipelineRequestV3 {
        gap_request: ObserverGapRequestV1 {
            task_id,
            grammar_profile_id,
            joint_limits,
            baselines,
            policy,
            information_loss_penalty,
        },
        transports,
    };
    if encode_observer_pipeline_request_v3(&result)? != bytes {
        return Err(ReplayV2Error("non-canonical pipeline-v3 request"));
    }
    event("pipeline-replay-v3", "decode-request-exit");
    Ok(result)
}

fn stage_tag(value: PipelineStageV3) -> u8 {
    event("pipeline-replay-v3", "stage-tag");
    match value {
        PipelineStageV3::Normalize => 1,
        PipelineStageV3::Transport => 2,
        PipelineStageV3::Observer => 3,
        PipelineStageV3::Explanation => 4,
        PipelineStageV3::Aggregate => 5,
    }
}

pub fn canonical_observer_pipeline_result_v3_bytes(
    result: &ObserverSynthesisPipelineResultV3,
) -> Result<Vec<u8>, ReplayV2Error> {
    event("pipeline-replay-v3", "encode-result-enter");
    let mut encoder = Encoder::new(RESULT_MAGIC);
    encoder.text(result.schema)?;
    encoder.u8(match result.status {
        PipelineStatusV3::Ready => 1,
        PipelineStatusV3::Incomplete => 2,
        PipelineStatusV3::Blocked => 3,
    });
    match result.failed_stage {
        Some(value) => {
            encoder.u8(1);
            encoder.u8(stage_tag(value));
        }
        None => encoder.u8(0),
    }
    encoder.optional_text(result.obstruction)?;
    encoder.text(&result.audit_digest)?;
    encoder.text(result.boundary)?;
    match &result.evidence {
        None => encoder.u8(0),
        Some(evidence) => {
            encoder.u8(1);
            encoder.text(&evidence.grammar_registry_digest)?;
            encoder.u16(evidence.transports.len())?;
            for row in &evidence.transports {
                encoder.u32(row.ordinal)?;
                encoder.text(&row.transport_digest)?;
                encoder.u8(match row.information_class {
                    TransportInformationClassV1::Bijection => 1,
                    TransportInformationClassV1::Injection => 2,
                    TransportInformationClassV1::Loss => 3,
                });
                encoder.u32(row.collision_count as usize)?;
                encoder.u32(row.cost as usize)?;
            }
            encoder.text(&evidence.differential_digest)?;
            encoder.u32(evidence.selected_transport_ordinal)?;
            encoder.text(&evidence.selected_transport_digest)?;
            encoder.u8(match evidence.selected_transport_information_class {
                TransportInformationClassV1::Bijection => 1,
                TransportInformationClassV1::Injection => 2,
                TransportInformationClassV1::Loss => 3,
            });
            encoder.u32(evidence.selected_transport_collision_count as usize)?;
            encoder.u32(evidence.selected_observer_ordinal)?;
            encoder.text(&evidence.selected_observer_digest)?;
            encoder.u32(evidence.selected_joint_cost)?;
            encoder.text(&evidence.observer_gap_receipt_digest)?;
            encoder.u8(match evidence.observer_gap_status {
                ObserverGapStatusV1::Positive => 1,
                ObserverGapStatusV1::NoGap => 2,
                ObserverGapStatusV1::Incomplete => 3,
                ObserverGapStatusV1::Blocked => 4,
            });
            encoder.u16(evidence.stages.len())?;
            for row in &evidence.stages {
                encoder.u32(row.ordinal)?;
                encoder.u8(stage_tag(row.stage));
                encoder.optional_text(row.predecessor_digest.as_deref())?;
                encoder.text(&row.output_digest)?;
                encoder.u32(row.cost)?;
                encoder.u32(row.limit)?;
                encoder.text(&row.stage_digest)?;
            }
            encoder.text(&evidence.evidence_digest)?;
        }
    }
    if encoder.bytes.len() > MAX_PIPELINE_RESULT_V3_BYTES {
        return Err(ReplayV2Error("pipeline-v3 result exceeds bound"));
    }
    event("pipeline-replay-v3", "encode-result-exit");
    Ok(encoder.bytes)
}

pub fn build_hmac_observer_pipeline_bundle_v3(
    request: &ObserverSynthesisPipelineRequestV3,
    signer_label: &str,
    key_id: [u8; 32],
    key: &[u8],
) -> Result<ReplayBundleV2, ReplayV2Error> {
    event("pipeline-replay-v3", "build-hmac-enter");
    let request_bytes = encode_observer_pipeline_request_v3(request)?;
    let result = run_observer_synthesis_pipeline_v3(request)
        .map_err(|_| ReplayV2Error("pipeline-v3 execution rejected"))?;
    let result_bytes = canonical_observer_pipeline_result_v3_bytes(&result)?;
    let bundle = build_hmac_payload_bundle_v2(
        ReplayPayloadKindV2::ObserverPipelineV3,
        &request_bytes,
        &result_bytes,
        signer_label,
        key_id,
        key,
    )?;
    event("pipeline-replay-v3", "build-hmac-exit");
    Ok(bundle)
}

pub fn build_ed25519_observer_pipeline_bundle_v3(
    request: &ObserverSynthesisPipelineRequestV3,
    signer_label: &str,
    signing_key: &SigningKey,
) -> Result<ReplayBundleV2, ReplayV2Error> {
    event("pipeline-replay-v3", "build-ed25519-enter");
    let request_bytes = encode_observer_pipeline_request_v3(request)?;
    let result = run_observer_synthesis_pipeline_v3(request)
        .map_err(|_| ReplayV2Error("pipeline-v3 execution rejected"))?;
    let result_bytes = canonical_observer_pipeline_result_v3_bytes(&result)?;
    let bundle = build_ed25519_payload_bundle_v2(
        ReplayPayloadKindV2::ObserverPipelineV3,
        &request_bytes,
        &result_bytes,
        signer_label,
        signing_key,
    )?;
    event("pipeline-replay-v3", "build-ed25519-exit");
    Ok(bundle)
}

pub(crate) fn validate_pipeline_replay_semantics_v3(
    bundle: &ReplayBundleV2,
    policy: &ReplayTrustPolicyV2,
) -> Result<(), ReplayV2Error> {
    event("pipeline-replay-v3", "validate-enter");
    let request = decode_observer_pipeline_request_v3(&bundle.worker_request)?;
    let rebuilt = run_observer_synthesis_pipeline_v3(&request)
        .map_err(|_| ReplayV2Error("authenticated pipeline-v3 request was rejected"))?;
    if policy.require_ready_receipt && rebuilt.status != PipelineStatusV3::Ready {
        return Err(ReplayV2Error(
            "authenticated pipeline-v3 result is not ready",
        ));
    }
    // PipelineV3 has no independent result decoder: exact regenerated bytes
    // are therefore its mandatory semantic validation, not an optional policy
    // strengthening.  `require_fresh_artifact` remains meaningful for the
    // legacy WorkerV1 payload only.
    if canonical_observer_pipeline_result_v3_bytes(&rebuilt)? != bundle.worker_receipt {
        return Err(ReplayV2Error(
            "authenticated pipeline-v3 result differs from fresh execution",
        ));
    }
    event("pipeline-replay-v3", "validate-exit");
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::observer_worker::{verify_replay_bundle_v2, HmacReplayTrustV2, ReplayTrustPolicyV2};

    #[test]
    fn pipeline_result_comparison_is_mandatory_even_when_legacy_fresh_flag_is_off() {
        let request = ObserverSynthesisPipelineRequestV3 {
            gap_request: ObserverGapRequestV1 {
                task_id: NativePartitionTaskId::OneVsThree,
                grammar_profile_id: ObserverGrammarProfileId::LegacyV1,
                joint_limits: JointSynthesisLimits::default(),
                baselines: vec![NamedObserverBaselineV1 {
                    name: "input".to_owned(),
                    observer_ordinal: 0,
                }],
                policy: ObserverGapPolicyV1::default(),
                information_loss_penalty: 0,
            },
            transports: vec![TransportTermV1 {
                source: FiniteDomainV1::new("pipeline-test-four", 4).unwrap(),
                target: FiniteDomainV1::new("pipeline-test-four", 4).unwrap(),
                op: TransportOpV1::Identity,
            }],
        };
        let request = encode_observer_pipeline_request_v3(&request).unwrap();
        let key_id = [0x55; 32];
        let key = [0x33; 32];
        let bundle = build_hmac_payload_bundle_v2(
            ReplayPayloadKindV2::ObserverPipelineV3,
            &request,
            b"authenticated-but-not-a-canonical-result",
            "mandatory-result-check",
            key_id,
            &key,
        )
        .unwrap();
        let policy = ReplayTrustPolicyV2 {
            allow_hmac_sha256: true,
            allow_ed25519: false,
            require_ready_receipt: false,
            require_fresh_artifact: false,
        };
        assert!(verify_replay_bundle_v2(
            &bundle,
            &policy,
            &HmacReplayTrustV2::new(key_id, &key).unwrap(),
        )
        .is_err());
    }
}
