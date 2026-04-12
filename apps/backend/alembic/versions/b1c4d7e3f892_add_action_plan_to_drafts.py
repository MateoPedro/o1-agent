"""add action_plan to drafts

Revision ID: b1c4d7e3f892
Revises: 9c3b12d4e076
Create Date: 2026-04-12 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'b1c4d7e3f892'
down_revision: Union[str, None] = '9c3b12d4e076'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('drafts', sa.Column('action_plan', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('drafts', 'action_plan')
