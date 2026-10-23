from typing_extensions import Annotated, TypedDict
from src.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI

_judge = ChatGoogleGenerativeAI(
    model=settings.gemini_model, temperature=0, google_api_key=settings.gemini_api_key
)


class CorrectnessGrade(TypedDict):
    explanation: Annotated[str, ..., "Explain your reasoning for the score"]
    correct: Annotated[bool, ..., "True if the answer is correct, False otherwise."]

correctness_instructions = CORRECTNESS_INSTRUCTIONS = """You are grading a student answer against a reference answer.
Grade ONLY on factual accuracy relative to the reference. Ignore differences in wording,
style, or extra detail as long as the facts match. Return correct=True only if the student
answer is factually consistent with the reference."""

_correctness = _judge.with_structured_output(CorrectnessGrade)

    
def correctness(inputs: dict, outputs: dict, reference_outputs: dict) -> bool:
    msg = (
        f"QUESTION:\n{inputs['question']}\n\n"
        f"REFERENCE ANSWER:\n{reference_outputs['answer']}\n\n"
        f"STUDENT ANSWER:\n{outputs['answer']}"
    )
    grade = _correctness.invoke([
        {"role": "system", "content": correctness_instructions},
        {"role": "user", "content": msg},
    ])
    return grade["correct"]


# ---------- relevance: answer vs question ----------
class RelevanceGrade(TypedDict):
    explanation: Annotated[str, ..., "Explain your reasoning for the score"]
    relevant: Annotated[bool, ..., "True if the answer addresses the question, False otherwise."]


relevance_instructions = """You are grading whether an answer is relevant to the question.
An answer is relevant if it directly addresses what the question asks and stays on topic.
Ignore factual accuracy here — judge ONLY relevance. Return relevant=True if it addresses
the question, False if it is off-topic or evasive."""

_relevance = _judge.with_structured_output(RelevanceGrade)


def relevance(inputs: dict, outputs: dict) -> bool:
    msg = (
        f"QUESTION:\n{inputs['question']}\n\n"
        f"ANSWER:\n{outputs['answer']}"
    )
    grade = _relevance.invoke([
        {"role": "system", "content": relevance_instructions},
        {"role": "user", "content": msg},
    ])
    return grade["relevant"]


# ---------- groundedness: answer vs retrieved documents ----------
class GroundednessGrade(TypedDict):
    explanation: Annotated[str, ..., "Explain your reasoning for the score"]
    grounded: Annotated[bool, ..., "True if the answer is supported by the documents, False otherwise."]


groundedness_instructions = """You are grading whether an answer is grounded in the
retrieved documents. The answer is grounded if EVERY factual claim it makes is supported
by the documents. If it introduces facts not present in the documents (hallucination),
return grounded=False. Judge ONLY grounding, not whether the answer is correct overall."""

_groundedness = _judge.with_structured_output(GroundednessGrade)


def groundedness(inputs: dict, outputs: dict) -> bool:
    docs = "\n\n".join(outputs["documents"])
    msg = (
        f"RETRIEVED DOCUMENTS:\n{docs}\n\n"
        f"ANSWER:\n{outputs['answer']}"
    )
    grade = _groundedness.invoke([
        {"role": "system", "content": groundedness_instructions},
        {"role": "user", "content": msg},
    ])
    return grade["grounded"]


# ---------- retrieval_relevance: retrieved documents vs question ----------
class RetrievalRelevanceGrade(TypedDict):
    explanation: Annotated[str, ..., "Explain your reasoning for the score"]
    relevant: Annotated[bool, ..., "True if the retrieved documents are relevant to the question."]


retrieval_relevance_instructions = """You are grading whether the retrieved documents are
relevant to the question. They are relevant if at least some of them contain information
that helps answer the question. If the documents are entirely unrelated to the question,
return relevant=False. Judge ONLY the documents' relevance, not the final answer."""

_retrieval_relevance = _judge.with_structured_output(RetrievalRelevanceGrade)


def retrieval_relevance(inputs: dict, outputs: dict) -> bool:
    docs = "\n\n".join(outputs["documents"])
    msg = (
        f"QUESTION:\n{inputs['question']}\n\n"
        f"RETRIEVED DOCUMENTS:\n{docs}"
    )
    grade = _retrieval_relevance.invoke([
        {"role": "system", "content": retrieval_relevance_instructions},
        {"role": "user", "content": msg},
    ])
    return grade["relevant"]