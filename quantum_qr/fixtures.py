from pathlib import Path
import os
import json
from quantum_qr.payload import (
    compute_tag,
    build_payload,
    encode_payload,
    tags_to_secret
)
from quantum_qr.qr_io import make_qr_code

# ---------------------------------------------------------
# Helper Functions (The Attacker's Toolkit)
# ---------------------------------------------------------

def tamper_data(payload: dict, new_data: str) -> dict:
    """Return a copy with data changed but the original tag kept."""
    return {**payload, "data": new_data}

def tamper_nonce(payload: dict, new_nonce: str) -> dict:
    """Return a copy with nonce changed but the original tag kept."""
    return {**payload, "nonce": new_nonce}

def tamper_tag(payload: dict, new_tag: str) -> dict:
    """Return a copy with the tag flipped directly."""
    return {**payload, "tag": new_tag}

def forge_with_wrong_key(data: str, nonce: str, wrong_key: bytes, n_bits: int) -> dict:
    """An attacker's payload: tag computed with a key they don't actually share."""
    forged_tag = compute_tag(wrong_key, data, nonce, n_bits)
    return build_payload(data, nonce, forged_tag, version="1")

# ---------------------------------------------------------
# Main Fixture Builder
# ---------------------------------------------------------

def build_fixture_set(key: bytes, out_dir: str, n_bits: int = 8) -> list[dict]:
    """
    Create one authentic QR plus one of each tamper type, write the QR images
    to out_dir, and return a list of manifest entries (ground truth).
    Ensures no false-negative hash collisions occur due to truncation.
    """
    os.makedirs(out_dir, exist_ok=True)
    
    base_data = "pay alice $10"
    fixed_nonce = "10101010" * 16 
    
    # 1. Authentic Payload
    authentic_tag = compute_tag(key, base_data, fixed_nonce, n_bits)
    authentic_payload = build_payload(base_data, fixed_nonce, authentic_tag)
    
    # --- COLLISION SAFEGUARDS ---
    
    # Safe Data Tamper
    tamper_counter = 0
    while True:
        test_data = "pay attacker $1000" + (f" (try {tamper_counter})" if tamper_counter > 0 else "")
        test_tag = compute_tag(key, test_data, fixed_nonce, n_bits)
        if "1" in tags_to_secret(authentic_tag, test_tag):
            safe_tampered_data = test_data
            break
        tamper_counter += 1

    # Safe Nonce Tamper
    tamper_counter = 0
    while True:
        # Flip bits sequentially if collision occurs
        test_nonce = ("0" if fixed_nonce[tamper_counter] == "1" else "1") + fixed_nonce[1:]
        test_tag = compute_tag(key, base_data, test_nonce, n_bits)
        if "1" in tags_to_secret(authentic_tag, test_tag):
            safe_tampered_nonce = test_nonce
            break
        tamper_counter += 1
        
    # Safe Forgery
    tamper_counter = 0
    while True:
        wrong_key = b"HACKER_STOLEN_DEVICE" + str(tamper_counter).encode()
        forged_tag = compute_tag(wrong_key, base_data, fixed_nonce, n_bits)
        if "1" in tags_to_secret(forged_tag, authentic_tag):
            safe_wrong_key = wrong_key
            break
        tamper_counter += 1
        
    # Direct Tag Tamper (Guaranteed no collision)
    flipped_tag = ("0" if authentic_tag[0] == "1" else "1") + authentic_tag[1:]

    # 2. Compile Fixtures
    fixtures = [
        {
            "type": "authentic",
            "filename": "fixture_00_authentic.png",
            "payload": authentic_payload,
            "expected_verdict": "authentic"
        },
        {
            "type": "data_tampered",
            "filename": "fixture_01_data.png",
            "payload": tamper_data(authentic_payload, safe_tampered_data),
            "expected_verdict": "tampered"
        },
        {
            "type": "nonce_tampered",
            "filename": "fixture_02_nonce.png",
            "payload": tamper_nonce(authentic_payload, safe_tampered_nonce),
            "expected_verdict": "tampered"
        },
        {
            "type": "tag_tampered",
            "filename": "fixture_03_tag.png",
            "payload": tamper_tag(authentic_payload, flipped_tag),
            "expected_verdict": "tampered"
        },
        {
            "type": "forged",
            "filename": "fixture_04_forged.png",
            "payload": forge_with_wrong_key(
                base_data, fixed_nonce, safe_wrong_key, n_bits
            ),
            "expected_verdict": "tampered"
        }
    ]
    
    # 3. Generate QR codes and Manifest
    manifest = []
    for fx in fixtures:
        payload = fx["payload"]
        
        expected_tag = compute_tag(key, payload["data"], payload["nonce"], n_bits)
        expected_secret = tags_to_secret(payload["tag"], expected_tag)
        
        qr_string = encode_payload(payload)
        make_qr_code(qr_string, os.path.join(out_dir, fx["filename"]))
        
        manifest.append({
            "file": fx["filename"],
            "type": fx["type"],
            "expected_verdict": fx["expected_verdict"],
            "expected_secret": expected_secret
        })
        
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=4)
        
    return manifest