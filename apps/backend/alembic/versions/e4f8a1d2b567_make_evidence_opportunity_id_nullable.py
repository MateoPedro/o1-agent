"""make evidence opportunity_id nullable

Revision ID: e4f8a1d2b567
Revises: d3e7f9b2c481
Create Date: 2026-04-12 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'e4f8a1d2b567'
down_revision: Union[str, None] = 'd3e7f9b2c481'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite doesn't support ALTER COLUMN, recreate the table
    with op.batch_alter_table('evidence') as batch_op:
        batch_op.alter_column('opportunity_id', nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('evidence') as batch_op:
        batch_op.alter_column('opportunity_id', nullable=False)
