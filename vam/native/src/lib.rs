mod dense;
mod frame;
mod intrinsic_json;
mod intrinsic_reader;
mod intrinsic_support;
#[cfg(test)]
mod intrinsic_tests;
mod intrinsic_types;
mod json;
pub mod observer_synthesis;
mod optimizer;
mod payload;
mod runtime;

pub use frame::{encode_vam0_frame, EncodedVam0Frame};
pub use intrinsic_json::{intrinsic_error_json, intrinsic_success_json};
pub use intrinsic_reader::inspect_vami;
pub use intrinsic_types::{IntrinsicFrameReport, IntrinsicNode};
pub use json::{error_json, success_json};
pub use optimizer::{
    optimize_observer_alias, optimize_slice, optimizer_report_json, optimizer_slice_json,
    OptimizationReport, OptimizationRow, OptimizedFrameEmission,
};
use payload::parse_payload;

const MAGIC: &[u8; 4] = b"VAM0";
const VERSION: u16 = 1;
const HEADER_LEN: usize = 14;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Instruction {
    pub op: String,
    pub args: Vec<WireArg>,
    pub line: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum WireArg {
    Int(i64),
    Reg(i64),
    Str(String),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FrameReport {
    pub magic: &'static str,
    pub version: u16,
    pub size: u32,
    pub crc32: u32,
    pub instructions: Vec<Instruction>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VamError {
    pub kind: &'static str,
    pub message: String,
}

impl VamError {
    pub(crate) fn new(kind: &'static str, message: impl Into<String>) -> Self {
        Self {
            kind,
            message: message.into(),
        }
    }
}

pub fn inspect_vam0(bytes: &[u8]) -> Result<FrameReport, VamError> {
    if bytes.len() < HEADER_LEN {
        return Err(VamError::new("short_frame", "short VAM0 frame"));
    }
    if &bytes[0..4] != MAGIC {
        return Err(VamError::new("magic", "bad VAM0 magic"));
    }
    let version = u16::from_be_bytes([bytes[4], bytes[5]]);
    if version != VERSION {
        return Err(VamError::new(
            "version",
            format!("unsupported VAM0 version: {version}"),
        ));
    }
    let size = u32::from_be_bytes([bytes[6], bytes[7], bytes[8], bytes[9]]);
    let crc32 = u32::from_be_bytes([bytes[10], bytes[11], bytes[12], bytes[13]]);
    let payload = &bytes[HEADER_LEN..];
    if payload.len() != size as usize {
        return Err(VamError::new("length", "VAM0 payload length mismatch"));
    }
    if crc32_ieee(payload) != crc32 {
        return Err(VamError::new("crc32", "VAM0 checksum mismatch"));
    }
    let text =
        std::str::from_utf8(payload).map_err(|_| VamError::new("payload", "bad VAM0 payload"))?;
    let instructions = parse_payload(text)?;
    Ok(FrameReport {
        magic: "VAM0",
        version,
        size,
        crc32,
        instructions,
    })
}

pub fn inspect_vamdense(bytes: &[u8]) -> Result<FrameReport, VamError> {
    dense::inspect_vamdense(bytes)
}

fn crc32_ieee(bytes: &[u8]) -> u32 {
    let mut crc = 0xffff_ffffu32;
    for &b in bytes {
        crc ^= b as u32;
        for _ in 0..8 {
            crc = if crc & 1 != 0 {
                (crc >> 1) ^ 0xedb8_8320
            } else {
                crc >> 1
            };
        }
    }
    !crc
}

#[cfg(test)]
mod tests {
    use super::*;

    #[rustfmt::skip]
    fn frame_bytes(payload: &str) -> Vec<u8> { let mut bytes = Vec::with_capacity(HEADER_LEN + payload.len()); bytes.extend_from_slice(MAGIC); bytes.extend_from_slice(&VERSION.to_be_bytes()); bytes.extend_from_slice(&(payload.len() as u32).to_be_bytes()); bytes.extend_from_slice(&crc32_ieee(payload.as_bytes()).to_be_bytes()); bytes.extend_from_slice(payload.as_bytes()); bytes }

    #[rustfmt::skip]
    fn bad_report() -> FrameReport { FrameReport { magic: "VAM0", version: 1, size: 0, crc32: 0, instructions: vec![Instruction { op: "REZ".into(), args: vec![WireArg::Str("dst".into()), WireArg::Str("root".into())], line: 9 }] } }

    #[test]
    fn inspect_vam0_round_trips_and_success_json_executes() {
        let payload =
            r#"[{"op":"REZ","line":7,"args":[{"t":"reg","v":1},{"t":"str","v":"root"}]}]"#;
        let report = inspect_vam0(&frame_bytes(payload)).unwrap();
        assert_eq!(report.version, 1);
        assert_eq!(report.instructions[0].op, "REZ");
        let json = success_json(&report);
        assert!(json.contains("\"ok\":true"));
        assert!(json.contains("\"instruction_count\":1"));
        assert!(json.contains("\"pc\":1"));
        assert!(json.contains("\"registers\":{\"%r1\""));
    }

    #[test]
    fn success_json_surfaces_executor_errors_at_boundary() {
        let json = success_json(&bad_report());
        assert!(json.contains("\"execution_error\""));
        assert!(json.contains("first operand must be destination register"));
    }
}
