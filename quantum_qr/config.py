import os


def get_key() -> bytes:
    """
    Retrieve the shared HMAC secret key for tamper verification.

    Attempts to read from the 'QTQR_KEY' environment variable. If missing,
    it falls back to a hardcoded demo key for local testing.

    Returns:
        The secret key as bytes.
    """
    key = os.environ.get("QTQR_KEY")

    if key is not None:
        return key.encode("utf-8")

    return b"DEMO_KEY_DO_NOT_USE_IN_PRODUCTION"
