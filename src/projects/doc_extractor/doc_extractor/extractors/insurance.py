import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

@dataclass
class InsurancePolicyFields:
    policy_number: str
    insured_name: str
    coverage_period: str
    premium_amount: str
    insurer_name: str

@dataclass
class InsuranceClaimFields:
    claim_number: str
    claimant_name: str
    date_of_loss: str
    claim_amount: str
    insurance_company: str

class InsuranceExtractor:
    @staticmethod
    def extract_policy_fields(text: str) -> InsurancePolicyFields:
        policy_number = re.search(r'(?:policy|pol)\s*[:#]?\s*([A-Z0-9-]+)', text, re.I)
        insured_name = re.search(r'(?:insured|name)\s*[:]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', text)
        coverage_period = re.search(r'(?:coverage|period)\s*[:]?\s*(\d{1,2}/\d{1,2}/\d{4}\s*-\s*\d{1,2}/\d{1,2}/\d{4})', text)
        premium_amount = re.search(r'(?:premium|amount)\s*[:$]?\s*([$\d,]+\.\d{2})', text)
        insurer_name = re.search(r'(?:insurer|company)\s*[:]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)

        return InsurancePolicyFields(
            policy_number=policy_number.group(1) if policy_number else "",
            insured_name=insured_name.group(1) if insured_name else "",
            coverage_period=coverage_period.group(1) if coverage_period else "",
            premium_amount=premium_amount.group(1) if premium_amount else "",
            insurer_name=insurer_name.group(1) if insurer_name else ""
        )

    @staticmethod
    def extract_claim_fields(text: str) -> InsuranceClaimFields:
        claim_number = re.search(r'(?:claim|clm)\s*[:#]?\s*([A-Z0-9-]+)', text, re.I)
        claimant_name = re.search(r'(?:claimant|name)\s*[:]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', text)
        date_of_loss = re.search(r'(?:date\s+of\s+loss|loss\s+date)\s*[:]?\s*(\d{1,2}/\d{1,2}/\d{4})', text)
        claim_amount = re.search(r'(?:claim\s+amount|amount)\s*[:$]?\s*([$\d,]+\.\d{2})', text)
        insurance_company = re.search(r'(?:insurance\s+company|insurer)\s*[:]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)

        return InsuranceClaimFields(
            claim_number=claim_number.group(1) if claim_number else "",
            claimant_name=claimant_name.group(1) if claimant_name else "",
            date_of_loss=date_of_loss.group(1) if date_of_loss else "",
            claim_amount=claim_amount.group(1) if claim_amount else "",
            insurance_company=insurance_company.group(1) if insurance_company else ""
        )

    def extract(self, doc_type: str, text: str) -> Dict[str, Union[str, Dict]]:
        if doc_type == "insurance_policy":
            fields = self.extract_policy_fields(text)
            return {
                "document_type": "insurance_policy",
                "extracted_fields": fields.__dict__,
                "text_snippet": text[:200] + "..." if len(text) > 200 else text
            }
        elif doc_type == "insurance_claim":
            fields = self.extract_claim_fields(text)
            return {
                "document_type": "insurance_claim",
                "extracted_fields": fields.__dict__,
                "text_snippet": text[:200] + "..." if len(text) > 200 else text
            }
        else:
            return {
                "document_type": "unknown",
                "extracted_fields": {},
                "text_snippet": text[:200] + "..." if len(text) > 200 else text
            }