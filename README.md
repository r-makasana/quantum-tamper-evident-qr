# Quantum Tamper-Evident QR Codes

A QR code system that uses true quantum randomness for nonce generation and the Deutsch-Jozsa algorithm for single-query tamper verification. Built with Qiskit.

> **Status:** In development — Day 3 of 21 complete. Quantum RNG and Deutsch-Jozsa (constant case) modules ready; balanced oracle, full QR pipeline, and hardware execution coming.

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

**Deutsch-Jozsa Circuit — Constant Case** (`quantum_qr/dj.py`)
- General-purpose `build_dj_circuit(oracle, n)` that wraps any n-bit oracle into the full DJ circuit
- `constant_oracle_zero(n)` and `constant_oracle_one(n)` for both constant cases
- Verified: constant oracles produce `'0...0'` measurements with 100% probability over 1024 shots
- Day 4 will add balanced oracles and demonstrate the tamper-detection direction

## Project structure

```
quantum-tamper-evident-qr/
├── quantum_qr/
│   ├── __init__.py
│   ├── qrng.py                       # Quantum random number generator
│   └── dj.py                         # Deutsch-Jozsa circuit + constant oracles
├── notebooks/
│   ├── day1_qrng.ipynb               # First random bit + Hadamard intuition
│   ├── day2_qrng_scaling.ipynb       # 128-bit scaling + statistical validation
│   └── day3_dj_constant.ipynb        # Deutsch-Jozsa, constant case
├── tests/
│   ├── test_qrng.py
│   └── test_dj.py
├── data/
│   └── sample_nonce.txt
├── LEARNINGS.md                      # Daily learning log
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
from quantum_qr.qrng import generate_quantum_nonce_hex
from quantum_qr.dj import build_dj_circuit, constant_oracle_zero
from qiskit_aer import AerSimulator

# 1. Generate a 128-bit quantum-random nonce
nonce = generate_quantum_nonce_hex(128)
print(nonce)  # 32 hex characters

# 2. Build and run a DJ circuit on a constant oracle
n = 4
oracle = constant_oracle_zero(n)
dj_circuit = build_dj_circuit(oracle, n)
counts = AerSimulator().run(dj_circuit, shots=1024).result().get_counts()
print(counts)  # {'0000': 1024} — constant!
```

## Validation results

**Quantum RNG** (`aer_simulator`, 128-qubit Hadamard circuit):

| Metric | Result |
|---|---|
| Total bits tested | 10,000 |
| Count of 0s / 1s | XXXX / XXXX  ← *fill in* |
| Chi-square p-value | 0.XX           ← *fill in* |

**Deutsch-Jozsa, constant case** (n = 4, 1024 shots each):

| Oracle | Measurement outcome | Frequency |
|---|---|---|
| `constant_oracle_zero` | `'0000'` | 100% |
| `constant_oracle_one`  | `'0000'` | 100% |

Notebooks contain histograms, circuit diagrams, and additional analysis.

## Roadmap

- [x] **Day 1** — Environment setup, first quantum random bit
- [x] **Day 2** — 128-bit QRNG module, statistical validation
- [x] **Day 3** — Deutsch-Jozsa circuit (constant oracles)
- [ ] **Day 4** — Deutsch-Jozsa balanced oracles + classical QR library setup
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
