import re
import json
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class ExtractedDocument:
    extracted_fields: Dict[str, Optional[str]]
    raw_text: str

def extract_dhs_fields(text: str) -> Dict[str, Optional[str]]:
    """Extract DHS/immigration training plan specific fields from text."""
    fields = {
        'student_name': None,
        'employer_name': None,
        'program_name': None,
        'expiration_date': None,
        'reference_number': None
    }

    # Student name pattern (look for "Student:", "Trainee:", or similar)
    name_match = re.search(
        r'(Student|Trainee)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        text,
        re.IGNORECASE
    )
    if name_match:
        fields['student_name'] = name_match.group(2).strip()

    # Employer name pattern (look for "Employer:", "Company:", or similar)
    employer_match = re.search(
        r'(Employer|Company|Organization)[:\s]+([A-Z][a-z]+(?:\s+[A-Za-z]+)*)',
        text,
        re.IGNORECASE
    )
    if employer_match:
        fields['employer_name'] = employer_match.group(2).strip()

    # Program name pattern
    program_match = re.search(
        r'(Program|Course|Training)[\s]*Name[:\s]+([A-Z][a-z]+(?:\s+[A-Za-z]+)*)',
        text,
        re.IGNORECASE
    )
    if program_match:
        fields['program_name'] = program_match.group(2).strip()

    # Expiration date pattern (various date formats)
    date_match = re.search(
        r'(Expiration|Expires|Valid Until)[:\s]+'
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|'
        r'[A-Z][a-z]+\s\d{1,2},\s\d{4})',
        text,
        re.IGNORECASE
    )
    if date_match:
        fields['expiration_date'] = date_match.group(2).strip()

    # Reference/ID number pattern
    id_match = re.search(
        r'(ID|Reference|Number|No)[:\s]*([A-Z0-9-]+)',
        text,
        re.IGNORECASE
    )
    if id_match:
        fields['reference_number'] = id_match.group(2).strip()

    return fields

def extract_invoice_fields(text: str) -> Dict[str, Optional[str]]:
    """Extract common invoice fields from text."""
    fields = {
        'invoice_number': None,
        'invoice_date': None,
        'due_date': None,
        'total_amount': None,
        'vendor_name': None
    }

    # Invoice number pattern
    inv_num_match = re.search(
        r'(Invoice|Bill)\s*(?:No|Number|#)[:\s]*([A-Z0-9-]+)',
        text,
        re.IGNORECASE
    )
    if inv_num_match:
        fields['invoice_number'] = inv_num_match.group(2).strip()

    # Invoice date pattern
    inv_date_match = re.search(
        r'(Invoice|Bill)\s*Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|'
        r'[A-Z][a-z]+\s\d{1,2},\s\d{4})',
        text,
        re.IGNORECASE
    )
    if inv_date_match:
        fields['invoice_date'] = inv_date_match.group(2).strip()

    # Due date pattern
    due_date_match = re.search(
        r'(Due|Payment)\s*Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|'
        r'[A-Z][a-z]+\s\d{1,2},\s\d{4})',
        text,
        re.IGNORECASE
    )
    if due_date_match:
        fields['due_date'] = due_date_match.group(2).strip()

    # Total amount pattern
    total_match = re.search(
        r'(Total|Amount Due|Balance)[:\s]+\$?(\d+\.\d{2})',
        text,
        re.IGNORECASE
    )
    if total_match:
        fields['total_amount'] = total_match.group(2).strip()

    # Vendor name pattern
    vendor_match = re.search(
        r'(From|Vendor|Supplier)[:\s]+([A-Z][a-z]+(?:\s+[A-Za-z]+)*)',
        text,
        re.IGNORECASE
    )
    if vendor_match:
        fields['vendor_name'] = vendor_match.group(2).strip()

    return fields

def extract_receipt_fields(text: str) -> Dict[str, Optional[str]]:
    """Extract common receipt fields from text."""
    fields = {
        'receipt_number': None,
        'date': None,
        'total': None,
        'payment_method': None,
        'merchant_name': None
    }

    # Receipt number pattern
    receipt_num_match = re.search(
        r'(Receipt|Confirmation)\s*(?:No|Number|#)[:\s]*([A-Z0-9-]+)',
        text,
        re.IGNORECASE
    )
    if receipt_num_match:
        fields['receipt_number'] = receipt_num_match.group(2).strip()

    # Date pattern
    date_match = re.search(
        r'(Date|Time)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|'
        r'[A-Z][a-z]+\s\d{1,2},\s\d{4})',
        text,
        re.IGNORECASE
    )
    if date_match:
        fields['date'] = date_match.group(2).strip()

    # Total amount pattern
    total_match = re.search(
        r'(Total|Amount|Subtotal)[:\s]+\$?(\d+\.\d{2})',
        text,
        re.IGNORECASE
    )
    if total_match:
        fields['total'] = total_match.group(2).strip()

    # Payment method pattern
    payment_match = re.search(
        r'(Payment\s*Method|Paid\s*With)[:\s]+([A-Z][a-z]+(?:\s+[A-Za-z]+)*)',
        text,
        re.IGNORECASE
    )
    if payment_match:
        fields['payment_method'] = payment_match.group(2).strip()

    # Merchant name pattern
    merchant_match = re.search(
        r'(Merchant|Store|Business)[:\s]+([A-Z][a-z]+(?:\s+[A-Za-z]+)*)',
        text,
        re.IGNORECASE
    )
    if merchant_match:
        fields['merchant_name'] = merchant_match.group(2).strip()

    return fields

def process(file_path: str) -> ExtractedDocument:
    """Process a document file and extract relevant fields."""
    # Read file content (simplified for this example)
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Determine document type based on content
    doc_type = 'unknown'
    if re.search(r'(Invoice|Bill)', text, re.IGNORECASE):
        doc_type = 'invoice'
    elif re.search(r'(Receipt|Confirmation)', text, re.IGNORECASE):
        doc_type = 'receipt'
    elif re.search(r'(Student|Trainee|Training Plan)', text, re.IGNORECASE):
        doc_type = 'dhs_training'

    # Extract fields based on document type
    extracted_fields = {}
    if doc_type == 'invoice':
        extracted_fields = extract_invoice_fields(text)
    elif doc_type == 'receipt':
        extracted_fields = extract_receipt_fields(text)
    elif doc_type == 'dhs_training':
        extracted_fields = extract_dhs_fields(text)

    # Return the extracted document
    return ExtractedDocument(
        extracted_fields=extracted_fields,
        raw_text=text
    )

def main():
    """Example usage of the document processor."""
    import sys
    if len(sys.argv) < 2:
        print("Usage: python doc_extractor.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    result = process(file_path)
    print(json.dumps(result.extracted_fields, indent=2))

if __name__ == '__main__':
    main()