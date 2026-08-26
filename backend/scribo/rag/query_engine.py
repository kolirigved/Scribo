from typing import List, Dict, Any, Optional
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

    def rewrite_query(self, question: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Rewrite and expand student query using Gemini for optimal hybrid retrieval:
        - Resolves ambiguous conversational references / pronouns from history
        - Expands technical acronyms and domain terminology
        - Enriches with academic keywords and synonyms
        """
        if not question or not question.strip():
            return question

        history_context = ""
        if history:
            formatted_turns = []
            for h in history[-6:]:  # Keep recent context
                role = "Student" if h.get("role") in ["user", "human"] else "Assistant"
                content = h.get("content", "").strip()
                if content:
                    formatted_turns.append(f"{role}: {content}")
            if formatted_turns:
                history_context = "Conversation History:\n" + "\n".join(formatted_turns) + "\n\n"

        system_prompt = (
            "You are an academic search query optimizer for a university lecture RAG system. "
            "Your job is to rewrite the student's question into an optimal, standalone search query for hybrid BM25 + dense vector search.\n"
            "Rules:\n"
            "1. Resolve any pronouns, follow-ups, or ambiguous references using conversation history.\n"
            "2. Expand course-related acronyms and abbreviations into their full terminology (e.g. 'DPD' -> 'Digital Predistortion', 'CIR' -> 'Channel Impulse Response', 'DoA' -> 'Direction of Arrival').\n"
            "3. Include essential technical keywords or domain concepts directly relevant to finding lecture notes and slides.\n"
            "4. Keep the query concise, dense, and directly focused on the search target.\n"
            "5. Return ONLY the rewritten query text. Do NOT include markdown, quotation marks, preamble, or explanation."
        )

        user_content = f"{history_context}Current Question: {question}\n\nOptimized Search Query:"

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[user_content],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.1,
                )
            )
            rewritten = response.text.strip().strip('"').strip("'").strip()
            if rewritten and len(rewritten) > 2:
                return rewritten
        except Exception:
            # Fallback gracefully to original question on any API or model error
            pass

        return question
        
    def query(
        self, 
        question: str, 
        course_id: Optional[str] = None,
        enable_query_rewriting: bool = True,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Execute an Advanced RAG query:
        1. (Optional) Rewrite student query for enhanced academic terminology and conversational context
        2. Retrieve candidate chunks via Hybrid Search (BM25 + Dense)
        3. Re-rank chunks using a Cross-Encoder (FlashRank)
        4. Format prompt with top verified chunks
        5. Generate grounded answer
        """
        # 1. Query Rewriting (if enabled)
        search_query = question
        rewritten_query = None
        if enable_query_rewriting:
            rewritten = self.rewrite_query(question, history=history)
            if rewritten and rewritten.lower() != question.lower():
                rewritten_query = rewritten
                search_query = rewritten

        # 2. Retrieve Candidate Chunks (top_k=15 for higher recall)
        results = self.vector_store.search(search_query, course_id=course_id, top_k=15)
        
        if not results and course_id:
            # Auto-index course notes if they exist on disk but haven't been indexed yet
            course_dir = settings.COURSES_DATA_DIR / course_id.lower()
            if course_dir.exists():
                from scribo.rag.chunker import split_markdown_by_headers, split_slides_by_page
                indexed_any = False
                for md_file in course_dir.glob("lecture_*.md"):
                    lecture_id = md_file.stem.replace("lecture_", "")
                    text = md_file.read_text(encoding="utf-8")
                    chunks = split_markdown_by_headers(text, course_id, lecture_id)
                    if chunks:
                        self.vector_store.add_chunks(chunks)
                        indexed_any = True
                
                for slides_file in course_dir.glob("lecture_*_slides.txt"):
                    lecture_id = slides_file.stem.replace("lecture_", "").replace("_slides", "")
                    text = slides_file.read_text(encoding="utf-8")
                    chunks = split_slides_by_page(text, course_id, lecture_id)
                    if chunks:
                        self.vector_store.add_chunks(chunks)
                        indexed_any = True
                        
                if indexed_any:
                    results = self.vector_store.search(search_query, course_id=course_id, top_k=15)

        if not results:
            return {
                "answer": "I don't have any notes indexed for this course yet.",
                "citations": [],
                "rewritten_query": rewritten_query,
                "query_rewriting_enabled": enable_query_rewriting
            }
            
        # 3. Re-Ranking with FlashRank
        passages = []
        for res in results:
            passages.append({
                "id": res["id"],
                "text": res["text"],
                "meta": res["metadata"]
            })
            
        rerank_request = RerankRequest(query=search_query, passages=passages)
        rerank_results = self.ranker.rerank(rerank_request)
        
        # Filter down to top 3 highly relevant chunks
        top_results = []
        for item in rerank_results[:3]:
            top_results.append({
                "id": item["id"],
                "text": item["text"],
                "metadata": item.get("meta", {})
            })
            
        # 4. Format Context
        context_blocks = []
        for res in top_results:
            meta = res["metadata"]
            timestamp_str = f" @ {meta['timestamp']}" if meta.get("timestamp") else ""
            source_tag = f"[{meta['course_id'].upper()} - {meta['lecture_id']}{timestamp_str}]"
            context_blocks.append(f"Source: {source_tag}\nContent: {res['text']}")
            
        context_str = "\n\n---\n\n".join(context_blocks)
        
        # 5. Prompt Construction
        system_prompt = (
            "You are Scribo, an academic AI assistant. You answer student questions based ONLY "
            "on the provided lecture notes context. You must include inline citations pointing to the exact "
            "Source tag provided (e.g. 'As noted in [ENG448 - lec01 @ 04:15]...'). "
            "If the answer is not in the context, say you don't know based on the current notes."
        )
        
        user_prompt = f"Context:\n{context_str}\n\nQuestion:\n{question}"
        
        # 6. Generate Answer
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
            "citations": top_results,
            "rewritten_query": rewritten_query,
            "query_rewriting_enabled": enable_query_rewriting
        }

