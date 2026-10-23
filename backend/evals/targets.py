import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_google_genai import ChatGoogleGenerativeAI

from src.config import settings
from src.db.session import SessionLocal
from src.rag.registry import get_retriever

_llm = ChatGoogleGenerativeAI(
    model=settings.gemini_model, google_api_key=settings.gemini_api_key
)

ANSWER_PROMPT = """Answer the question using ONLY the context below. If the context
does not contain the answer, say you don't have enough information.

Question: {question}

Context:
{context}

Answer:"""


def _flatten(content) -> str:
    """Gemini 3.x returns content as a list of blocks — join the text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
    return str(content)


def make_target(retriever_name: str):
    """Return a target(inputs) -> {answer, documents} bound to one retriever."""
    retriever = get_retriever(retriever_name)

    def target(inputs: dict) -> dict:
        question = inputs["question"]
        with SessionLocal() as db:
            chunks = retriever.retrieve(question, db, k=5)
        context = "\n\n".join(c.content for c in chunks)
        resp = _llm.invoke(ANSWER_PROMPT.format(question=question, context=context))
        return {"answer": _flatten(resp.content), "documents": [c.content for c in chunks]}

    return target
