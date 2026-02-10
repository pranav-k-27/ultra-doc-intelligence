import chromadb
from chromadb.config import Settings
from typing import List, Dict
import uuid

class VectorStore:
    def __init__(self, persist_directory: str = "./data/chroma_db"):
        """Initialize ChromaDB with persistence"""
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,  # Disable telemetry
                allow_reset=True
            )
        )
        
        self.collection = self.client.get_or_create_collection(
            name="logistics_docs",
            metadata={"description": "Logistics document chunks"}
        )
    
    def add_chunks(self, chunks: List[Dict]) -> int:
        """Add chunks to vector store"""
        documents = [chunk['content'] for chunk in chunks]
        
        # FIXED: Clean metadata - remove None values
        metadatas = []
        for chunk in chunks:
            clean_metadata = {}
            for key, value in chunk['metadata'].items():
                if value is not None:  # Only add non-None values
                    # Convert all values to strings for ChromaDB
                    clean_metadata[key] = str(value)
            metadatas.append(clean_metadata)
        
        ids = [str(uuid.uuid4()) for _ in chunks]
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        return len(chunks)
    
    def query(self, 
              query_text: str, 
              n_results: int = 5,
              filter_dict: Dict = None) -> List[Dict]:
        """Query vector store"""
        # FIXED: Clean filter_dict - remove None values
        if filter_dict:
            filter_dict = {k: v for k, v in filter_dict.items() if v is not None}
        
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=filter_dict if filter_dict else None
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })
        
        return formatted_results
    
    def clear_collection(self):
        """Clear all data"""
        self.client.delete_collection("logistics_docs")
        self.collection = self.client.create_collection("logistics_docs")