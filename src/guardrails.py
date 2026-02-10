
from typing import List, Dict
import re

def calculate_confidence(question: str, results: List[Dict], answer: str) -> float:
    """
    Calculate confidence score (0-1)
    UPDATED: More generous scoring for good retrievals
    """
    if not results:
        return 0.0
    
    # Metric 1: Top retrieval similarity
    # ChromaDB distances typically 0.5-2.0 for good matches
    top_distance = results[0]['distance']
    retrieval_score = max(0, 1 - min(top_distance / 2.5, 1.0))  # Relaxed from 2.0 to 2.5
    
    # Metric 2: Chunk agreement
    top_k = min(3, len(results))
    avg_distance = sum(r['distance'] for r in results[:top_k]) / top_k
    chunk_agreement = max(0, 1 - min(avg_distance / 2.5, 1.0))  # Relaxed
    
    # Metric 3: Answer quality
    answer_quality = _score_answer_quality(answer)
    
    # Weighted combination - UPDATED weights
    confidence = (
        0.3 * retrieval_score +      # Reduced from 0.4
        0.2 * chunk_agreement +      # Reduced from 0.3
        0.5 * answer_quality         # INCREASED from 0.3 - answer quality matters most!
    )
    
    return round(confidence, 2)

def _score_answer_quality(answer: str) -> float:
    """
    Simple heuristics for answer quality
    UPDATED: More generous scoring
    """
    score = 0.7  # Start higher (was 1.0)
    
    # Penalize "not found" heavily
    if "not found" in answer.lower() or "cannot find" in answer.lower():
        return 0.3
    
    # Bonus for specific content
    if re.search(r'\$[\d,]+', answer):  # Has dollar amounts
        score += 0.15
    
    if re.search(r'\d+', answer):  # Has numbers
        score += 0.1
    
    if '[Source' in answer:  # Has citations
        score += 0.05
    
    # Penalize very short answers
    if len(answer) < 20:
        score *= 0.9
    
    return min(1.0, score)

def apply_guardrails(answer: str, confidence: float) -> str:
    """
    Apply guardrails based on confidence threshold
    UPDATED: More reasonable thresholds
    """
    if confidence < 0.4:  # Was 0.5
        return f"⚠️ LOW CONFIDENCE ({confidence})\n\n{answer}\n\n⚠️ Please verify in original document."
    elif confidence < 0.65:  # Was 0.7
        return f"{answer}\n\n(Confidence: {confidence} - Recommend verification)"
    else:
        return answer

# NEW: Pre-LLM guardrail for early rejection
def check_retrieval_quality(results: List[Dict], threshold: float = 0.85) -> bool:
    """
    Check if retrieval quality is good enough to proceed
    Returns False if results are too poor (distance too high)
    
    threshold: Maximum acceptable distance (default 0.85)
    """
    if not results:
        return False
    
    # Check if best result is below threshold
    return results[0]['distance'] < threshold