import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from quantum_qr.qrng import generate_quantum_random_bits


def test_length_128():
    bits = generate_quantum_random_bits(128)
    assert len(bits) == 128


def test_binary_only():
    bits = generate_quantum_random_bits(128)
    assert set(bits).issubset({0, 1})
