from pathlib import Path
import os
from qrcode.exceptions import DataOverflowError

from quantum_qr.config import get_key
from quantum_qr.qrng import generate_quantum_random_bits
from quantum_qr.payload import compute_tag, build_payload, encode_payload
from quantum_qr.qr_io import make_qr_code

MAX_QR_PAYLOAD = 2000


def generate(
    data: str,
    output_path: str,
    n_bits: int = 8,
    key: bytes | str | None = None,
    nonce: str | None = None,
) -> dict:
    """
    Create a tamper-evident QR code and save it to disk.

    Args:
        data: The primary string payload to protect.
        output_path: The file path where the resulting QR code image will be saved.
        n_bits: The length of the HMAC tag and target quantum register (1-32).
        key: Optional shared secret key. If None, loaded from the environment.
        nonce: Optional fixed nonce for testing. If None, a quantum nonce is generated.

    Returns:
        A dictionary containing the payload, the encoded QR string, and the output path.

    Raises:
        ValueError: If data is empty, n_bits is invalid, or the payload is too large.
        TypeError: If the key format is not bytes or string.
    """
    if not isinstance(data, str) or not data.strip():
        raise ValueError("data must be a non-empty string")

    if not isinstance(n_bits, int):
        raise ValueError("n_bits must be an integer")

    if not (1 <= n_bits <= 32):
        raise ValueError("n_bits must be between 1 and 32")

    if key is None:
        key = get_key()
    elif isinstance(key, str):
        key = key.encode("utf-8")
    elif not isinstance(key, bytes):
        raise TypeError("key must be bytes, str, or None")

    output_dir = Path(output_path).parent
    if str(output_dir) != "":
        os.makedirs(output_dir, exist_ok=True)

    if nonce is None:
        nonce = generate_quantum_random_bits(128)

    tag = compute_tag(key, data, nonce, n_bits)
    payload = build_payload(data, nonce, tag)
    qr_string = encode_payload(payload)

    if len(qr_string) > MAX_QR_PAYLOAD:
        raise ValueError(
            f"QR payload exceeds maximum size ({len(qr_string)} > {MAX_QR_PAYLOAD} characters)"
        )

    try:
        make_qr_code(qr_string, output_path)
    except DataOverflowError as e:
        raise ValueError("QR payload is too large to encode") from e

    return {"payload": payload, "qr_string": qr_string, "output_path": output_path}
