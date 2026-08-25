from typing import List, Dict, Any
from google import genai
from google.genai import types
from scribo.config import settings
from scribo.rag.vector_store import VectorStore
from flashrank import Ranker, RerankRequest

class QueryEngine:
    def __init__(self):
        self.vector_store = VectorStore()
        key = settings.GEMINI_API_KEY
        if not key:
            raise ValueError("GEMINI_API_KEY is required for generation.")
        self.client = genai.Client(api_key=key)
        self.model = settings.DEFAULT_MODEL
        
        # Initialize FlashRank cross-encoder reranker
        cache_dir = settings.COURSES_DATA_DIR / "flashrank_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.ranker = Ranker(cache_dir=str(cache_dir))
        
    def query(self, question: str, course_id: str = None) -> Dict[str, Any]:
        """
        Execute an Advanced RAG query:
        1. Retrieve candidate chunks via Hybrid Search (BM25 + Dense)
        2. Re-rank chunks using a Cross-Encoder (FlashRank)
        3. Format prompt with top verified chunks
        4. Generate grounded answer
        """
        # 1. Retrieve Candidate Chunks (top_k=15 for higher recall)
        results = self.vector_store.search(question, course_id=course_id, top_k=15)
        
        if not results and course_id:
            # Auto-index course notes if they exist on disk but haven't been indexed yet
            course_dir = settings.COURSES_DATA_DIR / course_id.lower()
            if course_dir.exists():
                from scribo.rag.chunker import split_markdown_by_headers
                indexed_any = False
                for md_file in course_dir.glob("lecture_*.md"):
                    lecture_id = md_file.stem.replace("lecture_", "")
                    text = md_file.read_text(encoding="utf-8")
                    chunks = split_markdown_by_headers(text, course_id, lecture_id)
                    if chunks:
                        self.vector_store.add_chunks(chunks)
                        indexed_any = True
                if indexed_any:
                    results = self.vector_store.search(question, course_id=course_id, top_k=15)

        if not results:
            return {
                "answer": "I don't have any notes indexed for this course yet.",
                "citations": []
            }
            
        # 2. Re-Ranking with FlashRank
        passages = []
        for res in results:
            passages.append({
                "id": res["id"],
                "text": res["text"],
                "meta": res["metadata"]
            })
            
        rerank_request = RerankRequest(query=question, passages=passages)
        rerank_results = self.ranker.rerank(rerank_request)
        
        # Filter down to top 3 highly relevant chunks
        top_results = []
        for item in rerank_results[:3]:
            top_results.append({
                "id": item["id"],
                "text": item["text"],
                "metadata": item.get("meta", {})
            })
            
        # 3. Format Context
        context_blocks = []
        for res in top_results:
            meta = res["metadata"]
            timestamp_str = f" @ {meta['timestamp']}" if meta.get("timestamp") else ""
            source_tag = f"[{meta['course_id'].upper()} - {meta['lecture_id']}{timestamp_str}]"
            context_blocks.append(f"Source: {source_tag}\nContent: {res['text']}")
            
        context_str = "\n\n---\n\n".join(context_blocks)
        
        # 4. Prompt Construction
        system_prompt = (
            "You are Scribo, an academic AI assistant. You answer student questions based ONLY "
            "on the provided lecture notes context. You must include inline citations pointing to the exact "
            "Source tag provided (e.g. 'As noted in [ENG448 - lec01 @ 04:15]...'). "
            "If the answer is not in the context, say you don't know based on the current notes."
        )
        
        user_prompt = f"Context:\n{context_str}\n\nQuestion:\n{question}"
        
        # 5. Generate Answer
        response = self.client.models.generate_content(
            model=self.model,
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.3
            )
        )
        
        return {
            "answer": response.text,
            "citations": top_results
        }
