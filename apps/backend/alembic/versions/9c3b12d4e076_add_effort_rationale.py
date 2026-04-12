"""add effort_rationale to opportunities

Revision ID: 9c3b12d4e076
Revises: 7f4e91c2a055
Create Date: 2026-04-12 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '9c3b12d4e076'
down_revision: Union[str, None] = '7f4e91c2a055'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('opportunities', sa.Column('effort_rationale', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('opportunities', 'effort_rationale')
