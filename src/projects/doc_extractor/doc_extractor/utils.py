import re
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    document_type: str
    classification_confidence: float
    extracted_fields: Dict[str, Any]
    text_snippet: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

def normalize_text(text: str) -> str:
    """Normalize text by removing extra whitespace and converting to lowercase."""
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()

def validate_file_path(file_path: str) -> bool:
    """Check if file exists and has a supported extension."""
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return False
    
    supported_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff']
    if path.suffix.lower() not in supported_extensions:
        logger.error(f"Unsupported file extension: {path.suffix}")
        return False
    
    return True

def split_text_into_blocks(text: str, max_block_size: int = 1000) -> List[str]:
    """Split text into blocks of approximately max_block_size characters."""
    blocks = []
    while len(text) > max_block_size:
        split_pos = text.rfind(' ', 0, max_block_size)
        if split_pos == -1:
            split_pos = max_block_size
        blocks.append(text[:split_pos])
        text = text[split_pos:].lstrip()
    blocks.append(text)
    return blocks

def calculate_confidence(text: str, keywords: Dict[str, List[str]]) -> float:
    """Calculate confidence score based on keyword matches."""
    text = normalize_text(text)
    matches = 0
    total_keywords = sum(len(words) for words in keywords.values())
    
    if total_keywords == 0:
        return 0.0
    
    for doc_type, words in keywords.items():
        for word in words:
            if word.lower() in text:
                matches += 1
    
    return min(1.0, matches / total_keywords)

def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two dictionaries, with dict2 values taking precedence."""
    result = dict1.copy()
    result.update(dict2)
    return result

def get_file_extension(file_path: str) -> str:
    """Get lowercase file extension without the dot."""
    return Path(file_path).suffix[1:].lower()

def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max_length characters, adding ellipsis if truncated."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def main():
    """Demo utility functions."""
    test_text = "  This   is  a  TEST   string with   extra spaces.  "
    print(f"Normalized: '{normalize_text(test_text)}'")
    
    test_path = "test.pdf"
    print(f"Valid file: {validate_file_path(test_path)}")
    
    long_text = " ".join(["word"] * 500)
    blocks = split_text_into_blocks(long_text)
    print(f"Split into {len(blocks)} blocks")
    
    keywords = {
        "insurance": ["policy", "premium", "coverage"],
        "bank": ["statement", "balance", "transaction"]
    }
    confidence = calculate_confidence("This is a bank statement", keywords)
    print(f"Confidence score: {confidence:.2f}")

if __name__ == '__main__':
    main()