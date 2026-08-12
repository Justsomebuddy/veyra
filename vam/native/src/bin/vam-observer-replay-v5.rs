//! State-free threshold verifier for one VOR5 package read from standard input.
//!
//! Usage: `verify-threshold <epoch> <threshold> <key-spec>...`, where each
//! key-spec is exactly `64-lowercase-hex:first_epoch:last_epoch`.

use std::env;
use std::io::{self, Read};
use std::process;

use vam_native::observer_worker::{
    decode_autonomous_replay_package_v5, verify_autonomous_replay_package_v5, ReplayTrustKeyV5,
    ReplayTrustPolicyV5, MAX_AUTONOMOUS_REPLAY_V5_BYTES, MAX_REPLAY_TRUST_KEYS_V5,
};

fn debug(code: &'static str) {
    if env::var("VEYRA_NATIVE_DEBUG")
        .map(|value| matches!(value.as_str(), "1" | "true" | "TRUE" | "yes" | "YES"))
        .unwrap_or(false)
    {
        eprintln!("[veyra-native][observer-replay-v5] {code}");
    }
}

fn parse_u64(text: &str) -> Result<u64, &'static str> {
    debug("CLI_V5_U64_ENTER");
    if text.is_empty()
        || text.len() > 20
        || (text.len() > 1 && text.starts_with('0'))
        || !text.bytes().all(|byte| byte.is_ascii_digit())
    {
        debug("CLI_V5_U64_REJECT");
        return Err("number-shape");
    }
    let value = text.parse().map_err(|_| "number-shape")?;
    debug("CLI_V5_U64_EXIT");
    Ok(value)
}

fn parse_key(specification: &str) -> Result<ReplayTrustKeyV5, &'static str> {
    debug("CLI_V5_KEY_ENTER");
    if specification.len() > 96 {
        debug("CLI_V5_KEY_REJECT");
        return Err("key-spec-shape");
    }
    let parts = specification.split(':').collect::<Vec<_>>();
    let [hex, from, through] = parts.as_slice() else {
        debug("CLI_V5_KEY_REJECT");
        return Err("key-spec-shape");
    };
    if hex.len() != 64
        || !hex
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        debug("CLI_V5_KEY_REJECT");
        return Err("key-spec-shape");
    }
    let mut public_key = [0u8; 32];
    for (index, slot) in public_key.iter_mut().enumerate() {
        *slot =
            u8::from_str_radix(&hex[index * 2..index * 2 + 2], 16).map_err(|_| "key-spec-shape")?;
    }
    let key = ReplayTrustKeyV5::new(public_key, parse_u64(from)?, parse_u64(through)?)
        .map_err(|_| "key-spec-invalid")?;
    debug("CLI_V5_KEY_EXIT");
    Ok(key)
}

fn run() -> Result<(), &'static str> {
    debug("CLI_V5_ENTER");
    let arguments = env::args().collect::<Vec<_>>();
    if arguments.len() < 5
        || arguments[1] != "verify-threshold"
        || arguments.len() - 4 > MAX_REPLAY_TRUST_KEYS_V5
    {
        debug("CLI_V5_USAGE_REJECT");
        return Err("usage");
    }
    let epoch = parse_u64(&arguments[2])?;
    let threshold_u64 = parse_u64(&arguments[3])?;
    let threshold = u8::try_from(threshold_u64).map_err(|_| "threshold-shape")?;
    let keys = arguments[4..]
        .iter()
        .map(|value| parse_key(value))
        .collect::<Result<Vec<_>, _>>()?;
    let policy = ReplayTrustPolicyV5::new(epoch, threshold, keys).map_err(|_| "policy-invalid")?;
    let mut bytes = Vec::new();
    io::stdin()
        .take((MAX_AUTONOMOUS_REPLAY_V5_BYTES + 1) as u64)
        .read_to_end(&mut bytes)
        .map_err(|_| "package-read-blocked")?;
    if bytes.len() > MAX_AUTONOMOUS_REPLAY_V5_BYTES {
        return Err("package-size");
    }
    let package =
        decode_autonomous_replay_package_v5(&bytes).map_err(|_| "package-decode-blocked")?;
    verify_autonomous_replay_package_v5(&package, &policy)
        .map_err(|_| "package-verification-blocked")?;
    println!("verified");
    debug("CLI_V5_EXIT");
    Ok(())
}

fn main() {
    debug("CLI_V5_MAIN_ENTER");
    if let Err(reason) = run() {
        debug("CLI_V5_MAIN_REJECT");
        eprintln!("vam-observer-replay-v5 blocked: {reason}");
        process::exit(1);
    }
    debug("CLI_V5_MAIN_EXIT");
}
