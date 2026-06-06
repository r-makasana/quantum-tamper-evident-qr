import os
import pytest
from quantum_qr.verifier import decide, verify

# --- Gap 1: Threshold Sensitivity ---
def test_decide_threshold_sensitivity():
    """
    A custom accept_threshold changes the verdict on a borderline histogram.
    """
    # Create a histogram where P(zeros) = 600 / 1000 = 0.6
    counts = {"00000000": 600, "10101010": 400}
    
    # At a loose threshold (0.5), P(zeros) of 0.6 is acceptable
    res_loose = decide(counts, n_bits=8, accept_threshold=0.5)
    assert res_loose["verdict"] == "authentic"
    
    # At a strict threshold (0.7), P(zeros) of 0.6 fails validation
    res_strict = decide(counts, n_bits=8, accept_threshold=0.7)
    assert res_strict["verdict"] == "tampered"

# --- Gap 2: End-to-End Fixture Verification ---
# We use pytest.mark.parametrize to run the same test across all fixture types cleanly
@pytest.mark.parametrize("fixture_name, expected_verdict", [
    ("fixture_00_authentic.png", "authentic"), # Authentic
    ("fixture_01_data.png", "tampered"),      # Data Tampered
    ("fixture_02_nonce.png", "tampered"),     # Nonce Tampered
    ("fixture_03_tag.png", "tampered"),       # Tag Tampered
    ("fixture_04_forged.png", "tampered")     # Total Forgery
])
def test_verify_all_fixture_types(fixture_name, expected_verdict):
    """
    verify() produces the correct verdict for one fixture of each tamper type.
    """
    fixture_path = os.path.join("data/fixtures", fixture_name)
    
    # Gracefully skip if fixtures haven't been generated in this environment
    if not os.path.exists(fixture_path):
        pytest.skip(f"Fixture {fixture_name} not found. Run fixture generator first.")
        
    result = verify(fixture_path, n_bits=8, shots=1024)
    assert result["verdict"] == expected_verdict

def test_verify_corrupted_image(tmp_path):
    """
    verify() on a corrupted image produces an 'invalid' verdict.
    """
    corrupt_path = tmp_path / "corrupt_data.png"
    corrupt_path.write_text("This is definitely not a valid QR code or PNG file.")
    
    result = verify(str(corrupt_path))
    assert result["verdict"] == "invalid"
    assert "Decode failure" in result.get("reason", "")