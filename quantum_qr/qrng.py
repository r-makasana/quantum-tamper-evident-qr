from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


def generate_quantum_random_bits(n: int) -> list[int]:
    """
    Generate a sequence of true random bits using a quantum circuit simulator.

    Args:
        n: The number of random bits to generate.

    Returns:
        A list of integers (0 or 1) representing the measured quantum states.
    """
    simulator = AerSimulator()
    qc = QuantumCircuit(n, n)

    # Put all qubits in superposition
    qc.h(range(n))

    # Measure all qubits
    qc.measure(range(n), range(n))

    # Run circuit
    job = simulator.run(qc, shots=1)
    result = job.result()
    counts = result.get_counts()

    # Extract raw bitstring
    bitstring = list(counts.keys())[0]

    # Qiskit outputs right-to-left. Reverse it for standard left-to-right reading.
    corrected_bitstring = bitstring[::-1]

    # Convert to list of bits (integers)
    bits = [int(b) for b in corrected_bitstring]

    return bits


# n=int(input("Enter the number of random bits you want to generate:"))
# # Create simulator once
# simulator = AerSimulator()
# # Create 128-qubit QRNG circuit
# qc = QuantumCircuit(n, n)
# # Put all qubits into superposition
# qc.h(range(n))
# # Measure all qubits
# qc.measure(range(n), range(n))
# # Run the circuit with 1 shot (this generates 128 random bits at once)
# job = simulator.run(qc, shots=1)
# result = job.result()
# counts = result.get_counts()
# print("Counts:", counts)
# # Extract the single bitstring from counts
# bitstring = list(counts.keys())[0]  # Get the key (the measured bitstring)
# # Convert bitstring to a list of integers (0s and 1s)
# # bits = [int(bit) for bit in bitstring]
# bits = [int(bit) for bit in bitstring[::-1]]
# print("\n" + str(n) + " Random Bits:")
# print(bits)
# #circuit visualization
# qc.draw('mpl')
# plt.show()


# Multi shot approach to generate 128 random bits using a quantum circuit


# # Create simulator once
# simulator = AerSimulator()

# # Create 1-qubit QRNG circuit
# qc = QuantumCircuit(1, 1)

# # Put qubit into superposition
# qc.h(0)

# # Measure
# qc.measure(0, 0)

# # Run with 128 shots (this generates 128 random bits at once)
# job = simulator.run(qc, shots=128)
# result = job.result()
# counts = result.get_counts()

# print("Counts:", counts)

# # Convert counts → bit list
# bits = []
# for bit, count in counts.items():
#     bits.extend([int(bit)] * count)

# print("\n128 Random Bits:")
# print(bits)

# # Optional circuit visualization
# qc.draw('mpl')
# plt.show()


# Loop 128 times to generate 128 random bits using a quantum circuit

# # create sumulator
# simulator = AerSimulator()

# bit=[]
# for i in range(128):
# # Create a Quantum Circuit with 1 qubit and 1 classical bit
#     qc = QuantumCircuit(1, 1)

#     # Apply a Hadamard gate to qubit 0 to create a superposition
#     qc.h(0)

#     # Measure qubit 0 into classical bit 0
#     qc.measure(0, 0)

#     # Run the circuit once to get a single random shot
#     job = simulator.run(qc, shots=1)
#     result = job.result()

#     # Extract the counts dictionary (e.g., {'0': 1} or {'1': 1})
#     counts = result.get_counts()
#     # Get the measured bit (0 or 1) from the counts
#     measured_bit = list(counts.keys())[0]  # Get the key (the measured bit)
#     bit.append(int(measured_bit))
#     print(f"Bit{i+1}:{measured_bit}")

# # Final output of 128 random bits
# print("\n 128 random bits:", bit)


# # Optional: Draw the circuit to visually verify it
# qc.draw('mpl')
# plt.show()
