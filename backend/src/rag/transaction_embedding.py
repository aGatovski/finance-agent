from langchain_google_genai import GoogleGenerativeAIEmbeddings
from src.config import settings
from src.db.models import Transaction

_embedder = GoogleGenerativeAIEmbeddings(
    model=settings.embedding_model,
    google_api_key=settings.gemini_api_key,
    output_dimensionality=768,  # must match Vector(768) column in db/models.py
)


def format_transaction_for_embedding(tx: Transaction) -> str:
    """Converts a Transaction object into a clean semantic string for embedding."""
    parts = [
        tx.merchant or "",
        tx.description or "",
        tx.category or "",
        tx.type or "",
        
    ]
    return " | ".join(p for p in parts if p)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch embed a list of strings. Returns one vector per text."""
    return _embedder.embed_documents(texts)


def embed_query(text: str) -> list[float]:
    """Embed a single search query string."""
    return _embedder.embed_query(text)

