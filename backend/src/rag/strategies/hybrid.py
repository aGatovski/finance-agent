from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.models import KnowledgeChunk
from src.rag.knowledge_embedding import embed_knowledge_query
from src.rag.strategies.base import Retriever, RetrievedChunk

class HybridRetriever(Retriever):

    name = "hybrid"

    def __init__(self, candidate: int = 20):
        self.candidate = candidate

    def _dense_ids(self, query: str, db: Session) ->list[int]:
        vec = embed_knowledge_query(query)
        
        stmt = (
                select(KnowledgeChunk.id)
                .order_by(KnowledgeChunk.embedding.cosine_distance(vec))
                .where(KnowledgeChunk.embedding.is_not(None))
                .limit(self.candidate)
            )
        
        result = db.scalars(stmt).all()
        return list(result)

    def _lexical_ids(self, query: str, db: Session) -> list[int]:
        tsq = func.websearch_to_tsquery("english", query)
        stmt = (
            select(KnowledgeChunk.id)
            .where(KnowledgeChunk.content_tsv.op("@@")(tsq))
            .order_by(func.ts_rank(KnowledgeChunk.content_tsv, tsq).desc())
            .limit(self.candidate)
        )
        return list(db.scalars(stmt).all())

    def retrieve(self, query: str, db: Session, k: int = 5) -> list[RetrievedChunk]:
        RRF_K = 60

        dense = self._dense_ids(query, db)
        lexical = self._lexical_ids(query, db)

        scores: dict[int, float] = {}
        for ranked in (dense, lexical):
            for rank, cid in enumerate(ranked):
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (RRF_K + rank)

        # take top k fused ids based of score
        top_ids = sorted(scores, key=scores.get, reverse=True)[:k]

        rows = db.scalars(
            select(KnowledgeChunk).where(KnowledgeChunk.id.in_(top_ids))
        ).all()

        by_id = {r.id: r for r in rows}
        
        return [
            RetrievedChunk(
                id=cid,
                source=by_id[cid].source,
                title=by_id[cid].title,
                content=by_id[cid].content,
                score=scores[cid],
            )
            for cid in top_ids
        ]