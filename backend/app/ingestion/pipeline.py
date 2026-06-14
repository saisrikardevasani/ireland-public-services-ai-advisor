"""Ingestion orchestrator.

Connects crawler → chunker → embedder → database writer.
Idempotent: skips documents whose content_hash hasn't changed.
"""

import hashlib
import logging
import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.chunker import chunk_document
from app.ingestion.embedder import embed_texts
from app.models.schema import Chunk, Document

logger = logging.getLogger(__name__)


async def _document_needs_update(session: AsyncSession, url: str, content_hash: str) -> bool:
    """Return True if the document is new or its content has changed."""
    result = await session.execute(
        select(Document.content_hash).where(Document.url == url)
    )
    existing_hash = result.scalar_one_or_none()
    return existing_hash is None or existing_hash != content_hash


async def ingest_pages(session: AsyncSession, pages: list[dict]) -> dict:
    """Ingest a list of crawled pages into the database.

    Args:
        session: Async SQLAlchemy session
        pages: List of {url, title, content, content_hash} dicts from the crawler

    Returns:
        Stats dict with counts of new, updated, and skipped documents
    """
    stats = {"new": 0, "updated": 0, "skipped": 0, "chunks_created": 0}

    for page in pages:
        url = page["url"]
        # Compute hash if not already provided (e.g. when loading from fixtures)
        content_hash = page.get("content_hash") or hashlib.sha256(page["content"].encode()).hexdigest()
        needs_update = await _document_needs_update(session, url, content_hash)

        if not needs_update:
            logger.debug("Skipping unchanged: %s", url)
            stats["skipped"] += 1
            continue

        # Delete old document (cascades to chunks) if it exists
        await session.execute(
            text("DELETE FROM documents WHERE url = :url"), {"url": url}
        )

        # Create new document record
        doc = Document(
            id=uuid.uuid4(),
            source="citizensinformation",
            url=url,
            title=page["title"],
            content_hash=content_hash,
        )
        session.add(doc)
        await session.flush()  # assigns doc.id without committing

        # Chunk the content
        raw_chunks = chunk_document(page["content"])

        if not raw_chunks:
            logger.warning("No chunks produced for %s", url)
            continue

        # Embed all chunks in one batch (efficient — one model forward pass per batch)
        chunk_texts = [c["content"] for c in raw_chunks]
        embeddings = embed_texts(chunk_texts)

        # Write chunks to DB
        for raw_chunk, embedding in zip(raw_chunks, embeddings):
            chunk = Chunk(
                id=uuid.uuid4(),
                document_id=doc.id,
                chunk_index=raw_chunk["chunk_index"],
                content=raw_chunk["content"],
                parent_content=raw_chunk.get("parent_content"),
                embedding=embedding,
                token_count=raw_chunk["token_count"],
            )
            session.add(chunk)

        await session.commit()

        stats["chunks_created"] += len(raw_chunks)
        stats["new"] += 1

        logger.info(
            "Ingested: %s → %d chunks", url, len(raw_chunks)
        )

    return stats
