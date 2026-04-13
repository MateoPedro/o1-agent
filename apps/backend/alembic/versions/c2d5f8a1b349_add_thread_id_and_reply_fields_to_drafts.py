"""add thread_id and reply fields to drafts

Revision ID: c2d5f8a1b349
Revises: b1c4d7e3f892
Create Date: 2026-04-12 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c2d5f8a1b349'
down_revision: Union[str, None] = 'b1c4d7e3f892'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('drafts', sa.Column('thread_id', sa.String(255), nullable=True))
    op.add_column('drafts', sa.Column('reply_classification', sa.String(30), nullable=True))
    op.add_column('drafts', sa.Column('reply_summary', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('drafts', 'reply_summary')
    op.drop_column('drafts', 'reply_classification')
    op.drop_column('drafts', 'thread_id')
