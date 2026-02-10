"""
FastAPI Application: 3 endpoints
/upload, /ask, /extract
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
import shutil

from src.document_processor import DocumentProcessor
from src.vector_store import VectorStore
from src.rag_engine import RAGEngine
from src.extractor import StructuredExtractor

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="Ultra Doc Intelligence",
    description="RAG system for logistics documents",
    version="1.0.0"
)

# Enable CORS for Streamlit UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
# Initialize components - FIXED: Don't catch errors here
processor = DocumentProcessor(api_key=os.getenv("LLAMA_CLOUD_API_KEY"))
vector_store = VectorStore()
rag_engine = RAGEngine(
    api_key=os.getenv("OPENAI_API_KEY"),
    vector_store=vector_store
)
extractor = StructuredExtractor(api_key=os.getenv("OPENAI_API_KEY"))

print("✅ All components initialized successfully")

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Ultra Doc Intelligence API is running",
        "endpoints": ["/upload", "/ask", "/extract"]
    }

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process PDF document
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Save file temporarily
        file_path = f"./data/uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process document
        chunks = processor.process_pdf(file_path)
        
        # Store in vector database
        num_chunks = vector_store.add_chunks(chunks)
        
        # Extract reference ID
        reference_id = chunks[0]['metadata'].get('reference_id') if chunks else None
        doc_type = chunks[0]['metadata'].get('doc_type') if chunks else None
        
        return {
            "status": "success",
            "message": f"Processed {file.filename}",
            "chunks": num_chunks,
            "reference_id": reference_id,
            "doc_type": doc_type
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.post("/ask")
async def ask_question(
    question: str = Form(...),
    reference_id: str = Form(None)
):
    """
    Ask question about uploaded documents
    """
    try:
        if not question or len(question.strip()) == 0:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Get answer from RAG engine
        result = rag_engine.ask(question, reference_id)
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")

@app.post("/extract")
async def extract_data(reference_id: str = Form(...)):
    """
    Extract structured data from documents
    """
    try:
        if not reference_id:
            raise HTTPException(status_code=400, detail="reference_id is required")
        
        # Query all chunks for this shipment
        results = vector_store.query(
            query_text=reference_id,
            n_results=20,
            filter_dict={"reference_id": reference_id}
        )
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"No documents found for reference_id: {reference_id}"
            )
        
        # Extract structured data
        extracted = extractor.extract(results)
        
        return extracted
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Ultra Doc Intelligence API...")
    print("📄 API Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)