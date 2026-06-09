"""on delete cascade raw_records

Revision ID: ee2a46f9efa5
Revises: 6b5699261917
Create Date: 2026-03-26 10:30:36.561450

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee2a46f9efa5'
down_revision: Union[str, Sequence[str], None] = '6b5699261917'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.drop_constraint(
        "raw_records_raw_dataset_id_fkey",
        "raw_records",
        type_="foreignkey"
    )

    op.create_foreign_key(
        "raw_records_raw_dataset_id_fkey",
        "raw_records",
        "raw_datasets",
        ["raw_dataset_id"],
        ["id"],
        ondelete="CASCADE"
    )


def downgrade():
    op.drop_constraint(
        "raw_records_raw_dataset_id_fkey",
        "raw_records",
        type_="foreignkey"
    )

    op.create_foreign_key(
        "raw_records_raw_dataset_id_fkey",
        "raw_records",
        "raw_datasets",
        ["raw_dataset_id"],
        ["id"]
    )