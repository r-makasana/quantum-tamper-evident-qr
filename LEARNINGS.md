# Learnings

A running log of what I learned each day building this project. Honest, conversational, written for my future self.

## Day 1 — First Quantum Random Bit
- Set up Qiskit, qiskit-aer, and supporting libraries. Got a 1-qubit Hadamard + measure circuit running end-to-end.
- Key insight: a Hadamard gate turns |0⟩ into (|0⟩+|1⟩)/√2, so measurement gives 0 or 1 with equal probability — this is *intrinsic* randomness, not pseudo-random.
- Over 1024 shots, the histogram landed close to 50/50 with small statistical deviation. The deviation is statistics, not error — same reason flipping a fair coin 1024 times rarely gives exactly 512/512.
- Drew the circuit with `circuit.draw('mpl')` — turns out matplotlib diagrams are how every quantum paper shows circuits.

## Day 2 — Scaling to 128 bits + Statistical Validation
- Built `quantum_qr/qrng.py`. Implemented a 128-qubit parallel Hadamard circuit — one shot, 128 random bits.
- Considered three approaches (loop, parallel qubits, multi-shot single qubit). Went with parallel qubits because it best showcases quantum parallelism.
- Tripped on Qiskit's bitstring ordering — the rightmost character of the result string is qubit 0, not qubit n-1. Documented this in the module docstring so I don't get bitten again.
- Chi-square test on 10,000 quantum bits gave p = 0.XX → consistent with uniform distribution, null hypothesis not rejected.
- Compared with Python's `random.getrandbits()`. Both pass chi-square, but they differ philosophically: pseudo-random output is deterministic given the seed; quantum output is fundamentally probabilistic by the Born rule. That distinction matters for cryptographic nonces — a quantum nonce can't be reproduced by guessing a seed.

## Day 3 — Deutsch-Jozsa, Constant Case
- First non-trivial quantum algorithm working end-to-end.
- The five-layer DJ circuit structure: ancilla → |1⟩, then Hadamard on everything, then the oracle, then Hadamard on inputs only, then measure inputs.
- Biggest "aha" moment: **phase kickback**. Putting the ancilla in |−⟩ = (|0⟩−|1⟩)/√2 causes the oracle to output a phase factor (−1)^f(x) on the input register instead of writing into the ancilla. The function's output value gets *encoded as a phase*, and interference at the second Hadamard layer reads it out.
- For a constant function, all 2^n phases are identical, so the second Hadamard layer interferes them back into |0...0⟩. Any non-constant function breaks that perfect interference.
- Verified with both `constant_oracle_zero` (do nothing — identity) and `constant_oracle_one` (a single X on the ancilla) → both gave `'0000'` with 100% probability over 1024 shots.

## Day 4 — DJ Balanced Case + QR Pipeline
- Completed the Deutsch-Jozsa picture by building balanced oracles. A balanced oracle through DJ measures a **non-zero** bitstring — the mirror image of the constant case — because the phases no longer all align and don't interfere back to |0...0⟩.
- Built `oracle_from_secret(s)` computing f(x) = s·x (mod 2) by placing a CNOT to the ancilla for each '1' bit in s. This one function unifies everything: s = all-zeros gives a constant oracle, any non-zero s gives a balanced one.
- **Biggest realisation of the week:** DJ on `oracle_from_secret(s)` doesn't just say "balanced" — it *recovers s exactly* in a single query. That means the same circuit answering DJ's yes/no question also solves Bernstein-Vazirani. The original project used BV; mine uses the DJ framing of the same underlying machinery for tamper detection. Same physics, different question — siblings, not copies.
- Had to mind the bit-ordering again when reading the recovered secret back out.
- Built the classical half too: `quantum_qr/qr_io.py`. The `qrcode` library only *encodes*; for *decoding* I used OpenCV's `cv2.QRCodeDetector` rather than `pyzbar` because pyzbar needs the zbar system binary which is painful on Windows.
- Round-trip test passed: encode a string → PNG → decode back to the identical string. The classical pipeline is now ready to carry quantum payloads next week.

## Day 5 — Design Day (no code)
- Spent the whole day in `DESIGN.md`. No new modules, no new tests. At first it felt slow, but by the end I understood why senior engineers value design days so much — most of my Day 7+ work just got easier because the decisions are already made.
- Wrote a real threat model before writing the schema. The eye-opener was realising that *without* a shared key, an attacker could simply recompute the tag and the whole scheme detects nothing. So this is a keyed integrity system (HMAC), and key distribution is out of scope. Writing that limitation explicitly felt better than hand-waving past it.
- **The elegant bit:** the verifier doesn't compare hashes directly. Instead, it computes `s = tag_observed XOR tag_expected` and feeds `s` into `oracle_from_secret`. If the tags match, s = 0, DJ measures zero → authentic. If they differ, s ≠ 0, DJ measures exactly which bits disagree → tampered. A classical equality check has been re-expressed as DJ's natural constant-vs-balanced question. That's the conceptual centre of the whole project.
- Picked **n = 8** for the tag/oracle width: 8 input qubits + 1 ancilla = 9 qubits total, comfortably runs on every free IBM Quantum backend.
- Sketched both flows on paper first, then drew them as Mermaid diagrams. GitHub renders Mermaid in markdown automatically — looks much more professional than ASCII art.

## Day 6 — (tomorrow)
