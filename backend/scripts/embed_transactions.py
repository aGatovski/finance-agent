"""Backfill embeddings for all transactions that don't have one yet.

Standalone + resumable: it only touches rows where `embedding IS NULL`, commits
after every batch, and respects Google's free-tier rate limit (100 embed
requests/minute). Safe to Ctrl+C and re-run — it picks up where it left off.

Run from the backend/ directory:

    uv run python scripts/embed_transactions.py

Options:
    --batch 50     rows per batch / DB commit   (default 50)
    --rpm 90       target requests per minute   (default 90, stays under 100)
"""

from __future__ import annotations

import argparse
import os
import sys
import time

# Ensure the backend/ root (parent of scripts/) is importable as `src`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func, select

from src.db.models import Transaction
from src.db.session import SessionLocal
from src.rag.transaction_embedding import embed_texts, format_transaction_for_embedding

# Max times to wait out a 429 on the same batch before giving up for now.
MAX_RATE_LIMIT_RETRIES = 6


def is_rate_limit(err: Exception) -> bool:
    text = str(err)
    return "429" in text or "RESOURCE_EXHAUSTED" in text


def embed_batch_with_retry(texts: list[str]) -> list[list[float]]:
    """Embed one batch, retrying on 429 with backoff. Raises if it can't recover."""
    delay = 60  # seconds; grows on repeated rate limits
    for attempt in range(1, MAX_RATE_LIMIT_RETRIES + 1):
        try:
            return embed_texts(texts)
        except Exception as err:  # noqa: BLE001 - we re-raise non-rate-limit errors
            if not is_rate_limit(err):
                raise
            if attempt == MAX_RATE_LIMIT_RETRIES:
                raise RuntimeError(
                    "Still rate-limited after several retries — you may have hit "
                    "the daily free-tier cap. Re-run the script later (it resumes)."
                ) from err
            print(
                f"  rate limited (attempt {attempt}/{MAX_RATE_LIMIT_RETRIES}); "
                f"waiting {delay}s...",
                flush=True,
            )
            time.sleep(delay)
            delay = min(delay * 2, 300)  # cap backoff at 5 min
    raise AssertionError("unreachable")


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill transaction embeddings.")
    parser.add_argument("--batch", type=int, default=50, help="rows per batch (default 50)")
    parser.add_argument("--rpm", type=int, default=90, help="target requests/minute (default 90)")
    args = parser.parse_args()

    min_seconds_per_batch = args.batch / args.rpm * 60  # pace to stay under the cap

    with SessionLocal() as db:
        remaining = db.scalar(
            select(func.count()).select_from(Transaction).where(Transaction.embedding.is_(None))
        )
        total = db.scalar(select(func.count()).select_from(Transaction))

    if not remaining:
        print(f"Nothing to do — all {total} transactions are already embedded. ✅")
        return 0

    print(f"{remaining} of {total} transactions need embedding.")
    print(f"Batch size {args.batch}, target {args.rpm} req/min — this will take a few minutes.\n")

    done = 0
    while True:
        with SessionLocal() as db:
            batch = list(
                db.scalars(
                    select(Transaction)
                    .where(Transaction.embedding.is_(None))
                    .order_by(Transaction.id)
                    .limit(args.batch)
                )
            )
            if not batch:
                break

            started = time.monotonic()
            texts = [format_transaction_for_embedding(tx) for tx in batch]
            vectors = embed_batch_with_retry(texts)

            for tx, vec in zip(batch, vectors, strict=True):
                tx.embedding = vec
            db.commit()

            done += len(batch)
            print(f"  embedded {done}/{remaining}  (+{len(batch)})", flush=True)

            # Pace the next batch so we don't trip the per-minute limit.
            elapsed = time.monotonic() - started
            sleep_for = min_seconds_per_batch - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)

    with SessionLocal() as db:
        still_missing = db.scalar(
            select(func.count()).select_from(Transaction).where(Transaction.embedding.is_(None))
        )
    print(f"\nDone. {still_missing} transactions still missing an embedding.")
    return 0 if still_missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
