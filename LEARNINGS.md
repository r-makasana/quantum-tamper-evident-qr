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

## Day 6 — Payload Utilities + HMAC
- Built the classical glue layer: `quantum_qr/payload.py` (compute_tag, build_payload, encode_payload, decode_payload, tags_to_secret) and `quantum_qr/config.py` for key handling.
- **Why HMAC, not plain SHA-256:** a plain hash is keyless, so an attacker who edits the data just recomputes the hash and the tamper is invisible. HMAC folds in the secret key, so only someone who knows K can forge a valid tag. That one design choice is what makes the whole scheme actually detect anything.
- Kept the key out of source code — `get_key()` reads `QTQR_KEY` from the environment with a clearly-labelled demo fallback. Hardcoding a key would have undercut the entire threat model.
- **Best engineering decision so far:** I proved tamper detection works *purely classically* before wiring in any quantum. Authentic payload → tags_to_secret returns "00000000"; tampered payload → non-zero. Now the quantum layer is the only unknown left, so if DJ misbehaves next week I'll know the plumbing isn't the cause. Isolating the risky/novel component before testing it is something I want to keep doing.
- The XOR result from `tags_to_secret` is *literally* the secret string that `oracle_from_secret` will consume next week — the two modules were designed to click together, and now they do.
- Minor gotcha: bytes vs strings when feeding data into HMAC. Had to be deliberate about `.encode()` everywhere.

## Day 7 — The Generator Comes Together
- Built `quantum_qr/generator.py`. The `generate()` function ended up being about a dozen lines of pure orchestration: get key → quantum nonce → HMAC tag → build payload → base64 → QR image.
- **The payoff of modular design hit me today.** Because each of the previous six days produced a clean, single-purpose interface, assembling them into a working generator was almost boring — in the best way. No fighting, no reshaping, just calling the pieces in order. This is what people mean when they say good architecture makes the integration trivial.
- Noticed each call to `generate()` with the same message produces a *different* QR, because the nonce is freshly quantum-random every time. That's a desirable property: two identical messages don't produce identical, replayable QR codes.
- Closed the loop: read the generated QR back, decoded it, recomputed the tag, and `tags_to_secret` returned all zeros. So the generator already produces QRs my future verifier will accept — the two halves now meet in the middle.
- Used pytest's `tmp_path` fixture so generator tests don't litter the `data/` folder with throwaway PNGs. Small thing, but it keeps the repo clean.

## Day 8 — Generator Robustness
- Hardened `generate()` against bad input: empty data, oversized payloads, invalid n_bits, wrong key types, and missing output folders all now fail with clear messages.
- **Key principle learned: validate before doing expensive work.** All checks run *before* the quantum nonce generation — no reason to spin up a quantum circuit for input I'm about to reject. Fail fast, fail cheap.
- Realised "it works on the happy path" and "it's robust" are completely different bars. The gap between them is almost entirely edge-case thinking, and that's where most of today went.
- Unicode payloads (emoji, accents, other scripts) round-trip losslessly — they "just work" because JSON handles unicode and base64 handles the resulting bytes. The layered encoding I chose on Day 5 paid off without extra effort.
- Added an optional `nonce` injection parameter — a small example of **designing for testability**. It lets tests control otherwise-random behavior without compromising the real quantum-random default. This also sets up tomorrow's tampered-fixture work. Making the non-deterministic part injectable is a pattern I want to remember.
- Capped n_bits at 32 because n_bits becomes the qubit count in the DJ verifier, and even 32 qubits is large for current hardware.

