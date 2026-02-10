"""
Document Processing: Parse PDF → Markdown → Chunks
"""
import nest_asyncio
nest_asyncio.apply()

from llama_parse import LlamaParse
from typing import List, Dict
import re
from .utils import extract_reference_id, detect_doc_type

class DocumentProcessor:
    def __init__(self, api_key: str):
        """Initialize with LlamaParse"""
        self.parser = LlamaParse(
            api_key=api_key,
            result_type="markdown",
            parsing_instruction="""
            This is a logistics document. Preserve all tables.
            Maintain headers for sections like Pickup, Delivery, Rate Breakdown.
            """
        )
    
    def process_pdf(self, file_path: str) -> List[Dict]:
        """
        Main method: PDF → Structured chunks
        Returns: List of chunks with content + metadata
        """
        # Parse PDF to markdown
        documents = self.parser.load_data(file_path)
        markdown = documents[0].text
        
        # Extract metadata
        reference_id = extract_reference_id(markdown)
        doc_type = detect_doc_type(markdown)
        
        # DEBUG
        print(f"\n📄 Processing: {file_path}")
        print(f"🔖 Reference ID extracted: {reference_id}")
        print(f"📋 Doc type detected: {doc_type}")
        print(f"📝 Markdown preview (first 300 chars):\n{markdown[:300]}")
        
        metadata = {
            'reference_id': reference_id if reference_id else 'UNKNOWN',
            'doc_type': doc_type
        }
        
        # Split into chunks
        chunks = self._chunk_by_sections(markdown, metadata)
        
        return chunks
    
    def _chunk_by_sections(self, markdown: str, metadata: Dict) -> List[Dict]:
        """Split markdown by sections, keep each section intact"""
        chunks = []
        
        # Split by markdown headers (##)
        sections = re.split(r'\n(?=##\s)', markdown)
        
        # First section is header info (contains basic details)
        header = sections[0].strip()
        
        # Create a chunk for the header (important metadata)
        chunks.append({
            'content': header,
            'metadata': {
                **metadata,
                'chunk_id': 0,
                'section_type': 'header',
                'has_table': False
            }
        })
        
        # Process remaining sections
        for i, section in enumerate(sections[1:], start=1):
            # Add header context to each chunk for better retrieval
            chunk_content = f"{header}\n\n{section}"
            
            chunk = {
                'content': chunk_content,
                'metadata': {
                    **metadata,
                    'chunk_id': i,
                    'section_type': self._identify_section(section),
                    'has_table': '|' in section  # Markdown tables have |
                }
            }
            chunks.append(chunk)
        
        # If no sections found, create single chunk
        if len(chunks) == 1:  # Only header chunk
            chunks.append({
                'content': markdown,
                'metadata': {**metadata, 'chunk_id': 1, 'section_type': 'full_document', 'has_table': '|' in markdown}
            })
        
        return chunks
    
    def _identify_section(self, section: str) -> str:
        """Identify section type by keywords"""
        section_lower = section.lower()
        
        if 'rate' in section_lower and 'breakdown' in section_lower:
            return 'rates'
        elif 'pickup' in section_lower or 'stop' in section_lower and '1' in section:
            return 'pickup'
        elif 'delivery' in section_lower or 'drop' in section_lower or ('stop' in section_lower and '2' in section):
            return 'delivery'
        elif 'driver' in section_lower:
            return 'driver_details'
        elif 'instruction' in section_lower:
            return 'instructions'
        elif 'carrier details' in section_lower:
            return 'carrier_info'
        elif 'customer details' in section_lower:
            return 'customer_info'
        elif 'commodity' in section_lower or 'weight' in section_lower:
            return 'commodity_details'
        else:
            return 'general'