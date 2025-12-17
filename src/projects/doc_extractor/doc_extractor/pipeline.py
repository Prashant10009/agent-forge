from pathlib import Path
from typing import Any, Dict


def process_document(path: str) -> Dict[str, Any]:
    """
    Core entrypoint for document processing.

    For now this is a simple placeholder implementation:
    - checks that the file exists
    - returns a minimal structured dict describing the document

    This is designed to be easy to extend later with real OCR,
    classification, and field extraction logic.
    """
    p = Path(path)

    if not p.is_file():
        raise FileNotFoundError(f"Document not found: {path}")

    # TODO: plug in real document analysis (OCR, classification, extraction).
    # For now we just return a stub structure.
    return {
        "document_type": "unknown",
        "classification_confidence": 0.0,
        "extracted_fields": {},
        "text_snippet": "",
    }
