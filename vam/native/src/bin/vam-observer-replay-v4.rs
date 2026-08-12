//! State-free Ed25519 verifier for one exact VOR4 package from standard input.

use std::env;
use std::io;
use std::process;

use vam_native::observer_worker::{
    decode_autonomous_replay_package_v4, verify_autonomous_replay_package_v4,
};

fn debug(code: &'static str) {
    if env::var("VEYRA_NATIVE_DEBUG")
        .map(|value| matches!(value.as_str(), "1" | "true" | "TRUE" | "yes" | "YES"))
        .unwrap_or(false)
    {
        eprintln!("[veyra-native][observer-replay-v4] {code}");
    }
}

fn decode_public_key(text: &str) -> Result<[u8; 32], &'static str> {
    debug("PUBLIC_KEY_DECODE_ENTER");
    if text.len() != 64 || !text.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        debug("PUBLIC_KEY_DECODE_REJECT");
        return Err("public-key-shape");
    }
    let mut result = [0; 32];
    for (index, slot) in result.iter_mut().enumerate() {
        *slot = u8::from_str_radix(&text[index * 2..index * 2 + 2], 16)
            .map_err(|_| "public-key-shape")?;
    }
    debug("PUBLIC_KEY_DECODE_EXIT");
    Ok(result)
}

fn run() -> Result<(), &'static str> {
    debug("CLI_ENTER");
    let args = env::args().collect::<Vec<_>>();
    if args.len() != 3 || args[1] != "verify-ed25519" {
        debug("CLI_USAGE_REJECT");
        return Err("usage");
    }
    let key = decode_public_key(&args[2])?;
    let package = decode_autonomous_replay_package_v4(&mut io::stdin())
        .map_err(|_| "package-decode-blocked")?;
    verify_autonomous_replay_package_v4(&package, key)
        .map_err(|_| "package-verification-blocked")?;
    println!("verified");
    debug("CLI_EXIT");
    Ok(())
}

fn main() {
    debug("MAIN_ENTER");
    if let Err(reason) = run() {
        debug("MAIN_REJECT");
        eprintln!("vam-observer-replay-v4 blocked: {reason}");
        process::exit(1);
    }
    debug("MAIN_EXIT");
}
