"""005 — move pg_trgm extension to extensions schema

pg_trgm was installed in the public schema by migration 001. Supabase
exposes the public schema via PostgREST, which means pg_trgm functions
(similarity, show_trgm, etc.) are callable by the anon role. Moving the
extension to the extensions schema removes it from the public API surface.

The application does not use pg_trgm — it was added speculatively. The
postgres superuser's search_path includes extensions, so this move is
transparent if any future query does reference it.

Revision ID: 005
Revises: 004
Create Date: 2026-06-20
"""

from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Supabase-only: skip on vanilla Postgres (CI, local dev) where
    # the extensions schema does not exist.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'extensions')
               AND EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm')
            THEN
                ALTER EXTENSION pg_trgm SET SCHEMA extensions;
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm')
            THEN
                ALTER EXTENSION pg_trgm SET SCHEMA public;
            END IF;
        END
        $$;
    """)
