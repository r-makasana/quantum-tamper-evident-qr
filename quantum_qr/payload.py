import hmac
import hashlib
import json
import base64


def compute_tag(
    key: bytes,
    data: str,
    nonce,          # Removed strict str type hint so it accepts lists as well
    n_bits: int = 8
) -> str:
    """
    Compute an HMAC-based integrity tag.

    HMAC is used instead of plain SHA-256 because only someone who
    knows the secret key can generate a valid tag.

    Args:
        key: Shared secret key.
        data: Payload data.
        nonce: Quantum-generated nonce (accepts string or list of bits).
        n_bits: Number of bits to keep from the HMAC output.

    Returns:
        Binary string of length n_bits.
        Example: '01101001'
    """

    # FIX: Ensure nonce is a string before concatenating
    if isinstance(nonce, list):
        nonce = "".join(str(bit) for bit in nonce)

    # Concatenate payload components
    message = (data + nonce).encode("utf-8")

    # Compute HMAC-SHA256
    digest = hmac.new(
        key,
        message,
        hashlib.sha256
    ).digest()

    # Convert bytes to a binary string
    bit_string = ''.join(
        f'{byte:08b}'
        for byte in digest
    )

    # Return first n bits
    return bit_string[:n_bits]


def build_payload(
    data: str,
    nonce: str,
    tag: str,
    version: str = "1"
) -> dict:
    """
    Assemble the QR payload according to the schema.
    """

    return {
        "version": version,
        "data": data,
        # Ensure nonce is stored as a string in the dictionary
        "nonce": "".join(str(bit) for bit in nonce) if isinstance(nonce, list) else nonce,
        "tag": tag
    }


def encode_payload(payload: dict) -> str:
    """
    Convert:
        dict -> compact JSON -> base64 string

    This base64 string is what gets stored inside the QR code.
    """

    json_str = json.dumps(
        payload,
        separators=(',', ':')
    )

    encoded = base64.b64encode(
        json_str.encode("utf-8")
    )

    return encoded.decode("utf-8")


def decode_payload(b64: str) -> dict:
    """
    Convert:
        base64 string -> JSON -> dict
    """

    json_str = base64.b64decode(
        b64.encode("utf-8")
    ).decode("utf-8")

    return json.loads(json_str)


def tags_to_secret(
    tag_observed: str,
    tag_expected: str
) -> str:
    """
    Bitwise XOR of two equal-length binary tag strings.

    Matching tags:
        00000000
        -> authentic
        -> constant oracle

    Differing tags:
        non-zero bitstring
        -> tampered
        -> balanced oracle

    Returns:
        XOR result as a binary string.
    """

    assert len(tag_observed) == len(tag_expected), (
        "Tags must have the same length"
    )

    return ''.join(
        '1' if a != b else '0'
        for a, b in zip(tag_observed, tag_expected)
    )