from google import genai
from typing import List
from scribo.config import settings

class Embedder:
    """Wrapper for Google GenAI Text Embeddings."""
    
    def __init__(self, api_key: str = None):
        key = api_key or settings.GEMINI_API_KEY
        if not key:
            raise ValueError("GEMINI_API_KEY is required for embeddings.")
        self.client = genai.Client(api_key=key)
        self.model = "gemini-embedding-2"
        
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of strings."""
        if not texts:
            return []
            
        embeddings = []
        for text in texts:
            result = self.client.models.embed_content(
                model=self.model,
                contents=[text],
                config=genai.types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT"
                )
            )
            if isinstance(result.embeddings, list):
                embeddings.append(result.embeddings[0].values)
            else:
                embeddings.append(result.embeddings.values)
                
        return embeddings
            
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a search query."""
        result = self.client.models.embed_content(
            model=self.model,
            contents=[query],
            config=genai.types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY"
            )
        )
        if isinstance(result.embeddings, list):
            return result.embeddings[0].values
        return result.embeddings.values
