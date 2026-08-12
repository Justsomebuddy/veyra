//! Fixed native observer worker and parent supervisor entrypoint.

use std::{env, path::Path, process};
use vam_native::observer_worker::{
    encode_worker_receipt_frame, run_child_entry, supervise_current_executable,
    NativeWorkerRequestV1,
};

fn main() {
    let args = env::args().collect::<Vec<_>>();
    let result = if args.len() == 2 && args[1] == "--child" {
        run_child_entry().map(|_| Vec::new())
    } else if args.len() == 1 {
        let executable = env::current_exe().map_err(|_| "current-executable");
        executable
            .map_err(|reason| vam_native::observer_worker::NativeWorkerError { reason })
            .and_then(|path| {
                supervise_current_executable(Path::new(&path), &NativeWorkerRequestV1::default())
            })
            .and_then(|receipt| {
                encode_worker_receipt_frame(&receipt)
                    .map_err(|reason| vam_native::observer_worker::NativeWorkerError { reason })
            })
    } else {
        Err(vam_native::observer_worker::NativeWorkerError { reason: "usage" })
    };
    match result {
        Ok(bytes) => {
            if !bytes.is_empty() {
                use std::io::Write;
                if std::io::stdout().write_all(&bytes).is_err() {
                    process::exit(74);
                }
            }
        }
        Err(error) => {
            eprintln!("vam-observer-worker blocked: {}", error.reason);
            process::exit(1);
        }
    }
}
