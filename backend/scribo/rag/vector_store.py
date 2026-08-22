import chromadb
from typing import List, Dict, Any
from scribo.config import settings
from scribo.rag.chunker import Chunk
from scribo.rag.embedder import Embedder

class VectorStore:
    def __init__(self):
        # Initialize persistent ChromaDB client inside our data directory
        db_path = str(settings.COURSES_DATA_DIR / "chroma_db")
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedder = Embedder()
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="scribo_notes",
            metadata={"hnsw:space": "cosine"} # Use cosine similarity
        )
        
    def add_chunks(self, chunks: List[Chunk]):
        """Embed and store chunks in ChromaDB."""
        if not chunks:
            return
            
        texts = [chunk.text for chunk in chunks]
        embeddings = self.embedder.embed(texts)
        
        # Create unique IDs based on course, lecture, and index
        ids = [f"{chunk.metadata.course_id}_{chunk.metadata.lecture_id}_{i}" for i, chunk in enumerate(chunks)]
        
        # Prepare metadata (convert None to empty string as ChromaDB doesn't accept None)
        metadatas = []
        for chunk in chunks:
            meta = chunk.metadata.model_dump()
            if meta.get("timestamp") is None:
                meta["timestamp"] = ""
            metadatas.append(meta)
            
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
    def search(self, query: str, course_id: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the vector store for a query, optionally filtering by course."""
        query_embedding = self.embedder.embed_query(query)
        
        where_clause = {"course_id": course_id} if course_id else None
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause
        )
        
        # Format results nicely
        formatted_results = []
        if results["documents"] and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results and results["distances"] else None
                })
                
        return formatted_results
