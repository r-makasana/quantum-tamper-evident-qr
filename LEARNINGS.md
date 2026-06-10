# Learnings

A running log of what I learned each day building this project. Honest, conversational, written for my future self.

## Day 1 — First Quantum Random Bit
- Set up Qiskit, qiskit-aer, and supporting libraries. Got a 1-qubit Hadamard + measure circuit running end-to-end.
- A Hadamard gate turns |0⟩ into (|0⟩+|1⟩)/√2, so measurement gives 0 or 1 with equal probability — *intrinsic* randomness, not pseudo-random.
- Over 1024 shots the histogram landed near 50/50 with small deviation — statistics, not error, like a fair coin rarely giving exactly 512/512.

## Day 2 — Scaling to 128 bits + Statistical Validation
- Built `quantum_qr/qrng.py` with a 128-qubit parallel Hadamard circuit — one shot, 128 random bits.
- Tripped on Qiskit's bitstring ordering: the rightmost character is qubit 0. Documented it in the docstring.
- Chi-square test on 10,000 quantum bits gave p = 0.XX → consistent with uniform.
- Compared with Python's `random.getrandbits()`: both pass chi-square, but pseudo-random is deterministic given the seed while quantum is probabilistic by the Born rule. That matters for nonces — a quantum nonce can't be reproduced by guessing a seed.

## Day 3 — Deutsch-Jozsa, Constant Case
- First non-trivial quantum algorithm working end-to-end.
- Five-layer DJ structure: ancilla → |1⟩, Hadamard everything, oracle, Hadamard inputs only, measure inputs.
- Biggest "aha": **phase kickback**. The ancilla in |−⟩ makes the oracle output a (−1)^f(x) phase on the input register; interference at the second Hadamard layer reads it out.
- Constant function → all phases identical → interferes back to |0...0⟩. Verified both constant oracles give `'0000'` at 100%.

## Day 4 — DJ Balanced Case + QR Pipeline
- Balanced oracle through DJ measures **non-zero** — the mirror of the constant case.
- Built `oracle_from_secret(s)` = f(x) = s·x mod 2. s = zeros → constant; s ≠ 0 → balanced.
- **Key realisation:** DJ on `oracle_from_secret(s)` *recovers s* in one query — the same circuit solves Bernstein-Vazirani. The original project used BV; mine uses DJ framing of the same machinery for tamper detection. Siblings, not copies.
- Built `quantum_qr/qr_io.py`. `qrcode` only encodes; used OpenCV's `QRCodeDetector` to decode (avoiding pyzbar's zbar binary, painful on Windows). Round-trip works.

## Day 5 — Design Day (no code)
- A full day in `DESIGN.md`. Felt slow, but it made every later day easier.
- Wrote a threat model first. The eye-opener: without a shared key, an attacker just recomputes the tag and nothing is detected. So it's a keyed (HMAC) system; key distribution is out of scope.
- **The elegant bit:** the verifier doesn't compare hashes directly — it computes s = tag_observed XOR tag_expected and feeds s to `oracle_from_secret`. Match → s = 0 → constant → authentic; differ → s ≠ 0 → tampered. A classical equality check re-expressed as DJ's constant-vs-balanced question.
- Picked n = 8: 8 input + 1 ancilla = 9 qubits, fits any free IBM backend.

## Day 6 — Payload Utilities + HMAC
- Built `payload.py` (compute_tag, build/encode/decode_payload, tags_to_secret) and `config.py`.
- **Why HMAC, not plain SHA-256:** a plain hash is keyless, so an attacker recomputes it after editing. HMAC folds in the key, so only K-holders forge valid tags. That's what makes detection possible.
- Kept the key out of source via `get_key()` reading `QTQR_KEY` with a labelled demo fallback.
- **Best decision so far:** proved tamper detection works *purely classically* before adding quantum. Now the quantum layer is the only unknown.

## Day 7 — The Generator Comes Together
- `generate()` is ~12 lines of orchestration. Modular design made integration trivial.
- Same message → different QR each time (fresh quantum nonce) → no replayable duplicates.
- Used `tmp_path` so tests don't litter `data/`.

## Day 8 — Generator Robustness
- Hardened `generate()`: empty/oversized data, bad n_bits, wrong key type, missing folders all fail with clear messages.
- **Validate before expensive work** — no quantum run for input I'll reject.
- Unicode round-trips losslessly (JSON + base64 layering).
- Added optional `nonce` injection — designing for testability.

## Day 9 — The Tampered-Fixture Corpus
- Built the answer key before the thing it grades: `fixtures.py` + `manifest.json` with ground-truth verdicts and secrets.
- Varied attacks: data/nonce/tag tampering, wrong-key forgery, corruption.
- The 1-in-256 false-negative rate became real code — assert non-zero secret, retry on collision. Rate = 2^(−n_bits).

