"""update_dataset_status_enum

Revision ID: 6b5699261917
Revises: ef9dab731d82
Create Date: 2026-03-24 21:30:42.393922

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b5699261917'
down_revision: Union[str, Sequence[str], None] = 'ef9dab731d82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("ALTER TYPE dataset_status RENAME TO dataset_status_old")
    op.execute("CREATE TYPE dataset_status AS ENUM ('pending', 'processed', 'processed_with_errors', 'error')")
    op.execute("ALTER TABLE raw_datasets ALTER COLUMN status TYPE dataset_status USING status::text::dataset_status")
    op.execute("DROP TYPE dataset_status_old")

def downgrade():
    op.execute("ALTER TYPE dataset_status RENAME TO dataset_status_old")
    op.execute("CREATE TYPE dataset_status AS ENUM ('pending', 'staged', 'processed', 'error')")
    op.execute("ALTER TABLE raw_datasets ALTER COLUMN status TYPE dataset_status USING status::text::dataset_status")
    op.execute("DROP TYPE dataset_status_old")