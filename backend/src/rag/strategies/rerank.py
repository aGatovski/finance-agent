import json

from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy.orm import Session

from src.config import settings
from src.rag.strategies.base import Retriever, RetrievedChunk


class RerankRetriever(Retriever):
    """Fetch with a base retriever, then LLM-rerank to top-k."""

    name = "hybrid_rerank"

    def __init__(self, base: Retriever, candidates: int = 15):
        self.base = base             
        self.candidates = candidates 
        self._llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model, temperature=0,
            google_api_key=settings.gemini_api_key,
        )

    def retrieve(self, query: str, db: Session, k: int = 5) -> list[RetrievedChunk]:
        pool= self.base.retrieve(query, db, k=self.candidates)
        if len(pool) <= k:
            return pool

        order = self._rerank(query=query,pool=pool)
        return [pool[i] for i in order[:k]]


    def _rerank(self, query: str, pool: list[RetrievedChunk]) -> list[int]:
        """Ask the LLM to order the candidates by relevance. Returns a list of
        indices into `pool`, best first. Falls back to original order on any
        parse failure (never crashes retrieval)."""
        listing = "\n".join(f"[{i}] {c.content[:300]}" for i, c in enumerate(pool))
        prompt = (
            "Rank the passages by how well they answer the question.\n"
            f"Question: {query}\n\nPassages:\n{listing}\n\n"
            "Return ONLY a JSON array of passage numbers, best first. Example: [3, 0, 5]"
        )
        resp = self._llm.invoke(prompt)

        content = resp.content
        if isinstance(content, list):
            text = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )
        else:
            text = str(content)

        
        try:
            order = json.loads(text[text.index("[") : text.rindex("]") + 1])
            order = [i for i in order if isinstance(i, int) and 0 <= i < len(pool)]
        except Exception:
            order = []
        # append any indices the LLM dropped, so we never lose candidates
        order += [i for i in range(len(pool)) if i not in order]
        return order
