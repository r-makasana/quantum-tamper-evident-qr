from typing import Optional
from qiskit import transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel

from quantum_qr.qr_io import read_qr_code
from quantum_qr.payload import decode_payload, compute_tag, tags_to_secret
from quantum_qr.config import get_key
from quantum_qr.dj import oracle_from_secret_string, dj_circuit

def decide(counts: dict[str, int], n_bits: int, 
           accept_threshold: float = 0.5, 
           confidence_floor: float = 0.0) -> dict:
    """
    Turn a shot-count histogram into a probabilistic verdict.
    """
    total_shots = sum(counts.values())
    if total_shots == 0:
        return {"verdict": "invalid", "confidence": 0.0, "p_zeros": 0.0, "measured_secret": None}

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
        "measured_secret": best_outcome
    }

def verify(qr_path: str, n_bits: int = 8, key: Optional[bytes] = None, 
           shots: int = 1024, accept_threshold: float = 0.5, 
           confidence_floor: float = 0.0, noise_model: Optional[NoiseModel] = None) -> dict:
    """
    Read a QR, run the DJ tamper check, and return a verdict dict.
    """
    # 1. Safely attempt to read and decode
    try:
        b64_payload = read_qr_code(qr_path)
        decoded = decode_payload(b64_payload)
        data = decoded['data']
        nonce = decoded['nonce']
        tag_observed = decoded['tag']
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
            "counts": None
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
    
    # 5. Run on simulator (with optional noise injection)
    simulator = AerSimulator(noise_model=noise_model)
    compiled_circuit = transpile(built_circuit, simulator)
    job = simulator.run(compiled_circuit, shots=shots)
    counts = job.result().get_counts()
    
    # 6. Decide based on probability distribution
    decision = decide(
        counts, 
        n_bits, 
        accept_threshold=accept_threshold, 
        confidence_floor=confidence_floor
    )
    
    return {
        **decision,
        "data": data,
        "classical_secret": classical_secret,
        "agree": decision["measured_secret"] == ("0" * n_bits) if decision["verdict"] == "authentic" else True
    }