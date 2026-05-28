# Quantum Tamper-Evident QR Codes

A QR code system that uses true quantum randomness for nonce generation and the Deutsch-Jozsa algorithm for single-query tamper verification. Built with Qiskit.

> **Status:** In development — Day 4 of 21 complete. Quantum RNG, Deutsch-Jozsa (constant + balanced), and the classical QR encode/decode pipeline are all working. Payload design, full generator/verifier, and hardware execution coming.

## Motivation

Standard QR codes are vulnerable to physical swap attacks (common in payment fraud) and digital tampering. This project explores whether quantum primitives can strengthen QR integrity:

- **True randomness** — Nonces come from quantum measurements (Hadamard + measure), not pseudo-random functions, so they cannot be reproduced from a seed.
- **Single-query verification** — A Deutsch-Jozsa oracle lets a verifier detect tampering in one quantum query: untampered → constant oracle → measures all zeros; tampered → balanced oracle → measures non-zero.

This is primarily a learning and engineering exploration. A classical HMAC achieves tamper detection with less complexity; the value here is in implementing real quantum algorithms end-to-end and running them on actual quantum hardware.

## What's working today

**Quantum Random Number Generator** (`quantum_qr/qrng.py`)
- 128-qubit parallel Hadamard circuit, single-shot measurement
- Returns binary or hex nonces of arbitrary length
- Validated for uniformity with chi-square test (p = 0.XX on 10,000 bits)  ← *replace with your value*
- Side-by-side comparison with Python's `random.getrandbits` in the notebook

**Deutsch-Jozsa Circuit — Constant & Balanced** (`quantum_qr/dj.py`)
- General-purpose `build_dj_circuit(oracle, n)` that wraps any n-bit oracle into the full DJ circuit
- `constant_oracle_zero(n)` / `constant_oracle_one(n)` — constant cases (DJ measures all zeros)
- `balanced_oracle(n)` — parity oracle (DJ measures non-zero)
- `oracle_from_secret(s)` — computes f(x) = s·x mod 2; unifies constant (s = 0) and balanced (s ≠ 0), and DJ recovers the secret s in a single query (the Bernstein-Vazirani behavior)

**Classical QR Pipeline** (`quantum_qr/qr_io.py`)
- `make_qr(data, path)` — encode any string into a QR image (via `qrcode`)
- `read_qr(path)` — decode a QR image back to its string (via OpenCV's `QRCodeDetector`)
- Verified lossless round-trip encode → decode

## Project structure

```
quantum-tamper-evident-qr/
├── quantum_qr/
│   ├── __init__.py
│   ├── qrng.py                       # Quantum random number generator
│   ├── dj.py                         # Deutsch-Jozsa circuit + oracles (constant, balanced, secret)
│   └── qr_io.py                      # Classical QR encode/decode
├── notebooks/
|   ├── data/
│   |   ├──  sample_nonce.txt
|   |   ├──  test_qr.png
│   ├── day1_qrng.ipynb               # First random bit + Hadamard intuition
│   ├── day2_qrng_scaling.ipynb       # 128-bit scaling + statistical validation
│   ├── day3_dj_constant.ipynb        # Deutsch-Jozsa, constant case
│   └── day4_dj_balanced_and_qr.ipynb # Balanced oracles, secret recovery, QR round-trip
├── tests/
│   ├── test_qrng.py
│   ├── test_dj.py
│   ├── test_qr_io.py
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
from quantum_qr.dj import build_dj_circuit, oracle_from_secret
from quantum_qr.qr_io import make_qr, read_qr
from qiskit_aer import AerSimulator

# 1. Generate a 128-bit quantum-random nonce
nonce = generate_quantum_nonce_hex(128)
print(nonce)  # 32 hex characters

# 2. DJ recovers a secret string in a single query (Bernstein-Vazirani behavior)
secret = "1010"
dj_circuit = build_dj_circuit(oracle_from_secret(secret), n=len(secret))
counts = AerSimulator().run(dj_circuit, shots=1024).result().get_counts()
print(counts)  # {'1010': 1024} (mind bit ordering)

# 3. Classical QR round-trip
make_qr("hello quantum world", "data/test_qr.png")
print(read_qr("data/test_qr.png"))  # "hello quantum world"
```

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

**Classical QR:** lossless encode → decode round-trip verified.

Notebooks contain histograms, circuit diagrams, and additional analysis.

## Roadmap

- [x] **Day 1** — Environment setup, first quantum random bit
- [x] **Day 2** — 128-bit QRNG module, statistical validation
- [x] **Day 3** — Deutsch-Jozsa circuit (constant oracles)
- [x] **Day 4** — DJ balanced oracles, secret recovery, QR encode/decode pipeline
- [ ] **Day 5–6** — QR payload format design
- [ ] **Day 7–11** — Generator module: combines QRNG + DJ oracle + QR image
- [ ] **Day 12–16** — Verifier module: reads QR and runs DJ check
- [ ] **Day 17–18** — Execution on real IBM Quantum hardware + noise benchmarks
- [ ] **Day 19–21** — Polish, CLI, final documentation

## References

- Deutsch, D. & Jozsa, R. (1992). Rapid solutions of problems by quantum computation. *Proc. R. Soc. Lond. A* 439, 553–558.
- Bernstein, E. & Vazirani, U. (1997). Quantum complexity theory. *SIAM J. Comput.* 26(5), 1411–1473.
- Nielsen, M. & Chuang, I. *Quantum Computation and Quantum Information.*
- [Qiskit Documentation](https://docs.quantum.ibm.com/)

## License

MIT