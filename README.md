# Quantum Tamper-Evident QR Codes

A QR code system that uses true quantum randomness for nonce generation and the Deutsch-Jozsa algorithm for single-query tamper verification. Built with Qiskit.

> **Status:** In development — Day 12 of 21 complete. Both halves now exist: a generator that issues tamper-evident QRs and a Deutsch-Jozsa verifier that judges them on a simulator. Next: corpus-wide accuracy, then real quantum hardware.

![QR gallery — the same message produces two different codes thanks to a fresh quantum nonce each time](data/gallery.png)

## Motivation

Standard QR codes are vulnerable to physical swap attacks (common in payment fraud) and digital tampering. This project explores whether quantum primitives can strengthen QR integrity:

- **True randomness** — Nonces come from quantum measurements (Hadamard + measure), not pseudo-random functions, so they cannot be reproduced from a seed.
- **Single-query verification** — A Deutsch-Jozsa oracle lets a verifier detect tampering in one quantum query: untampered → constant oracle → measures all zeros; tampered → balanced oracle → measures non-zero.

This is primarily a learning and engineering exploration. A classical HMAC achieves tamper detection with less complexity; the value here is in implementing real quantum algorithms end-to-end and quantifying how reliably they run on actual quantum hardware. The verifier's verdict is driven by the quantum measurement; on a noiseless simulator it round-trips by construction, and its robustness becomes a measured quantity on noisy hardware (see Roadmap, Days 17–18).

## Design

The full payload schema, threat model, generate/verify flows, and limitations are documented in [`DESIGN.md`](DESIGN.md). In short:

- QR payload is a base64-encoded JSON object: `{version, data, nonce, tag}`
- `nonce` is 128 bits from the quantum RNG
- `tag` is an HMAC-SHA256(K, data || nonce) truncated to **n = 8 bits**
- Verification: recompute the expected tag, XOR with the observed tag to get a secret `s`, build `oracle_from_secret(s)`, run DJ
- Authentic QR → s = 0 → constant oracle → DJ measures zeros
- Tampered QR → s ≠ 0 → balanced oracle → DJ measures the differing bits

## What's working today

**Verifier** (`quantum_qr/verifier.py`)
- `verify(qr_path, n_bits=8, key=None, shots=1024)` — reads a QR, runs the DJ tamper check, returns a verdict dict
- Verdict (`authentic`/`tampered`) is driven by the quantum measurement
- Returns the measured secret, the classical secret, an `agree` correctness flag, and the full histogram
- Wrong key correctly flags an authentic QR as tampered (the key is load-bearing)

**Generator** (`quantum_qr/generator.py`)
- `generate(data, output_path, n_bits=8, key=None, nonce=None)` — one call produces a tamper-evident QR and returns its payload metadata
- Fail-fast validation, QR capacity guard, full UTF-8 support, fresh quantum nonce per call

**Command-Line Interface** (`quantum_qr/cli.py`, `quantum_qr/__main__.py`)
- `python -m quantum_qr generate "<data>" -o out.png [-n 8] [--json]`
- Friendly errors and proper exit codes; `verify` subcommand arriving in Day 15

**Test Fixtures** (`quantum_qr/fixtures.py`)
- Labeled corpus of authentic + tampered QRs with a `manifest.json` ground-truth answer key

**Payload Layer** (`quantum_qr/payload.py`, `quantum_qr/config.py`)
- `compute_tag`, `build/encode/decode_payload`, `tags_to_secret`, `get_key()` (via `QTQR_KEY` env var)

**Deutsch-Jozsa Circuit** (`quantum_qr/dj.py`)
- `build_dj_circuit`, `constant_oracle_zero/one`, `balanced_oracle`, `oracle_from_secret(s)` (recovers s in one query — Bernstein-Vazirani behavior)

**Quantum RNG** (`quantum_qr/qrng.py`)
- 128-qubit Hadamard circuit; binary/hex nonces; chi-square validated (p = 0.XX)  ← *replace with your value*

**Classical QR I/O** (`quantum_qr/qr_io.py`)
- `make_qr` / `read_qr` — lossless encode/decode via `qrcode` and OpenCV

## Project structure

