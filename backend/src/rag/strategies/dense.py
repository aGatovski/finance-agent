from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import KnowledgeChunk
from src.rag.knowledge_embedding import embed_knowledge_query
from src.rag.strategies.base import Retriever, RetrievedChunk


class DenseRetriever(Retriever):
    """Config A — pure semantic (vector) search.

    Embed the query with the SAME model used for the chunks, then return the k
    chunks with the smallest cosine distance. This is the baseline: everything
    else (hybrid, rerank) is measured against it.
    """

    name = "dense"

    def retrieve(self, query: str, db: Session, k: int = 5) -> list[RetrievedChunk]:
        vec = embed_knowledge_query(query)
        stmt = (
            select(
                KnowledgeChunk,
                KnowledgeChunk.embedding.cosine_distance(vec).label("distance"),
            )
            .where(KnowledgeChunk.embedding.is_not(None))
            .order_by("distance")
            .limit(k)
        )
        results: list[RetrievedChunk] = []
        for chunk, distance in db.execute(stmt):
            results.append(
                RetrievedChunk(
                    id=chunk.id,
                    source=chunk.source,
                    title=chunk.title,
                    content=chunk.content,
                    score=1.0 - distance,  # distance -> similarity (higher = better)
                )
            )
        return results
