//! Small dependency-free SHA-256 and HMAC-SHA256 for worker evidence binding.

use super::event;

const INITIAL: [u32; 8] = [
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
];
const K: [u32; 64] = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
];

pub(super) fn sha256(data: &[u8]) -> [u8; 32] {
    event("DIGEST_ENTER", "hashing bounded bytes");
    let bit_len = (data.len() as u64).wrapping_mul(8);
    let mut padded = Vec::with_capacity((data.len() + 72) & !63);
    padded.extend_from_slice(data);
    padded.push(0x80);
    while padded.len() % 64 != 56 {
        padded.push(0);
    }
    padded.extend_from_slice(&bit_len.to_be_bytes());
    let mut state = INITIAL;
    for chunk in padded.chunks_exact(64) {
        let mut words = [0u32; 64];
        for (index, word) in chunk.chunks_exact(4).enumerate() {
            words[index] = u32::from_be_bytes([word[0], word[1], word[2], word[3]]);
        }
        for index in 16..64 {
            let s0 = words[index - 15].rotate_right(7)
                ^ words[index - 15].rotate_right(18)
                ^ (words[index - 15] >> 3);
            let s1 = words[index - 2].rotate_right(17)
                ^ words[index - 2].rotate_right(19)
                ^ (words[index - 2] >> 10);
            words[index] = words[index - 16]
                .wrapping_add(s0)
                .wrapping_add(words[index - 7])
                .wrapping_add(s1);
        }
        let [mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut h] = state;
        for index in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let choice = (e & f) ^ ((!e) & g);
            let first = h
                .wrapping_add(s1)
                .wrapping_add(choice)
                .wrapping_add(K[index])
                .wrapping_add(words[index]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let majority = (a & b) ^ (a & c) ^ (b & c);
            let second = s0.wrapping_add(majority);
            h = g;
            g = f;
            f = e;
            e = d.wrapping_add(first);
            d = c;
            c = b;
            b = a;
            a = first.wrapping_add(second);
        }
        for (slot, value) in state.iter_mut().zip([a, b, c, d, e, f, g, h]) {
            *slot = slot.wrapping_add(value);
        }
    }
    let mut output = [0u8; 32];
    for (target, word) in output.chunks_exact_mut(4).zip(state) {
        target.copy_from_slice(&word.to_be_bytes());
    }
    event("DIGEST_EXIT", "bounded bytes hashed");
    output
}

pub(super) fn domain_sha256(domain: &[u8], payload: &[u8]) -> [u8; 32] {
    event("DOMAIN_DIGEST_ENTER", "hashing domain-separated bytes");
    let mut framed = Vec::with_capacity(domain.len() + payload.len() + 1);
    framed.extend_from_slice(domain);
    framed.push(0);
    framed.extend_from_slice(payload);
    let result = sha256(&framed);
    event("DOMAIN_DIGEST_EXIT", "domain-separated bytes hashed");
    result
}

pub(super) fn hmac_sha256(key: &[u8], message: &[u8]) -> [u8; 32] {
    event(
        "HMAC_ENTER",
        "authenticating bounded digest without logging key material",
    );
    let mut block = [0u8; 64];
    if key.len() > block.len() {
        block[..32].copy_from_slice(&sha256(key));
    } else {
        block[..key.len()].copy_from_slice(key);
    }
    let mut inner = Vec::with_capacity(64 + message.len());
    inner.extend(block.iter().map(|byte| byte ^ 0x36));
    inner.extend_from_slice(message);
    let inner_digest = sha256(&inner);
    let mut outer = Vec::with_capacity(96);
    outer.extend(block.iter().map(|byte| byte ^ 0x5c));
    outer.extend_from_slice(&inner_digest);
    let result = sha256(&outer);
    block.fill(0);
    inner.fill(0);
    outer.fill(0);
    event("HMAC_EXIT", "bounded digest authenticated");
    result
}

pub(super) fn constant_time_eq(left: &[u8], right: &[u8]) -> bool {
    event(
        "CONSTANT_TIME_COMPARE_ENTER",
        "comparing fixed authentication bytes",
    );
    if left.len() != right.len() {
        event(
            "CONSTANT_TIME_COMPARE_REJECT",
            "authentication byte lengths differ",
        );
        return false;
    }
    let mut difference = 0u8;
    for (left, right) in left.iter().zip(right) {
        difference |= left ^ right;
    }
    let result = difference == 0;
    event(
        "CONSTANT_TIME_COMPARE_EXIT",
        "fixed authentication bytes compared",
    );
    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn standard_sha_and_hmac_vectors() {
        assert_eq!(
            sha256(b"abc"),
            [
                0xba, 0x78, 0x16, 0xbf, 0x8f, 0x01, 0xcf, 0xea, 0x41, 0x41, 0x40, 0xde, 0x5d, 0xae,
                0x22, 0x23, 0xb0, 0x03, 0x61, 0xa3, 0x96, 0x17, 0x7a, 0x9c, 0xb4, 0x10, 0xff, 0x61,
                0xf2, 0x00, 0x15, 0xad
            ]
        );
        assert_eq!(
            hmac_sha256(b"key", b"The quick brown fox jumps over the lazy dog"),
            [
                0xf7, 0xbc, 0x83, 0xf4, 0x30, 0x53, 0x84, 0x24, 0xb1, 0x32, 0x98, 0xe6, 0xaa, 0x6f,
                0xb1, 0x43, 0xef, 0x4d, 0x59, 0xa1, 0x49, 0x46, 0x17, 0x59, 0x97, 0x47, 0x9d, 0xbc,
                0x2d, 0x1a, 0x3c, 0xd8
            ]
        );
        assert_eq!(
            hmac_sha256(
                &[0xaa; 131],
                b"Test Using Larger Than Block-Size Key - Hash Key First",
            ),
            [
                0x60, 0xe4, 0x31, 0x59, 0x1e, 0xe0, 0xb6, 0x7f, 0x0d, 0x8a, 0x26, 0xaa, 0xcb, 0xf5,
                0xb7, 0x7f, 0x8e, 0x0b, 0xc6, 0x21, 0x37, 0x28, 0xc5, 0x14, 0x05, 0x46, 0x04, 0x0f,
                0x0e, 0xe3, 0x7f, 0x54,
            ]
        );
    }
}
