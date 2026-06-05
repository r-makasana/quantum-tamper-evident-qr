import os
import json
import pytest
import qrcode

from quantum_qr.generator import generate
from quantum_qr.verifier import verify

# Keys for testing the cryptographic properties
TEST_KEY = b"TEST_SECRET_KEY_12345"
WRONG_KEY = b"WRONG_KEY_99999999999"

def test_verify_authentic_qr(tmp_path):
    """Verify that a freshly generated QR passes verification."""
    # tmp_path is a built-in pytest fixture that creates a temporary directory
    qr_path = str(tmp_path / "auth_test.png")
    
    # 1. Generate an authentic QR
    generate("pay bob $50", qr_path, key=TEST_KEY)
    
    # 2. Verify it with the same key
    result = verify(qr_path, key=TEST_KEY)
    
    # 3. Assertions
    assert result["verdict"] == "authentic"
    assert result["agree"] is True
    # If it's authentic, the target secret should be all zeros (assuming 8-bit default)
    assert result["measured_secret"] == "00000000"


def test_verify_tampered_fixture():
    """Verify a tampered fixture fails and matches the expected manifest secret."""
    manifest_path = "data/fixtures/manifest.json"
    
    # Safely skip this test if the fixtures haven't been generated yet
    if not os.path.exists(manifest_path):
        pytest.skip("Fixtures not found. Run the fixture generation script first.")
        
    # Load the JSON list
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
        
    # FIX: Loop through the manifest and explicitly find a tampered fixture
    tampered_fixture = None
    for item in manifest:
        # If the secret has a '1' in it, the tags didn't match, meaning it's tampered!
        if "1" in item["expected_secret"]:
            tampered_fixture = item
            break
            
    if tampered_fixture is None:
        pytest.skip("Could not find a tampered fixture in the manifest to test.")
        
    # Handle whichever key name your JSON uses
    fixture_name = tampered_fixture.get("filename") or tampered_fixture.get("file")
    expected_secret = tampered_fixture["expected_secret"]
    
    fixture_path = f"data/fixtures/{fixture_name}"
    
    # Verify it (letting it fall back to the config.py DEMO key used for fixtures)
    result = verify(fixture_path)
    
    # Assertions
    assert result["verdict"] == "tampered"
    assert result["measured_secret"] == expected_secret
    
    # This proves classical_secret == measured_secret ALWAYS holds on the simulator
    assert result["agree"] is True

def test_verify_wrong_key(tmp_path):
    """Prove the security property: verifying with the wrong key flags it as tampered."""
    qr_path = str(tmp_path / "wrong_key_test.png")
    
    # 1. Generate with the CORRECT key
    generate("pay charlie $100", qr_path, key=TEST_KEY)
    
    # 2. Verify with the WRONG key
    result = verify(qr_path, key=WRONG_KEY)
    
    # 3. Assertions
    assert result["verdict"] == "tampered"
    
    # Even though it's "tampered", the simulator should still perfectly read 
    # the non-zero secret created by the mismatched tags.
    assert result["agree"] is True

def test_verify_invalid_qr(tmp_path):
    """Verify that a corrupted or undecodable QR returns an 'invalid' verdict."""
    qr_path = str(tmp_path / "garbage_qr.png")
    
    # Create a perfectly valid image, but with a garbage payload
    img = qrcode.make("This is definitely not a base64 encoded JSON string!")
    img.save(qr_path)
    
    # Verify it
    result = verify(qr_path)
    
    # Assertions
    assert result["verdict"] == "invalid"
    assert "reason" in result
    assert result["agree"] is False
    assert result["measured_secret"] is None

from quantum_qr.verifier import decide

def test_decide_logic():
    # 1. Clear Authentic
    res1 = decide({"00000000": 1000}, n_bits=8)
    assert res1["verdict"] == "authentic"
    assert res1["confidence"] == 1.0

    # 2. Clear Tampered
    res2 = decide({"10110010": 1000}, n_bits=8)
    assert res2["verdict"] == "tampered"

    # 3. Threshold sensitivity (p_zeros = 0.6)
    counts = {"00000000": 600, "11111111": 400}
    # Pass at 0.5 threshold
    assert decide(counts, 8, accept_threshold=0.5)["verdict"] == "authentic"
    # Fail at 0.7 threshold
    assert decide(counts, 8, accept_threshold=0.7)["verdict"] == "tampered"

    # 4. Confidence floor
    # A flat distribution with low confidence
    flat_counts = {"00000000": 250, "11111111": 250, "01010101": 250, "10101010": 250}
    res4 = decide(flat_counts, 8, confidence_floor=0.3)
    assert res4["verdict"] == "inconclusive"