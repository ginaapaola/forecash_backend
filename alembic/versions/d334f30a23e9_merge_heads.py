"""merge heads

Revision ID: d334f30a23e9
Revises: bcbb03a85216, ee2a46f9efa5
Create Date: 2026-03-26 10:54:16.391515

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd334f30a23e9'
down_revision: Union[str, Sequence[str], None] = ('bcbb03a85216', 'ee2a46f9efa5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
