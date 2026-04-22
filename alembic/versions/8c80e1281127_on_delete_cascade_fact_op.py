"""on delete cascade fact_op

Revision ID: 8c80e1281127
Revises: d334f30a23e9
Create Date: 2026-03-26 11:25:55.355889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c80e1281127'
down_revision: Union[str, Sequence[str], None] = 'd334f30a23e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.drop_constraint(
        "fact_operations_raw_dataset_id_fkey",
        "fact_operations",
        type_="foreignkey"
    )

    op.create_foreign_key(
        "fact_operations_raw_dataset_id_fkey",
        "fact_operations",
        "raw_datasets",
        ["raw_dataset_id"],
        ["id"],
        ondelete="CASCADE"
    )
