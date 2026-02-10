
from openai import OpenAI
import json
from typing import Dict, List

class StructuredExtractor:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def extract(self, chunks: List[Dict]) -> Dict:
        """
        FIXED: Extract per document type, then merge
        
        chunks: List of chunks with metadata (from vector store query)
        Returns: Merged JSON with all 11 fields
        """
        # Step 1: Group chunks by document type
        doc_groups = self._group_by_doc_type(chunks)
        
        # Step 2: Extract from each document type separately
        extractions = {}
        for doc_type, doc_chunks in doc_groups.items():
            content = "\n\n".join([c['content'] for c in doc_chunks])
            extractions[doc_type] = self._extract_from_content(content, doc_type)
        
        # Step 3: Merge with priority rules
        merged = self._merge_extractions(extractions)
        
        return merged
    
    def _group_by_doc_type(self, chunks: List[Dict]) -> Dict[str, List[Dict]]:
        """Group chunks by document type"""
        groups = {}
        for chunk in chunks:
            doc_type = chunk['metadata'].get('doc_type', 'unknown')
            if doc_type not in groups:
                groups[doc_type] = []
            groups[doc_type].append(chunk)
        return groups
    
    def _extract_from_content(self, content: str, doc_type: str) -> Dict:
        """
        Extract from a single document type
        Uses doc_type to guide extraction
        """
        # Define schema (same for all, but prompt varies)
        schema = {
            "shipment_id": "string or null",
            "shipper": "string or null",
            "consignee": "string or null",
            "pickup_datetime": "ISO format or null",
            "delivery_datetime": "ISO format or null",
            "equipment_type": "string or null",
            "mode": "string or null",
            "rate": "number or null",
            "currency": "string or null",
            "weight": "number or null",
            "carrier_name": "string or null"
        }
        
        # Customize prompt based on doc type
        if doc_type == 'carrier_rc':
            rate_instruction = "For 'rate': Extract CARRIER PAY (what carrier receives), NOT customer rate"
        elif doc_type == 'shipper_rc':
            rate_instruction = "For 'rate': Extract CUSTOMER RATE (what shipper pays), NOT carrier pay"
        else:
            rate_instruction = "For 'rate': Extract the main rate/charge amount"
        
        prompt = f"""Extract logistics information from this {doc_type.upper()} document:

{content}

Return JSON with these fields (use null if not found):
{json.dumps(schema, indent=2)}

RULES:
- Extract ONLY explicit information, do not infer
- {rate_instruction}
- For dates, use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
- For rate, extract numeric value only (no $ or currency symbols)
- Use null for missing fields, not empty strings
- For shipper/consignee, extract the NAME, not full address

JSON:"""
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        # Parse JSON
        result_text = response.choices[0].message.content
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        
        try:
            extracted = json.loads(result_text)
        except json.JSONDecodeError:
            # Fallback: return empty schema
            extracted = {k: None for k in schema.keys()}
        
        return extracted
    
    def _merge_extractions(self, extractions: Dict[str, Dict]) -> Dict:
        """
        CRITICAL: Merge extractions with priority rules
        
        Priority:
        - shipment_id, pickup_datetime, delivery_datetime: ANY source (should be same)
        - rate: SHIPPER RC (customer-facing rate)
        - carrier_name: CARRIER RC
        - shipper, consignee: BOL preferred, else any
        - Other fields: First non-null value
        """
        merged = {}
        
        # Priority order for different fields
        priority_map = {
            'rate': ['shipper_rc', 'carrier_rc', 'bol'],  # Customer rate preferred
            'carrier_name': ['carrier_rc', 'shipper_rc', 'bol'],
            'shipper': ['bol', 'shipper_rc', 'carrier_rc'],
            'consignee': ['bol', 'shipper_rc', 'carrier_rc'],
            'default': ['shipper_rc', 'carrier_rc', 'bol']  # Default priority
        }
        
        # Get all possible fields
        all_fields = set()
        for ext in extractions.values():
            all_fields.update(ext.keys())
        
        # Merge each field
        for field in all_fields:
            # Get priority order for this field
            priority = priority_map.get(field, priority_map['default'])
            
            # Find first non-null value following priority
            for doc_type in priority:
                if doc_type in extractions and extractions[doc_type].get(field) is not None:
                    merged[field] = extractions[doc_type][field]
                    break
            else:
                merged[field] = None
        
        # BONUS: Add metadata about which docs were used
        merged['_metadata'] = {
            'sources': list(extractions.keys()),
            'extraction_note': 'Merged from multiple document types with priority rules'
        }
        
        # BONUS: If we have both customer and carrier rates, note the margin
        if 'shipper_rc' in extractions and 'carrier_rc' in extractions:
            customer_rate = extractions['shipper_rc'].get('rate')
            carrier_rate = extractions['carrier_rc'].get('rate')
            if customer_rate and carrier_rate:
                merged['_metadata']['margin'] = customer_rate - carrier_rate
        
        return merged