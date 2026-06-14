"""Hybrid retrieval: BM25 (tsvector) + dense (pgvector) fused with RRF,
then reranked with a cross-encoder (v0.3).

Pipeline:
  1. BM25 search  → top 20 by ts_rank
  2. Dense search → top 20 by cosine similarity
  3. RRF fusion   → top 20 combined (expanded pool for reranker)
  4. Rerank       → cross-encoder scores all 20, returns top N

Why RRF before reranking?
  RRF gives the reranker a diverse, high-recall candidate set.
  The reranker then applies precision — it reads query+passage together,
  something embedding models can't do.
"""

import logging
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.ingestion.embedder import embed_query

logger = logging.getLogger(__name__)

RRF_K = 60


@dataclass
class RetrievedChunk:
    id: str
    document_id: str
    content: str
    parent_content: str | None
    url: str
    title: str
    rrf_score: float


async def bm25_search(session: AsyncSession, query: str, k: int) -> list[dict]:
    """Full-text search using Postgres tsvector + ts_rank_cd."""
    result = await session.execute(
        text("""
            SELECT
                CAST(c.id AS TEXT)          AS id,
                CAST(c.document_id AS TEXT) AS document_id,
                c.content,
                c.parent_content,
                d.url,
                d.title,
                ts_rank_cd(c.content_tsv, plainto_tsquery('english', :query)) AS score
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.content_tsv @@ plainto_tsquery('english', :query)
            ORDER BY score DESC
            LIMIT :k
        """),
        {"query": query, "k": k},
    )
    return [dict(row._mapping) for row in result]


async def dense_search(
    session: AsyncSession, query_embedding: list[float], k: int
) -> list[dict]:
    """Cosine similarity search via pgvector (HNSW index from migration 002)."""
    vec_literal = "[" + ",".join(f"{x:.8f}" for x in query_embedding) + "]"

    result = await session.execute(
        text(f"""
            SELECT
                CAST(c.id AS TEXT)          AS id,
                CAST(c.document_id AS TEXT) AS document_id,
                c.content,
                c.parent_content,
                d.url,
                d.title,
                1 - (c.embedding <=> '{vec_literal}'::vector) AS score
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.embedding IS NOT NULL
            ORDER BY c.embedding <=> '{vec_literal}'::vector
            LIMIT :k
        """),
        {"k": k},
    )
    return [dict(row._mapping) for row in result]


def rrf_fusion(
    bm25_results: list[dict],
    dense_results: list[dict],
    final_k: int,
) -> list[RetrievedChunk]:
    """Merge two ranked lists with Reciprocal Rank Fusion."""
    scores: dict[str, float] = {}
    metadata: dict[str, dict] = {}

    for rank, row in enumerate(bm25_results, start=1):
        doc_id = row["id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (RRF_K + rank)
        metadata[doc_id] = row

    for rank, row in enumerate(dense_results, start=1):
        doc_id = row["id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (RRF_K + rank)
        metadata.setdefault(doc_id, row)

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:final_k]

    return [
        RetrievedChunk(
            id=doc_id,
            document_id=metadata[doc_id]["document_id"],
            content=metadata[doc_id]["content"],
            parent_content=metadata[doc_id].get("parent_content"),
            url=metadata[doc_id]["url"],
            title=metadata[doc_id]["title"],
            rrf_score=score,
        )
        for doc_id, score in ranked
    ]


async def retrieve(session: AsyncSession, query: str) -> list[RetrievedChunk]:
    """Run hybrid retrieval + reranking for a user query."""
    query_embedding = embed_query(query)

    bm25_results = await bm25_search(session, query, settings.bm25_top_k)
    dense_results = await dense_search(session, query_embedding, settings.dense_top_k)

    logger.debug(
        "BM25 returned %d, dense returned %d candidates",
        len(bm25_results),
        len(dense_results),
    )

    # Pass a larger pool to the reranker (top 20 instead of top 5)
    # so it has more candidates to choose from
    rerank_pool = settings.bm25_top_k if settings.reranker_enabled else settings.final_top_k
    candidates = rrf_fusion(bm25_results, dense_results, rerank_pool)

    if settings.reranker_enabled:
        from app.pipeline.reranker import rerank
        chunks = rerank(query, candidates, settings.final_top_k)
        logger.info(
            "Returning %d chunks after reranking for query: %s...",
            len(chunks), query[:60],
        )
    else:
        chunks = candidates[: settings.final_top_k]
        logger.info(
            "Returning %d chunks after RRF (reranker disabled) for query: %s...",
            len(chunks), query[:60],
        )

    return chunks
