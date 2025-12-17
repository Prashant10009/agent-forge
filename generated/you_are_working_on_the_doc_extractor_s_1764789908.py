import json
import re
import pathlib
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional


# ------------------------
# Light‑weight classifier
# ------------------------
@dataclass
class ClassificationResult:
    document_type: str
    confidence: float


def _simple_classifier(text: str) -> ClassificationResult:
    """
    Very small rule‑based classifier. It looks for keywords in the first
    200 characters and assigns a confidence based on keyword matches.
    """
    keywords = {
        "invoice": ("Invoice", 1.0),
        "receipt": ("Receipt", 0.9),
        "report": ("Report", 0.8),
        "letter": ("Letter", 0.7),
        "contract": ("Contract", 0.9),
        "proposal": ("Proposal", 0.75),
    }

    header = text[:200].lower()
    matched: List[Tuple[str, float]] = []

    for kw, (doc_type, score) in keywords.items():
        if kw in header:
            matched.append((doc_type, score))

    if matched:
        # Pick the highest scoring match
        best_type, best_score = max(matched, key=lambda x: x[1])
        return ClassificationResult(best_type, best_score)
    else:
        return ClassificationResult("Unknown", 0.5)


# ------------------------
# Text extraction helper
# ------------------------
def _extract_text_from_file(file_path: Path) -> str:
    """Open a TXT or PDF file and return its textual content."""
    if file_path.suffix.lower() == ".txt":
        return file_path.read_text(encoding="utf-8", errors="ignore")

    if file_path.suffix.lower() == ".pdf":
        try:
            import PyPDF2
        except ImportError:
            raise RuntimeError(
                "PDF extraction requires PyPDF2. Install with `pip install PyPDF2`."
            )

        with open(file_path, "rb") as fp:
            reader = PyPDF2.PdfReader(fp)
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages)

    raise ValueError(f"Unsupported file format: {file_path.suffix}")


# ------------------------
# Field extraction (dummy)
# ------------------------
def _extract_fields(text: str) -> Dict[str, Any]:
    """
    Dummy field extraction. In a real system this could be a OCR or
    NLP model that extracts structured data.
    """
    # For demo purposes, we just look for a simple "Date:" line
    fields: Dict[str, Any] = {}
    date_match = re.search(r"date[:\s]+(\d{4}-\d{2}-\d{2})", text.lower())
    if date_match:
        fields["date"] = date_match.group(1)

    return fields


# ------------------------
# Main public API
# ------------------------
def process(path: str | Path) -> Dict[str, Any]:
    """
    Public entry point for the doc_extractor suite.

    Parameters
    ----------
    path : str | Path
        Path to the document to process.

    Returns
    -------
    Dict[str, Any]
        JSON‑serialisable dictionary containing:
            - document_type
            - classification_confidence
            - full_text
            - text_snippet
            - extracted_fields
            - metadata
    """
    file_path = Path(path).expanduser().resolve()

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    full_text = _extract_text_from_file(file_path)

    classification = _simple_classifier(full_text)

    extracted_fields = _extract_fields(full_text)

    snippet = full_text[:300].replace("\n", " ") if full_text else ""

    metadata = {
        "file_name": file_path.name,
        "file_size_bytes": file_path.stat().st_size,
        "file_extension": file_path.suffix.lower(),
    }

    result: Dict[str, Any] = {
        "document_type": classification.document_type,
        "classification_confidence": classification.confidence,
        "full_text": full_text,
        "text_snippet": snippet,
        "extracted_fields": extracted_fields,
        "metadata": metadata,
    }

    return result


# ------------------------
# CLI demo
# ------------------------
def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="doc_extractor: process a document and output JSON"
    )
    parser.add_argument("filepath", help="Path to the file to process")
    args = parser.parse_args()

    try:
        result = process(args.filepath)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as exc:
        print(f"Error: {exc}", flush=True)
        exit(1)


if __name__ == "__main__":
    main()
```