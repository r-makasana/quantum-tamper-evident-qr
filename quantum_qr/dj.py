from qiskit import QuantumCircuit


def dj_circuit(oracle: QuantumCircuit, n: int) -> QuantumCircuit:
    """
    Build the Deutsch-Jozsa quantum circuit for a given oracle.

    Args:
        oracle: The quantum circuit representing the function to be evaluated.
        n: The number of input qubits.

    Returns:
        A complete QuantumCircuit including initialization, the oracle, and measurement.
    """
    # Total qubits = n (input) + 1 (output)
    qc = QuantumCircuit(n + 1, n)

    # Step 1: Initialize the output qubit to |1>
    ancilla = n  # index of last qubit
    qc.x(ancilla)

    # Step 2: Apply Hadamard gates to all qubits
    for i in range(n + 1):
        qc.h(i)

    # Step 3: Apply the oracle
    qc.append(oracle.to_gate(), range(n + 1))

    # Step 4: Apply Hadamard gates to the input qubits
    for i in range(n):
        qc.h(i)

    # Step 5: Measure the input qubits
    for i in range(n):
        qc.measure(i, i)

    return qc


def const_oracle_zero(n: int) -> QuantumCircuit:
    """
    Create a constant oracle that always evaluates to 0.

    Args:
        n: The number of input qubits.

    Returns:
        A QuantumCircuit representing the constant zero oracle.
    """
    oracle = QuantumCircuit(n + 1)
    # For constant zero, do nothing (oracle leaves state unchanged)
    return oracle


def const_oracle_one(n: int) -> QuantumCircuit:
    """
    Create a constant oracle that always evaluates to 1.

    Args:
        n: The number of input qubits.

    Returns:
        A QuantumCircuit representing the constant one oracle.
    """
    oracle = QuantumCircuit(n + 1)
    ancilla = n
    # For constant one, flip the output qubit (X gate)
    oracle.x(ancilla)
    return oracle


def balanced_oracle(n: int) -> QuantumCircuit:
    """
    Create a balanced oracle using CNOT gates.

    Args:
        n: The number of input qubits.

    Returns:
        A QuantumCircuit representing a balanced oracle.
    """
    oracle = QuantumCircuit(n + 1)
    ancilla = n
    # For balanced, we can use a CNOT from each input qubit to the output
    for i in range(n):
        oracle.cx(i, ancilla)
    return oracle


def oracle_from_secret_string(s: str) -> QuantumCircuit:
    """
    Create an oracle based on a specific secret binary string (Bernstein-Vazirani).

    Args:
        s: A binary string representing the secret.

    Returns:
        A QuantumCircuit that encodes the secret string via CNOT gates.
    """
    n = len(s)
    oracle = QuantumCircuit(n + 1)
    ancilla = n
    for i, bit in enumerate(s):
        if bit == "1":
            oracle.cx(i, ancilla)
    return oracle
