# Quantum Tamper-Evident QR Codes

A QR code system that uses true quantum randomness for nonce generation and the Deutsch-Jozsa algorithm for single-query tamper verification. Built with Qiskit.

> **Status:** In development — Day 6 of 21 complete. All quantum/classical building blocks, the design, and the full classical payload layer (HMAC tag + encode/decode + tamper bridge) are working. Tamper detection is already demonstrable classically; the quantum verification layer is wired in next.

## Motivation

Standard QR codes are vulnerable to physical swap attacks (common in payment fraud) and digital tampering. This project explores whether quantum primitives can strengthen QR integrity:

- **True randomness** — Nonces come from quantum measurements (Hadamard + measure), not pseudo-random functions, so they cannot be reproduced from a seed.
- **Single-query verification** — A Deutsch-Jozsa oracle lets a verifier detect tampering in one quantum query: untampered → constant oracle → measures all zeros; tampered → balanced oracle → measures non-zero.

This is primarily a learning and engineering exploration. A classical HMAC achieves tamper detection with less complexity; the value here is in implementing real quantum algorithms end-to-end and running them on actual quantum hardware.

## Design

The full payload schema, threat model, generate/verify flows, and limitations are documented in [`DESIGN.md`](DESIGN.md). In short:

- QR payload is a base64-encoded JSON object: `{version, data, nonce, tag}`
- `nonce` is 128 bits from the quantum RNG
- `tag` is an HMAC-SHA256(K, data || nonce) truncated to **n = 8 bits**
- Verification: recompute the expected tag, XOR with the observed tag to get a secret `s`, build `oracle_from_secret(s)`, run DJ
- Authentic QR → s = 0 → constant oracle → DJ measures zeros
- Tampered QR → s ≠ 0 → balanced oracle → DJ measures the differing bits

## What's working today

**Quantum Random Number Generator** (`quantum_qr/qrng.py`)
- 128-qubit parallel Hadamard circuit, single-shot measurement
- Returns binary or hex nonces of arbitrary length
- Validated for uniformity with chi-square test (p = 0.XX on 10,000 bits)  ← *replace with your value*

**Deutsch-Jozsa Circuit — Constant & Balanced** (`quantum_qr/dj.py`)
- `build_dj_circuit(oracle, n)` wraps any n-bit oracle into the full DJ circuit
- `constant_oracle_zero/one`, `balanced_oracle`, and `oracle_from_secret(s)`
- `oracle_from_secret` unifies constant (s = 0) and balanced (s ≠ 0); DJ recovers s in one query (Bernstein-Vazirani behavior)

**Classical QR Pipeline** (`quantum_qr/qr_io.py`)
- `make_qr(data, path)` / `read_qr(path)` — lossless encode/decode via `qrcode` and OpenCV

**Payload Layer** (`quantum_qr/payload.py`, `quantum_qr/config.py`)
- `compute_tag(key, data, nonce, n_bits)` — HMAC-SHA256 truncated to n bits
- `build_payload` / `encode_payload` / `decode_payload` — schema ↔ base64 JSON
- `tags_to_secret(observed, expected)` — XOR bridge that feeds DJ's oracle
- `get_key()` — key via `QTQR_KEY` env var with a documented demo fallback
- **Tamper detection already verified end-to-end classically** (authentic → all zeros, tampered → non-zero)

## Project structure

```
quantum-tamper-evident-qr/
├── quantum_qr/
│   ├── __init__.py
│   ├── qrng.py                       # Quantum random number generator
│   ├── dj.py                         # Deutsch-Jozsa circuit + oracles
│   ├── qr_io.py                      # Classical QR encode/decode
│   ├── payload.py                    # HMAC tag, payload encode/decode, tags-to-secret
│   └── config.py                     # Shared-key handling
├── notebooks/
│   ├── day1_qrng.ipynb
│   ├── day2_qrng_scaling.ipynb
│   ├── day3_dj_constant.ipynb
│   ├── day4_dj_balanced_and_qr.ipynb
│   └── day6_payload.ipynb            # Classical tamper-detection demo
├── tests/
│   ├── test_qrng.py
│   ├── test_dj.py
│   ├── test_qr_io.py
│   └── test_payload.py
├── data/
│   ├── sample_nonce.txt
│   └── design_sketch.jpg
├── DESIGN.md                         # Threat model, schema, flows, limitations
├── LEARNINGS.md                      # Daily learning log
└── README.md
```

