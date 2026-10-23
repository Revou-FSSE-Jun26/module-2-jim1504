"""add role check constraint to users

Locks the users.role column to the three roles the application recognises:
customer, content_manager, and admin. Until now the column was a free-form
varchar(20), so a typo or a stray write could leave a user holding a role that
no permission check would ever match.

Any existing row whose role is not one of the three is normalised to 'customer'
before the constraint is applied, so the upgrade cannot fail on legacy data.

Revision ID: c31f7a9e4b02
Revises: e6435f039eab
Create Date: 2026-09-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c31f7a9e4b02'
down_revision = 'e6435f039eab'
branch_labels = None
depends_on = None

VALID_ROLES = ("customer", "content_manager", "admin")


def upgrade():
    # Normalise anything unexpected first, so the constraint always applies cleanly.
    op.execute(
        sa.text(
            "update users set role = 'customer' "
            "where role is null or role not in ('customer', 'content_manager', 'admin')"
        )
    )

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'chk_users_role',
            "role in ('customer', 'content_manager', 'admin')",
        )


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('chk_users_role', type_='check')
