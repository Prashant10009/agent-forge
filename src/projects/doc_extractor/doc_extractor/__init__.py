import os

def process(file_path: str) -> dict:
    """
    Extract text from a document and return a standardized result dictionary.

    Parameters
    ----------
    file_path : str
        Path to the document to be processed.

    Returns
    -------
    dict
        A dictionary containing at least the following keys:

        - document_type : str
            Defaults to 'unknown'.
        - classification_confidence : float
            Defaults to 0.5.
        - extracted_fields : dict
            Defaults to an empty dict.
        - text : str
            The full extracted text (may be empty). Text is never truncated.
        - text_snippet : str
            The first 500 characters of the extracted text,
            or the entire text if it is shorter.

    Notes
    -----
    The function handles UTF‑8 text files, PDF files (using `pdfplumber` if
    installed, with a graceful fallback), and common image file extensions
    (text is left empty for those). Unsupported or malformed files result in
    the default dictionary without raising exceptions.
    """
    # Default result to be returned in case of any error
    defaults = {
        "document_type": "unknown",
        "classification_confidence": 0.5,
        "extracted_fields": {},
        "text": "",
        "text_snippet": "",
    }

    try:
        if not os.path.isfile(file_path):
            return defaults

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        full_text = ""

        # Text files
        if ext == ".txt":
            try:
                with open(file_path, "r", encoding="utf-8") as fh:
                    full_text = fh.read()
            except Exception:
                return defaults

        # PDF files
        elif ext == ".pdf":
            try:
                import pdfplumber  # type: ignore
            except ImportError:
                full_text = ""
            else:
                try:
                    with pdfplumber.open(file_path) as pdf:
                        pages_text = [page.extract_text() or "" for page in pdf.pages]
                    full_text = "\n".join(pages_text)
                except Exception:
                    full_text = ""

        # Image files
        elif ext in {".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".gif"}:
            full_text = ""

        else:
            # Unsupported format
            return defaults

        result = defaults.copy()
        result["text"] = full_text
        result["text_snippet"] = full_text[:500] if full_text else ""
        return result

    except Exception:
        return defaults


__all__ = ["process"]