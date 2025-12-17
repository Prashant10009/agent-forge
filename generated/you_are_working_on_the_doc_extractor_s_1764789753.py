import os
import json
import sys
import unittest
import tempfile

# Optional imports – the modules may not be installed in the user's environment.
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import camelot
except ImportError:
    camelot = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    from PIL import Image
except ImportError:
    Image = None


def _read_pdf_text(pdf_path):
    """Extract text from a PDF using pdfplumber."""
    if pdfplumber is None:
        raise ImportError("pdfplumber is required for PDF processing.")
    full_text = ""
    num_pages = 0
    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)
        for page in pdf.pages:
            full_text += page.extract_text() or ""
    return full_text, num_pages


def _extract_tables(pdf_path):
    """Extract tables from a PDF using camelot."""
    if camelot is None:
        raise ImportError("camelot is required for table extraction.")
    try:
        tables = camelot.read_pdf(pdf_path, pages="all")
        extracted = []
        for table in tables:
            extracted.append(table.df.to_dict(orient="records"))
        return extracted
    except Exception:
        # In case camelot fails on certain PDFs
        return []


def _ocr_image(image_path):
    """Perform OCR on an image using pytesseract."""
    if pytesseract is None or Image is None:
        raise ImportError("pytesseract and Pillow (PIL) are required for image OCR.")
    img = Image.open(image_path)
    return pytesseract.image_to_string(img)


def _classify_document(text):
    """Very naive document type classification based on text content."""
    if not text:
        return "unknown"
    text_lower = text.lower()
    if "invoice" in text_lower:
        return "invoice"
    if "receipt" in text_lower:
        return "receipt"
    if "letter" in text_lower:
        return "letter"
    return "generic"


def process(path):
    """
    Main entry point for the doc_extractor package.
    Accepts a file path to a PDF or an image and returns a JSON‑safe dict.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")

    _, ext = os.path.splitext(path)
    full_text = ""
    num_pages = 0
    extracted_tables = []
    metadata = {"file_path": path}

    if ext.lower() == ".pdf":
        if pdfplumber is None:
            raise ImportError("pdfplumber is required to process PDF files.")
        full_text, num_pages = _read_pdf_text(path)
        metadata["num_pages"] = num_pages
        if camelot is not None:
            extracted_tables = _extract_tables(path)
            metadata["num_tables"] = len(extracted_tables)
    else:
        # Treat any non‑PDF file as an image for OCR
        if Image is None or pytesseract is None:
            raise ImportError("pytesseract and Pillow (PIL) are required to process image files.")
        full_text = _ocr_image(path)
        metadata["num_pages"] = 1  # treat as single page

    document_type = _classify_document(full_text)
    classification_confidence = 0.0
    if document_type == "invoice":
        classification_confidence = 0.92
    elif document_type == "receipt":
        classification_confidence = 0.88
    elif document_type == "letter":
        classification_confidence = 0.81
    elif document_type == "generic":
        classification_confidence = 0.75
    else:
        classification_confidence = 0.0

    result = {
        "document_type": document_type,
        "classification_confidence": classification_confidence,
        "full_text": full_text,
        "text_snippet": full_text[:200] if full_text else "",
        "extracted_fields": extracted_tables,
        "metadata": metadata,
    }
    return result


# Simple unit tests for the `process` function.
class TestDocExtractor(unittest.TestCase):
    def test_non_existing_file(self):
        with self.assertRaises(FileNotFoundError):
            process("non_existing_file.xyz")

    def test_image_processing(self):
        # Create a simple PNG image with PIL
        if Image is None:
            self.skipTest("Pillow (PIL) is not installed.")
        img = Image.new("RGB", (200, 50), color="white")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            img.save(tmp.name)
            tmp_path = tmp.name

        try:
            result = process(tmp_path)
            self.assertIsInstance(result, dict)
            self.assertIn("document_type", result)
            self.assertIn("classification_confidence", result)
            self.assertIn("full_text", result)
            self.assertIn("text_snippet", result)
            self.assertIn("metadata", result)
        finally:
            os.unlink(tmp_path)

    def test_pdf_processing(self):
        if pdfplumber is None:
            self.skipTest("pdfplumber is not installed.")
        # Create a very simple PDF using pdfplumber's writer if available
        try:
            import fpdf  # simple PDF generation
        except ImportError:
            self.skipTest("fpdf is not installed for PDF generation.")
        pdf = fpdf.FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Hello Invoice", ln=True)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf.output(tmp.name)
            tmp_path = tmp.name

        try:
            result = process(tmp_path)
            self.assertIsInstance(result, dict)
            self.assertEqual(result["document_type"], "invoice")
        finally:
            os.unlink(tmp_path)


def main():
    """Simple command line interface that processes a file passed as argument."""
    if len(sys.argv) < 2:
        print("Usage: python generated_you_are_working_on_the_doc_extractor_s_1764789753.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    try:
        output = process(file_path)
        print(json.dumps(output, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        unittest.main(argv=[sys.argv[0]], verbosity=2)
    else:
        main()