## Installation

Requires Python 3.10 or newer.

```bash
git clone https://github.com/YOUR_USERNAME/quantum-tamper-evident-qr.git
cd quantum-tamper-evident-qr
pip install qiskit qiskit-aer qrcode[pil] opencv-python numpy matplotlib pylatexenc jupyter pytest scipy
```

## Quick start

```python
from quantum_qr.qrng import generate_quantum_nonce_hex
from quantum_qr.payload import compute_tag, build_payload, encode_payload, decode_payload, tags_to_secret
from quantum_qr.config import get_key

key = get_key()
data = "pay alice $10"
nonce = generate_quantum_nonce_hex(128)

# Issue a payload
tag = compute_tag(key, data, nonce, n_bits=8)
qr_string = encode_payload(build_payload(data, nonce, tag))

# Verify a payload (classical half)
p = decode_payload(qr_string)
expected = compute_tag(key, p["data"], p["nonce"], n_bits=8)
secret = tags_to_secret(p["tag"], expected)
print(secret)  # '00000000' if authentic, non-zero if tampered
```

The `secret` above is exactly what gets fed into `oracle_from_secret` for the quantum verification step (coming next).

## Validation results

**Quantum RNG** (`aer_simulator`, 128-qubit Hadamard circuit):

| Metric | Result |
|---|---|
| Total bits tested | 10,000 |
| Count of 0s / 1s | XXXX / XXXX  ← *fill in* |
| Chi-square p-value | 0.XX           ← *fill in* |

**Deutsch-Jozsa** (n = 4, 1024 shots each):

| Oracle | Measurement | Frequency |
|---|---|---|
| `constant_oracle_zero` | `'0000'` | 100% |
| `constant_oracle_one`  | `'0000'` | 100% |
| `balanced_oracle`      | non-zero | 100% |
| `oracle_from_secret("1010")` | `'1010'` (recovered) | 100% |

**Classical tamper detection:** authentic payload → `tags_to_secret` returns all zeros; tampered payload → non-zero. Verified in `notebooks/day6_payload.ipynb`.

## Roadmap

- [x] **Day 1** — Environment setup, first quantum random bit
- [x] **Day 2** — 128-bit QRNG module, statistical validation
- [x] **Day 3** — Deutsch-Jozsa circuit (constant oracles)
- [x] **Day 4** — DJ balanced oracles, secret recovery, QR encode/decode pipeline
- [x] **Day 5** — Payload schema, threat model, verify-flow design (`DESIGN.md`)
- [x] **Day 6** — Payload encode/decode, HMAC tag, tamper bridge (classical detection working)
- [ ] **Day 7–11** — Generator module: combines QRNG + HMAC + QR image into one `generate()`
- [ ] **Day 12–16** — Verifier module: reads QR and runs the DJ check on quantum hardware/simulator
- [ ] **Day 17–18** — Execution on real IBM Quantum hardware + noise benchmarks
- [ ] **Day 19–21** — Polish, CLI, final documentation

## References

- Deutsch, D. & Jozsa, R. (1992). Rapid solutions of problems by quantum computation. *Proc. R. Soc. Lond. A* 439, 553–558.
- Bernstein, E. & Vazirani, U. (1997). Quantum complexity theory. *SIAM J. Comput.* 26(5), 1411–1473.
- Nielsen, M. & Chuang, I. *Quantum Computation and Quantum Information.*
- [Qiskit Documentation](https://docs.quantum.ibm.com/)

## License

MIT