```
quantum-tamper-evident-qr/
├── quantum_qr/
│   ├── __init__.py                   # Public API + package docstring
│   ├── qrng.py                       # Quantum random number generator
│   ├── dj.py                         # Deutsch-Jozsa circuit + oracles
│   ├── qr_io.py                      # Classical QR encode/decode
│   ├── payload.py                    # HMAC tag, payload encode/decode, tags-to-secret
│   ├── config.py                     # Shared-key handling
│   ├── generator.py                  # End-to-end generate()
│   ├── verifier.py                   # DJ-based verify()
│   ├── fixtures.py                   # Authentic + tampered fixture builder
│   ├── cli.py                        # argparse CLI (generate; verify in Day 15)
│   └── __main__.py                   # enables `python -m quantum_qr`
├── notebooks/
│   ├── day1_qrng.ipynb
│   ├── day2_qrng_scaling.ipynb
│   ├── day3_dj_constant.ipynb
│   ├── day4_dj_balanced_and_qr.ipynb
│   ├── day6_payload.ipynb
│   ├── day7_generator.ipynb
│   ├── day8_generator_robustness.ipynb
│   ├── day9_fixtures.ipynb
│   ├── day10_cli.ipynb
│   ├── day11_gallery.ipynb
│   └── day12_verifier.ipynb
├── tests/
│   ├── test_qrng.py
│   ├── test_dj.py
│   ├── test_qr_io.py
│   ├── test_payload.py
│   ├── test_generator.py
│   ├── test_fixtures.py
│   ├── test_cli.py
│   └── test_verifier.py
├── data/
│   ├── sample_nonce.txt
│   ├── design_sketch.jpg
│   ├── gallery.png
│   ├── alice_payment.png
│   └── fixtures/                     # generated QR corpus + manifest.json
├── DESIGN.md                         # Threat model, schema, flows, limitations
├── LEARNINGS.md                      # Daily learning log
├── requirements.txt
└── README.md
```

## Installation

Requires Python 3.10 or newer.

```bash
git clone https://github.com/YOUR_USERNAME/quantum-tamper-evident-qr.git
cd quantum-tamper-evident-qr
pip install -r requirements.txt
```

## Quick start

```python
from quantum_qr import generate
from quantum_qr.verifier import verify

# Issue a tamper-evident QR
generate("pay alice $10", "data/alice_payment.png")

# Verify it with the quantum (Deutsch-Jozsa) check
result = verify("data/alice_payment.png")
print(result["verdict"])          # 'authentic'
print(result["agree"])            # True  (quantum measurement matches classical secret)

# A tampered fixture verifies as tampered
print(verify("data/fixtures/fixture_01_data.png")["verdict"])  # 'tampered'
```

## Command-line usage

```bash
# Generate a tamper-evident QR
python -m quantum_qr generate "pay alice $10" -o data/alice.png

# Machine-readable output for scripting
python -m quantum_qr generate "pay alice $10" -o data/alice.png --json
```

Exit codes: `0` success, `1` application error, `2` usage error. (A `verify` subcommand lands on Day 15.)

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
| `constant_oracle_zero` / `constant_oracle_one` | `'0000'` | 100% |
| `balanced_oracle`      | non-zero | 100% |
| `oracle_from_secret("1010")` | `'1010'` (recovered) | 100% |

**Verifier** (`aer_simulator`): authentic QRs → `authentic`; tampered fixtures → `tampered`; DJ-measured secret matches the classical secret 100% of the time (`agree = True`). Corpus-wide accuracy numbers land on Day 13.

## Roadmap

- [x] **Day 1** — Environment setup, first quantum random bit
- [x] **Day 2** — 128-bit QRNG module, statistical validation
- [x] **Day 3** — Deutsch-Jozsa circuit (constant oracles)
- [x] **Day 4** — DJ balanced oracles, secret recovery, QR encode/decode pipeline
- [x] **Day 5** — Payload schema, threat model, verify-flow design (`DESIGN.md`)
- [x] **Day 6** — Payload encode/decode, HMAC tag, tamper bridge
- [x] **Day 7** — Core `generate()`: QRNG + HMAC + QR image end to end
- [x] **Day 8** — Generator robustness: input validation and edge cases
- [x] **Day 9** — Test-fixture generator (authentic + deliberately tampered QRs)
- [x] **Day 10** — Command-line interface + generator tests
- [x] **Day 11** — Generator polish, docstrings, dependency pinning, QR gallery
- [x] **Day 12** — Core DJ-based `verify()` on the simulator
- [ ] **Day 13** — Verifier accuracy across the full fixture corpus
- [ ] **Day 14** — Probabilistic handling: shots, majority voting, confidence thresholds
- [ ] **Day 15** — `verify` CLI subcommand + verifier tests
- [ ] **Day 16** — Verifier polish + accuracy/confusion-matrix visual
- [ ] **Day 17–18** — Execution on real IBM Quantum hardware + noise benchmarks
- [ ] **Day 19–21** — Final polish, full CLI, documentation

## References

- Deutsch, D. & Jozsa, R. (1992). Rapid solutions of problems by quantum computation. *Proc. R. Soc. Lond. A* 439, 553–558.
- Bernstein, E. & Vazirani, U. (1997). Quantum complexity theory. *SIAM J. Comput.* 26(5), 1411–1473.
- Nielsen, M. & Chuang, I. *Quantum Computation and Quantum Information.*
- [Qiskit Documentation](https://docs.quantum.ibm.com/)

## License

MIT