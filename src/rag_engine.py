"""
RAG Engine: Retrieve + Generate answers
"""
from openai import OpenAI
from typing import List, Dict, Tuple
from .vector_store import VectorStore
from .guardrails import calculate_confidence, apply_guardrails

class RAGEngine:
    def __init__(self, api_key: str, vector_store: VectorStore):
        """Initialize with OpenAI and vector store"""
        self.client = OpenAI(api_key=api_key)
        self.vector_store = vector_store
    
    def ask(self, question: str, reference_id: str = None) -> Dict:
        """
        Main method: Question → Answer with confidence
        """
        # Build smart filter
        filter_dict = self._build_filter(question, reference_id)
        
        # Retrieve MORE results for diversity
        all_results = self.vector_store.query(
            query_text=question,
            n_results=15,  # Get many results
            filter_dict=filter_dict
        )
        
        # CRITICAL: Ensure diversity by doc_type
        results = self._ensure_diversity(all_results, target=5)
        
        # DEBUG
        print(f"\n🔍 Query: {question}")
        print(f"📊 Total results: {len(all_results)}")
        print(f"📊 After diversity: {len(results)}")
        if results:
            print(f"📏 Top distance: {results[0]['distance']}")
            doc_types = [r['metadata'].get('doc_type') for r in results]
            print(f"📄 Final doc types: {doc_types}")
        
        # Check if we have results
        if not results or results[0]['distance'] > 2.0:
            return {
                'answer': "❌ Not found in document - no relevant content retrieved.",
                'confidence': 0.0,
                'sources': []
            }
        
        # Generate answer
        answer, _ = self._generate_answer(question, results)
        
        # Calculate confidence
        confidence = calculate_confidence(question, results, answer)
        final_answer = apply_guardrails(answer, confidence)
        
        return {
            'answer': final_answer,
            'confidence': confidence,
            'sources': [
                {
                    'content': r['content'][:200] + '...',
                    'doc_type': r['metadata'].get('doc_type'),
                    'section': r['metadata'].get('section_type'),
                    'distance': round(r['distance'], 3)
                }
                for r in results[:3]
            ]
        }
    
    def _ensure_diversity(self, results: List[Dict], target: int = 5) -> List[Dict]:
        """
        FIXED: Aggressive diversity enforcement
        Ensures each doc_type gets representation
        """
        if not results:
            return []
        
        # Group by doc_type
        by_type = {}
        for r in results:
            doc_type = r['metadata'].get('doc_type', 'unknown')
            if doc_type not in by_type:
                by_type[doc_type] = []
            by_type[doc_type].append(r)
        
        # Strategy: Take 1 from each type first (round 1)
        # Then take 2nd from each type (round 2), etc.
        diversified = []
        doc_types = list(by_type.keys())
        max_per_type = (target // len(doc_types)) + 1
        
        # Round-robin across types
        for round_num in range(max_per_type):
            for doc_type in doc_types:
                if len(diversified) >= target:
                    break
                if round_num < len(by_type[doc_type]):
                    diversified.append(by_type[doc_type][round_num])
            if len(diversified) >= target:
                break
        
        return diversified[:target]
    
    def _build_filter(self, question: str, reference_id: str = None) -> Dict:
        """Build smart filters based on question intent"""
        filter_dict = {}
        
        if reference_id:
            filter_dict['reference_id'] = reference_id
        
        question_lower = question.lower()
        
        # Only filter by doc_type if VERY specific
        if 'carrier pay' in question_lower or 'carrier cost' in question_lower:
            filter_dict['doc_type'] = 'carrier_rc'
        elif 'customer rate' in question_lower or 'customer pay' in question_lower:
            filter_dict['doc_type'] = 'shipper_rc'
        elif 'bill of lading' in question_lower or 'bol' in question_lower:
            filter_dict['doc_type'] = 'bol'
        # DON'T filter for generic "rate" query - we want all docs!
        
        print(f"🔎 Filter: {filter_dict}")
        return filter_dict
    
    def _generate_answer(self, question: str, results: List[Dict]) -> Tuple[str, str]:
        """Generate answer from retrieved context"""
        context = "\n\n---\n\n".join([
            f"[Source {i+1} - {r['metadata'].get('doc_type')} - {r['metadata'].get('section_type')}]\n{r['content']}" 
            for i, r in enumerate(results)
        ])
        
        # Detect verification questions
        is_verification = any(word in question.lower() for word in ['same', 'consistent', 'match', 'all documents', 'across'])
        
        if is_verification:
            instructions = """CRITICAL INSTRUCTIONS:
    1. This is a verification question - check ALL sources provided
    2. Look for the specific value in EACH source
    3. Answer "Yes" only if ALL sources show the same value
    4. Answer "No" if sources differ or if some sources don't mention it
    5. Be specific about which sources have what values
    6. Keep answer to 2-3 sentences"""
        else:
            instructions = """CRITICAL INSTRUCTIONS:
    1. Answer ONLY the specific question asked
    2. If asked about ONE thing, answer ONLY that
    3. If asked generically about "the rate", explain there are two rates
    4. Keep answer focused and concise (2-3 sentences)
    5. Cite sources in brackets like [Source 1]"""
        
        prompt = f"""You are analyzing logistics documents for shipment LD53657.

    Context from multiple documents:
    {context}

    Question: {question}

    {instructions}

    Answer:"""
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=150
        )
        
        answer = response.choices[0].message.content
        return answer, context
