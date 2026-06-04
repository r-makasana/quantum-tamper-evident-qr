import hmac
import hashlib
import json
import base64


def compute_tag(key: bytes, data: str, nonce: str | list[int], n_bits: int = 8) -> str:
    """
    Compute an HMAC-SHA256 tag truncated to n bits.

    Args:
        key: Shared secret key for HMAC validation.
        data: The message being protected.
        nonce: Quantum-random nonce bound into the tag.
        n_bits: Tag width in bits to retain (1-32).

    Returns:
        An n_bits-length binary string, e.g., '01101001'.
    """
    if isinstance(nonce, list):
        nonce = "".join(str(bit) for bit in nonce)

    message = (data + nonce).encode("utf-8")

    digest = hmac.new(key, message, hashlib.sha256).digest()

    bit_string = "".join(f"{byte:08b}" for byte in digest)
    return bit_string[:n_bits]


def build_payload(
    data: str, nonce: str | list[int], tag: str, version: str = "1"
) -> dict:
    """
    Assemble the QR payload dictionary according to the standard schema.

    Args:
        data: The protected string message.
        nonce: The quantum-generated nonce.
        tag: The truncated HMAC validation tag.
        version: Schema version string.

    Returns:
        A dictionary containing the structured payload.
    """
    return {
        "version": version,
        "data": data,
        "nonce": (
            "".join(str(bit) for bit in nonce) if isinstance(nonce, list) else nonce
        ),
        "tag": tag,
    }


def encode_payload(payload: dict) -> str:
    """
    Encode a payload dictionary into a compact Base64 string for QR storage.

    Args:
        payload: The structured payload dictionary.

    Returns:
        A Base64 encoded string representing the minified JSON payload.
    """
    json_str = json.dumps(payload, separators=(",", ":"))
    encoded = base64.b64encode(json_str.encode("utf-8"))
    return encoded.decode("utf-8")


def decode_payload(b64: str) -> dict:
    """
    Decode a Base64 payload string back into a Python dictionary.

    Args:
        b64: The Base64 encoded string retrieved from a QR code.

    Returns:
        The decoded payload as a dictionary.
    """
    json_str = base64.b64decode(b64.encode("utf-8")).decode("utf-8")
    return json.loads(json_str)


def tags_to_secret(tag_observed: str, tag_expected: str) -> str:
    """
    Perform a bitwise XOR of two equal-length binary tags to determine the oracle secret.

    Args:
        tag_observed: The tag extracted from the QR code.
        tag_expected: The tag recomputed by the verifier using the shared key.

    Returns:
        A binary string representing the XOR difference. All zeros indicates an authentic payload.

    Raises:
        AssertionError: If the provided tags differ in length.
    """
    assert len(tag_observed) == len(tag_expected), "Tags must have the same length"

    return "".join("1" if a != b else "0" for a, b in zip(tag_observed, tag_expected))
