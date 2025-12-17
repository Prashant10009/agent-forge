import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

@dataclass
class LegalDocument:
    document_type: str
    classification_confidence: float
    extracted_fields: Dict[str, str]
    text_snippet: str

class LegalExtractor:
    """Base class for legal document extractors."""
    
    DOCUMENT_TYPE = "legal_document"
    CONFIDENCE_THRESHOLD = 0.7
    
    def __init__(self):
        self.patterns = {
            'party_names': r'(?:party|parties|between)\s*:?\s*([A-Za-z\s,]+)',
            'effective_date': r'(?:effective|date)\s*:?\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})',
            'termination_date': r'(?:termination|expiration)\s*:?\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})',
            'jurisdiction': r'(?:jurisdiction|governing law)\s*:?\s*([A-Za-z\s]+)'
        }
    
    def extract(self, text: str) -> LegalDocument:
        """Extract fields from legal document text."""
        extracted_fields = {}
        
        for field, pattern in self.patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_fields[field] = match.group(1).strip()
        
        snippet = self._generate_snippet(text)
        return LegalDocument(
            document_type=self.DOCUMENT_TYPE,
            classification_confidence=self.CONFIDENCE_THRESHOLD,
            extracted_fields=extracted_fields,
            text_snippet=snippet
        )
    
    def _generate_snippet(self, text: str, max_length: int = 200) -> str:
        """Generate a short snippet from the text."""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."

class ContractExtractor(LegalExtractor):
    """Extractor for general contracts."""
    
    DOCUMENT_TYPE = "contract"
    CONFIDENCE_THRESHOLD = 0.85
    
    def __init__(self):
        super().__init__()
        self.patterns.update({
            'contract_title': r'(?:agreement|contract)\s*:\s*([A-Za-z0-9\s]+)',
            'signature_date': r'(?:signed|executed)\s*on\s*:?\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})'
        })

class LeaseAgreementExtractor(ContractExtractor):
    """Extractor for lease agreements."""
    
    DOCUMENT_TYPE = "lease_agreement"
    CONFIDENCE_THRESHOLD = 0.9
    
    def __init__(self):
        super().__init__()
        self.patterns.update({
            'property_address': r'(?:property|premises)\s*:?\s*([0-9A-Za-z\s,]+)',
            'monthly_rent': r'(?:rent|monthly payment)\s*:?\s*(\$[0-9,]+)',
            'security_deposit': r'(?:security deposit)\s*:?\s*(\$[0-9,]+)'
        })

class LegalExtractorFactory:
    """Factory for creating appropriate legal document extractors."""
    
    @staticmethod
    def get_extractor(text: str) -> LegalExtractor:
        """Determine the appropriate extractor based on document content."""
        text_lower = text.lower()
        
        if 'lease' in text_lower and ('property' in text_lower or 'premises' in text_lower):
            return LeaseAgreementExtractor()
        elif 'contract' in text_lower or 'agreement' in text_lower:
            return ContractExtractor()
        
        return LegalExtractor()