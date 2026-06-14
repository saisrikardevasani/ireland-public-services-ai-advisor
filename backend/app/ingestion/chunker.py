"""Hierarchical chunker (v0.3).

Two-level chunking strategy:
  - Child chunk (128 words): embedded and retrieved. Small = precise match.
  - Parent chunk (512 words): the surrounding window sent to the LLM as context.
    Larger = richer context for generation.

Why hierarchical?
  Cosine similarity works best on short, focused passages. But LLMs need
  more surrounding context to give a complete answer. Hierarchical chunking
  gives you both: retrieve with precision, generate with context.

  Example: the phrase "€13.50 per hour" retrieves exactly the right chunk.
  But the LLM also needs the surrounding paragraph explaining who it applies
  to and when it was updated. The parent window provides that.
"""


def chunk_document(
    content: str,
    child_size: int = 128,
    parent_size: int = 512,
    child_overlap: int = 20,
) -> list[dict]:
    """Split content into hierarchical child/parent chunks.

    Returns a list of dicts:
      {chunk_index, content, parent_content, token_count}

    `content`        — child chunk (128 words) — used for embedding + BM25
    `parent_content` — parent window (512 words) — sent to LLM as context
    `token_count`    — word count of the child chunk
    """
    words = content.split()

    if not words:
        return []

    chunks = []
    step = child_size - child_overlap

    for i in range(0, len(words), step):
        child_words = words[i : i + child_size]

        if len(child_words) < 20:
            break

        # Centre the parent window on the child chunk
        half_extra = (parent_size - child_size) // 2
        parent_start = max(0, i - half_extra)
        parent_end = min(len(words), parent_start + parent_size)
        # Shift left if we hit the end of the document
        if parent_end - parent_start < parent_size:
            parent_start = max(0, parent_end - parent_size)
        parent_words = words[parent_start:parent_end]

        chunks.append(
            {
                "chunk_index": len(chunks),
                "content": " ".join(child_words),
                "parent_content": " ".join(parent_words),
                "token_count": len(child_words),
            }
        )

    return chunks
