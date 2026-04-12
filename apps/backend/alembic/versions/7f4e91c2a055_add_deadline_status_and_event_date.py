"""add deadline_status and event_date to opportunities

Revision ID: 7f4e91c2a055
Revises: 33bdaf08f8db
Create Date: 2026-04-11 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '7f4e91c2a055'
down_revision: Union[str, None] = '33bdaf08f8db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('opportunities', sa.Column('deadline_status', sa.String(20), nullable=False, server_default='unknown'))
    op.add_column('opportunities', sa.Column('event_date', sa.Date(), nullable=True))

    # Backfill: rows that already have a deadline date → mark as "specific"
    op.execute(
        "UPDATE opportunities SET deadline_status = 'specific' WHERE deadline IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_column('opportunities', 'event_date')
    op.drop_column('opportunities', 'deadline_status')
