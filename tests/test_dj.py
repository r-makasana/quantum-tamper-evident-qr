import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from qiskit_aer import AerSimulator
from qiskit import transpile

from quantum_qr.dj import (
    dj_circuit,
    const_oracle_zero,
    const_oracle_one
)


def run_circuit(circuit, shots=1024):
    """
    Helper function to run a circuit on AerSimulator.
    """
    simulator = AerSimulator()

    compiled = transpile(circuit, simulator)

    job = simulator.run(compiled, shots=shots)

    result = job.result()

    return result.get_counts()


def test_constant_zero_oracle():
    """
    DJ with constant-zero oracle should always output 0000.
    """

    n = 4

    oracle = const_oracle_zero(n)

    circuit = dj_circuit(oracle, n)

    counts = run_circuit(circuit)

    assert counts == {'0000': 1024}


def test_constant_one_oracle():
    """
    DJ with constant-one oracle should always output 0000.
    """

    n = 4

    oracle = const_oracle_one(n)

    circuit = dj_circuit(oracle, n)

    counts = run_circuit(circuit)

    assert counts == {'0000': 1024}


def test_dj_circuit_size():
    """
    Verify correct number of qubits and classical bits.
    """

    n = 4

    oracle = const_oracle_zero(n)

    circuit = dj_circuit(oracle, n)

    # n input qubits + 1 ancilla
    assert circuit.num_qubits == 5

    # n classical bits
    assert circuit.num_clbits == 4