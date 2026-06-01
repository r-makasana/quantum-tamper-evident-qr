import sys
import os

# Add the parent directory to Python's search path
sys.path.append(os.path.abspath('..'))
from quantum_qr.config import get_key
from quantum_qr.qrng import generate_quantum_random_bits
from quantum_qr.payload import (
    compute_tag,
    build_payload,
    encode_payload
)
from quantum_qr.qr_io import make_qr_code


def generate(
    data: str,
    output_path: str,
    n_bits: int = 8,
    key: bytes | None = None
) -> dict:
    """
    Create a tamper-evident QR for `data`, write the QR image
    to `output_path`, and return metadata describing what was produced.
    """

    if key is None:
        key = get_key()

    # Generate quantum nonce
    nonce = generate_quantum_random_bits(128)

    # Compute HMAC-derived tag
    tag = compute_tag(key, data, nonce, n_bits)

    # Build payload
    payload = build_payload(data, nonce, tag)

    # Encode payload for QR storage
    qr_string = encode_payload(payload)

    # Write QR image
    make_qr_code(qr_string, output_path)

    return {
        "payload": payload,
        "qr_string": qr_string,
        "output_path": output_path
    }