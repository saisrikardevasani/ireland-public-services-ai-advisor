"""Cross-encoder reranker (v0.3).

Why rerank?
  BM25 and dense retrieval each score a passage independently of the query.
  A cross-encoder reads the query and passage TOGETHER, producing a much more
  accurate relevance score — at the cost of being too slow to run over the
  whole corpus (it can't be pre-indexed like embeddings).

  The two-stage pattern:
    1. Retrieve: BM25 + dense → top 20 candidates (fast, approximate)
    2. Rerank:   cross-encoder scores all 20 pairs → top 5 (slow, precise)

  BAAI/bge-reranker-base is ~280MB. First call downloads and caches it.
  Subsequent calls are fast (~10ms for 20 passages on CPU).
"""

import logging

from app.config import settings
from app.pipeline.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)

_reranker = None


def _get_reranker():
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        logger.info("Loading reranker model: %s", settings.reranker_model)
        _reranker = CrossEncoder(settings.reranker_model)
    return _reranker


def rerank(query: str, chunks: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
    """Score query-passage pairs with a cross-encoder and return the top_k.

    Uses the child chunk content for scoring (same text that was embedded),
    ensuring the reranker and retriever see the same representation.
    """
    if not chunks:
        return chunks

    model = _get_reranker()
    pairs = [(query, chunk.content) for chunk in chunks]
    scores: list[float] = model.predict(pairs).tolist()

    ranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)

    logger.debug(
        "Reranker scores: %s",
        [(c.title[:30], f"{s:.3f}") for c, s in ranked[:top_k]],
    )

    return [chunk for chunk, _ in ranked[:top_k]]
