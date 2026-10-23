"""enable row level security on every public table (Supabase)

Fixes the Supabase Security Advisor error "Table public.<name> is public, but RLS
has not been enabled" (lint rls_disabled_in_public).

Why it matters: Supabase serves every table in the public schema through its
auto-generated Data API (PostgREST). Anyone holding the project's publishable
(anon) key -- which is meant to be public -- could read and write these tables
directly, bypassing this Flask API and all of its rules.

What this does:
  * ENABLE ROW LEVEL SECURITY on each table, with NO policies -- the Data API's
    roles (anon, authenticated) get no rows at all.
  * REVOKE their table and sequence grants too: Supabase grants them full access to
    new public tables by default, and policies alone don't take grants back. The
    default privileges are revoked as well, so future tables start closed.

Why the API keeps working: Flask connects as the `postgres` role, which owns these
tables, and a table's owner is not subject to its RLS policies unless FORCE ROW
LEVEL SECURITY is set (it isn't). So nothing changes for this API.

On plain PostgreSQL (local development, tests) the anon/authenticated roles don't
exist; the grant changes are skipped there and only RLS is enabled.

Revision ID: 9a4b1d3e6c82
Revises: 8f3a0c2d5b71
Create Date: 2026-10-22

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '9a4b1d3e6c82'
down_revision = '8f3a0c2d5b71'
branch_labels = None
depends_on = None

TABLES = (
    "users",
    "categories",
    "products",
    "orders",
    "order_items",
    "site_content",
    "site_settings",
    "alembic_version",
)
DATA_API_ROLES = "anon, authenticated"

# Only touch grants when the Supabase roles exist.
_IF_SUPABASE = "DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN {sql} END IF; END $$;"


def upgrade():
    for table in TABLES:
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")

    revokes = " ".join(
        [f"REVOKE ALL ON TABLE public.{table} FROM {DATA_API_ROLES};" for table in TABLES]
        + [
            f"REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM {DATA_API_ROLES};",
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM {DATA_API_ROLES};",
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM {DATA_API_ROLES};",
        ]
    )
    op.execute(_IF_SUPABASE.format(sql=revokes))


def downgrade():
    grants = " ".join(
        [f"GRANT ALL ON TABLE public.{table} TO {DATA_API_ROLES};" for table in TABLES]
        + [
            f"GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO {DATA_API_ROLES};",
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {DATA_API_ROLES};",
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {DATA_API_ROLES};",
        ]
    )
    op.execute(_IF_SUPABASE.format(sql=grants))

    for table in TABLES:
        op.execute(f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY")
