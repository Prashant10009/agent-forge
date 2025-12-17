from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import json

@dataclass
class ExtractedField:
    name: str
    value: Any
    confidence: float

@dataclass
class ExtractionResult:
    document_type: str
    classification_confidence: float
    extracted_fields: List[ExtractedField]
    text_snippet: str

    def to_json(self) -> str:
        return json.dumps({
            "document_type": self.document_type,
            "classification_confidence": self.classification_confidence,
            "extracted_fields": [
                {"name": field.name, "value": field.value, "confidence": field.confidence}
                for field in self.extracted_fields
            ],
            "text_snippet": self.text_snippet
        }, indent=2)

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: str) -> ExtractionResult:
        """Extract and classify document from given file path."""
        pass

    @abstractmethod
    def supported_types(self) -> List[str]:
        """Return list of document types this extractor supports."""
        pass

    def _validate_file(self, file_path: str) -> None:
        """Basic file validation (exists, readable)."""
        try:
            with open(file_path, 'rb'):
                pass
        except IOError as e:
            raise ValueError(f"Invalid file: {file_path}") from e