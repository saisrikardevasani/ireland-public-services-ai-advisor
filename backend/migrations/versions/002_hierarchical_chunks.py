"""Add parent_content column + HNSW vector index for v0.3.

Revision ID: 002
Revises: 001
Create Date: 2026-06-14

Changes:
  - parent_content TEXT: stores the wider 512-word window around each 128-word
    child chunk. Retrieved child, LLM sees parent. Better context, same precision.
  - HNSW index on embedding: approximate nearest-neighbour search. Required once
    the corpus grows beyond ~50K chunks where exact scan becomes too slow.
    Parameters: m=16, ef_construction=64 are sensible defaults for recall/speed.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Parent context window — NULL for any chunks ingested before this migration
    op.execute("ALTER TABLE chunks ADD COLUMN parent_content TEXT")

    # HNSW approximate nearest-neighbour index for cosine similarity
    # m=16: neighbours per node (higher = better recall, more memory)
    # ef_construction=64: search width during build (higher = better quality index)
    op.execute("""
        CREATE INDEX idx_chunks_embedding_hnsw
        ON chunks USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_chunks_embedding_hnsw")
    op.execute("ALTER TABLE chunks DROP COLUMN IF EXISTS parent_content")
