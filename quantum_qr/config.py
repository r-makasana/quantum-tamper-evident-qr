import os


def get_key() -> bytes:
    """
    Return the shared HMAC key.

    Reads from the QTQR_KEY environment variable.

    Falls back to a demo key for local development and testing only.
    This fallback MUST NOT be used in production.
    """

    key = os.environ.get("QTQR_KEY")

    if key is not None:
        return key.encode("utf-8")

    # Local development/testing fallback only.
    # In a real deployment, the key should come from a secure source.
    return b"DEMO_KEY_DO_NOT_USE_IN_PRODUCTION"