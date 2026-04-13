"""add source to evidence

Revision ID: d3e7f9b2c481
Revises: c2d5f8a1b349
Create Date: 2026-04-12 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'd3e7f9b2c481'
down_revision: Union[str, None] = 'c2d5f8a1b349'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('evidence', sa.Column('source', sa.String(20), nullable=False, server_default='opportunity'))


def downgrade() -> None:
    op.drop_column('evidence', 'source')
