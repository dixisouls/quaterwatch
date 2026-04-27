"""add pipeline_stage to jobs

Revision ID: 0002_add_pipeline_stage
Revises: 0001_initial
Create Date: 2026-04-27 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002_add_pipeline_stage"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("pipeline_stage", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "pipeline_stage")