## Day 10 — Command-Line Interface
- `python -m quantum_qr generate ...` via `cli.py` + `__main__.py`.
- Thought about *use*: exit codes for scripts, `--json` for piping, friendly errors.
- `main(argv=None)` makes the CLI testable without subprocesses.

## Day 11 — Generator Polish
- Consistent docstrings + type hints, clean public API, `__version__`, pinned `requirements.txt`.
- The QR gallery (same message → two different QRs) is the strongest one-glance argument for the quantum nonce.

## Day 12 — The Quantum Verifier
- `verify()` reads a QR, derives the secret, runs DJ, returns a verdict driven by the quantum measurement.
- **Most important realisation:** the verifier round-trips perfectly on a simulator because building the oracle requires the secret DJ then recovers. Not a flaw — the honest truth: demonstrative on a noiseless simulator, measurable on noisy hardware.
- `agree` field = built-in circuit-correctness check. Wrong-key test proves the key is load-bearing.

## Day 13 — Corpus Evaluation Harness
- `evaluate_corpus()` scores `verify()` across the corpus: accuracy, recall, precision, confusion matrix, per-type breakdown.
- **Recall is the headline metric** — a false negative means accepting a forgery.
- 100% on simulator validates consistency, not quantum advantage. Hardened `verify()` to return `"invalid"` on undecodable QRs. Froze baseline to `eval_simulator.json`.

## Day 14 — Probabilistic Decision Rule + Noise
- Separated `decide()` (counts → verdict) from execution — unit-testable with hand-built histograms.
- Added an accept threshold on P(zeros) and an "inconclusive" confidence floor.
- Simulated depolarizing noise and watched the clean peak smear. The noise sweep is the first analysis a classical HMAC couldn't produce.
- **Debugging lesson:** a flat-at-zero sweep was a bug, not physics — at p=0 the authentic curve *must* be 1.0. Cause: the ancilla snuck into the measurement register. Always sanity-check the value you already know.

## Day 15 — verify CLI Subcommand
- Completed the CLI with `verify`. The reserved subcommand slot from Day 10 made it drop in cleanly.
- **Exit codes encode the verdict:** 0 authentic, 3 tampered, 4 invalid, 1 operational, 2 usage — so the tool gates shell pipelines like `grep`.
- Composability — how a tool works with other tools — is a step up in how I design software.

## Day 16 — Verifier Polish + Backend Injection
- Docstring/type-hint pass on the verifier modules.
- **Made the quantum backend injectable**, defaulting to the simulator. Running on hardware becomes a one-line change.
- Fourth use of the same pattern: make the swappable thing a parameter (nonce → argv → key → backend).
- Confusion-matrix plotter; noiseless vs noisy side by side previews what hardware will do.

## Day 17 — First Hardware Run
- Ran Deutsch-Jozsa on a real IBM quantum computer.
- The textbook's `IBMQ.load_account()` is dead. Current path: `qiskit-ibm-runtime` + `QiskitRuntimeService` + the `SamplerV2` primitive, and circuits must be transpiled to the device's native gates and connectivity first.
- The transpiled depth **ballooned** compared to my clean circuit — that inflation is exactly why hardware is noisy.
- The result was a dominant `'0000'` peak with a real scatter around it, not the perfect 100% the simulator gives. That gap between simulator and hardware is the honest heart of the project.
- Hardware queues are unpredictable — submit, save the job id, come back. Don't burn limited QPU time re-submitting.

## Day 18 — Hardware Benchmark
- Completed the injectable-backend abstraction with `run_counts`: Aer uses `.run()`, IBM hardware uses `SamplerV2` after transpilation. The clean parameter from Day 16 needed one more layer because hardware runs through primitives, not direct `.run()`.
- Ran a representative subset of the corpus on a real device in a single batched job to respect limited free QPU time.
- **Headline result:** 100% on the simulator, <X>% on hardware, with the gap coming from decoherence and the depth inflation transpilation introduces. <If applicable: one tampered fixture slipped through as a false negative — the security-critical failure mode, and a concrete argument for more shots or error mitigation.>
- This sim-vs-hardware comparison is the one result in the whole project that a classical HMAC fundamentally could not produce.

## Day 19 — Final Documentation
- Turned `DESIGN.md` from a Day 5 plan into a living document by folding in real hardware findings — the limitations I *predicted* are now limitations I *measured*.
- Wrote a "How it works" section a non-expert could follow, which forced me to explain the whole system in three plain sentences. If I can't explain it simply, I don't understand it well enough — and now I can.
- Repo hygiene: added a LICENSE file, scanned git history to confirm my IBM token never got committed, and set up CI so the test suite runs on every push.
- Realised the documentation is probably what a hiring manager will spend the most time on — and a threat model, living design doc, honest hardware results, daily logs, and CI together are rarer than the quantum content itself.
