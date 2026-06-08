"""
Quantum verification engine for Tamper-Evident QR codes.

This module orchestrates the reading, decoding, and quantum simulation necessary
to verify a payload's authenticity using the Deutsch-Jozsa algorithm.
"""

from typing import Optional, Dict, Any
from qiskit import transpile
from qiskit.providers import Backend
from qiskit_aer import AerSimulator

from quantum_qr.qr_io import read_qr_code
from quantum_qr.payload import decode_payload, compute_tag, tags_to_secret
from quantum_qr.config import get_key
from quantum_qr.dj import oracle_from_secret_string, dj_circuit


def decide(
    counts: Dict[str, int],
    n_bits: int,
    accept_threshold: float = 0.5,
    confidence_floor: float = 0.0,
) -> Dict[str, Any]:
    """
    Turn a quantum measurement shot-count histogram into a probabilistic verdict.

    Evaluates the quantum measurement counts against a confidence floor and an
    acceptance threshold to determine if the payload is authentic, tampered,
    or if the result is inconclusive due to severe noise.

    Args:
        counts (Dict[str, int]): The measurement histogram from the quantum simulation or hardware.
        n_bits (int): The number of bits in the quantum register.
        accept_threshold (float, optional): The minimum probability of the all-zeros
            state required to declare the QR authentic. Defaults to 0.5.
        confidence_floor (float, optional): The minimum probability of the most frequent
            state required to make a conclusive decision. Defaults to 0.0.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - verdict (str): "authentic", "tampered", "inconclusive", or "invalid".
            - confidence (float): The probability of the single most frequent outcome.
            - p_zeros (float): The probability of the all-zeros outcome.
            - measured_secret (Optional[str]): The most frequent bitstring measured.
    """
    total_shots = sum(counts.values())
    if total_shots == 0:
        return {
            "verdict": "invalid",
            "confidence": 0.0,
            "p_zeros": 0.0,
            "measured_secret": None,
        }

    probs = {bitstring: count / total_shots for bitstring, count in counts.items()}

    # Normalize keys to big-endian (reversing Qiskit's little-endian output)
    normalized_probs = {k[::-1]: v for k, v in probs.items()}

    zeros_key = "0" * n_bits
    p_zeros = normalized_probs.get(zeros_key, 0.0)

    # Confidence: Probability of the single most frequent outcome
    best_outcome = max(normalized_probs, key=normalized_probs.get)
    confidence = normalized_probs[best_outcome]

    verdict = "tampered"
    if confidence < confidence_floor:
        verdict = "inconclusive"
    elif p_zeros >= accept_threshold:
        verdict = "authentic"

    return {
        "verdict": verdict,
        "confidence": confidence,
        "p_zeros": p_zeros,
        "measured_secret": best_outcome,
    }


def verify(
    qr_path: str,
    n_bits: int = 8,
    key: Optional[bytes] = None,
    shots: int = 1024,
    accept_threshold: float = 0.5,
    confidence_floor: float = 0.0,
    backend: Optional[Backend] = None,
) -> Dict[str, Any]:
    """
    Read a QR code, run the Deutsch-Jozsa tamper check, and return a verdict.

    This function orchestrates the entire verification pipeline: reading the image,
    decoding the payload, computing the expected tag, constructing the quantum
    circuits, executing the simulation, and applying the decision rule.

    Args:
        qr_path (str): The filesystem path to the QR code image.
        n_bits (int, optional): The number of bits in the secret/tag. Defaults to 8.
        key (Optional[bytes], optional): The secret key for HMAC. If None, it is loaded
            from the environment via config. Defaults to None.
        shots (int, optional): Number of quantum circuit executions. Defaults to 1024.
        accept_threshold (float, optional): Threshold for P(zeros) to accept as authentic. Defaults to 0.5.
        confidence_floor (float, optional): Minimum confidence to avoid an inconclusive result. Defaults to 0.0.
        backend (Optional[Backend], optional): The Qiskit backend to execute the
            circuit on. Defaults to AerSimulator() if None.

    Returns:
        Dict[str, Any]: A detailed dictionary containing the verification results:
            - verdict (str): "authentic", "tampered", "invalid", or "inconclusive".
            - confidence (float): The statistical confidence of the measurement.
            - p_zeros (float): The raw probability of measuring the all-zeros state.
            - measured_secret (Optional[str]): The observed bitstring.
            - classical_secret (Optional[str]): The expected classical secret.
            - data (Optional[str]): The decoded payload data.
            - agree (bool): True if the measured secret indicates authenticity.
            - reason (Optional[str]): Description of the error if the verdict is invalid.
    """
    # 1. Safely attempt to read and decode
    try:
        b64_payload = read_qr_code(qr_path)
        decoded = decode_payload(b64_payload)
        data = decoded["data"]
        nonce = decoded["nonce"]
        tag_observed = decoded["tag"]
    except Exception as e:
        return {
            "verdict": "invalid",
            "reason": f"Decode failure: {str(e)}",
            "measured_secret": None,
            "p_zeros": 0.0,
            "confidence": 0.0,
            "classical_secret": None,
            "agree": False,
            "data": None,
            "counts": None,
        }

    # 2. Resolve key
    if key is None:
        key = get_key()

    # 3. Compute expected tag and classical secret
    tag_expected = compute_tag(key, data, nonce, n_bits)
    classical_secret = tags_to_secret(tag_observed, tag_expected)

    # 4. Build quantum circuits
    oracle = oracle_from_secret_string(classical_secret)
    built_circuit = dj_circuit(oracle, n_bits)

    # 5. Run on backend (Dependency Injection)
    if backend is None:
        backend = AerSimulator()

    compiled_circuit = transpile(built_circuit, backend)
    job = backend.run(compiled_circuit, shots=shots)
    counts = job.result().get_counts()

    # 6. Decide based on probability distribution
    decision = decide(
        counts,
        n_bits,
        accept_threshold=accept_threshold,
        confidence_floor=confidence_floor,
    )

    return {
        **decision,
        "data": data,
        "classical_secret": classical_secret,
        "agree": (
            decision["measured_secret"] == ("0" * n_bits)
            if decision["verdict"] == "authentic"
            else True
        ),
    }
