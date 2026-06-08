import os
from typing import List, Dict, Any, Optional
from qiskit.providers import Backend
from quantum_qr.verifier import verify


def evaluate_corpus(
    corpus_dir: str,
    n_bits: int = 8,
    shots: int = 1024,
    backend: Optional[Backend] = None,  # <-- Add backend parameter
) -> List[Dict[str, Any]]:
    """
    Run the quantum verifier against a directory of generated test fixtures.

    Args:
        corpus_dir (str): Path to the directory containing QR code fixtures.
        n_bits (int, optional): Number of bits in the secret. Defaults to 8.
        shots (int, optional): Number of quantum shots per run. Defaults to 1024.
        backend (Optional[Backend], optional): The Qiskit backend to run the
            simulations/hardware executions on. Defaults to AerSimulator.

    Returns:
        List[Dict[str, Any]]: Evaluation records for each fixture.
    """
    if not os.path.exists(corpus_dir):
        raise FileNotFoundError(f"Corpus directory not found: {corpus_dir}")

    results: List[Dict[str, Any]] = []

    for filename in sorted(os.listdir(corpus_dir)):
        if not filename.endswith(".png"):
            continue

        filepath = os.path.join(corpus_dir, filename)

        # Determine ground truth from filename
        if "baseline" in filename.lower() or "authentic" in filename.lower():
            expected_verdict = "authentic"
        else:
            expected_verdict = "tampered"

        # Execute the verification pipeline with the injected backend
        result = verify(
            filepath, n_bits=n_bits, shots=shots, backend=backend  # <-- Pass it through
        )

        predicted_verdict = result.get("verdict", "invalid")
        is_correct = predicted_verdict == expected_verdict

        results.append(
            {
                "filename": filename,
                "expected_verdict": expected_verdict,
                "predicted_verdict": predicted_verdict,
                "expected_secret": result.get("classical_secret"),
                "measured_secret": result.get("measured_secret"),
                "confidence": result.get("confidence", 0.0),
                "p_zeros": result.get("p_zeros", 0.0),
                "is_correct": is_correct,
                "reason": result.get("reason"),
            }
        )

    return results
