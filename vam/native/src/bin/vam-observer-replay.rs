//! Independent Ed25519 verifier for one bounded VOR2 bundle read from stdin.

use std::env;
use std::io;
use std::process;

use vam_native::observer_worker::{
    decode_replay_bundle_v2_exact, verify_replay_bundle_v2, Ed25519ReplayTrustV2,
    ReplayTrustPolicyV2,
};

fn debug(code: &'static str) {
    if env::var("VEYRA_NATIVE_DEBUG")
        .map(|value| matches!(value.as_str(), "1" | "true" | "TRUE" | "yes" | "YES"))
        .unwrap_or(false)
    {
        eprintln!("[veyra-native][observer-replay] {code}");
    }
}

fn decode_public_key(text: &str) -> Result<[u8; 32], &'static str> {
    debug("PUBLIC_KEY_DECODE_ENTER");
    if text.len() != 64 || !text.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        debug("PUBLIC_KEY_DECODE_REJECT");
        return Err("public-key-shape");
    }
    let mut result = [0u8; 32];
    for (index, slot) in result.iter_mut().enumerate() {
        *slot = u8::from_str_radix(&text[index * 2..index * 2 + 2], 16)
            .map_err(|_| "public-key-shape")?;
    }
    debug("PUBLIC_KEY_DECODE_EXIT");
    Ok(result)
}

fn run() -> Result<(), &'static str> {
    debug("REPLAY_CLI_ENTER");
    let args = env::args().collect::<Vec<_>>();
    if args.len() != 3 || args[1] != "verify-ed25519" {
        debug("REPLAY_CLI_REJECT");
        return Err("usage");
    }
    let public_key = decode_public_key(&args[2])?;
    let trust = Ed25519ReplayTrustV2::new(public_key).map_err(|_| "public-key-invalid")?;
    let bundle =
        decode_replay_bundle_v2_exact(&mut io::stdin()).map_err(|_| "bundle-decode-blocked")?;
    verify_replay_bundle_v2(&bundle, &ReplayTrustPolicyV2::ed25519_only(), &trust)
        .map_err(|_| "bundle-verification-blocked")?;
    println!("verified");
    debug("REPLAY_CLI_EXIT");
    Ok(())
}

fn main() {
    debug("MAIN_ENTER");
    if let Err(reason) = run() {
        debug("MAIN_REJECT");
        eprintln!("vam-observer-replay blocked: {reason}");
        process::exit(1);
    }
    debug("MAIN_EXIT");
}
