# from asyncio import run
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from quantum_qr.generator import generate
from quantum_qr.payload import (
    compute_tag,
    decode_payload
)
from quantum_qr.qr_io import read_qr_code


def test_generate_creates_file(tmp_path):
    output_file = tmp_path / "test_qr.png"

    result = generate(
        data="pay alice $10",
        output_path=str(output_file),
        key=b"TEST_KEY"
    )

    assert output_file.exists()


def test_generate_computes_correct_tag(tmp_path):
    key = b"TEST_KEY"

    output_file = tmp_path / "test_qr.png"

    result = generate(
        data="pay alice $10",
        output_path=str(output_file),
        key=key
    )

    payload = result["payload"]

    expected_tag = compute_tag(
        key,
        payload["data"],
        payload["nonce"],
        n_bits=8
    )

    assert payload["tag"] == expected_tag


def test_generated_qr_round_trip(tmp_path):
    key = b"TEST_KEY"

    output_file = tmp_path / "test_qr.png"

    result = generate(
        data="pay alice $10",
        output_path=str(output_file),
        key=key
    )

    qr_string = read_qr_code(str(output_file))

    decoded_payload = decode_payload(qr_string)

    assert decoded_payload == result["payload"]


def test_same_data_produces_different_nonces(tmp_path):
    key = b"TEST_KEY"

    file1 = tmp_path / "qr1.png"
    file2 = tmp_path / "qr2.png"

    result1 = generate(
        data="pay alice $10",
        output_path=str(file1),
        key=key
    )

    result2 = generate(
        data="pay alice $10",
        output_path=str(file2),
        key=key
    )

    nonce1 = result1["payload"]["nonce"]
    nonce2 = result2["payload"]["nonce"]

    assert nonce1 != nonce2