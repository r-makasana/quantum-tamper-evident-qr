from typing import Optional
from qiskit import transpile
from qiskit_aer import AerSimulator

# Assuming these are the modules you built in the previous days:
from quantum_qr.qr_io import read_qr_code
from quantum_qr.payload import decode_payload, compute_tag, tags_to_secret
from quantum_qr.config import get_key
from quantum_qr.dj import oracle_from_secret_string, dj_circuit

def verify(qr_path: str, n_bits: int = 8, key: Optional[bytes] = None, shots: int = 1024) -> dict:
    """Read a QR, run the DJ tamper check, and return a verdict dict."""
    
    # 1. Read and decode the payload
    b64_payload = read_qr_code(qr_path)
    decoded = decode_payload(b64_payload)
    
    data = decoded['data']
    nonce = decoded['nonce']
    tag_observed = decoded['tag']
    
    # 2. Resolve the key
    if key is None:
        key = get_key()
        
    # 3. Recompute expected tag classically
    tag_expected = compute_tag(key, data, nonce, n_bits)
    
    # 4. Derive the classical secret (s)
    classical_secret = tags_to_secret(tag_observed, tag_expected)
    
    # 5. Build quantum circuits
    oracle = oracle_from_secret_string(classical_secret)
    built_circuit = dj_circuit(oracle, n_bits)
    
    # 6. Run on AerSimulator
    simulator = AerSimulator()
    compiled_circuit = transpile(built_circuit, simulator)
    job = simulator.run(compiled_circuit, shots=shots)
    result = job.result()
    counts = result.get_counts(compiled_circuit)
    
    # 7. Take the most frequent measured bitstring
    raw_measured = max(counts, key=counts.get)
    
    # Mind bit ordering (Task 4 anticipation): 
    # Qiskit outputs bitstrings in little-endian order (q_{n-1} ... q_0).
    # If your classical secret is ordered left-to-right (index 0 to n-1),
    # you usually need to reverse the Qiskit output so they match.
    measured_secret = raw_measured[::-1] 
    
    # 8. Verdict: all zeros -> authentic, anything else -> tampered
    is_authentic = all(bit == '0' for bit in measured_secret)
    verdict = "authentic" if is_authentic else "tampered"
    
    # 9. Return rich dict
    return {
        "verdict": verdict,
        "measured_secret": measured_secret,
        "classical_secret": classical_secret,
        "agree": measured_secret == classical_secret,
        "data": data,
        "counts": counts
    }