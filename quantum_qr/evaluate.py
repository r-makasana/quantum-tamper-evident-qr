import os
import json
from typing import Optional
from quantum_qr.verifier import verify

def evaluate_corpus(fixtures_dir: str, manifest_path: str, key: Optional[bytes] = None, shots: int = 1024) -> dict:
    """
    Run verify() on every fixture in the manifest, compute standard security metrics
    (Recall, Precision, Accuracy), and return a rich evaluation report.
    """
    # 1. Load the manifest
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
        
    # Counters for the confusion matrix (Positive = Tampered, Negative = Authentic)
    TP = 0  # True Positive:  Tampered correctly rejected
    FN = 0  # False Negative: Tampered wrongly accepted (Dangerous!)
    TN = 0  # True Negative:  Authentic correctly accepted
    FP = 0  # False Positive: Authentic wrongly rejected (False Alarm)
    
    per_fixture_results = []
    tamper_breakdown = {}
    
    # 2. Iterate through each fixture
    for item in manifest:
        filename = item.get("filename") or item.get("file")
        expected_secret = item["expected_secret"]
        # Standard corpora usually track the type of attack (e.g., 'data_tamper', 'tag_tamper')
        tamper_type = item.get("type", "unknown") 
        
        # Ground Truth Deduction
        is_expected_authentic = all(bit == '0' for bit in expected_secret)
        expected_verdict = "authentic" if is_expected_authentic else "tampered"
        
        filepath = os.path.join(fixtures_dir, filename)
        
        # 3. Run Verification
        result = verify(filepath, key=key, shots=shots)
        predicted_verdict = result["verdict"]
        
        # 4. Evaluate against the Confusion Matrix
        is_correct = False
        
        if expected_verdict == "tampered":
            # Initialize breakdown tracker for this tamper type
            if tamper_type not in tamper_breakdown:
                tamper_breakdown[tamper_type] = {"total": 0, "caught": 0}
            tamper_breakdown[tamper_type]["total"] += 1
            
            # Did we successfully catch the tamper? ("invalid" counts as a catch)
            if predicted_verdict in ["tampered", "invalid"]:
                TP += 1
                is_correct = True
                tamper_breakdown[tamper_type]["caught"] += 1
            else:
                FN += 1
                
        else: # expected_verdict == "authentic"
            if predicted_verdict == "authentic":
                TN += 1
                is_correct = True
            else:
                FP += 1

        # Record detail
        per_fixture_results.append({
        "filename": filename,
        "expected_verdict": expected_verdict,
        "predicted_verdict": predicted_verdict,
        "expected_secret": expected_secret,
        "measured_secret": result.get("measured_secret"),
        "confidence": result.get("confidence"), # Add this
        "p_zeros": result.get("p_zeros"),       # Add this
        "is_correct": is_correct,
        "reason": result.get("reason")
        })

    # 5. Calculate final InfoSec metrics safely (preventing division by zero)
    total = TP + TN + FP + FN
    accuracy = (TP + TN) / total if total > 0 else 0.0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
    
    # Calculate recall specifically per tamper type
    for t_type, stats in tamper_breakdown.items():
        stats["recall"] = stats["caught"] / stats["total"] if stats["total"] > 0 else 0.0

    # 6. Compile and return the report
    return {
        "metrics": {
            "total": total,
            "accuracy": accuracy,
            "recall": recall,       # The headline security metric
            "precision": precision
        },
        "confusion_matrix": {
            "TP": TP, "TN": TN,
            "FP": FP, "FN": FN
        },
        "breakdown": tamper_breakdown,
        "details": per_fixture_results
    }