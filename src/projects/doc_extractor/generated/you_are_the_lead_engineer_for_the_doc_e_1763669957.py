import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Union
import PyPDF2  # Assuming this is used in the existing implementation

class ResumeExtractor:
    """Handles resume/CV specific extraction logic."""
    
    RESUME_SECTION_KEYWORDS = [
        'experience', 'education', 'skills', 'projects',
        'work history', 'professional experience', 'summary'
    ]
    
    PHONE_REGEX = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
    EMAIL_REGEX = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
    
    @staticmethod
    def is_resume(text: str) -> float:
        """Determine if text appears to be a resume/CV and return confidence score."""
        text_lower = text.lower()
        section_hits = sum(1 for section in ResumeExtractor.RESUME_SECTION_KEYWORDS 
                          if section in text_lower)
        
        if section_hits >= 3:
            return 0.9
        elif section_hits >= 2:
            return 0.7
        elif section_hits >= 1:
            return 0.5
        return 0.0
    
    @staticmethod
    def extract_fields(text: str) -> Dict[str, Union[str, List[str], Dict]]:
        """Extract resume-specific fields from text."""
        fields = {}
        
        # Extract contact info
        emails = list(set(ResumeExtractor.EMAIL_REGEX.findall(text)))
        if emails:
            fields['email'] = emails[0]
        
        phones = list(set(ResumeExtractor.PHONE_REGEX.findall(text)))
        if phones:
            fields['phone'] = phones[0][0] if isinstance(phones[0], tuple) else phones[0]
        
        # Simple name extraction (first line with title case)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines[:5]:  # Check first few lines for name
            if line.istitle() and len(line.split()) in (2, 3):
                fields['name'] = line
                break
        
        return fields

def process(file_path: str) -> dict:
    """
    Process a document file and extract structured information.
    
    Args:
        file_path: Path to the document file (PDF, etc.)
    
    Returns:
        Dictionary containing extracted document information
    """
    # Basic metadata
    result = {
        "document_type": "unknown",
        "classification_confidence": 0.5,
        "extracted_fields": {},
        "metadata": {
            "source_path": file_path,
            "timestamp": datetime.utcnow().isoformat(),
            "extraction_method": "pdf_text"  # Default, may be updated
        }
    }
    
    try:
        # Extract text from PDF (simplified - actual implementation may differ)
        text = ""
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            result['metadata']['num_pages'] = len(reader.pages)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        
        result['full_text'] = text
        result['text_snippet'] = text[:200] + "..." if len(text) > 200 else text
        
        # Check if this is a resume
        resume_confidence = ResumeExtractor.is_resume(text)
        if resume_confidence >= 0.5:
            result['document_type'] = "resume"
            result['classification_confidence'] = resume_confidence
            result['extracted_fields'] = ResumeExtractor.extract_fields(text)
            
    except Exception as e:
        result['error'] = str(e)
    
    return result

def main():
    """Test the extractor with a sample file."""
    import sys
    if len(sys.argv) > 1:
        result = process(sys.argv[1])
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python doc_extractor.py <file_path>")

if __name__ == '__main__':
    main()