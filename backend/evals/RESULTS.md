# RAG Retrieval Evaluation — Results Summary

LangSmith evaluation of three retrieval strategies against the golden dataset
(`golden.jsonl`, **16 examples**). Graders are LLM-as-judge booleans (`evaluators.py`):
correctness, groundedness, relevance, and retrieval_relevance.

## Results

| Strategy        | Correctness | Groundedness | Relevance | Retrieval Rel. | Avg Latency | Avg Tokens | Total Cost |
|-----------------|:-----------:|:------------:|:---------:|:--------------:|:-----------:|:----------:|:----------:|
| dense           | 93.8%       | 93.8%        | 93.8%     | 100%           | 14.0s       | 1,254      | $0.0084    |
| hybrid          | 93.8%       | 93.8%        | 93.8%     | 100%           | 18.3s       | 1,247      | $0.0083    |
| **hybrid_rerank** | **93.8%** | **100%**     | **100%**  | **100%**       | 56.0s       | 2,390      | $0.0149    |

## Which performed best

**`hybrid_rerank` had the best answer quality.** It scored a perfect 100% on
groundedness and relevance (vs. 93.8% for the other two) and tied the top
correctness score. The reranking step filters retrieved context down to the
most pertinent passages, which eliminated the one ungrounded/off-topic answer
the other strategies produced.

The trade-off is cost: it was **~3–4× slower** (56s vs. 14–18s) and used
**~2× the tokens** (~$0.0149 vs. ~$0.0083 total), since reranking runs an extra
model pass over a larger candidate set.

### Notes
- **dense** and **hybrid** were effectively tied on every quality metric; adding
  sparse/keyword retrieval (hybrid) gave no quality gain here and was slightly
  slower, so it isn't worth the added complexity on this dataset.
- All three achieved 100% retrieval_relevance — the retrievers consistently
  surfaced relevant documents; the quality differences came from how well the
  final answer used them.

## Recommendation
- **Prioritize answer quality** → use **`hybrid_rerank`**.
- **Prioritize latency/cost** → use **`dense`**; it matches `hybrid_rerank` on
  correctness at a quarter of the latency and ~55% of the cost.
