## Day 1 - Environment setup, first quantum random bit

## Day 2 — 128-bit Quantum Random Number Generator + Validation

Today I built a scalable quantum random number generator using a 128-qubit circuit in Qiskit. I learned how quantum superposition and measurement can be used to generate random bitstrings.

I also implemented statistical validation using chi-square testing and compared quantum randomness with Python’s pseudo-random generator. Both passed statistical tests, but I understood that PRNGs are deterministic while QRNGs derive entropy from physical quantum measurement.

Finally, I added unit tests using pytest to ensure correctness and consistency of the generated bitstrings.