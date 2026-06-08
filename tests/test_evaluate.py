import os
import pytest
from quantum_qr.evaluate import evaluate_corpus

def test_evaluate_corpus_simulator_baseline():
    """
    Verify the simulator baseline directly using the new evaluate_corpus signature.
    Under a noiseless simulator, all predictions should be perfectly correct.
    """
    fixtures_dir = "data/fixtures/"
    
    # Check if we have fixtures generated
    if not os.path.exists(os.path.join(fixtures_dir, "fixture_00_authentic.png")):
        pytest.skip("Fixtures not found. Run the fixture generation script first.")

    # Run evaluation (note: no manifest_path passed here anymore!)
    results = evaluate_corpus(fixtures_dir)
    
    # We expect a list of results
    assert isinstance(results, list)
    assert len(results) > 0
    
    for res in results:
        # Under an ideal noiseless simulator, the math is perfect
        assert res["is_correct"] is True
        if res["expected_verdict"] == "authentic":
            assert res["p_zeros"] == 1.0
        else:
            assert res["p_zeros"] == 0.0

def test_evaluate_handles_invalid_fixtures(tmp_path):
    """
    Ensure 'invalid' (corrupted) fixtures are handled without crashing 
    and are properly labeled as 'invalid'.
    """
    # Create a fake corrupt image
    garbage_file = tmp_path / "corrupt_fixture.png"
    garbage_file.write_text("I am not a valid QR code")
    
    # Run evaluation on the temporary directory
    results = evaluate_corpus(str(tmp_path))
    
    assert len(results) == 1
    res = results[0]
    
    assert res["filename"] == "corrupt_fixture.png"
    # Because 'baseline' is not in the filename, the harness expects 'tampered'
    assert res["expected_verdict"] == "tampered" 
    # But the verifier correctly flags it as invalid before running quantum circuits
    assert res["predicted_verdict"] == "invalid"
    assert "Decode failure" in res["reason"]


# import os
# import json
# import pytest
# from quantum_qr.evaluate import evaluate_corpus


# def test_evaluate_corpus_simulator_baseline():
#     """
#     Verify the simulator baseline:
#     1. 100% accuracy and recall.
#     2. Zero off-diagonal entries (no False Positives or False Negatives).
#     """
#     fixtures_dir = "data/fixtures/"
#     manifest_path = "data/fixtures/manifest.json"

#     if not os.path.exists(manifest_path):
#         pytest.skip("Fixtures not found. Run the fixture generation script first.")

#     # Run evaluation
#     report = evaluate_corpus(fixtures_dir, manifest_path)

#     # Assertions
#     metrics = report["metrics"]
#     cm = report["confusion_matrix"]

#     assert metrics["accuracy"] == 1.0, "Simulator accuracy should be 100%"
#     assert metrics["recall"] == 1.0, "Simulator recall should be 100%"

#     # Confusion Matrix: Off-diagonals must be zero on the noiseless simulator
#     assert cm["FP"] == 0, "False Positives should be zero on simulator"
#     assert cm["FN"] == 0, "False Negatives should be zero on simulator"


# def test_evaluate_handles_invalid_fixtures(tmp_path):
#     """
#     Ensure 'invalid' (corrupted) fixtures are counted correctly as caught tampered items.
#     """
#     # Create a minimal manifest that includes one invalid fixture
#     manifest_path = tmp_path / "test_manifest.json"

#     # Assume you have a helper to generate a truly corrupted file
#     # (or just use a file with garbage content)
#     garbage_file = tmp_path / "corrupt.png"
#     with open(garbage_file, "w") as f:
#         f.write("I am not a valid QR code")

#     manifest = [
#         {
#             "filename": "corrupt.png",
#             "expected_secret": "00000001",  # This means it is tampered
#         }
#     ]

#     with open(manifest_path, "w") as f:
#         json.dump(manifest, f)

#     # Run evaluation
#     report = evaluate_corpus(str(tmp_path), str(manifest_path))

#     # The verifier should label this "invalid", which counts as catching the tamper
#     # We calculate 'correct' by summing TP + TN from our metrics
#     correct_count = report["confusion_matrix"]["TP"] + report["confusion_matrix"]["TN"]
#     assert correct_count == 1
#     assert report["details"][0]["predicted_verdict"] == "invalid"
