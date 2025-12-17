import json
import os
from datetime import datetime
from typing import Dict, Any
import PyPDF2
from typing import Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Core document processing class that handles text extraction and classification."""
    
    @staticmethod
    def extract_text(file_path: str) -> Optional[str]:
        """Extract text from a document file.
        
        Args:
            file_path: Path to the document file.
            
        Returns:
            Extracted text as a string, or None if extraction fails.
        """
        try:
            if file_path.lower().endswith('.pdf'):
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() or ""
                    return text
            else:
                logger.warning(f"Unsupported file type: {file_path}")
                return None
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {str(e)}")
            return None

    @staticmethod
    def classify_document(text: str) -> Dict[str, Any]:
        """Classify the document type based on extracted text.
        
        Args:
            text: Extracted text from the document.
            
        Returns:
            Dictionary with document_type and classification_confidence.
        """
        # Simple keyword-based classification - can be replaced with ML model
        text_lower = text.lower()
        doc_type = "unknown"
        confidence = 0.3
        
        if any(word in text_lower for word in ["invoice", "bill"]):
            doc_type = "invoice"
            confidence = 0.7
        elif "receipt" in text_lower:
            doc_type = "receipt"
            confidence = 0.7
        elif any(word in text_lower for word in ["contract", "agreement"]):
            doc_type = "contract"
            confidence = 0.6
        elif any(word in text_lower for word in ["passport", "id", "driver license"]):
            doc_type = "id_document"
            confidence = 0.8
            
        return {
            "document_type": doc_type,
            "classification_confidence": confidence
        }

    @staticmethod
    def extract_fields(text: str, doc_type: str) -> Dict[str, Any]:
        """Extract structured fields based on document type.
        
        Args:
            text: Extracted text from the document.
            doc_type: Classified document type.
            
        Returns:
            Dictionary of extracted fields.
        """
        if doc_type == "unknown":
            return {}
            
        fields = {}
        text_lower = text.lower()
        
        if doc_type == "invoice":
            # Simple pattern matching for demo - replace with proper parsing
            if "total" in text_lower:
                total_index = text_lower.find("total")
                fields["total_amount"] = text[total_index:total_index+20].strip()
                
        elif doc_type == "receipt":
            if "date" in text_lower:
                date_index = text_lower.find("date")
                fields["date"] = text[date_index:date_index+20].strip()
                
        return fields

def process(file_path: str) -> Dict[str, Any]:
    """Main processing function that extracts and structures document data.
    
    Args:
        file_path: Path to the document file.
        
    Returns:
        Dictionary containing extracted document information.
        
    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the file can't be processed.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    # Extract text
    full_text = DocumentProcessor.extract_text(file_path)
    if not full_text:
        raise ValueError(f"Failed to extract text from {file_path}")
        
    # Classify document
    classification = DocumentProcessor.classify_document(full_text)
    
    # Extract fields
    extracted_fields = DocumentProcessor.extract_fields(
        full_text, classification["document_type"]
    )
    
    # Get metadata
    num_pages = 0
    if file_path.lower().endswith('.pdf'):
        with open(file_path, 'rb') as file:
            num_pages = len(PyPDF2.PdfReader(file).pages)
    
    metadata = {
        "source_path": file_path,
        "num_pages": num_pages,
        "timestamp": datetime.utcnow().isoformat(),
        "extraction_method": "pypdf" if file_path.lower().endswith('.pdf') else "unknown"
    }
    
    # Build result
    result = {
        "document_type": classification["document_type"],
        "classification_confidence": classification["classification_confidence"],
        "full_text": full_text,
        "extracted_fields": extracted_fields,
        "metadata": metadata
    }
    
    # Verify JSON serialization
    try:
        json.dumps(result)
    except TypeError as e:
        logger.error(f"Result contains non-serializable data: {str(e)}")
        raise ValueError("Failed to serialize result to JSON") from e
        
    return result

def main():
    """Example usage of the doc_extractor module."""
    import sys
    if len(sys.argv) != 2:
        print("Usage: python -m doc_extractor <file_path>")
        sys.exit(1)
        
    try:
        result = process(sys.argv[1])
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()