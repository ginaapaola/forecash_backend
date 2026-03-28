"""on delete cascade

Revision ID: bcbb03a85216
Revises: 6b5699261917
Create Date: 2026-03-26 10:14:17.395876

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bcbb03a85216'
down_revision: Union[str, Sequence[str], None] = '6b5699261917'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
