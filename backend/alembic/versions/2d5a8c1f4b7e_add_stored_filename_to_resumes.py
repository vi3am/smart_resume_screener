"""add stored filename to resumes

Revision ID: 2d5a8c1f4b7e
Revises: d6e3c7a1f90b
Create Date: 2026-10-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2d5a8c1f4b7e"
down_revision: Union[str, Sequence[str], None] = "d6e3c7a1f90b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("resumes", sa.Column("stored_filename", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("resumes", "stored_filename")
