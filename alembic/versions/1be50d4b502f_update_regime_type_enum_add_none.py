"""update_regime_type_enum_add_none

Revision ID: 1be50d4b502f
Revises: e1e7f691c143
Create Date: 2026-03-20 17:37:22.217736

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1be50d4b502f'
down_revision: Union[str, Sequence[str], None] = 'e1e7f691c143'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL no permite ALTER TYPE dentro de una transacción
    # por eso usamos COMMIT previo con execute
    op.execute("ALTER TYPE regime_type ADD VALUE 'NONE'")

def downgrade() -> None:
    # PostgreSQL no permite eliminar valores de un ENUM directamente
    # hay que recrear el tipo completo
    op.execute("ALTER TABLE company ALTER COLUMN regime_type DROP DEFAULT")
    op.execute("UPDATE company SET regime_type = NULL WHERE regime_type = 'NONE'")
    op.execute("ALTER TABLE company ALTER COLUMN regime_type TYPE VARCHAR")
    op.execute("DROP TYPE regime_type")
    op.execute("CREATE TYPE regime_type AS ENUM('SIMPLE', 'ORDINARY')")
    op.execute("ALTER TABLE company ALTER COLUMN regime_type TYPE regime_type USING regime_type::regime_type")