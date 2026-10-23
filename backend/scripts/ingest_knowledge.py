"""Ingest finance-education markdown into the knowledge_chunks table.

Header-aware chunking: split at markdown headings so each chunk is a coherent
section, then cap oversized sections with a recursive splitter. Embeds each
chunk with the knowledge embedder and stores it, then builds the keyword
(tsvector) column for hybrid/BM25 search.

Resumable: a source filename already present in the table is skipped, and each
document is written in a single commit — so a crash or rate-limit never leaves a
half-ingested document. Re-running only ingests NEW files.

Run from backend/, passing one or more folders (scanned non-recursively):

    uv run python scripts/ingest_knowledge.py \
        "C:/Users/I752228/Desktop/finance-docs-to-inject" \
        "C:/Users/I752228/Desktop/finance-docs-to-inject/pfg-financial-literacy"
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from sqlalchemy import func, select, text as sql_text

from src.db.models import KnowledgeChunk
from src.db.session import SessionLocal
from src.rag.knowledge_embedding import embed_knowledge_texts

HEADERS_TO_SPLIT_ON = [("#", "h1"), ("##", "h2"), ("###", "h3")]
MAX_RATE_LIMIT_RETRIES = 6


def _strip_frontmatter(text: str) -> str:
    """Remove a leading YAML frontmatter block (--- ... ---) — pure metadata,
    no value for retrieval."""
    return re.sub(r"^\s*---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)


def chunk_markdown(
    text: str, chunk_size: int = 1500, chunk_overlap: int = 200
) -> list[tuple[str, str | None]]:
    """Return [(chunk_text, section_title), ...] for one markdown document.

    Two-level strategy:
      1. Header split  -> one piece per section (semantic boundary).
      2. Size cap      -> break any still-too-long section into <=chunk_size.
    """
    text = _strip_frontmatter(text)

    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS_TO_SPLIT_ON,
        strip_headers=False,  # keep the heading text inside the chunk for context
    )
    sections = header_splitter.split_text(text)

    size_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    chunks: list[tuple[str, str | None]] = []
    for sec in sections:
        # Deepest available header becomes the section title.
        title = sec.metadata.get("h3") or sec.metadata.get("h2") or sec.metadata.get("h1")
        for piece in size_splitter.split_text(sec.page_content):
            piece = piece.strip()
            if piece:
                chunks.append((piece, title))
    return chunks


def _is_rate_limit(err: Exception) -> bool:
    return "429" in str(err) or "RESOURCE_EXHAUSTED" in str(err)


def embed_with_retry(texts: list[str]) -> list[list[float]]:
    """Embed one batch, backing off on 429. Raises if it can't recover."""
    delay = 60
    for attempt in range(1, MAX_RATE_LIMIT_RETRIES + 1):
        try:
            return embed_knowledge_texts(texts)
        except Exception as err:  # noqa: BLE001 - re-raise non-rate-limit errors
            if not _is_rate_limit(err):
                raise
            if attempt == MAX_RATE_LIMIT_RETRIES:
                raise RuntimeError(
                    "Still rate-limited — likely the daily cap. Re-run later "
                    "(already-ingested files are skipped)."
                ) from err
            print(f"  rate limited {attempt}/{MAX_RATE_LIMIT_RETRIES}; waiting {delay}s...", flush=True)
            time.sleep(delay)
            delay = min(delay * 2, 300)
    raise AssertionError("unreachable")


def collect_md(dirs: list[str]) -> list[Path]:
    """Top-level *.md in each dir (non-recursive)."""
    files: list[Path] = []
    for d in dirs:
        base = Path(d)
        if base.is_dir():
            files.extend(sorted(base.glob("*.md")))
        else:
            print(f"  ! not a directory: {d}", flush=True)
    return files


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest markdown into knowledge_chunks.")
    ap.add_argument("dirs", nargs="+", help="source folders (non-recursive)")
    ap.add_argument("--batch", type=int, default=50, help="chunks per embed call")
    ap.add_argument("--chunk-size", type=int, default=1500)
    ap.add_argument("--chunk-overlap", type=int, default=200)
    args = ap.parse_args()

    files = collect_md(args.dirs)
    if not files:
        print("No .md files found.")
        return 1

    with SessionLocal() as db:
        existing = set(db.scalars(select(KnowledgeChunk.source).distinct()))
    todo = [f for f in files if f.name not in existing]

    # Chunk everything up front (free, no embedding) and process SMALLEST-FIRST,
    # so a partial run under a quota cap commits as many whole documents as
    # possible before a large one (e.g. the glossary) can exhaust the budget.
    plan: list[tuple[Path, list[tuple[str, str | None]]]] = []
    for path in todo:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        chunks = chunk_markdown(raw, args.chunk_size, args.chunk_overlap)
        if chunks:
            plan.append((path, chunks))
    plan.sort(key=lambda pc: len(pc[1]))

    planned_chunks = sum(len(c) for _, c in plan)
    print(f"{len(files)} md files; {len(existing)} already ingested; "
          f"{len(plan)} to do ({planned_chunks} chunks).\n")

    for path, chunks in plan:
        # Embed all chunk texts (batched), then write the whole doc in one commit.
        contents = [c for c, _ in chunks]
        vectors: list[list[float]] = []
        for i in range(0, len(contents), args.batch):
            vectors.extend(embed_with_retry(contents[i : i + args.batch]))

        rows = [
            KnowledgeChunk(
                source=path.name, title=title, chunk_index=idx,
                content=content, embedding=vec,
            )
            for idx, ((content, title), vec) in enumerate(zip(chunks, vectors, strict=True))
        ]
        with SessionLocal() as db:
            db.add_all(rows)
            db.commit()
        print(f"  {path.name}: stored {len(rows)} chunks", flush=True)

    # Populate the keyword column for any rows missing it (the BM25/hybrid half).
    with SessionLocal() as db:
        db.execute(sql_text(
            "UPDATE knowledge_chunks SET content_tsv = to_tsvector('english', content) "
            "WHERE content_tsv IS NULL"
        ))
        db.commit()
        total = db.scalar(select(func.count()).select_from(KnowledgeChunk))
    print(f"\nDone. {total} chunks in knowledge_chunks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
