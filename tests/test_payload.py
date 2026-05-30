import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from quantum_qr import payload  # Adjust import path based on your project structure

# --- Test Fixtures/Constants ---
SECRET_KEY = b"test_shared_secret_key_123"
DEFAULT_DATA = "pay alice $10"
DEFAULT_NONCE = "0110100101101001"


def test_compute_tag_deterministic():
    """compute_tag is deterministic (same inputs -> same tag)"""
    tag1 = payload.compute_tag(
        key=SECRET_KEY, 
        data=DEFAULT_DATA, 
        nonce=DEFAULT_NONCE, 
        n_bits=8
    )
    tag2 = payload.compute_tag(
        key=SECRET_KEY, 
        data=DEFAULT_DATA, 
        nonce=DEFAULT_NONCE, 
        n_bits=8
    )
    
    assert tag1 == tag2
    assert len(tag1) == 8


def test_compute_tag_changes_with_data():
    """Changing the data changes the tag"""
    tag_alice = payload.compute_tag(
        key=SECRET_KEY, 
        data="pay alice $10", 
        nonce=DEFAULT_NONCE
    )
    tag_bob = payload.compute_tag(
        key=SECRET_KEY, 
        data="pay bob $10", 
        nonce=DEFAULT_NONCE
    )
    
    assert tag_alice != tag_bob


def test_encode_decode_payload():
    """encode_payload then decode_payload returns the original dict"""
    tag = payload.compute_tag(SECRET_KEY, DEFAULT_DATA, DEFAULT_NONCE)
    
    original_payload = payload.build_payload(
        data=DEFAULT_DATA, 
        nonce=DEFAULT_NONCE, 
        tag=tag
    )
    
    encoded = payload.encode_payload(original_payload)
    decoded = payload.decode_payload(encoded)
    
    assert original_payload == decoded


def test_tags_to_secret_identical():
    """tags_to_secret of two identical tags is all zeros"""
    tag = "10101010"
    secret = payload.tags_to_secret(tag, tag)
    
    assert secret == "00000000"


def test_tags_to_secret_different():
    """tags_to_secret of two different tags has at least one 1"""
    tag1 = "10101010"
    tag2 = "10101011"  # Last bit flipped
    secret = payload.tags_to_secret(tag1, tag2)
    
    assert "1" in secret
    assert secret == "00000001"


def test_tags_to_secret_length_mismatch_raises():
    """tags_to_secret raises on length mismatch"""
    tag_short = "1010"
    tag_long = "10101010"
    
    # Python's assert statement raises an AssertionError
    with pytest.raises(AssertionError, match="Tags must have the same length"):
        payload.tags_to_secret(tag_short, tag_long)