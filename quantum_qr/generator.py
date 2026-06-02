# Add the parent directory to Python's search path
from pathlib import Path
import os

from quantum_qr.config import get_key
from quantum_qr.qrng import generate_quantum_random_bits
from quantum_qr.payload import (
    compute_tag,
    build_payload,
    encode_payload
)
from quantum_qr.qr_io import make_qr_code
from qrcode.exceptions import DataOverflowError
# Safe payload limit.
# QR Version 40 can hold more, but JSON + Base64 expansion
# makes it easy to exceed practical scan limits.
MAX_QR_PAYLOAD = 2000


def generate(
    data: str,
    output_path: str,
    n_bits: int = 8,
    key: bytes | str | None = None,
    nonce: str | None = None
) -> dict:
    """
    Create a tamper-evident QR for `data`, write the image to
    `output_path`, and return metadata describing what was produced.
    """

    # -----------------------------
    # Validate data
    # -----------------------------
    if not isinstance(data, str) or not data.strip():
        raise ValueError(
            "data must be a non-empty string"
        )

    # -----------------------------
    # Validate n_bits
    # -----------------------------
    # n_bits becomes the number of input qubits in the
    # DJ/Bernstein-Vazirani verifier. Large values become
    # impractical on current quantum hardware.
    if not isinstance(n_bits, int):
        raise ValueError(
            "n_bits must be an integer"
        )

    if not (1 <= n_bits <= 32):
        raise ValueError(
            "n_bits must be between 1 and 32"
        )

    # -----------------------------
    # Validate / normalize key
    # -----------------------------
    if key is None:
        key = get_key()

    elif isinstance(key, str):
        key = key.encode("utf-8")

    elif not isinstance(key, bytes):
        raise TypeError(
            "key must be bytes, str, or None"
        )

    # -----------------------------
    # Ensure output directory exists
    # -----------------------------
    output_dir = Path(output_path).parent

    if str(output_dir) != "":
        os.makedirs(
            output_dir,
            exist_ok=True
        )

    # -----------------------------
    # Generate quantum nonce
    # -----------------------------
    if nonce is None:
        nonce = generate_quantum_random_bits(128)

    # -----------------------------
    # Compute tag
    # -----------------------------
    tag = compute_tag(
        key,
        data,
        nonce,
        n_bits
    )

    payload = build_payload(
    data,
    nonce,
    tag
    )

    qr_string = encode_payload(payload)

    # Validate QR payload size before generating image
    if len(qr_string) > MAX_QR_PAYLOAD:
        raise ValueError(
            f"QR payload exceeds maximum size "
            f"({len(qr_string)} > {MAX_QR_PAYLOAD} characters)"
    )

    try:
        make_qr_code(
            qr_string,
            output_path
    )
    except DataOverflowError as e:
        raise ValueError(
        "QR payload is too large to encode"
    ) from e

    return {
        "payload": payload,
        "qr_string": qr_string,
        "output_path": output_path
    }