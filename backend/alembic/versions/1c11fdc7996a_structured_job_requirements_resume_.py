"""structured job requirements, resume status, scoring runs

Revision ID: 1c11fdc7996a
Revises: 7a4583153bec
Create Date: 2026-09-28 12:44:28.109959

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '1c11fdc7996a'
down_revision: Union[str, Sequence[str], None] = '7a4583153bec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    # --- job_postings: comma string -> real list, plus new structured fields ---
    op.alter_column(
        "job_postings", "required_skills",
        existing_type=sa.Text(),
        type_=postgresql.ARRAY(sa.Text()),
        postgresql_using=r"""
            CASE
                WHEN required_skills IS NULL OR btrim(required_skills) = ''
                    THEN ARRAY[]::text[]
                ELSE regexp_split_to_array(btrim(required_skills), '\s*,\s*')
            END
        """,
    )
    op.alter_column(
        "job_postings", "required_skills",
        nullable=False,
        server_default=sa.text("'{}'::text[]"),
    )
    op.add_column("job_postings", sa.Column(
        "min_years_experience", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("job_postings", sa.Column(
        "min_education_level", sa.String(), nullable=False, server_default="high_school"))
    op.create_check_constraint(
        "ck_job_postings_min_years_nonneg", "job_postings", "min_years_experience >= 0")
    op.create_check_constraint(
        "ck_job_postings_min_education_level", "job_postings",
        "min_education_level IN ('high_school', 'associate', 'bachelor', 'master', 'phd')")

    # --- resumes: processing state ---
    op.add_column("resumes", sa.Column(
        "status", sa.String(), nullable=False, server_default="processing"))
    op.add_column("resumes", sa.Column("failure_reason", sa.Text(), nullable=True))
    op.create_check_constraint(
        "ck_resumes_status", "resumes", "status IN ('processing', 'done', 'failed')")
    # every existing resume was processed synchronously, so it is already done
    op.execute("UPDATE resumes SET status = 'done'")

    # --- scoring runs and their per-resume results ---
    op.create_table(
        "scoring_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(),
        sa.ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("weights", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_scoring_runs_job_id", "scoring_runs", ["job_id"])

    op.create_table(
        "scoring_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scoring_run_id", sa.Integer(),
        sa.ForeignKey("scoring_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resume_id", sa.Integer(),
        sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skills_score", sa.Float(), nullable=False),
        sa.Column("experience_score", sa.Float(), nullable=False),
        sa.Column("education_score", sa.Float(), nullable=False),
        sa.Column("semantic_score", sa.Float(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("matched_skills", postgresql.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'::text[]")),
        sa.Column("missing_skills", postgresql.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'::text[]")),
        sa.UniqueConstraint("scoring_run_id", "resume_id", name="uq_scoring_results_run_resume"),
    )
    op.create_index("ix_scoring_results_scoring_run_id", "scoring_results", ["scoring_run_id"])
    op.create_index("ix_scoring_results_resume_id", "scoring_results", ["resume_id"])


def downgrade() -> None:
    op.drop_table("scoring_results")
    op.drop_table("scoring_runs")

    op.drop_constraint("ck_resumes_status", "resumes", type_="check")
    op.drop_column("resumes", "failure_reason")
    op.drop_column("resumes", "status")

    op.drop_constraint("ck_job_postings_min_education_level", "job_postings", type_="check")
    op.drop_constraint("ck_job_postings_min_years_nonneg", "job_postings", type_="check")
    op.drop_column("job_postings", "min_education_level")
    op.drop_column("job_postings", "min_years_experience")

    # the array default must go before the type can change back
    op.alter_column("job_postings", "required_skills", server_default=None, nullable=True)
    op.alter_column(
        "job_postings", "required_skills",
        existing_type=postgresql.ARRAY(sa.Text()),
        type_=sa.Text(),
        postgresql_using="array_to_string(required_skills, ', ')",
    )