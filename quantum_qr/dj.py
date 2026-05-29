from qiskit import QuantumCircuit

def dj_circuit(oracle:QuantumCircuit, n:int) -> QuantumCircuit:
    # Total qubits = n (input) + 1 (output)
    qc= QuantumCircuit(n+1, n)
    # Step 1: Initialize the output qubit to |1>
    ancilla = n  # index of last qubit
    qc.x(ancilla)
    # Step 2: Apply Hadamard gates to all qubits
    for i in range(n+1):
        qc.h(i)
    # Step 3: Apply the oracle
    qc.append(oracle.to_gate(), range(n+1))
    # Step 4: Apply Hadamard gates to the input qubits
    for i in range(n):
        qc.h(i)
    # Step 5: Measure the input qubits
    for i in range(n):
        qc.measure(i, i)
    return qc

# constant oracles 
def const_oracle_zero(n:int) -> QuantumCircuit:
    oracle = QuantumCircuit(n+1)
    # For constant zero, do nothing (oracle leaves state unchanged)
    return oracle

def const_oracle_one(n:int) -> QuantumCircuit:
    oracle = QuantumCircuit(n+1)
    ancilla = n  # index of last qubit
    # For constant one, flip the output qubit (X gate)
    oracle.x(ancilla)  # Flip the last qubit (output)
    return oracle
    
# balanced oracle

def balanced_oracle(n:int) -> QuantumCircuit:
    oracle = QuantumCircuit(n+1)
    # For balanced, we can use a CNOT from each input qubit to the output
    ancilla = n  # index of last qubit
    for i in range(n):
        oracle.cx(i, ancilla)  # Flip output if input qubit is 1
    return oracle

# also called vazirani-bernstain algorithm
def oracle_from_secret_string(s:str) -> QuantumCircuit:    
    n = len(s)
    oracle = QuantumCircuit(n+1)
    ancilla = n  # index of last qubit
    for i, bit in enumerate(s):
        if bit == '1':
            oracle.cx(i, ancilla)  # Flip output if input qubit is 1
    return oracle