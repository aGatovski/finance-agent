from langchain_google_genai import GoogleGenerativeAIEmbeddings
from src.config import settings


_kb_embedder  = GoogleGenerativeAIEmbeddings(
    model=settings.embedding_model,
    google_api_key=settings.gemini_api_key,
    output_dimensionality=768,  
)

def embed_knowledge_texts(texts: list[str]) -> list[list[float]]:
    """Batch-embed chunk texts"""
    return _kb_embedder.embed_documents(texts)

def embed_knowledge_query(query: str) ->list[float]:
    """Embed search query"""
    return _kb_embedder.embed_query(query)

