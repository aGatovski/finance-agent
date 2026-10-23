from src.rag.strategies.base import Retriever
from src.rag.strategies.dense import DenseRetriever
from src.rag.strategies.hybrid import HybridRetriever
from src.rag.strategies.rerank import RerankRetriever

# Every config the benchmark compares, by name.
RETRIEVER_NAMES = ["dense", "hybrid", "hybrid_rerank"]

def get_retriever(name: str) -> Retriever:
    """Construct a retriever by name — the single place configs are wired."""
    if name == "dense":
        return DenseRetriever()
    if name == "hybrid":
        return HybridRetriever()
    if name == "hybrid_rerank":
        return RerankRetriever(base=HybridRetriever())
    raise ValueError(f"unknown retriever: {name!r}")