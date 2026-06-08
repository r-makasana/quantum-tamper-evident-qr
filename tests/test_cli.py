# from asyncio import run
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import pytest
from quantum_qr.cli import main


def test_verify_authentic(tmp_path):
    """Verify on a freshly generated authentic QR returns 0."""
    qr_path = str(tmp_path / "alice_payment.png")

    # 1. Generate a fresh QR
    assert main(["generate", "pay alice $10", "-o", qr_path]) == 0

    # 2. Verify it
    assert main(["verify", qr_path]) == 0


def test_verify_tampered():
    """Verify on a tampered fixture returns 3."""
    fixture_path = "data/fixtures/fixture_01_data.png"

    # Skip gracefully if the user hasn't generated fixtures yet in this environment
    if not os.path.exists(fixture_path):
        pytest.skip(f"Tampered fixture {fixture_path} not found.")

    assert main(["verify", fixture_path]) == 3


def test_verify_corrupted(tmp_path):
    """Verify on a corrupted fixture returns 4."""
    corrupted_path = tmp_path / "corrupted.png"
    corrupted_path.write_text("This is definitely not a valid image file.")

    assert main(["verify", str(corrupted_path)]) == 4


def test_verify_missing():
    """Verify on a missing path returns 1."""
    assert main(["verify", "data/does_not_exist_at_all.png"]) == 1


def test_verify_json_output(tmp_path, capsys):
    """--json output parses as JSON and contains the verdict."""
    qr_path = str(tmp_path / "json_test.png")

    # Generate the test file
    main(["generate", "json test", "-o", qr_path])

    # Clear out the stdout buffer from the generate command
    capsys.readouterr()

    # Run verify with the --json flag
    assert main(["verify", qr_path, "--json"]) == 0

    # Capture stdout and parse it
    captured = capsys.readouterr()

    try:
        parsed_json = json.loads(captured.out)
    except json.JSONDecodeError:
        pytest.fail("CLI did not output valid JSON")

    # Assert expected keys are present
    assert "verdict" in parsed_json
    assert parsed_json["verdict"] == "authentic"
    assert "confidence" in parsed_json
    assert "p_zeros" in parsed_json
