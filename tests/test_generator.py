import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from quantum_qr.generator import generate
from quantum_qr.payload import compute_tag, decode_payload
from quantum_qr.qr_io import read_qr_code

# ---------------------------------------------------------
# EXISTING SUCCESS-PATH TESTS
# ---------------------------------------------------------


def test_generate_creates_file(tmp_path):
    output_file = tmp_path / "test_qr.png"

    result = generate(
        data="pay alice $10", output_path=str(output_file), key=b"TEST_KEY"
    )

    assert output_file.exists()


def test_generate_computes_correct_tag(tmp_path):
    key = b"TEST_KEY"
    output_file = tmp_path / "test_qr.png"

    result = generate(data="pay alice $10", output_path=str(output_file), key=key)

    payload = result["payload"]

    expected_tag = compute_tag(key, payload["data"], payload["nonce"], n_bits=8)

    assert payload["tag"] == expected_tag


def test_generated_qr_round_trip(tmp_path):
    key = b"TEST_KEY"
    output_file = tmp_path / "test_qr.png"

    result = generate(data="pay alice $10", output_path=str(output_file), key=key)

    qr_string = read_qr_code(str(output_file))
    decoded_payload = decode_payload(qr_string)

    assert decoded_payload == result["payload"]


def test_same_data_produces_different_nonces(tmp_path):
    key = b"TEST_KEY"

    file1 = tmp_path / "qr1.png"
    file2 = tmp_path / "qr2.png"

    result1 = generate(data="pay alice $10", output_path=str(file1), key=key)

    result2 = generate(data="pay alice $10", output_path=str(file2), key=key)

    nonce1 = result1["payload"]["nonce"]
    nonce2 = result2["payload"]["nonce"]

    assert nonce1 != nonce2


# ---------------------------------------------------------
# NEW EDGE-CASE & FAILURE TESTS
# ---------------------------------------------------------


def test_empty_data_raises_value_error(tmp_path):
    with pytest.raises(ValueError, match="data must be a non-empty string"):
        generate(data="", output_path=str(tmp_path / "empty.png"), key=b"TEST")

    with pytest.raises(ValueError, match="data must be a non-empty string"):
        generate(data="   ", output_path=str(tmp_path / "empty2.png"), key=b"TEST")


def test_n_bits_out_of_bounds_raises_error(tmp_path):
    with pytest.raises(ValueError, match="n_bits must be between 1 and 32"):
        generate(
            data="valid", output_path=str(tmp_path / "0.png"), n_bits=0, key=b"TEST"
        )

    with pytest.raises(ValueError, match="n_bits must be between 1 and 32"):
        generate(
            data="valid", output_path=str(tmp_path / "100.png"), n_bits=100, key=b"TEST"
        )


def test_large_payload_raises_capacity_error(tmp_path):
    large_data = "A" * 5000
    with pytest.raises(ValueError, match="QR payload exceeds maximum size"):
        generate(data=large_data, output_path=str(tmp_path / "large.png"), key=b"TEST")


def test_unicode_payload_round_trips(tmp_path):
    unicode_data = "Pay Alice 10€ 💸 & ¥500"
    output_file = tmp_path / "unicode.png"

    result = generate(data=unicode_data, output_path=str(output_file), key=b"TEST")

    qr_string = read_qr_code(str(output_file))
    decoded_payload = decode_payload(qr_string)

    assert decoded_payload["data"] == unicode_data


def test_str_key_matches_bytes_key(tmp_path):
    # Using a fixed nonce ensures the only difference being tested is the key format
    fixed_nonce = "10101010"

    res_str = generate(
        data="test",
        output_path=str(tmp_path / "str.png"),
        key="TEST_KEY",
        nonce=fixed_nonce,
    )
    res_bytes = generate(
        data="test",
        output_path=str(tmp_path / "bytes.png"),
        key=b"TEST_KEY",
        nonce=fixed_nonce,
    )

    assert res_str["payload"] == res_bytes["payload"]
    assert res_str["qr_string"] == res_bytes["qr_string"]


def test_fixed_nonce_produces_identical_qr(tmp_path):
    fixed_nonce = "0123456789abcdef"

    res1 = generate(
        data="test", output_path=str(tmp_path / "1.png"), key=b"TEST", nonce=fixed_nonce
    )
    res2 = generate(
        data="test", output_path=str(tmp_path / "2.png"), key=b"TEST", nonce=fixed_nonce
    )

    assert res1["qr_string"] == res2["qr_string"]
