import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from quantum_qr.qr_io import make_qr_code, read_qr_code


def test_qr_round_trip(tmp_path):
    data = "quantum-test-123"

    file_path = tmp_path / "test_qr.png"

    # Encode
    make_qr_code(data, str(file_path))

    # Decode
    decoded = read_qr_code(str(file_path))

    assert decoded == data
