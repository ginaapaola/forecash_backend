"""roles managed for company

Revision ID: 093b2eed3338
Revises: 82ad3f05e53a
Create Date: 2026-02-26 23:27:36.306886
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = '093b2eed3338'
down_revision: Union[str, Sequence[str], None] = '82ad3f05e53a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    company_role_enum = sa.Enum(
        'LEGAL_REPRESENTATIVE',
        'USER',
        name='company_role'
    )
    company_role_enum.create(op.get_bind())

    op.add_column(
        'user_company',
        sa.Column(
            'role',
            company_role_enum,
            nullable=False
        )
    )

    op.alter_column(
        'user_company',
        'user_id',
        existing_type=sa.INTEGER(),
        nullable=False
    )

    op.alter_column(
        'user_company',
        'company_id',
        existing_type=sa.INTEGER(),
        nullable=False
    )

    op.alter_column(
        'users',
        'role',
        existing_type=postgresql.ENUM(
            'SUPER_ADMIN',
            'LEGAL_REPRESENTATIVE',
            'USER',
            name='user_role'
        ),
        nullable=True
    )


def downgrade() -> None:
    op.alter_column(
        'users',
        'role',
        existing_type=postgresql.ENUM(
            'SUPER_ADMIN',
            'LEGAL_REPRESENTATIVE',
            'USER',
            name='user_role'
        ),
        nullable=False
    )

    op.alter_column(
        'user_company',
        'company_id',
        existing_type=sa.INTEGER(),
        nullable=True
    )

    op.alter_column(
        'user_company',
        'user_id',
        existing_type=sa.INTEGER(),
        nullable=True
    )

    op.drop_column('user_company', 'role')

    company_role_enum = sa.Enum(
        'LEGAL_REPRESENTATIVE',
        'USER',
        name='company_role'
    )
    company_role_enum.drop(op.get_bind())