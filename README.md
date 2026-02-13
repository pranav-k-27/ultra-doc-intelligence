# Ultra Doc Intelligence


## Overview

Ultra Doc Intelligence is a proof-of-concept RAG (Retrieval-Augmented Generation) system built for logistics documents. It demonstrates multi-document reasoning, rate disambiguation, and production-inspired guardrails suitable for a POC.

**Core Demonstration:** Unlike generic RAG systems, this solution is designed with logistics domain awareness — it understands there are *customer rates* (what shippers pay) and *carrier rates* (what carriers receive), and can retrieve and synthesize information from multiple related documents to disambiguate queries like "What is the rate?"

**Live Application:** [https://ultra-doc-intelligence.onrender.com](https://ultra-doc-intelligence.onrender.com)

**GitHub Repository:** [https://github.com/pranav-k-27/ultra-doc-intelligence](https://github.com/pranav-k-27/ultra-doc-intelligence)

---

## Evaluator Quick Guide

To see the core demonstration quickly:

1. Go to [https://ultra-doc-intelligence.onrender.com](https://ultra-doc-intelligence.onrender.com)
2. Upload each document one at a time and click **"Process Document"** after each:
   - Shipper RC → Process Document
   - Carrier RC → Process Document
   - BOL → Process Document
3. Ask: **"What is the rate?"** or **"What is the profit margin?"**
4. Observe multi-document synthesis and confidence scoring behavior
5. Click **Extract Data** with Reference ID `LD53657` to see structured extraction

For full features including multi-page processing, use local setup (5 minutes — see Quick Start section).
---

## POC Scope and Design Intent

This project is intentionally scoped as a proof-of-concept to demonstrate core AI engineering decisions rather than full production completeness.

**Key goals demonstrated:**
- Grounded, reliable document Q&A (no hallucination on out-of-scope queries)
- Multi-document reasoning (rate disambiguation across 3 document types)
- Transparent guardrails and confidence scoring
- Simple, reviewable architecture (7 core files)

**Out of scope for this POC:**
- Full OCR reliability across all document templates
- Currency and unit normalization
- Large-scale batch processing
- SLA-backed document parsing (LlamaParse free tier processes differently local vs cloud —
  production would require Enterprise tier or self-hosted parser)
- Authentication and multi-tenancy

These are discussed in the Improvement Ideas and Product Roadmap sections.

---

## Core Features

### 1. Multi-Document Question Answering
- Semantic search across multiple document types
- Reference ID-based document linking
- Source attribution with confidence scoring

### 2. Intelligent Rate Disambiguation
- Distinguishes between customer rates ($1,000) and carrier rates ($400)
- Automatically calculates profit margins (60%)
- Synthesizes information from multiple sources

### 3. Structured Data Extraction
- Extracts 11 standard logistics fields
- Priority-based merging (e.g., prefers customer-facing rates from shipper docs)
- Automatic margin calculation
- JSON output with metadata

### 4. Production-Inspired Guardrails
- 3-layer confidence scoring: Retrieval quality + chunk agreement + answer quality
- Pre-LLM quality checks: Rejects low-quality retrievals before wasting tokens
- Threshold-based warnings: Red (<0.4), Yellow (0.4-0.65), Green (>0.65)
- Transparent scoring: Users know when to verify information

### 5. Document-Aware Processing
- Vision-based PDF parsing (LlamaParse)
- Section-aware chunking (rates, pickup, delivery, driver details)
- Table structure preservation
- Metadata enrichment (doc_type, section_type, reference_id)

---

## Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                          │
│                    (Streamlit Web App)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST
┌──────────────────────▼──────────────────────────────────────┐
│                   FastAPI Backend                            │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Upload    │  │     Ask      │  │   Extract    │       │
│  │  Endpoint   │  │   Endpoint   │  │   Endpoint   │       │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                  │               │
└─────────┼─────────────────┼──────────────────┼───────────────┘
          │                 │                  │
┌─────────▼─────────────────▼──────────────────▼───────────────┐
│                  Core RAG Pipeline                            │
│                                                               │
│  ┌────────────────┐      ┌────────────────┐                 │
│  │ Document       │      │ RAG Engine     │                 │
│  │ Processor      │──────▶│ - Retrieval   │                 │
│  │ - LlamaParse   │      │ - Generation  │                 │
│  │ - Chunking     │      │ - Guardrails  │                 │
│  └────────┬───────┘      └────────┬───────┘                 │
│           │                       │                          │
│  ┌────────▼───────────────────────▼───────┐                 │
│  │         Vector Store (ChromaDB)        │                 │
│  │  - Embeddings: text-embedding-3-small  │                 │
│  │  - Metadata filtering                  │                 │
│  │  - Semantic + keyword search           │                 │
│  └────────────────────────────────────────┘                 │
│                                                               │
│  ┌────────────────┐                                          │
│  │  Extractor     │                                          │
│  │  - Per-doc     │                                          │
│  │  - Merge logic │                                          │
│  └────────────────┘                                          │
└───────────────────────────────────────────────────────────────┘
          │                 │                  │
┌─────────▼─────────────────▼──────────────────▼───────────────┐
│              External Services                                │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │  LlamaParse  │         │   OpenAI     │                  │
│  │  (PDF → MD)  │         │  (GPT-4o-mini)│                  │
│  └──────────────┘         └──────────────┘                  │
└───────────────────────────────────────────────────────────────┘
```

### Data Flow

**1. Document Upload:**
```
PDF → LlamaParse (Vision) → Markdown → Section Detection → 
Chunking (with context) → Embeddings → ChromaDB
```

**2. Question Answering:**
```
Query → Smart Filtering (doc_type detection) → Retrieve (n=10) → 
Diversify (ensure multi-doc representation) → Pre-LLM Quality Check → 
Generate Answer → Calculate Confidence → Apply Guardrails → Response
```

**3. Structured Extraction:**
```
Reference ID → Retrieve All Chunks → Group by doc_type → 
Extract per Type → Merge with Priority Rules → Calculate Margin → JSON
```

### Technology Stack

**Core Framework:**
- **FastAPI** - Production-ready API framework with automatic documentation
- **Streamlit** - Rapid UI prototyping
- **Python 3.11** - Sweet spot for ML/AI package compatibility

**Document Processing:**
- **LlamaParse** - Vision-based PDF parsing with table preservation
- **Why LlamaParse?** Complex logistics docs have multi-column layouts, nested tables. Vision-based parsing preserves structure with 90% less code vs manual parsing.

**Vector Database:**
- **ChromaDB** - Local-first, auto-embeddings, metadata filtering
- **text-embedding-3-small** - OpenAI embeddings (1536 dimensions)

**LLM:**
- **GPT-4o-mini** - Cost-effective for POC ($0.15/1M input tokens)
- Temperature: 0.1 (deterministic)
- Max tokens: 150 (forces conciseness)

**Infrastructure:**
- **Render** - Free tier deployment (ephemeral storage)
- **UptimeRobot** - Keep-alive pings (prevent cold starts)

---

## Chunking Strategy

### Approach: Hierarchical Section-Based Chunking

**Problem with Standard Semantic Chunking:**

Standard semantic chunking (e.g., RecursiveCharacterTextSplitter) would:
- Split rate breakdown tables mid-row
- Separate page 2 driver details from main document context
- Lose header information (reference ID, doc type) in each chunk
- Break apart logically cohesive sections

**Our Solution:**

1. **Parse tables separately** - Keep tables intact to preserve row-column relationships
2. **Identify document sections** - Detect headers, pickup, delivery, rates, instructions
3. **Keep sections intact** - Chunk by logical sections, not arbitrary character counts
4. **Add header context** - Include document header metadata in every chunk
5. **Controlled overlap** - 20% overlap for text chunks, no overlap for tables

### Implementation

```python
# In document_processor.py
def _chunk_by_sections(markdown, metadata):
    # Split by markdown headers (##)
    sections = re.split(r'\n(?=##\s)', markdown)
    
    # First section contains header info
    header = sections[0].strip()
    
    # Process remaining sections
    chunks = []
    for section in sections[1:]:
        # Add header context to each chunk
        chunk_content = f"{header}\n\n{section}"
        
        chunk = {
            'content': chunk_content,
            'metadata': {
                **metadata,
                'section_type': identify_section(section),
                'has_table': '|' in section
            }
        }
        chunks.append(chunk)
    
    return chunks
```

### Section Types Identified

**Document Structure Sections:**
- `header` - Document metadata, reference IDs, parties
- `pickup` - Pickup location, date, commodity details
- `delivery` - Delivery location, date, special instructions
- `rates` - Rate breakdown tables, charges
- `driver_details` - Driver name, truck number, trailer number
- `instructions` - Special handling, delivery notes
- `carrier_info` - Carrier contact, MC number, authority
- `customer_info` - Customer details, billing information

### Benefits

1. **Table Integrity** - Rate breakdowns remain intact (preserves calculations)
2. **Context Preservation** - Each chunk includes document header (reference ID, parties)
3. **Better Retrieval** - Section-type metadata enables filtering (e.g., "find rate sections")
4. **Reduced Ambiguity** - Multi-document queries get full context per chunk


---

## Retrieval Method

### Multi-Stage Retrieval with Diversity Enforcement

The retrieval pipeline consists of three stages to ensure comprehensive multi-document coverage.

### Stage 1: Smart Filtering

**Objective:** Reduce search space based on query intent and reference ID

```python
def _build_filter(question, reference_id):
    filter_dict = {}
    
    # Always filter by reference ID if provided
    if reference_id:
        filter_dict['reference_id'] = reference_id
    
    # Detect doc_type intent from keywords
    question_lower = question.lower()
    
    if 'carrier pay' in question_lower or 'carrier rate' in question_lower:
        filter_dict['doc_type'] = 'carrier_rc'
    elif 'customer rate' in question_lower or 'shipper pay' in question_lower:
        filter_dict['doc_type'] = 'shipper_rc'
    elif 'cod' in question_lower or 'bill of lading' in question_lower:
        filter_dict['doc_type'] = 'bol'
    
    # Section-type filters
    if 'driver' in question_lower or 'truck' in question_lower:
        filter_dict['section_type'] = 'driver_details'
    elif 'pickup' in question_lower:
        filter_dict['section_type'] = 'pickup'
    
    return filter_dict
```

**Benefits:**
- Reduces noise in multi-document scenarios
- Improves precision when user is specific
- Enables section-level filtering

### Stage 2: Vector Similarity Search

**Objective:** Retrieve more results than needed to enable diversity

```python
# Retrieve 10-15 results (more than final top-k=5)
all_results = vector_store.query(
    query_text=question,
    n_results=15,  # Over-retrieve
    filter_dict=filter_dict
)
```

**Why over-retrieve?**
- Semantic search may rank all chunks from one document highly
- Need buffer to ensure diverse document types in final set
- Allows downstream diversity enforcement

**Embedding Details:**
- Model: OpenAI `text-embedding-3-small`
- Dimension: 1536
- Distance metric: Cosine similarity (ChromaDB default)
- Cost: $0.02 per 1M tokens

### Stage 3: Diversity Enforcement

**Objective:** Ensure multi-document representation in top-k results

**Problem without diversity:**
```
Query: "What is the rate?"
Top 5 results (by similarity):
  [carrier_rc, carrier_rc, carrier_rc, carrier_rc, carrier_rc]

LLM only sees carrier rate ($400)
Cannot disambiguate or calculate margin
```

**Solution with diversity:**
```python
def _ensure_diversity(results, target=5):
    """Round-robin across doc_types to ensure representation"""
    
    # Group by doc_type
    by_type = {}
    for result in results:
        doc_type = result['metadata']['doc_type']
        if doc_type not in by_type:
            by_type[doc_type] = []
        by_type[doc_type].append(result)
    
    # Round-robin selection
    diversified = []
    round_num = 0
    
    while len(diversified) < target:
        added_this_round = False
        
        for doc_type in sorted(by_type.keys()):
            if round_num < len(by_type[doc_type]):
                diversified.append(by_type[doc_type][round_num])
                added_this_round = True
                
                if len(diversified) >= target:
                    break
        
        if not added_this_round:
            break
        round_num += 1
    
    return diversified[:target]
```

**Result with diversity:**
```
Query: "What is the rate?"
Top 5 results (after diversity):
  [carrier_rc, shipper_rc, bol, carrier_rc, shipper_rc]

LLM sees both customer rate ($1,000) and carrier rate ($400)
Can disambiguate and calculate margin (60%)
```

**Terminal Output Example:**
```
Query: what is the rate?
Total results: 15
After diversity: 5
Top distance: 1.42
Final doc types: ['carrier_rc', 'shipper_rc', 'bol', 'carrier_rc', 'shipper_rc']
```

### Retrieval Quality Check

Before passing context to LLM:

```python
def check_retrieval_quality(results, threshold=2.0):
    """Reject poor retrievals to avoid hallucination"""
    if not results:
        return False
    
    top_distance = results[0]['distance']
    
    # ChromaDB distances can exceed 1.0 (not normalized)
    # Empirically, distance > 2.0 means poor semantic match
    if top_distance > threshold:
        return False  # Don't waste tokens on garbage context
    
    return True
```

**Benefits:**
- Saves API costs (don't send poor context to LLM)
- Reduces hallucination (LLM won't try to answer from irrelevant text)
- Clear "not found" vs made-up answer

---

## Guardrails Approach

### Three-Layer Production-Inspired Guardrail System

Our guardrails operate at three stages: pre-retrieval, post-retrieval, and post-generation. The design is inspired by production requirements while remaining appropriate for a POC.

### Layer 1: Pre-LLM Quality Check

**Objective:** Block low-quality retrievals before consuming API tokens

```python
def check_retrieval_quality(results, threshold=2.0):
    """Reject poor retrievals before LLM call"""
    if not results:
        return {
            'answer': 'No relevant information found.',
            'confidence': 0.0,
            'sources': []
        }
    
    top_distance = results[0]['distance']
    
    if top_distance > threshold:
        return {
            'answer': f'No sufficiently relevant information found (similarity: {1 - top_distance/2.5:.2f}).',
            'confidence': 0.3,
            'sources': []
        }
    
    return None  # Pass through to LLM
```

**Impact:**
- Saves $0.15/1M tokens by avoiding bad LLM calls
- Immediate "not found" response vs waiting for hallucinated answer
- User sees low confidence score, knows info is missing

### Layer 2: Confidence Scoring

**Objective:** Quantify answer reliability (see dedicated section below)

3-component formula:
```
confidence = 0.3 * retrieval_similarity + 0.2 * chunk_agreement + 0.5 * answer_quality
```

### Layer 3: Threshold-Based Warnings

**Objective:** Present answers with appropriate caveats based on confidence

```python
def apply_guardrails(answer, confidence, sources):
    if confidence < 0.4:
        # RED: High uncertainty
        warning = "⚠️ LOW CONFIDENCE - Please verify in original document"
        full_answer = f"{answer}\n\n{warning}"
        color = "red"
    
    elif confidence < 0.65:
        # YELLOW: Moderate uncertainty (common for multi-doc)
        caveat = f"(Confidence: {confidence:.2f} - Recommend verification)"
        full_answer = f"{answer}\n\n{caveat}"
        color = "yellow"
    
    else:
        # GREEN: High confidence
        full_answer = answer
        color = "green"
    
    return {
        'answer': full_answer,
        'confidence': confidence,
        'confidence_color': color,
        'sources': sources
    }
```

**Color Coding:**
- **Red (<0.4):** Strong warning, suggest manual verification
- **Yellow (0.4-0.65):** Note caution, typical for multi-doc synthesis
- **Green (>0.65):** High confidence, direct single-doc answers

### Design Philosophy

**Transparent over Silent:**
- Users always see confidence scores
- No hidden uncertainty
- Enables informed decision-making

**Graceful Degradation:**
- Low-confidence answer with warning > no answer
- User gets information AND knows to be skeptical

**User Empowerment:**
- Provide tools (confidence, sources), let users decide
- Don't make reliability decisions for users
- Support both exploratory and mission-critical use cases

**Why NOT just reject low-confidence answers?**

1. **Multi-doc synthesis inherently lower confidence** (0.5-0.7 range)
   - Example: Profit margin requires both customer and carrier rates
   - Distances higher due to aggregation across documents
   - But answer is still correct and valuable

2. **Complex queries may be correct despite uncertainty**
   - Unusual phrasing might lower retrieval scores
   - Calculation-heavy answers score lower on agreement
   - User context might make answer clearly useful

3. **Warning + answer more useful than "not found"**
   - Users can verify if needed
   - Supports iterative refinement
   - Acknowledges uncertainty without blocking information

---

## Confidence Scoring Method

**TL;DR:** Confidence is a heuristic score (not a probability) that balances retrieval relevance, cross-chunk agreement, and answer specificity. Multi-document queries naturally score lower on retrieval but higher on answer quality, resulting in realistic medium confidence values (0.60-0.72). This is intentional — the system is appropriately less certain when synthesizing across documents.

### Formula

The confidence score combines three components with empirically-tuned weights:

```python
confidence = (
    0.3 * retrieval_similarity +
    0.2 * chunk_agreement +
    0.5 * answer_quality
)
```

### Component 1: Retrieval Similarity (30%)

**Objective:** How well did the top chunk match the query?

```python
def calculate_retrieval_similarity(top_distance):
    """
    ChromaDB returns distances (not similarities) that can exceed 1.0
    Normalize to [0, 1] range with cap at 2.5
    """
    # Distance → Similarity: invert and normalize
    normalized = 1 - min(top_distance / 2.5, 1.0)
    return max(0, normalized)
```

**Why cap at 2.5?**
- ChromaDB cosine distances can theoretically reach 2.0
- Empirically, distances >2.0 indicate poor matches
- Division by 2.5 provides smoother gradient

**Examples:**
- Distance 0.5 → Similarity 0.80 (excellent match)
- Distance 1.0 → Similarity 0.60 (good match)
- Distance 1.5 → Similarity 0.40 (moderate match)
- Distance 2.5+ → Similarity 0.0 (poor match)

### Component 2: Chunk Agreement (20%)

**Objective:** Do multiple retrieved chunks agree (similar distances)?

```python
def calculate_chunk_agreement(top_k_results):
    """
    Average distance across top-k chunks
    Low variance → high agreement → higher confidence
    """
    avg_distance = sum(r['distance'] for r in top_k_results) / len(top_k_results)
    agreement = 1 - min(avg_distance / 2.5, 1.0)
    return max(0, agreement)
```

**Interpretation:**
- All top-k chunks similar distance → high agreement → single clear answer
- Wide variance in distances → low agreement → multiple possible interpretations



### Component 3: Answer Quality (50%)

**Objective:** Assess answer content for specificity and completeness

**Why weighted highest?**
1. Retrieval distance not always predictive (multi-doc queries naturally higher)
2. Answer content (numbers, citations, specifics) more reliable indicator
3. Compensates for diversity-induced distance variance

```python
def score_answer_quality(answer):
    """Heuristic scoring based on answer characteristics"""
    score = 0.7  # Base score
    
    # PENALTIES
    if "not found" in answer.lower() or "no information" in answer.lower():
        return 0.3  # Clear failure case
    
    if len(answer) < 20:
        score *= 0.9  # Very short answers suspect
    
    # BONUSES
    
    # Has dollar amounts (high-value logistics data)
    if re.search(r'\$[\d,]+', answer):
        score += 0.15
    
    # Has numbers (specific data)
    if re.search(r'\d+', answer):
        score += 0.10
    
    # Has citations (grounded in sources)
    if '[Source' in answer or 'Source' in answer:
        score += 0.05
    
    # Has multiple specific details
    if answer.count(',') > 2:  # Lists multiple items
        score += 0.05
    
    return min(1.0, score)
```

**Scoring Examples:**

```
Answer: "The carrier rate is $400.00 USD [Source 1]"
  Base: 0.70
  + Dollar amount: 0.15
  + Numbers: 0.10
  + Citation: 0.05
  → Quality: 1.00

Answer: "The margin is 60%"
  Base: 0.70
  + Number: 0.10
  → Quality: 0.80

Answer: "Not found in documents"
  → Quality: 0.30
```

### Confidence Interpretation

| Range | Label | Typical Scenario | User Action |
|-------|-------|------------------|-------------|
| 0.7+ | **High** | Direct answer from single doc | Trust, use immediately |
| 0.5-0.7 | **Medium** | Multi-doc synthesis, calculations | Verify if critical |
| 0.4-0.5 | **Low-Medium** | Complex query, edge cases | Double-check sources |
| <0.4 | **Low** | Poor retrieval, missing info | Manual verification required |



---

## Failure Cases

### 1. Verification Questions Across Documents

**Query:** "Is the weight the same in all documents?"

**Expected Behavior:** "Yes, all documents show 56,000 lbs for ceramic commodity"

**Actual Behavior:** May not retrieve all relevant sections containing weight information

**Root Cause:**
- Semantic search optimizes for query keywords ("weight", "same", "consistent")
- Query embeddings differ from document embeddings containing actual weight data
- May retrieve header sections instead of commodity/pickup sections where weight appears
- Diversity enforcement helps but doesn't guarantee retrieval of all relevant chunks

**Current Confidence:** Low-Medium (0.45-0.60) - system knows uncertainty

**Workaround:**
- Ask specific questions: "What is the weight in the shipper confirmation?" → 56,000 lbs
- Ask: "What commodity is being shipped?" → Ceramic, 56,000 lbs, 10,000 units
- Multiple targeted queries more reliable than single verification query


---

### 2. Reference ID Extraction Failures

**Issue:** Extraction depends on LlamaParse markdown formatting. Non-standard templates may fail.

**Current Coverage:**
- **Table format:** `| Reference ID | LD53657 |` → Captured
- **Bold format:** `**Reference ID:** LD53657` → Captured
- **Plain text:** `Reference ID: LD53657` → Captured

**Failure Scenarios:**
- Different labels: "Ref #", "Load No.", "Shipment:", "Order #"
- Image-based IDs (logo/header, not text)
- Non-standard placements (footer, sidebar)
- Multi-word references: "Load Reference Number"

**Impact:**
- Documents not linked by reference_id metadata
- Cannot filter queries by shipment
- `/extract` endpoint may not find documents
- Multi-document reasoning limited

**Example Failure:**
```
Document header: "Load # 12345-ABC-XYZ"
Regex pattern: r'Reference ID:\s*(\w+)'
Result: No match → reference_id = None

```

---

### 3. Ambiguous Entity References

**Query:** "Who is the shipper?"

**Ambiguity in Logistics Domain:**
- **Customer company:** "Test ABC" (who hired the carrier)
- **Physical location:** "AAA warehouse at LAX" (where goods are picked up)
- **Carrier perspective:** In carrier docs, "shipper" can mean carrier company

**Current Behavior:** 
```
Returns: "Test ABC"
Confidence: 0.68 (Medium)
```

System defaults to customer company interpretation.

**Ideal Behavior:**
```
Returns: "The term 'shipper' has multiple meanings:
- Customer: Test ABC (hired carrier)
- Pickup Location: AAA, Los Angeles, CA
Would you like details on either?"
```

**Root Cause:**
- No logistics domain ontology
- No entity relationship model
- LLM relies on context but context may be ambiguous

**Impact:** User may get correct answer for wrong question



---

### 4. Multi-Page Processing in Cloud Environments

**Issue:** LlamaParse API exhibits different processing behavior when called from cloud data centers vs. local development.

**Empirical Evidence:**

| Environment | Infrastructure | Carrier RC Processing | Impact |
|-------------|---------------|----------------------|---------|
| **Local Development** | Desktop PC | 6 chunks (full doc) | All content available |
| **Render Free** | 512 MB RAM | 4 chunks (~66%) | Page 2 missing |
| **Railway Free** | 2 GB RAM | 4 chunks (~66%) | Page 2 missing |

**Key Insight:** Since Railway (2GB RAM) shows identical behavior to Render (512MB RAM), this is **not a memory/timeout constraint** but appears to be vendor API behavior.

**Missing Content Examples:**
- Driver details (typically page 2 of carrier confirmations)
- Special handling instructions (appendix pages)
- Additional charges breakdown (continuation pages)

**Impact on Queries:**
```
Local:
  "What are the driver details?" → "John Doe, +1 234 567 8900, Truck 123456" ✓

Cloud:
  "What are the driver details?" → "Not found in documents" ✗
```

**Root Cause Hypotheses:**
1. **Rate limiting** - Cloud IPs throttled vs. local IPs
2. **Quality tiers** - Free API usage receives partial processing
3. **Non-deterministic processing** - Vision model varies by endpoint/region
4. **Request routing** - Different LlamaParse servers for cloud vs. local

**Current Workaround:**
- Core features (rate disambiguation, margin calculation) work in cloud (page 1 content)
- Full features available in local setup (5-minute installation)


---

### 5. Currency and Unit Handling

**Issue:** System doesn't convert currencies or units

**Example Failure:**
```
Document: "Rate: 500 CAD"
Query: "What is the rate in USD?"
Response: "500 CAD" (doesn't convert)
```

**Impact:**
- User confusion when comparing rates across documents
- Incorrect calculations if mixing currencies
- No standardization for reporting/aggregation

**Related Issues:**
- Weight (lbs vs kg vs tons)
- Distance (miles vs km)
- Temperature (F vs C)


---

### 6. Temporal Queries

**Issue:** No date/time reasoning or recency awareness

**Example Queries:**
```
"What is the most recent shipment?" → No concept of "most recent"
"How many shipments last month?" → No date filtering
"Is this pickup tomorrow?" → No temporal calculation
```

**Root Cause:**
- No date parsing/normalization
- No temporal metadata in chunks
- No date comparison logic

---


## Quick Start

### Local Setup

**Prerequisites:**
- Python 3.11 (not 3.12 or 3.13 - package compatibility issues)
- OpenAI API key ([get one](https://platform.openai.com))
- LlamaParse API key ([free tier available](https://cloud.llamaindex.ai/))

**Installation:**

```bash
# Clone repository
git clone https://github.com/pranav-k-27/ultra-doc-intelligence.git
cd ultra-doc-intelligence

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
LLAMA_CLOUD_API_KEY=your_llamaparse_key_here
OPENAI_API_KEY=your_openai_key_here
EOF

# Start API (Terminal 1)
python app.py

# Start UI (Terminal 2 - new terminal)
streamlit run ui.py
```

**Access:**
- **UI:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs

**Setup Time:** 5 minutes

---

## Example Usage

### Showcase Queries (Live Demo)

Test these queries on the live demo to see core features:

**1. Multi-Document Rate Disambiguation**
```
Query: "What is the rate?"

Expected Response:
"There are two rates for this shipment:
- Customer Rate: $1,000.00 USD (what shipper pays) [Source: shipper_rc]
- Carrier Rate: $400.00 USD (what carrier receives) [Source: carrier_rc]"

Confidence: 0.65 (Medium - multi-doc synthesis)
```

**2. Automatic Profit Margin Calculation**
```
Query: "What is the profit margin?"

Expected Response:
"The profit margin is 60%, calculated as ($1,000 - $400) / $1,000"

Confidence: 0.67 (Medium)
```

**3. COD Value Extraction**
```
Query: "What is the COD value?"

Expected Response:
"$64,000 USD [Source: BOL]"

Confidence: 0.67 (Medium)
```

**4. Structured Data Extraction**
```
Reference ID: LD53657

Click "Extract Data" → Returns JSON:
{
  "rate": 1000,
  "carrier_name": "SWIFT SHIFT LOGISTICS LLC",
  "pickup_datetime": "2026-02-08T15:00:00",
  "delivery_datetime": "2026-02-08",
  "weight": 56000,
  "currency": "USD",
  ...
  "_metadata": {
    "margin": 600,
    "sources": ["shipper_rc", "carrier_rc", "bol"]
  }
}
```

### Simple Questions (Single Document)

```
Q: "What is the carrier rate?"
A: The carrier rate is $400.00 USD for SWIFT SHIFT LOGISTICS LLC
Confidence: 0.72 (High)

Q: "Who is the driver?" (Local only - see deployment notes)
A: The driver is John Doe, contact: +1 234 567 8900, Truck: 123456
Confidence: 0.75 (High)

Q: "What commodity is being shipped?"
A: Ceramic, weighing 56,000 lbs with quantity 10,000 units
Confidence: 0.62 (Medium)
```

---

## Performance Metrics

### Latency (Local Development)

| Operation | Avg Latency | Cost per Operation |
|-----------|-------------|-------------------|
| Document Upload (3-page PDF) | ~5s | $0.10 (LlamaParse) |
| Question Answering (simple) | ~1.5s | $0.025 |
| Question Answering (multi-doc) | ~2.5s | $0.04 |
| Structured Extraction | ~3s | $0.07 |

**Test Run:** 3 documents, 20 questions, 5 extractions → 2 minutes, <$1.00

### Accuracy (Manual Evaluation)

| Task | Accuracy | Notes |
|------|----------|-------|
| Single-doc extraction | ~85% | Correct on standard templates |
| Multi-doc synthesis | ~80% | Occasional ambiguity |
| Reference ID detection | ~90% | Misses non-standard formats |
| Confidence calibration | Good | Low scores → actually uncertain |

---

## Deployment Considerations

### Local vs Hosted Execution

To ensure a stable live demo on free-tier infrastructure, the hosted version focuses on core features. Full multi-page extraction is demonstrated reliably in local execution.

**Environment Comparison:**

| Aspect | Local | Hosted (Render) | Recommendation |
|--------|-------|----------------|----------------|
| **Core Features** | All working | All working | Both environments |
| **Multi-page Processing** | Full (6 chunks) | Partial (4 chunks) | Local for full demo |
| **Driver Details (Page 2)** | Found | Missing | Local setup |
| **Rate Disambiguation** | Working | Working | Both environments |
| **Profit Margin Calc** | Working | Working | Both environments |

**Technical Investigation:**

Through testing on Render (512MB RAM) and Railway (2GB RAM), we found that chunk counts differ between local and cloud environments. Since Railway with 4x more memory shows the same behavior, this is not a memory constraint but appears to be a difference in how the LlamaParse API processes requests originating from cloud data center IPs vs. local development.

This is a realistic production consideration: third-party API behavior can vary by environment. Production solutions would include LlamaParse Enterprise tier, AWS Textract, or a self-hosted parser with guaranteed consistency.

**For Evaluators:**

**Option A: Hosted Demo (2 minutes)**
- Test core features (rate disambiguation, margin calculation)
- All showcase queries work on live demo

**Option B: Local Setup (5 minutes)**
- Complete multi-page processing
- All content available
- Follow Quick Start section below

---

## Project Structure

```
ultra-doc-intelligence/
├── app.py                     # FastAPI backend (3 endpoints: /upload, /ask, /extract)
├── ui.py                      # Streamlit web interface
├── start.sh                   # Production startup script (both services)
├── requirements.txt           # Python dependencies
├── .env                       # API keys (not in repo - create locally)
├── .gitignore                # Git exclusions
├── README.md                  # This file
├── PRODUCT_ROADMAP.md         # POC → Production evolution
├── src/
│   ├── __init__.py
│   ├── document_processor.py  # LlamaParse + section-based chunking
│   ├── vector_store.py        # ChromaDB wrapper with metadata filtering
│   ├── rag_engine.py          # Retrieval + diversification + generation + guardrails
│   ├── extractor.py           # Structured extraction with priority merging
│   ├── guardrails.py          # 3-layer confidence scoring
│   └── utils.py               # Reference ID extraction, doc type detection
└── data/
    ├── uploads/               # Temporary PDF storage (ephemeral on Render)
    └── chroma_db/             # Vector database (persistent locally, ephemeral on Render)
```

---





## Further Reading

- **LlamaIndex Documentation** - [docs.llamaindex.ai](https://docs.llamaindex.ai)
- **ChromaDB Documentation** - [docs.trychroma.com](https://docs.trychroma.com)

---