## Day 9 — The Tampered-Fixture Corpus
- Built the answer key before building the thing it grades. `quantum_qr/fixtures.py` produces authentic and deliberately tampered QRs, and `data/fixtures/manifest.json` records each one's ground-truth verdict and expected secret.
- You genuinely can't evaluate a verifier without labeled test data. Manufacturing my own corpus — with varied, deliberate attacks (data swap, nonce swap, tag flip, wrong-key forgery, corruption) — is something I'd never have thought to do, but it's obviously how you'd validate a real security tool.
- The 1-in-256 false-negative rate stopped being an abstract line in DESIGN.md and became code I had to handle: the builder now asserts every tampered fixture has a non-zero secret, and retries on the rare collision. The collision rate is exactly 2^(−n_bits) — a concrete reason production would use a larger tag.
- Reused Day 8's injected-nonce seam to make every fixture reproducible. The testability hook I added "for later" turned out to be load-bearing one day later.

## Day 10 — Command-Line Interface
- Wrapped the generator in a proper CLI: `python -m quantum_qr generate "..." -o out.png`. Needed a `cli.py` (argparse with subcommands) and a `__main__.py` to make `python -m quantum_qr` work.
- Building a CLI forced me to think about how the tool gets *used*, not just whether it works: exit codes so it can chain in shell scripts (`... && echo ok`), a `--json` flag so other programs can capture the nonce and tag, and friendly error messages instead of dumping a stack trace at the user.
- Designed `main(argv=None)` so tests can drive the CLI by passing an argument list directly — no subprocess spawning, no `sys.argv` monkeypatching. Same testability instinct as the injected nonce on Day 8: make the external input a parameter.
- Used a subcommand structure (`generate` now, `verify` reserved) so next week's verifier slots in without restructuring. Designing the seam before I need it.
- Learned the exit-code convention the hard way: argparse exits with code 2 on usage errors all on its own, so I only had to handle 0 (success) and 1 (application error like bad data).

## Day 11 — Generator Polish
- No new features — a quality pass. Consistent Google-style docstrings and full type hints across every module, a clean public API in `__init__.py` (`from quantum_qr import generate` now works), a package docstring, and `__version__`.
- Polish day felt low-stakes but it's exactly what makes a repo trustworthy at a glance. A reviewer judges quality in seconds from the import surface and docstring consistency, long before they read the logic.
- Pinned dependencies in `requirements.txt` so the project actually installs for someone else — an unpinned Qiskit could pull a breaking version on a fresh clone.
- **Best 40 minutes of the day:** the QR gallery. Generating the same message twice produces two *visibly different* QR images because each gets a fresh quantum nonce. That single picture is the strongest one-glance argument for why a quantum-random nonce matters — it makes replay resistance visible.
- This closes the generator phase: the tool is feature-complete, robust, documented, runnable from the command line, and visually demonstrated. Everything from here is the verifier — where the quantum circuit finally does the judging.

## Day 12 — The Quantum Verifier
- Built `quantum_qr/verifier.py`. `verify()` reads a QR, recomputes the expected tag, derives the secret, builds the DJ circuit from it, runs it on the simulator, and returns a verdict driven by the quantum measurement. The system now makes an authentic-vs-tampered decision.
- **The most important realisation of the whole project:** the DJ verifier round-trips perfectly on a simulator because building the oracle requires the very secret that DJ then recovers. I stopped seeing that as a flaw and started seeing it as the honest truth of the project — the quantum step is *demonstrative* on a noiseless simulator, and its robustness only becomes a real, measurable quantity on noisy hardware (Days 17–18). Being able to say that clearly is worth more than pretending the quantum part does something a classical check couldn't.
- Added an `agree` field comparing the DJ-measured secret to the classically-derived one. On the simulator it's `True` every time, which is a built-in correctness check on the circuit construction.
- Bit ordering bit me again, exactly where I expected — the measured secret came out reversed relative to the manifest until I applied the convention consistently. Glad I documented it on Day 2.
- Wrote a test proving that verifying with the *wrong* key flags an authentic QR as tampered. That's the security property made concrete: without the shared key, verification fails. The key is load-bearing, not decorative.

