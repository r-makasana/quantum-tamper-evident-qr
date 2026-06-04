import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import pytest
from quantum_qr.cli import main

def test_cli_generate_success(tmp_path):
    """main(["generate", ...]) returns 0 and creates the file"""
    output_file = tmp_path / "q.png"
    argv = ["generate", "hello", "-o", str(output_file)]
    
    exit_code = main(argv)
    
    assert exit_code == 0
    assert output_file.exists()

def test_cli_generate_empty_data(tmp_path):
    """main(["generate", "", ...]) returns 1 (empty data)"""
    output_file = tmp_path / "bad.png"
    argv = ["generate", "", "-o", str(output_file)]
    
    exit_code = main(argv)
    
    assert exit_code == 1
    # Ensure the script cleanly aborted before making a file
    assert not output_file.exists()

def test_cli_generate_bad_bits(tmp_path):
    """main(["generate", ... "-n", "99"]) returns 1 (bad bits)"""
    output_file = tmp_path / "x.png"
    argv = ["generate", "hi", "-o", str(output_file), "-n", "99"]
    
    exit_code = main(argv)
    
    assert exit_code == 1

def test_cli_json_mode_produces_parseable_json(tmp_path, capsys):
    """--json mode produces parseable JSON to stdout"""
    output_file = tmp_path / "json_test.png"
    argv = ["generate", "secret payload", "-o", str(output_file), "--json"]
    
    exit_code = main(argv)
    assert exit_code == 0
    
    # capsys captures everything the script printed to stdout/stderr
    captured = capsys.readouterr()
    
    try:
        # If this crashes, the output wasn't valid JSON!
        parsed_output = json.loads(captured.out)
    except json.JSONDecodeError:
        pytest.fail("CLI output was not valid JSON")
        
    # Verify the JSON structure contains our expected keys
    assert "payload" in parsed_output
    assert "qr_string" in parsed_output
    assert parsed_output["output_path"] == str(output_file)
    assert parsed_output["payload"]["data"] == "secret payload"