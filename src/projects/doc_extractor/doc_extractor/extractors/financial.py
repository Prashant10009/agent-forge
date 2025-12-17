import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

@dataclass
class FinancialDocument:
    document_type: str
    classification_confidence: float
    extracted_fields: Dict[str, Union[str, float, None]]
    text_snippet: str

class FinancialExtractor:
    @staticmethod
    def extract_bank_statement(text: str) -> FinancialDocument:
        account_number = None
        balance = None
        date = None
        
        # Extract account number patterns like XXXXXXX1234
        account_match = re.search(r'Account\s*[:#]?\s*([A-Z0-9-]+)', text, re.IGNORECASE)
        if account_match:
            account_number = account_match.group(1).strip()
        
        # Extract balance patterns like $1,234.56 or 1234.56
        balance_match = re.search(r'(?:Balance|Total)\s*[:$]?\s*([$\d,]+\.\d{2})', text, re.IGNORECASE)
        if balance_match:
            balance_str = balance_match.group(1).replace('$', '').replace(',', '')
            try:
                balance = float(balance_str)
            except ValueError:
                pass
        
        # Extract date patterns like MM/DD/YYYY or Month DD, YYYY
        date_match = re.search(r'(?:Date|As of)\s*[:]?\s*([\d/]+|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}, \d{4})', text, re.IGNORECASE)
        if date_match:
            date = date_match.group(1).strip()
        
        snippet = text[:200] + "..." if len(text) > 200 else text
        
        return FinancialDocument(
            document_type="bank_statement",
            classification_confidence=0.9,
            extracted_fields={
                "account_number": account_number,
                "balance": balance,
                "statement_date": date
            },
            text_snippet=snippet
        )

    @staticmethod
    def extract_insurance_policy(text: str) -> FinancialDocument:
        policy_number = None
        effective_date = None
        premium = None
        
        policy_match = re.search(r'(?:Policy|Policy\s*#)\s*[:]?\s*([A-Z0-9-]+)', text, re.IGNORECASE)
        if policy_match:
            policy_number = policy_match.group(1).strip()
        
        date_match = re.search(r'(?:Effective|Date)\s*[:]?\s*([\d/]+|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}, \d{4})', text, re.IGNORECASE)
        if date_match:
            effective_date = date_match.group(1).strip()
        
        premium_match = re.search(r'(?:Premium|Amount)\s*[:$]?\s*([$\d,]+\.\d{2})', text, re.IGNORECASE)
        if premium_match:
            premium_str = premium_match.group(1).replace('$', '').replace(',', '')
            try:
                premium = float(premium_str)
            except ValueError:
                pass
        
        snippet = text[:200] + "..." if len(text) > 200 else text
        
        return FinancialDocument(
            document_type="insurance_policy",
            classification_confidence=0.85,
            extracted_fields={
                "policy_number": policy_number,
                "effective_date": effective_date,
                "premium_amount": premium
            },
            text_snippet=snippet
        )

    @staticmethod
    def extract_insurance_claim(text: str) -> FinancialDocument:
        claim_number = None
        claim_date = None
        claim_amount = None
        
        claim_match = re.search(r'(?:Claim|Claim\s*#)\s*[:]?\s*([A-Z0-9-]+)', text, re.IGNORECASE)
        if claim_match:
            claim_number = claim_match.group(1).strip()
        
        date_match = re.search(r'(?:Date|Incident)\s*[:]?\s*([\d/]+|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}, \d{4})', text, re.IGNORECASE)
        if date_match:
            claim_date = date_match.group(1).strip()
        
        amount_match = re.search(r'(?:Amount|Total)\s*[:$]?\s*([$\d,]+\.\d{2})', text, re.IGNORECASE)
        if amount_match:
            amount_str = amount_match.group(1).replace('$', '').replace(',', '')
            try:
                claim_amount = float(amount_str)
            except ValueError:
                pass
        
        snippet = text[:200] + "..." if len(text) > 200 else text
        
        return FinancialDocument(
            document_type="insurance_claim",
            classification_confidence=0.8,
            extracted_fields={
                "claim_number": claim_number,
                "claim_date": claim_date,
                "claim_amount": claim_amount
            },
            text_snippet=snippet
        )

    @classmethod
    def extract_from_text(cls, text: str, doc_type: str) -> FinancialDocument:
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        if doc_type == "bank_statement":
            return cls.extract_bank_statement(text)
        elif doc_type == "insurance_policy":
            return cls.extract_insurance_policy(text)
        elif doc_type == "insurance_claim":
            return cls.extract_insurance_claim(text)
        else:
            return FinancialDocument(
                document_type="unknown",
                classification_confidence=0.0,
                extracted_fields={},
                text_snippet=text[:200] + "..." if len(text) > 200 else text
            )