"""add product details and the site content/settings tables

Products gain what the storefront's product page shows: the manufacturer's page
(official_url), a credited summary of it (overview, overview_source), the image
gallery and the specification table (JSONB lists), and where the specs came from.

site_content holds the editable homepage and About page (one JSON document per
page); site_settings holds the store's settings and logo in a single row (id = 1).

Revision ID: 8f3a0c2d5b71
Revises: 7d2e9b1c4a60
Create Date: 2026-10-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '8f3a0c2d5b71'
down_revision = '7d2e9b1c4a60'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('official_url', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('overview', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('overview_source', sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column('images', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False)
        )
        batch_op.add_column(
            sa.Column('specs', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False)
        )
        batch_op.add_column(sa.Column('specs_source', sa.Text(), nullable=True))

    op.create_table(
        'site_content',
        sa.Column('key', sa.String(length=20), nullable=False),
        sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('key'),
    )
    op.create_table(
        'site_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('logo', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('id = 1', name='chk_site_settings_single_row'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('site_settings')
    op.drop_table('site_content')
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('specs_source')
        batch_op.drop_column('specs')
        batch_op.drop_column('images')
        batch_op.drop_column('overview_source')
        batch_op.drop_column('overview')
        batch_op.drop_column('official_url')
