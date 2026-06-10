import os
import random
from quantum_qr import generate, verify
from quantum_qr.qr_io import read_qr_code, make_qr_code
from quantum_qr.payload import encode_payload, decode_payload
from qiskit_aer.noise import NoiseModel, depolarizing_error
from qiskit_aer import AerSimulator

def get_noisy_backend():
    noise_model = NoiseModel()
    error = depolarizing_error(0.01, 1) # 1% error
    noise_model.add_all_qubit_quantum_error(error, ['u1', 'u2', 'u3'])
    return AerSimulator(noise_model=noise_model)

def run_blind_holdout(n_samples=1000, use_noise=False):
    test_dir = "blind_test_data"
    os.makedirs(test_dir, exist_ok=True)
    answers = {}
    backend = get_noisy_backend() if use_noise else None
    
    print(f"Generating {n_samples} samples...")
    for i in range(n_samples):
        msg = f"Message {i}"
        path = os.path.join(test_dir, f"test_{i:04d}.png")
        
        if random.random() < 0.5:
            generate(msg, path)
            answers[path] = "authentic"
        else:
            generate(msg, path)
            # Tamper: Edit data, retain tag
            payload = decode_payload(read_qr_code(path))
            payload["data"] = "Tampered"
            make_qr_code(encode_payload(payload), path)
            answers[path] = "tampered"

    print("Running verification...")
    false_negatives = 0
    correct = 0
    
    for path, expected in answers.items():
        # verify() now supports backend injection
        verdict = verify(path, backend=backend)["verdict"]
        
        if verdict == expected:
            correct += 1
        elif expected == "tampered" and verdict == "authentic":
            false_negatives += 1
            
    total_tampered = sum(1 for v in answers.values() if v == "tampered")
    print(f"\n--- Results ---")
    print(f"Accuracy: {correct/n_samples:.2%}")
    print(f"False Negatives (Collisions): {false_negatives} / {total_tampered}")
    print(f"Observed Collision Rate: {false_negatives/total_tampered:.4%}")

if __name__ == "__main__":
    run_blind_holdout(n_samples=1000, use_noise=True)