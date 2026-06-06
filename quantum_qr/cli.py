import os
import sys
import json
import argparse
from quantum_qr.generator import generate
from quantum_qr.verifier import verify


def handle_generate(args: argparse.Namespace) -> int:
    """
    Execute the generation process based on parsed command-line arguments.
    """
    try:
        result = generate(data=args.data, output_path=args.output, n_bits=args.bits)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Success! QR code saved to: {result['output_path']}")
            print(f"   Payload Data : {result['payload']['data']}")
            print(f"   Tag ({args.bits}-bit) : {result['payload']['tag']}")
            print(f"   Nonce Length : {len(result['payload']['nonce'])} bits")

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return 1


def handle_verify(args: argparse.Namespace) -> int:
    """
    Execute the verification process based on parsed command-line arguments.
    """
    # 1. Fail-fast on missing files to prevent cryptic library errors
    if not os.path.exists(args.qr_path):
        print(f"Error: QR code file not found at '{args.qr_path}'", file=sys.stderr)
        return 1

    # 2. Run the quantum verification pipeline
    try:
        result = verify(
            args.qr_path,
            n_bits=args.bits,
            shots=args.shots,
            accept_threshold=args.threshold
        )
    except Exception as e:
        print(f"Operational error during verification: {e}", file=sys.stderr)
        return 1

    # 3. Format the output
    if args.json:
        # Standard Output for scripts and pipelines
        print(json.dumps(result, indent=2))
    else:
        # Human-friendly diagnostic output
        verdict = result.get('verdict', 'unknown').upper()
        print(f"VERDICT: {verdict}")
        
        if verdict in ["AUTHENTIC", "TAMPERED"]:
            print(f"confidence: {result.get('confidence', 0.0):.2f}")
            print(f"P(zeros):   {result.get('p_zeros', 0.0):.2f}")
            
        if verdict == "TAMPERED":
            measured = result.get("measured_secret", "")
            if measured:
                # DJ expects all 0s. Find indices where measured bit is '1'
                diff_bits = [str(i) for i, bit in enumerate(measured) if bit == '1']
                diff_str = ",".join(diff_bits)
                print(f"measured secret: {measured}   (bits {diff_str} differ from expected)")
                
        elif verdict == "INVALID":
            print(f"reason: {result.get('reason')}")

    # 4. Map the verdict to the semantic exit codes
    v = result.get("verdict")
    if v == "authentic":
        return 0
    elif v == "tampered":
        return 3
    elif v == "invalid":
        return 4
    else:
        return 1


def main(argv: list[str] | None = None) -> int:
    """
    Parse command-line arguments and route to the appropriate CLI subcommand handler.
    """
    parser = argparse.ArgumentParser(
        prog="quantum_qr", description="Quantum Tamper-Evident QR Toolkit"
    )

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    # --- Generate Command ---
    gen_parser = subparsers.add_parser(
        "generate", help="Create a tamper-evident QR code from a string payload"
    )
    gen_parser.add_argument(
        "data", type=str, help="The string payload to encode (e.g., 'pay alice $10')"
    )
    gen_parser.add_argument(
        "-o", "--output", required=True, help="Filepath to save the generated QR image"
    )
    gen_parser.add_argument(
        "-n", "--bits", type=int, default=8, help="Number of bits for the HMAC truncation and quantum register (default: 8)"
    )
    gen_parser.add_argument(
        "--json", action="store_true", help="Output machine-readable JSON to stdout instead of standard text"
    )

    # --- Verify Command ---
    verify_parser = subparsers.add_parser(
        "verify", help="Verify a quantum tamper-evident QR code"
    )
    verify_parser.add_argument(
        "qr_path", type=str, help="Path to the QR code image"
    )
    verify_parser.add_argument(
        "--shots", type=int, default=1024, help="Number of quantum shots (default: 1024)"
    )
    verify_parser.add_argument(
        "--threshold", type=float, default=0.5, help="P(zeros) acceptance threshold (default: 0.5)"
    )
    verify_parser.add_argument(
        "-n", "--bits", type=int, default=8, help="Number of bits in the secret (default: 8)"
    )
    verify_parser.add_argument(
        "--json", action="store_true", help="Output machine-readable JSON to stdout instead of standard text"
    )

    args = parser.parse_args(argv)

    if args.command == "generate":
        return handle_generate(args)
    elif args.command == "verify":
        return handle_verify(args)

    return 1


if __name__ == "__main__":
    sys.exit(main())