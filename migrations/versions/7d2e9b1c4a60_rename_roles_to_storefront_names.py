"""rename roles to the storefront's names

The RevoTech storefront and this API now share one role model:

    old             new
    admin        -> superadmin   (everything, including users and settings)
    content_manager -> admin      (catalogue, orders, page content)
    customer        customer

The rename runs in that order (admin first) so the two updates never collide.

Revision ID: 7d2e9b1c4a60
Revises: c31f7a9e4b02
Create Date: 2026-10-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d2e9b1c4a60'
down_revision = 'c31f7a9e4b02'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('chk_users_role', 'users', type_='check')
    op.execute(sa.text("update users set role = 'superadmin' where role = 'admin'"))
    op.execute(sa.text("update users set role = 'admin' where role = 'content_manager'"))
    op.create_check_constraint('chk_users_role', 'users', "role in ('customer', 'admin', 'superadmin')")


def downgrade():
    op.drop_constraint('chk_users_role', 'users', type_='check')
    op.execute(sa.text("update users set role = 'content_manager' where role = 'admin'"))
    op.execute(sa.text("update users set role = 'admin' where role = 'superadmin'"))
    op.create_check_constraint('chk_users_role', 'users', "role in ('customer', 'content_manager', 'admin')")
