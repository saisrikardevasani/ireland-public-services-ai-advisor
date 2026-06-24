"""004 — enable Row Level Security on all public tables

Blocks all PostgREST (anon/authenticated role) access to every table.
The FastAPI backend connects via a direct postgres superuser connection
(DATABASE_URL / DATABASE_SYNC_URL) which bypasses RLS entirely, so no
application behaviour changes.

Without RLS, any client with the Supabase project URL and anon key can
read, write, and delete all rows via the auto-generated PostgREST API.

Revision ID: 004
Revises: 003
Create Date: 2026-06-20
"""

from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("alembic_version", "documents", "chunks", "feedback"):
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;")
        # Force RLS even for table owners (belt-and-suspenders for Supabase)
        op.execute(f"ALTER TABLE public.{table} FORCE ROW LEVEL SECURITY;")


def downgrade() -> None:
    for table in ("alembic_version", "documents", "chunks", "feedback"):
        op.execute(f"ALTER TABLE public.{table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY;")
