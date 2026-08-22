from typing import List, Dict, Any
from google import genai
from google.genai import types
from scribo.config import settings
from scribo.rag.vector_store import VectorStore

class QueryEngine:
    def __init__(self):
        self.vector_store = VectorStore()
        key = settings.GEMINI_API_KEY
        if not key:
            raise ValueError("GEMINI_API_KEY is required for generation.")
        self.client = genai.Client(api_key=key)
        self.model = settings.DEFAULT_MODEL
        
    def query(self, question: str, course_id: str = None) -> Dict[str, Any]:
        """
        Execute a RAG query:
        1. Retrieve relevant chunks
        2. Format prompt
        3. Generate grounded answer
        """
        # 1. Retrieve
        results = self.vector_store.search(question, course_id=course_id, top_k=5)
        
        if not results:
            return {
                "answer": "I don't have any notes indexed for this course yet.",
                "citations": []
            }
            
        # 2. Format Context
        context_blocks = []
        for res in results:
            meta = res["metadata"]
            timestamp_str = f" @ {meta['timestamp']}" if meta.get("timestamp") else ""
            source_tag = f"[{meta['course_id'].upper()} - {meta['lecture_id']}{timestamp_str}]"
            context_blocks.append(f"Source: {source_tag}\nContent: {res['text']}")
            
        context_str = "\n\n---\n\n".join(context_blocks)
        
        # 3. Prompt Construction
        system_prompt = (
            "You are Scribo, an academic AI assistant. You answer student questions based ONLY "
            "on the provided lecture notes context. You must include inline citations pointing to the exact "
            "Source tag provided (e.g. 'As noted in [ENG448 - lec01 @ 04:15]...'). "
            "If the answer is not in the context, say you don't know based on the current notes."
        )
        
        user_prompt = f"Context:\n{context_str}\n\nQuestion:\n{question}"
        
        # 4. Generate Answer
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
            "citations": results
        }
