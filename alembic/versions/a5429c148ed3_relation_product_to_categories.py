"""relation product to categories

Revision ID: a5429c148ed3
Revises: 8c80e1281127
Create Date: 2026-04-03 10:14:53.490373

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5429c148ed3'
down_revision: Union[str, Sequence[str], None] = '8c80e1281127'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'dim_products',
        sa.Column('category_id', sa.Integer(), nullable=True)
    )

    op.create_foreign_key(
        'fk_dim_products_category',
        'dim_products',
        'dim_categories',
        ['category_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_dim_products_category', 'dim_products', type_='foreignkey')
    op.drop_column('dim_products', 'category_id')
