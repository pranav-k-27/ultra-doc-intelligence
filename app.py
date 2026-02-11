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

# SET WORKING DIRECTORY FIRST
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"📂 Working directory: {os.getcwd()}")

# CREATE DATA DIRECTORIES
os.makedirs("data/uploads", exist_ok=True)
os.makedirs("data/chroma_db", exist_ok=True)
print("✅ Data directories created")

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

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
processor = DocumentProcessor(api_key=os.getenv("LLAMA_CLOUD_API_KEY"))
vector_store = VectorStore()
rag_engine = RAGEngine(
    api_key=os.getenv("OPENAI_API_KEY"),
    vector_store=vector_store
)
extractor = StructuredExtractor(api_key=os.getenv("OPENAI_API_KEY"))

print("✅ All components initialized successfully")

@app.get("/")
@app.head("/")
def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Ultra Doc Intelligence API is running",
        "endpoints": ["/upload", "/ask", "/extract"]
    }

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process PDF document"""
    try:
        print(f"\n📤 Received upload request: {file.filename}")
        
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Save file
        file_path = f"./data/uploads/{file.filename}"
        print(f"💾 Saving to: {file_path}")
        print(f"📂 Current directory: {os.getcwd()}")
        print(f"📁 Upload dir exists: {os.path.exists('./data/uploads')}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"✅ File saved: {os.path.exists(file_path)}")
        print(f"📏 File size: {os.path.getsize(file_path)} bytes")
        
        # Process document
        print(f"🔄 Processing with LlamaParse...")
        chunks = processor.process_pdf(file_path)
        print(f"✅ Created {len(chunks)} chunks")
        
        # Store in vector database
        num_chunks = vector_store.add_chunks(chunks)
        
        # Extract metadata
        reference_id = chunks[0]['metadata'].get('reference_id') if chunks else None
        doc_type = chunks[0]['metadata'].get('doc_type') if chunks else None
        
        print(f"✅ Upload complete: {num_chunks} chunks, ref_id: {reference_id}")
        
        return {
            "status": "success",
            "message": f"Processed {file.filename}",
            "chunks": num_chunks,
            "reference_id": reference_id,
            "doc_type": doc_type
        }
    
    except Exception as e:
        print(f"\n❌ ERROR in upload:")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        import traceback
        print("   Full traceback:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/ask")
async def ask_question(
    question: str = Form(...),
    reference_id: str = Form(None)
):
    """Ask question about uploaded documents"""
    try:
        if not question or len(question.strip()) == 0:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        result = rag_engine.ask(question, reference_id)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")

@app.post("/extract")
async def extract_data(reference_id: str = Form(...)):
    """Extract structured data from documents"""
    try:
        if not reference_id:
            raise HTTPException(status_code=400, detail="reference_id is required")
        
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
    
    uvicorn.run(
        app, 
        host="127.0.0.1",
        port=8000,
        loop="asyncio"
    ) 