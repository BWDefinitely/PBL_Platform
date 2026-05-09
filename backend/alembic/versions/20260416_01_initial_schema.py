"""initial schema

Revision ID: 20260416_01
Revises:
Create Date: 2026-04-16
"""

from alembic import op
import sqlalchemy as sa


revision = "20260416_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"], unique=False)

    op.create_table(
        "student_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("student_code", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("class_name", sa.String(length=64), nullable=True),
        sa.Column("grade", sa.String(length=32), nullable=True),
        sa.UniqueConstraint("user_id", name="uq_student_profiles_user_id"),
    )
    op.create_index("ix_student_profiles_student_code", "student_profiles", ["student_code"], unique=True)

    op.create_table(
        "teacher_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("organization", sa.String(length=128), nullable=True),
        sa.Column("subject", sa.String(length=128), nullable=True),
        sa.UniqueConstraint("user_id", name="uq_teacher_profiles_user_id"),
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_teacher_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("term", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "project_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="member"),
        sa.UniqueConstraint("project_id", "student_id", name="uq_project_student"),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("deadline", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="todo"),
    )

    op.create_table(
        "assessment_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_assessment_runs_run_id", "assessment_runs", ["run_id"], unique=True)

    op.create_table(
        "assessments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("student_code", sa.String(length=64), nullable=False),
        sa.Column("milestone", sa.String(length=16), nullable=False),
        sa.Column("composite_score", sa.Float(), nullable=False),
        sa.Column("student_tier", sa.String(length=64), nullable=False),
        sa.Column("assessed_at", sa.String(length=64), nullable=True),
        sa.Column("narrative_summary", sa.Text(), nullable=True),
        sa.Column("dissent_count", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("run_id", "student_code", "milestone", name="uq_run_student_milestone"),
    )

    op.create_table(
        "domain_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assessment_id", sa.Integer(), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("domain", sa.String(length=8), nullable=False),
        sa.Column("normalized", sa.Float(), nullable=False),
        sa.Column("tier", sa.String(length=64), nullable=True),
        sa.UniqueConstraint("assessment_id", "domain", name="uq_assessment_domain"),
    )

    op.create_table(
        "dimension_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assessment_id", sa.Integer(), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dimension", sa.String(length=16), nullable=False),
        sa.Column("final_score", sa.Integer(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.UniqueConstraint("assessment_id", "dimension", name="uq_assessment_dimension"),
    )

    op.create_table(
        "assessment_flags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assessment_id", sa.Integer(), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("intervention_alert", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("equity_flag", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("unresolved_dimensions", sa.Text(), nullable=True),
        sa.UniqueConstraint("assessment_id", name="uq_assessment_flags_assessment_id"),
    )

    op.create_table(
        "evidence_snippets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assessment_id", sa.Integer(), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=False),
        sa.Column("trace_ref", sa.String(length=255), nullable=True),
    )

    op.create_table(
        "report_artifacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("artifact_type", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=512), nullable=False),
        sa.Column("meta_json", sa.Text(), nullable=True),
        sa.UniqueConstraint("run_id", "name", name="uq_run_artifact_name"),
    )


def downgrade() -> None:
    op.drop_table("report_artifacts")
    op.drop_table("evidence_snippets")
    op.drop_table("assessment_flags")
    op.drop_table("dimension_scores")
    op.drop_table("domain_scores")
    op.drop_table("assessments")
    op.drop_index("ix_assessment_runs_run_id", table_name="assessment_runs")
    op.drop_table("assessment_runs")
    op.drop_table("tasks")
    op.drop_table("project_members")
    op.drop_table("projects")
    op.drop_table("teacher_profiles")
    op.drop_index("ix_student_profiles_student_code", table_name="student_profiles")
    op.drop_table("student_profiles")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
