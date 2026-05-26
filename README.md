# Quantum Tamper-Evident QR Codes

A QR code system that uses true quantum randomness for nonce generation and (planned) the Deutsch-Jozsa algorithm for single-query tamper verification. Built with Qiskit.

> **Status:** In development — Day 2 of 21 complete. Quantum RNG module ready and validated; tamper-verification pipeline coming.

## Motivation

Standard QR codes are vulnerable to physical swap attacks (common in payment fraud) and digital tampering. This project explores whether quantum primitives can strengthen QR integrity:

- **True randomness** — Nonces come from quantum measurements (Hadamard + measure), not pseudo-random functions, so they cannot be reproduced from a seed.
- **Single-query verification (planned)** — A Deutsch-Jozsa oracle will let a verifier detect tampering in one quantum query instead of recomputing a full hash.

This is primarily a learning and engineering exploration. A classical HMAC achieves tamper detection with less complexity; the value here is in implementing real quantum algorithms end-to-end and running them on actual quantum hardware.

## What's working today

**Quantum Random Number Generator** (`quantum_qr/qrng.py`)
- 128-qubit parallel Hadamard circuit, single-shot measurement
- Returns binary or hex nonces of arbitrary length
- Validated for uniformity with chi-square test (p = 0.XX on 10,000 bits)  ← *replace with your value*
- Side-by-side comparison with Python's `random.getrandbits` in the notebook

## Project structure

```
quantum-tamper-evident-qr/
├── quantum_qr/
│   ├── __init__.py
│   └── qrng.py                       # Quantum random number generator
├── notebooks/
│   ├── day1_qrng.ipynb               # First random bit + Hadamard intuition
│   └── day2_qrng_scaling.ipynb       # 128-bit scaling + statistical validation
├── tests/
│   └── test_qrng.py
├── data/
│   └── sample_nonce.txt
└── README.md
```

## Installation

Requires Python 3.10 or newer.

```bash
git clone https://github.com/YOUR_USERNAME/quantum-tamper-evident-qr.git
cd quantum-tamper-evident-qr
pip install qiskit qiskit-aer qrcode[pil] numpy matplotlib pylatexenc jupyter pytest scipy
```

## Quick start

```python
from quantum_qr.qrng import generate_quantum_random_bits, generate_quantum_nonce_hex

# 128-bit binary string from quantum measurements
bits = generate_quantum_random_bits(128)
print(bits)

# Or as a hex nonce, ready for storage in a QR payload
nonce = generate_quantum_nonce_hex(128)
print(nonce)  # 32 hex characters
```

## Validation results

Quantum bits generated from a 128-qubit Hadamard circuit on `aer_simulator`:

| Metric | Result |
|---|---|
| Total bits tested | 10,000 |
| Count of 0s / 1s | XXXX / XXXX  ← *fill in* |
| Chi-square p-value | 0.XX           ← *fill in* |

Notebook: `notebooks/day2_qrng_scaling.ipynb` — includes histograms, circuit diagram, and a contrast with pseudo-random output.

## Roadmap

- [x] **Day 1** — Environment setup, first quantum random bit
- [x] **Day 2** — 128-bit QRNG module, statistical validation
- [ ] **Day 3–4** — Deutsch-Jozsa circuit (constant and balanced oracles)
- [ ] **Day 5–6** — QR payload format design
- [ ] **Day 7–11** — Generator module: combines QRNG + DJ oracle + QR image
- [ ] **Day 12–16** — Verifier module: reads QR and runs DJ check
- [ ] **Day 17–18** — Execution on real IBM Quantum hardware + noise benchmarks
- [ ] **Day 19–21** — Polish, CLI, final documentation

## References

- Deutsch, D. & Jozsa, R. (1992). Rapid solutions of problems by quantum computation. *Proc. R. Soc. Lond. A* 439, 553–558.
- Nielsen, M. & Chuang, I. *Quantum Computation and Quantum Information.*
- [Qiskit Documentation](https://docs.quantum.ibm.com/)

## License

MIT
