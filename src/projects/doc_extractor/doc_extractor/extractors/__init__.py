from typing import Dict, Any, Optional
from dataclasses import dataclass
import abc

@dataclass
class ExtractedField:
    name: str
    value: Any
    confidence: float

class BaseExtractor(abc.ABC):
    @abc.abstractmethod
    def extract(self, text: str) -> Dict[str, ExtractedField]:
        pass

    @classmethod
    @abc.abstractmethod
    def supported_document_types(cls) -> list[str]:
        pass

class InsurancePolicyExtractor(BaseExtractor):
    @classmethod
    def supported_document_types(cls) -> list[str]:
        return ["insurance_policy"]

    def extract(self, text: str) -> Dict[str, ExtractedField]:
        fields = {}
        # TODO: Implement actual extraction logic
        return fields

class InsuranceClaimExtractor(BaseExtractor):
    @classmethod
    def supported_document_types(cls) -> list[str]:
        return ["insurance_claim"]

    def extract(self, text: str) -> Dict[str, ExtractedField]:
        fields = {}
        # TODO: Implement actual extraction logic
        return fields

class BankStatementExtractor(BaseExtractor):
    @classmethod
    def supported_document_types(cls) -> list[str]:
        return ["bank_statement"]

    def extract(self, text: str) -> Dict[str, ExtractedField]:
        fields = {}
        # TODO: Implement actual extraction logic
        return fields

class PoliceReportExtractor(BaseExtractor):
    @classmethod
    def supported_document_types(cls) -> list[str]:
        return ["police_report"]

    def extract(self, text: str) -> Dict[str, ExtractedField]:
        fields = {}
        # TODO: Implement actual extraction logic
        return fields

class ContractExtractor(BaseExtractor):
    @classmethod
    def supported_document_types(cls) -> list[str]:
        return ["contract"]

    def extract(self, text: str) -> Dict[str, ExtractedField]:
        fields = {}
        # TODO: Implement actual extraction logic
        return fields

def get_extractor(document_type: str) -> Optional[BaseExtractor]:
    extractors = [
        InsurancePolicyExtractor(),
        InsuranceClaimExtractor(),
        BankStatementExtractor(),
        PoliceReportExtractor(),
        ContractExtractor()
    ]
    
    for extractor in extractors:
        if document_type in extractor.supported_document_types():
            return extractor
    return None