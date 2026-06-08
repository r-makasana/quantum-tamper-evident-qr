"""
Quantum verification engine for Tamper-Evident QR codes.

This module orchestrates the reading, decoding, and quantum simulation/execution
necessary to verify a payload's authenticity using the Deutsch-Jozsa algorithm.
"""

from typing import Optional, Dict, Any
from qiskit import transpile, QuantumCircuit
from qiskit.providers import Backend
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import SamplerV2 as Sampler
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

from quantum_qr.qr_io import read_qr_code
from quantum_qr.payload import decode_payload, compute_tag, tags_to_secret
from quantum_qr.config import get_key
from quantum_qr.dj import oracle_from_secret_string, dj_circuit


def run_counts(circuit: QuantumCircuit, backend: Optional[Backend] = None, shots: int = 1024) -> Dict[str, int]:
    """
    Run a circuit on any backend and return a counts dict.
    
    Args:
        circuit: The QuantumCircuit to execute.
        backend: Optional backend (AerSimulator or IBM Runtime backend).
        shots: Number of times to execute the circuit.
        
    Returns:
        Dict[str, int]: Histogram of measurement outcomes.
    """
    # 1. Fallback to local simulator path
    if backend is None or isinstance(backend, AerSimulator):
        sim = backend or AerSimulator()
        compiled = transpile(circuit, sim)
        return sim.run(compiled, shots=shots).result().get_counts()
    
    # 2. Modern Runtime path (IBM Hardware)
    else:
        # Transpile to ISA (Instruction Set Architecture) for the specific QPU
        pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
        isa_circuit = pm.run(circuit)
        
        # Run via SamplerV2
        sampler = Sampler(backend)
        job = sampler.run([(isa_circuit,)], shots=shots)
        
        # Extract counts from the first pub result (using register 'c')
        return job.result()[0].data.c.get_counts()


def decide(
    counts: Dict[str, int],
    n_bits: int,
    accept_threshold: float = 0.5,
    confidence_floor: float = 0.0,
) -> Dict[str, Any]:
    """
    Turn a quantum measurement shot-count histogram into a probabilistic verdict.
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

    # 5. Run using the new execution abstraction layer
    # This automatically dispatches to local simulator or hardware as needed
    counts = run_counts(built_circuit, backend=backend, shots=shots)

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