## Day 13 — Corpus Evaluation Harness
- Built `quantum_qr/evaluate.py`. `evaluate_corpus()` runs `verify()` across the whole labeled corpus and scores it against the manifest — accuracy, recall, precision, a confusion matrix, and a per-tamper-type breakdown.
- Framed tamper detection as a binary classifier where **recall is the metric that matters**, because a false negative means accepting a forgery — far worse than a false positive (rejecting a real QR). Saying which error is worse, and why, is part of taking a security tool seriously.
- Got 100% on the simulator, and made myself write down honestly what that does and doesn't mean: it confirms the corpus, the integration, and the bit-ordering are all consistent. It is **not** evidence that quantum adds detection power — on a noiseless simulator the DJ readout matches the classical secret by construction. The real accuracy test is on noisy hardware.
- Hardened `verify()` to return `"invalid"` (rather than crash) on undecodable/corrupted QRs. A real verifier must never throw on malformed input — an unparseable QR is simply not authentic.
- Froze the simulator result to `data/eval_simulator.json` as a baseline, so the Day 18 hardware run becomes a clean before/after comparison.

## Day 14 — Probabilistic Decision Rule + Noise
- Separated `decide()` (a pure function: counts histogram → verdict) from the quantum execution. Now I can unit-test the decision logic with hand-built distributions and no circuits at all — the cleanest seam I've added yet.
- Added an accept threshold on `P(zeros)` and an "inconclusive" confidence floor. On a noiseless simulator the verdict is unchanged (P(zeros) is exactly 1.0 or 0.0), but these become essential the moment hardware noise spreads the outcomes.
- Simulated depolarizing noise with `qiskit-aer` and watched the clean DJ peak smear out as noise rose. That made the threshold and the inconclusive band feel *necessary* rather than arbitrary.
- The noise sweep plot (`data/noise_sweep.png`) is the first piece of analysis in this whole project that a classical HMAC simply couldn't produce — it's genuinely about quantum execution behaviour. Authentic `P(zeros)` starts at 1.0 and decays; tampered stays near 0; the threshold line shows the noise budget the verifier tolerates.
- **Debugging lesson of the day:** my first sweep plot had both curves flat at zero. The tell was the noiseless endpoint — at p=0 the authentic curve *must* be 1.0, so a flat-zero authentic curve is a bug, not physics. The cause was the ancilla sneaking into the measurement register, so my `"0"*n_bits` lookup never matched the longer counts keys. **Always sanity-check the value you already know before trusting the rest of the curve.**

## Day 15 — verify CLI Subcommand
- Added the `verify` command, completing the CLI (`generate` + `verify`). The reserved subcommand slot from Day 10 meant it dropped in cleanly.
- **Made the exit codes encode the verdict:** 0 authentic, 3 tampered, 4 invalid, 1 operational error, 2 usage. So the tool gates shell pipelines like `verify qr.png && release_funds.sh`, the way `grep` returns 1 on no match.
- Thinking about how a tool *composes* with other tools — not just whether it runs — is a step up in how I design software.
- Surfacing which bits differ on a tampered result shows the quantum measurement carried real information, not just a yes/no.

## Day 16 — Verifier Polish + Backend Injection
- Docstring and type-hint pass on `verifier.py` and `evaluate.py` to match the rest of the codebase.
- **Made the quantum backend an injectable parameter**, defaulting to the simulator. Running on real hardware next week is now a one-line change — pass a different backend — not a rewrite.
- That's the *fourth* time I've reached for the same pattern: make the swappable thing a parameter (nonce → argv → key → backend). It's becoming my signature move, and it's the right instinct every time.
- Added `verify` and `decide` to the public API; bumped `__version__` to 0.2.0 now that verification exists.
- Built a confusion-matrix plotter and rendered noiseless vs noisy side by side (`data/confusion_matrix.png`). The noiseless matrix proves the logic is correct; the noisy one previews what hardware will do — and shows which error type (false negative vs false positive) noise produces first. An honest, real result that also validates the plotting code before hardware data arrives.

## Day 17 — (next)