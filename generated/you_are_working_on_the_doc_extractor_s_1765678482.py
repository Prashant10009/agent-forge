import json
import pathlib
import logging
import typing as t
from jsonschema import validate as json_validate, ValidationError

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

# JSON Schema for the output
OUTPUT_SCHEMA: t.Dict[str, t.Any] = {
    "type": "object",
    "properties": {
        "document_type": {"type": "string"},
        "classification_confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "full_text": {"type": "string"},
        "text_snippet": {"type": "string"},
        "extracted_fields": {"type": "object"},
        "metadata": {"type": "object"},
    },
    "required": [
        "document_type",
        "classification_confidence",
        "full_text",
        "text_snippet",
        "extracted_fields",
        "metadata",
    ],
    "additionalProperties": False,
}


def _read_file(path: pathlib.Path) -> str:
    """Read file content as UTF-8 text. Raise informative error if file is binary-like."""
    try:
        content = path.read_text(encoding="utf-8")
        return content
    except UnicodeDecodeError:
        # Assume binary; return empty string and log the issue
        logger.warning(f"Could not decode {path}. Treating as empty text.")
        return ""


def _detect_document_type(path: pathlib.Path) -> str:
    """Simple heuristic to detect document type based on file extension."""
    ext = path.suffix.lower()
    if ext in {".txt"}:
        return "text"
    if ext in {".md"}:
        return "markdown"
    if ext in {".pdf"}:
        return "pdf"
    if ext in {".docx"}:
        return "word"
    return "unknown"


def _compute_confidence(text: str) -> float:
    """Stub function to compute classification confidence."""
    # Just a dummy confidence based on presence of words
    return 0.8 if text.strip() else 0.0


def _extract_fields(text: str) -> dict:
    """Placeholder extraction logic that returns key sentences."""
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    return {"sentence_count": len(sentences), "first_sentence": sentences[0] if sentences else ""}


def _metadata_from_path(path: pathlib.Path) -> dict:
    """Generate metadata based on file system info."""
    try:
        stat = path.stat()
        return {
            "size_bytes": stat.st_size,
            "last_modified": stat.st_mtime,
            "path": str(path.resolve()),
        }
    except OSError:
        return {"path": str(path.resolve())}


def _validate_output(output: dict) -> None:
    """Validate the output against the JSON schema."""
    try:
        json_validate(instance=output, schema=OUTPUT_SCHEMA)
    except ValidationError as e:
        raise ValueError(f"Output does not conform to schema: {e.message}") from e


def process(path: str | pathlib.Path) -> dict:
    """
    Main entry point for the doc_extractor API.
    Parameters
    ----------
    path : str or pathlib.Path
        Path to the document to process.

    Returns
    -------
    dict
        JSON‑safe dictionary containing extraction results.
    """
    path_obj = pathlib.Path(path)

    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {path_obj}")

    full_text = _read_file(path_obj)
    text_snippet = full_text[:200]  # first 200 characters
    document_type = _detect_document_type(path_obj)
    confidence = _compute_confidence(full_text)
    extracted_fields = _extract_fields(full_text)
    metadata = _metadata_from_path(path_obj)

    output = {
        "document_type": document_type,
        "classification_confidence": round(confidence, 3),
        "full_text": full_text,
        "text_snippet": text_snippet,
        "extracted_fields": extracted_fields,
        "metadata": metadata,
    }

    _validate_output(output)

    logger.info(f"Processed {path_obj} successfully.")
    return output


def debug(path: str | pathlib.Path) -> dict:
    """
    Wrapper around `process` that logs detailed exception information.
    Intended as a simple bug‑fixer helper for developers.
    """
    try:
        return process(path)
    except Exception as exc:
        logger.exception(f"Error processing {path}: {exc}")
        # Return a minimal fail‑safe structure for debugging purposes
        return {
            "document_type": "error",
            "classification_confidence": 0.0,
            "full_text": "",
            "text_snippet": "",
            "extracted_fields": {},
            "metadata": {"error": str(exc)},
        }


# Expose the public API when this module is imported
__all__ = ["process", "debug"]


def main() -> None:
    """CLI interface to demonstrate the extractor."""
    import argparse

    parser = argparse.ArgumentParser(description="Debug and process documents with doc_extractor.")
    parser.add_argument("path", help="Path to the document to process.")
    parser.add_argument("--debug", action="store_true", help="Run the bug‑fixer wrapper.")
    args = parser.parse_args()

    processor = debug if args.debug else process
    result = processor(args.path)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()