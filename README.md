# Quantum Tamper-Evident QR Codes

![tests](https://github.com/YOUR_USERNAME/quantum-tamper-evident-qr/actions/workflows/tests.yml/badge.svg)

A QR code system that uses true quantum randomness for nonce generation and the Deutsch-Jozsa algorithm for single-query tamper verification. Built with Qiskit and run on real IBM Quantum hardware.

![QR gallery — the same message produces two different codes thanks to a fresh quantum nonce each time](data/gallery.png)

## Motivation

Standard QR codes are vulnerable to physical swap attacks (common in payment fraud) and digital tampering. This project explores whether quantum primitives can strengthen QR integrity:

- **True randomness** — Nonces come from quantum measurements (Hadamard + measure), not pseudo-random functions, so they cannot be reproduced from a seed.
- **Single-query verification** — A Deutsch-Jozsa oracle lets a verifier detect tampering in one quantum query.

This is primarily a learning and engineering exploration. A classical HMAC achieves tamper detection with less complexity; the value here is implementing real quantum algorithms end-to-end and quantifying how reliably they run on actual quantum hardware.

## How it works

1. **Generate** — a quantum random number generator produces a 128-bit nonce; an HMAC tag binds the data and nonce under a secret key; everything is packed (JSON → base64) into the QR image.
2. **Verify** — the verifier recomputes the expected tag, XORs it with the QR's tag to get a difference string `s`, and turns `s` into a Deutsch-Jozsa oracle.
3. **Decide** — running Deutsch-Jozsa recovers `s` in a single quantum query: all zeros → authentic, anything else → tampered (and the non-zero bits show exactly where the tags disagree).

On a noiseless simulator this is exact by construction; on real hardware the recovery degrades measurably with noise (see Results).

## Design

The full payload schema, threat model, generate/verify flows, limitations, and post-build findings are documented in [`DESIGN.md`](DESIGN.md). In short:

- QR payload is a base64-encoded JSON object: `{version, data, nonce, tag}`
- `nonce` is 128 bits from the quantum RNG
- `tag` is HMAC-SHA256(K, data || nonce) truncated to **n = 8 bits**
- Verification XORs observed vs expected tag → secret `s` → `oracle_from_secret(s)` → DJ
- Authentic → s = 0 → constant oracle → DJ measures zeros; tampered → s ≠ 0 → balanced → non-zero

## Results

**Simulator (full corpus):** 100% accuracy, 100% recall, zero false negatives. Expected on a noiseless backend — it validates the pipeline and corpus consistency, not quantum advantage.

**Real hardware (IBM `<backend name>` ← fill in, `<N>`-fixture subset):**
- Subset accuracy: `<X>%` ← *fill in from `data/eval_hardware.json`*
- Authentic P(zeros): 1.00 (simulator) → `<0.9x>` (hardware) ← *fill in*
- `<note any false negatives or which fixtures degraded>` ← *fill in*

The gap is decoherence and gate error, amplified by the depth inflation transpilation introduces when mapping the circuit onto the device's native gate set and qubit connectivity. The Deutsch-Jozsa algorithm is correct in principle (perfect on the simulator) and measurably degrades on current NISQ hardware — a concrete, quantitative finding about today's devices.

![Verifier robustness: P(zeros) for authentic vs tampered QRs against depolarizing noise, with the accept threshold](data/noise_sweep.png)

![Confusion matrix: noiseless simulator vs real hardware](data/confusion_matrix.png)

## What's working

**Verifier** (`quantum_qr/verifier.py`)
- `verify(qr_path, n_bits=8, key=None, shots=1024, accept_threshold=0.5, confidence_floor=0.0, backend=None)` — returns a verdict dict
- Verdicts: `authentic`, `tampered`, `invalid` (undecodable QR — never crashes)
- **Injectable backend** via `run_counts()` — same code runs on noiseless sim, noisy sim, or real IBM hardware (Aer `.run()` vs `SamplerV2` primitive)
- `decide(counts, ...)` — pure decision function; returns verdict, `confidence`, `p_zeros`, `measured_secret`; noise-robust threshold + "inconclusive" floor
- Wrong key correctly flags an authentic QR as tampered

**Evaluation Harness** (`quantum_qr/evaluate.py`)
- `evaluate_corpus(...)` — accuracy, recall, precision, confusion matrix, per-tamper-type breakdown
- `plot_confusion_matrix(...)`; baselines in `data/eval_simulator.json` and `data/eval_hardware.json`

**Generator** (`quantum_qr/generator.py`)
- `generate(data, output_path, n_bits=8, key=None, nonce=None)` — QRNG → HMAC tag → payload → QR image
- Fail-fast validation, capacity guard, full UTF-8 support, fresh quantum nonce per call

**Command-Line Interface** (`quantum_qr/cli.py`, `quantum_qr/__main__.py`)
- `python -m quantum_qr generate "<data>" -o out.png [-n 8] [--json]`
- `python -m quantum_qr verify <path> [--shots N] [--threshold T] [--bits 8] [--json]`
- Verdict-encoding exit codes (0/3/4) and friendly errors

**Supporting modules**
- `payload.py` / `config.py` — HMAC tag, payload encode/decode, tags-to-secret, keyed via `QTQR_KEY`
- `dj.py` — DJ circuit + oracles; `oracle_from_secret(s)` recovers s in one query (Bernstein-Vazirani)
- `qrng.py` — 128-qubit Hadamard RNG, chi-square validated (p = 0.XX) ← *fill in*
- `qr_io.py` — lossless QR encode/decode via `qrcode` + OpenCV
- `fixtures.py` — labeled corpus + `manifest.json` answer key

## Project structure

```
quantum-tamper-evident-qr/
├── quantum_qr/
│   ├── __init__.py                   # Public API (generate, verify, decide, ...) + version
│   ├── qrng.py                       # Quantum random number generator
│   ├── dj.py                         # Deutsch-Jozsa circuit + oracles
│   ├── qr_io.py                      # Classical QR encode/decode
│   ├── payload.py                    # HMAC tag, payload encode/decode, tags-to-secret
│   ├── config.py                     # Shared-key handling
│   ├── generator.py                  # End-to-end generate()
│   ├── verifier.py                   # DJ verify() + decide() + run_counts() (backend-agnostic)
│   ├── evaluate.py                   # Corpus evaluation + confusion-matrix plot
│   ├── fixtures.py                   # Authentic + tampered fixture builder
│   ├── cli.py                        # argparse CLI (generate + verify)
│   └── __main__.py                   # enables `python -m quantum_qr`
├── notebooks/
│   ├── day1_qrng.ipynb  …  day16_polish.ipynb
│   ├── day17_hardware.ipynb          # First DJ run on real hardware
│   └── day18_hardware_benchmark.ipynb# Sim-vs-hardware comparison
├── tests/
│   ├── test_qrng.py … test_evaluate.py   # all simulator-based; run in CI without credentials
├── data/
│   ├── gallery.png
│   ├── noise_sweep.png
│   ├── confusion_matrix.png
│   ├── eval_simulator.json           # frozen simulator baseline
│   ├── eval_hardware.json            # real hardware subset results
│   ├── hardware_run_n4.json          # first raw hardware counts
│   ├── design_sketch.jpg
│   └── fixtures/                     # generated QR corpus + manifest.json
├── .github/workflows/tests.yml       # CI: pytest on every push
├── DESIGN.md                         # Threat model, schema, flows, limitations, findings
├── LEARNINGS.md                      # Daily learning log
├── LICENSE
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

Running on real hardware additionally requires a free IBM Quantum account (quantum.cloud.ibm.com) and saved credentials via `qiskit-ibm-runtime`. The simulator path and the full test suite need no credentials.

## Quick start

```python
from quantum_qr import generate, verify

generate("pay alice $10", "data/alice_payment.png")

result = verify("data/alice_payment.png")
print(result["verdict"])       # 'authentic'
print(result["confidence"])    # ~1.0 on the simulator

print(verify("data/fixtures/fixture_01_data.png")["verdict"])  # 'tampered'
```

## Command-line usage

```bash
python -m quantum_qr generate "pay alice $10" -o data/alice.png
python -m quantum_qr verify data/alice.png          # exit code encodes the verdict
python -m quantum_qr verify data/alice.png --json
```

Exit codes: `0` authentic, `3` tampered, `4` invalid, `1` operational error, `2` usage error — so the tool gates shell pipelines, e.g. `python -m quantum_qr verify qr.png && ./next_step.sh`.

## Testing

```bash
pytest -v
```

All `<N>` ← *fill in* tests pass; CI runs them on every push (simulator-only, no IBM credentials required).

## Roadmap

- [x] **Days 1–4** — QRNG, Deutsch-Jozsa (constant + balanced), QR encode/decode
- [x] **Day 5** — Threat model, schema, verify-flow design (`DESIGN.md`)
- [x] **Day 6** — HMAC tag, payload encode/decode, tamper bridge
- [x] **Days 7–11** — Generator: core, robustness, fixtures, CLI, polish + gallery
- [x] **Days 12–16** — Verifier: core, corpus accuracy, decision rule + noise, CLI verify, injectable backend
- [x] **Day 17** — First Deutsch-Jozsa run on real IBM Quantum hardware
- [x] **Day 18** — Hardware benchmark + simulator-vs-hardware comparison
- [x] **Day 19** — Final documentation: results, findings, CI, repo hygiene


## References

- Deutsch, D. & Jozsa, R. (1992). Rapid solutions of problems by quantum computation. *Proc. R. Soc. Lond. A* 439, 553–558.
- Bernstein, E. & Vazirani, U. (1997). Quantum complexity theory. *SIAM J. Comput.* 26(5), 1411–1473.
- Nielsen, M. & Chuang, I. *Quantum Computation and Quantum Information.*
- [Qiskit Documentation](https://docs.quantum.ibm.com/)

## License

MIT — see [`LICENSE`](LICENSE).