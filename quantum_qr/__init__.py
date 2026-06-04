"""Quantum Tamper-Evident QR Codes.

A QR system using quantum-random nonces and the Deutsch-Jozsa algorithm
for single-query tamper verification.
"""

from quantum_qr.generator import generate
from quantum_qr.payload import decode_payload, compute_tag, tags_to_secret
from quantum_qr.qr_io import make_qr_code, read_qr_code

# Explicitly define the public API of the package
__all__ = [
    "generate",
    "decode_payload",
    "compute_tag",
    "tags_to_secret",
    "make_qr_code",
    "read_qr_code",
]

__version__ = "0.1.0"
