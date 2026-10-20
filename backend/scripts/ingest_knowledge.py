from __future__ import annotations
import os 
import sys

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
HEADERS_TO_SPLIT_ON = [("#", "h1"), ("##", "h2"), ("###", "h3")]

def chunk_markdown(
    text: str, chunk_size: int = 1500, chunk_overlap: int = 200
) -> list[tuple[str, str | None]]:
    """Return [(chunk_text, section_title), ...] for one markdown document.

    Two-level strategy:
      1. Header split  -> one piece per section (semantic boundary).
      2. Size cap       -> break any still-too-long section into <=chunk_size.
    """
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS_TO_SPLIT_ON,
        strip_headers=False,  
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