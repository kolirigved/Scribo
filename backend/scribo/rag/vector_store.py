import chromadb
from typing import List, Dict, Any
from scribo.config import settings
from scribo.rag.chunker import Chunk
from scribo.rag.embedder import Embedder
from rank_bm25 import BM25Okapi

def tokenize(text: str) -> List[str]:
    return text.lower().split()

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
        
        self._init_bm25()
        
    def _init_bm25(self):
        """Fetch all documents to build the BM25 index."""
        all_data = self.collection.get(include=["documents", "metadatas"])
        self.bm25_docs = all_data["documents"]
        self.bm25_ids = all_data["ids"]
        self.bm25_metadatas = all_data["metadatas"]
        
        if self.bm25_docs:
            tokenized_corpus = [tokenize(doc) for doc in self.bm25_docs]
            self.bm25 = BM25Okapi(tokenized_corpus)
        else:
            self.bm25 = None

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
            
        self.collection.upsert(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        # Rebuild BM25 index after adding chunks
        self._init_bm25()
        
    def search(self, query: str, course_id: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the vector store using Hybrid Search (Dense + BM25) and RRF."""
        query_embedding = self.embedder.embed_query(query)
        where_clause = {"course_id": course_id.lower()} if course_id else None
        
        # Dense search
        dense_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 2,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )
        
        dense_ranks = {}
        combined_docs = {}
        if dense_results["documents"] and dense_results["documents"][0]:
            for rank, (doc_id, text, meta, dist) in enumerate(zip(
                dense_results["ids"][0],
                dense_results["documents"][0],
                dense_results["metadatas"][0],
                dense_results["distances"][0]
            )):
                dense_ranks[doc_id] = rank + 1
                combined_docs[doc_id] = {"id": doc_id, "text": text, "metadata": meta, "distance": dist}
        
        # Sparse search (BM25)
        sparse_ranks = {}
        if self.bm25:
            tokenized_query = tokenize(query)
            scores = self.bm25.get_scores(tokenized_query)
            
            valid_indices = []
            for i, meta in enumerate(self.bm25_metadatas):
                if not course_id or meta.get("course_id") == course_id.lower():
                    valid_indices.append(i)
                    
            scored_indices = [(scores[i], i) for i in valid_indices if scores[i] > 0]
            scored_indices.sort(reverse=True, key=lambda x: x[0])
            
            for rank, (score, idx) in enumerate(scored_indices[:top_k * 2]):
                doc_id = self.bm25_ids[idx]
                sparse_ranks[doc_id] = rank + 1
                if doc_id not in combined_docs:
                    combined_docs[doc_id] = {
                        "id": doc_id,
                        "text": self.bm25_docs[idx],
                        "metadata": self.bm25_metadatas[idx],
                        "distance": None
                    }
                    
        # RRF (Reciprocal Rank Fusion)
        k = 60
        rrf_scores = {}
        for doc_id in combined_docs:
            dense_rank = dense_ranks.get(doc_id, 1000)
            sparse_rank = sparse_ranks.get(doc_id, 1000)
            rrf_score = 1.0 / (k + dense_rank) + 1.0 / (k + sparse_rank)
            rrf_scores[doc_id] = rrf_score
            
        sorted_doc_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        formatted_results = []
        for doc_id in sorted_doc_ids[:top_k]:
            formatted_results.append(combined_docs[doc_id])
            
        return formatted_results
