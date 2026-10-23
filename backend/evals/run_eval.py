"""Run the LangSmith evaluation for one or more retriever configs.

Each config becomes its own LangSmith experiment against the golden dataset,
graded by the four LLM-judge evaluators. LangSmith's dashboard then compares the
experiments (dense vs hybrid vs hybrid_rerank) side by side.

Run ONE config at a time to stay under free-tier quota:
    uv run python evals/run_eval.py dense
    uv run python evals/run_eval.py hybrid
    uv run python evals/run_eval.py hybrid_rerank
Omit the argument to run all three in sequence.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langsmith import Client

from evals.evaluators import correctness, groundedness, relevance, retrieval_relevance
from evals.targets import make_target
from src.config import settings
from src.rag.registry import RETRIEVER_NAMES

DATASET = "Financial Literacy Q&A"
EVALUATORS = [correctness, relevance, groundedness, retrieval_relevance]


def main() -> int:
    client = Client(api_key=settings.langsmith_api_key)
    configs = sys.argv[1:] or RETRIEVER_NAMES

    for name in configs:
        print(f"\n=== evaluating config: {name} ===", flush=True)
        client.evaluate(
            make_target(name),
            data=DATASET,
            evaluators=EVALUATORS,
            experiment_prefix=f"rag-{name}",
            max_concurrency=1,  # serialize calls to respect free-tier rate limits
        )
        print(f"  done: {name}", flush=True)

    print("\nAll requested configs evaluated — open LangSmith to compare experiments.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
