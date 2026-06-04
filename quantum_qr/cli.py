import argparse
import sys
import json
from quantum_qr.generator import generate


def handle_generate(args: argparse.Namespace) -> int:
    """
    Execute the generation process based on parsed command-line arguments.

    Args:
        args: The argparse Namespace containing 'data', 'output', 'bits', and 'json' flags.

    Returns:
        An integer exit code. Returns 0 upon successful generation, or 1 if an error occurs.
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


def main(argv: list[str] | None = None) -> int:
    """
    Parse command-line arguments and route to the appropriate CLI subcommand handler.

    Args:
        argv: Optional list of argument strings for testing. If None, uses sys.argv.

    Returns:
        An integer exit code representing the result of the command.
    """
    parser = argparse.ArgumentParser(
        prog="quantum_qr", description="Quantum Tamper-Evident QR Code Generator"
    )

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

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
        "-n",
        "--bits",
        type=int,
        default=8,
        help="Number of bits for the HMAC truncation and quantum register (default: 8)",
    )
    gen_parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON to stdout instead of standard text",
    )

    args = parser.parse_args(argv)

    if args.command == "generate":
        return handle_generate(args)

    return 1


if __name__ == "__main__":
    sys.exit(main())
