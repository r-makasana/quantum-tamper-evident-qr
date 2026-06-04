import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest

from quantum_qr.fixtures import build_fixture_set
from quantum_qr.qr_io import read_qr_code
from quantum_qr.payload import decode_payload, compute_tag, tags_to_secret


# ---------------------------------------------------------
# Pytest Fixture (Runs once for the whole file)
# ---------------------------------------------------------
@pytest.fixture(scope="module")
def fixture_corpus(tmp_path_factory):
    """
    Generates the fixture set once in a temporary directory
    and provides the key, directory path, and manifest to all tests.
    """
    # Create a module-level temporary directory
    out_dir = tmp_path_factory.mktemp("tamper_fixtures")
    key = b"TEST_CORPUS_KEY"
    n_bits = 8

    # Generate the corpus
    manifest = build_fixture_set(key, str(out_dir), n_bits)

    return key, out_dir, manifest, n_bits


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------


def test_build_produces_expected_files(fixture_corpus):
    """build_fixture_set produces the expected number of QR files plus a manifest"""
    _, out_dir, manifest, _ = fixture_corpus

    # We expect 5 fixtures based on our taxonomy
    assert len(manifest) == 5

    # Verify manifest.json was created
    manifest_path = out_dir / "manifest.json"
    assert manifest_path.exists()

    # Check that the number of files in the directory equals manifest entries + 1 (the manifest itself)
    files_on_disk = list(out_dir.iterdir())
    assert len(files_on_disk) == len(manifest) + 1


def test_manifest_files_exist_on_disk(fixture_corpus):
    """Every manifest file actually exists on disk"""
    _, out_dir, manifest, _ = fixture_corpus

    for entry in manifest:
        img_path = out_dir / entry["file"]
        assert (
            img_path.exists()
        ), f"File {entry['file']} is in manifest but missing from disk"


def test_expected_secrets_zero_and_nonzero(fixture_corpus):
    """
    Every authentic entry has expected_secret of all zeros.
    Every tampered entry has a non-zero expected_secret.
    """
    _, _, manifest, n_bits = fixture_corpus

    for entry in manifest:
        if entry["expected_verdict"] == "authentic":
            assert entry["expected_secret"] == "0" * n_bits
        else:
            assert (
                "1" in entry["expected_secret"]
            ), f"Tampered fixture {entry['file']} had all zeros!"


def test_reloading_reproduces_secret(fixture_corpus):
    """Reloading each fixture reproduces its manifest secret"""
    key, out_dir, manifest, n_bits = fixture_corpus

    for entry in manifest:
        img_path = str(out_dir / entry["file"])

        # 1. Read and decode
        qr_string = read_qr_code(img_path)
        payload = decode_payload(qr_string)

        # 2. Recompute tag and secret
        expected_tag = compute_tag(key, payload["data"], payload["nonce"], n_bits)
        computed_secret = tags_to_secret(payload["tag"], expected_tag)

        # 3. Assert match
        assert computed_secret == entry["expected_secret"], (
            f"Reload mismatch for {entry['file']}. "
            f"Expected {entry['expected_secret']}, got {computed_secret}"
        )
