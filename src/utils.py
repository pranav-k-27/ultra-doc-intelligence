"""
Utility functions for metadata extraction
"""
import re
from typing import Optional

def extract_reference_id(text: str) -> Optional[str]:
    """Extract reference ID from document text"""
    # Pattern 1: Table format | Reference ID | LD53657 |
    table_match = re.search(r'\|\s*Reference\s+ID\s*\|\s*([A-Z0-9]+)', text, re.IGNORECASE)
    if table_match:
        return table_match.group(1)
    
    # Pattern 2: Bold format **Reference ID:** LD53657
    bold_match = re.search(r'\*\*Reference\s+ID[:\s]*\*\*\s*([A-Z0-9]+)', text, re.IGNORECASE)
    if bold_match:
        return bold_match.group(1)
    
    # Pattern 3: Plain text Reference ID: LD53657
    plain_match = re.search(r'Reference\s+ID[:\s]+([A-Z0-9]+)', text, re.IGNORECASE)
    if plain_match:
        return plain_match.group(1)
    
    # Pattern 4: Load ID variations
    load_match = re.search(r'Load\s+ID[:\s]+([A-Z0-9]+)', text, re.IGNORECASE)
    if load_match:
        return load_match.group(1)
    
    # Pattern 5: Direct pattern match (LD followed by numbers, BOL followed by numbers)
    direct_match = re.search(r'\b(LD[0-9]{5}|BOL[0-9]{5})\b', text)
    if direct_match:
        return direct_match.group(1)
    
    return "UNKNOWN"

def detect_doc_type(text: str) -> str:
    """Detect document type from content"""
    text_lower = text.lower()
    
    if 'customer rate' in text_lower or 'customer details' in text_lower:
        return 'shipper_rc'
    elif 'carrier rate' in text_lower or 'carrier details' in text_lower:
        return 'carrier_rc'
    elif 'bill of lading' in text_lower:
        return 'bol'
    else:
        return 'unknown'