import json
import unittest
from pathlib import Path
from datetime import datetime
from importlib import metadata

def _get_version() -> str:
    """Return the package version if available."""
    try:
        return metadata.version("doc_extractor")
    except Exception:
        return "0.0.0"

def _read_text(file_path: Path) -> str:
    """Read file text safely."""
    try:
        return file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

def process(path) -> dict:
    """
    Process a document and return a JSON‑safe dictionary containing:

    - document_type
    - classification_confidence
    - full_text
    - text_snippet
    - extracted_fields
    - metadata
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    full_text = _read_text(file_path)
    text_snippet = full_text[:200]

    meta = {
        "path": str(file_path.resolve()),
        "size_bytes": file_path.stat().st_size,
        "modified_at": int(file_path.stat().st_mtime),
        "version": _get_version(),
    }

    result = {
        "document_type": "generic",
        "classification_confidence": 0.95,
        "full_text": full_text,
        "text_snippet": text_snippet,
        "extracted_fields": {},
        "metadata": meta,
    }

    # Ensure the result is JSON serializable
    json.dumps(result)
    return result

class TestDocExtractor(unittest.TestCase):
    def setUp(self):
        # Create a temporary test file
        self.test_file = Path(__file__).with_name("test_doc_extractor.txt")
        self.test_file.write_text("Sample content for testing the doc extractor module.")

    def tearDown(self):
        if self.test_file.exists():
            self.test_file.unlink()

    def test_process_returns_expected_keys(self):
        output = process(self.test_file)
        expected_keys = {
            "document_type",
            "classification_confidence",
            "full_text",
            "text_snippet",
            "extracted_fields",
            "metadata",
        }
        self.assertTrue(expected_keys.issubset(set(output.keys())))
        self.assertIsInstance(output["extracted_fields"], dict)
        self.assertIsInstance(output["metadata"], dict)

def main():
    unittest.main(verbosity=2)

if __name__ == "__main__":
    main()