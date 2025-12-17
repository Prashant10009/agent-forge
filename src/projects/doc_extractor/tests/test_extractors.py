import unittest
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class ExtractedDocument:
    document_type: str
    classification_confidence: float
    extracted_fields: Dict[str, str]
    text_snippet: str

class TestFieldExtractors(unittest.TestCase):
    def test_insurance_policy_extraction(self):
        test_text = """
        INSURANCE POLICY
        Policy Number: POL-12345678
        Effective Date: 2023-01-15
        Expiration Date: 2024-01-14
        Premium Amount: $1,200.00
        Insured: John Doe
        """
        
        expected_fields = {
            "policy_number": "POL-12345678",
            "effective_date": "2023-01-15",
            "expiration_date": "2024-01-14",
            "premium_amount": "$1,200.00",
            "insured_name": "John Doe"
        }
        
        result = self._mock_extract(test_text, "insurance_policy")
        self.assertEqual(result.extracted_fields, expected_fields)

    def test_bank_statement_extraction(self):
        test_text = """
        BANK STATEMENT
        Account Number: 9876543210
        Statement Period: 01/01/2023 - 01/31/2023
        Account Holder: Jane Smith
        Opening Balance: $5,000.00
        Closing Balance: $6,250.50
        """
        
        expected_fields = {
            "account_number": "9876543210",
            "statement_period": "01/01/2023 - 01/31/2023",
            "account_holder": "Jane Smith",
            "opening_balance": "$5,000.00",
            "closing_balance": "$6,250.50"
        }
        
        result = self._mock_extract(test_text, "bank_statement")
        self.assertEqual(result.extracted_fields, expected_fields)

    def test_police_report_extraction(self):
        test_text = """
        POLICE REPORT
        Case Number: CR-2023-0456
        Date of Incident: 02/15/2023
        Reporting Officer: Det. Robert Johnson
        Location: 123 Main St, Anytown
        """
        
        expected_fields = {
            "case_number": "CR-2023-0456",
            "incident_date": "02/15/2023",
            "reporting_officer": "Det. Robert Johnson",
            "incident_location": "123 Main St, Anytown"
        }
        
        result = self._mock_extract(test_text, "police_report")
        self.assertEqual(result.extracted_fields, expected_fields)

    def _mock_extract(self, text: str, doc_type: str) -> ExtractedDocument:
        extractors = {
            "insurance_policy": self._extract_insurance_policy,
            "bank_statement": self._extract_bank_statement,
            "police_report": self._extract_police_report
        }
        
        extractor = extractors.get(doc_type)
        if not extractor:
            raise ValueError(f"No extractor for document type: {doc_type}")
            
        fields = extractor(text)
        return ExtractedDocument(
            document_type=doc_type,
            classification_confidence=0.95,  # mock confidence
            extracted_fields=fields,
            text_snippet=text[:100] + "..." if len(text) > 100 else text
        )

    def _extract_insurance_policy(self, text: str) -> Dict[str, str]:
        fields = {}
        lines = text.split('\n')
        for line in lines:
            if "Policy Number:" in line:
                fields["policy_number"] = line.split(":")[1].strip()
            elif "Effective Date:" in line:
                fields["effective_date"] = line.split(":")[1].strip()
            elif "Expiration Date:" in line:
                fields["expiration_date"] = line.split(":")[1].strip()
            elif "Premium Amount:" in line:
                fields["premium_amount"] = line.split(":")[1].strip()
            elif "Insured:" in line:
                fields["insured_name"] = line.split(":")[1].strip()
        return fields

    def _extract_bank_statement(self, text: str) -> Dict[str, str]:
        fields = {}
        lines = text.split('\n')
        for line in lines:
            if "Account Number:" in line:
                fields["account_number"] = line.split(":")[1].strip()
            elif "Statement Period:" in line:
                fields["statement_period"] = line.split(":")[1].strip()
            elif "Account Holder:" in line:
                fields["account_holder"] = line.split(":")[1].strip()
            elif "Opening Balance:" in line:
                fields["opening_balance"] = line.split(":")[1].strip()
            elif "Closing Balance:" in line:
                fields["closing_balance"] = line.split(":")[1].strip()
        return fields

    def _extract_police_report(self, text: str) -> Dict[str, str]:
        fields = {}
        lines = text.split('\n')
        for line in lines:
            if "Case Number:" in line:
                fields["case_number"] = line.split(":")[1].strip()
            elif "Date of Incident:" in line:
                fields["incident_date"] = line.split(":")[1].strip()
            elif "Reporting Officer:" in line:
                fields["reporting_officer"] = line.split(":")[1].strip()
            elif "Location:" in line:
                fields["incident_location"] = line.split(":")[1].strip()
        return fields

if __name__ == '__main__':
    unittest.main()