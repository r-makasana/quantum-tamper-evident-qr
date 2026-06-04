# Add the parent directory to Python's search path
from pathlib import Path

import argparse
import sys
import json
from quantum_qr.generator import generate

def handle_generate(args: argparse.Namespace) -> int:
    """Handler for the 'generate' subcommand."""
    try:
        # Call your existing generate function
        result = generate(
            data=args.data,
            output_path=args.output,
            n_bits=args.bits
        )
        
        # Output handling: The core of Task 4
        if args.json:
            # Output ONLY valid JSON to stdout
            print(json.dumps(result, indent=2))
        else:
            # Human-friendly output
            print(f"✅ Success! QR code saved to: {result['output_path']}")
            print(f"   Payload Data : {result['payload']['data']}")
            print(f"   Tag ({args.bits}-bit) : {result['payload']['tag']}")
            print(f"   Nonce Length : {len(result['payload']['nonce'])} bits")
            
        return 0  # Exit code 0: Success

    except ValueError as e:
        # Write errors to stderr so they don't corrupt piped JSON output
        print(f"Error: {e}", file=sys.stderr)
        return 1  # Exit code 1: Application Error
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return 1

def main(argv: list[str] | None = None) -> int:
    """Parse args and dispatch. Returns an exit code. argv=None uses sys.argv."""
    
    parser = argparse.ArgumentParser(
        prog="quantum_qr",
        description="Quantum Tamper-Evident QR Code Generator"
    )
    
    subparsers = parser.add_subparsers(
        dest="command", 
        required=True,
        help="Available commands"
    )

    # --- GENERATE COMMAND ---
    gen_parser = subparsers.add_parser(
        "generate", 
        help="Create a tamper-evident QR code from a string payload"
    )
    gen_parser.add_argument(
        "data", 
        type=str, 
        help="The string payload to encode (e.g., 'pay alice $10')"
    )
    gen_parser.add_argument(
        "-o", "--output", 
        required=True, 
        help="Filepath to save the generated QR image"
    )
    gen_parser.add_argument(
        "-n", "--bits", 
        type=int, 
        default=8, 
        help="Number of bits for the HMAC truncation and quantum register (default: 8)"
    )
    gen_parser.add_argument(
        "--json", 
        action="store_true", 
        help="Output machine-readable JSON to stdout instead of standard text"
    )

    # Parse the arguments
    args = parser.parse_args(argv)

    # Dispatch to the correct handler
    if args.command == "generate":
        return handle_generate(args)
        
    return 1

if __name__ == "__main__":
    sys.exit(main())