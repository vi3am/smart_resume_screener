"""unique active resume filename per job

Revision ID: b3e8c1a92d04
Revises: 1c11fdc7996a
Create Date: 2026-10-23 17:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3e8c1a92d04"
down_revision: Union[str, Sequence[str], None] = "1c11fdc7996a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_resumes_job_filename_active",
        "resumes",
        ["job_id", "filename"],
        unique=True,
        postgresql_where=sa.text("status IN ('processing', 'done')"),
    )


def downgrade() -> None:
    op.drop_index("uq_resumes_job_filename_active", table_name="resumes")
