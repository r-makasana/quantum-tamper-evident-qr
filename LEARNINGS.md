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
- Realised DJ and Bernstein-Vazirani share the same circuit shape — same phase-kickback trick. That's why the original project's BV approach and my DJ approach are siblings, not duplicates: same machinery, different question asked of f.

## Day 4 — (tomorrow)
