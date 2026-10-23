from abc import ABC, abstractmethod
from dataclasses import dataclass

from sqlalchemy.orm import Session


@dataclass
class RetrievedChunk:
    """One retrieved result. `score` meaning is strategy-specific (cosine
    similarity, RRF score, rerank score) — we keep it so the eval harness and
    debugging can inspect *why* something ranked where it did."""
    id: int
    source: str
    title: str | None
    content: str
    score: float


class Retriever(ABC):
    """The single contract every strategy implements.

    An abstract base class: each strategy subclasses Retriever and implements
    retrieve(). Python refuses to instantiate a subclass that doesn't."""

    name: str

    @abstractmethod
    def retrieve(self, query: str, db: Session, k: int = 5) -> list[RetrievedChunk]:
        """Return the top-k chunks for `query`, best first."""
        ...
