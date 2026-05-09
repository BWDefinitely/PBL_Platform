"""add process data tables

Revision ID: 20260416_02
Revises: 20260416_01
Create Date: 2026-04-16
"""

from alembic import op
import sqlalchemy as sa


revision = "20260416_02"
down_revision = "20260416_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_code", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=True),
        sa.Column("milestone", sa.String(length=16), nullable=True),
        sa.Column("sent_at", sa.String(length=64), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
    )
    op.create_index("ix_chat_messages_student_code", "chat_messages", ["student_code"], unique=False)

    op.create_table(
        "doc_contributions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_code", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=True),
        sa.Column("milestone", sa.String(length=16), nullable=True),
        sa.Column("section_title", sa.String(length=255), nullable=True),
        sa.Column("content_excerpt", sa.Text(), nullable=True),
        sa.Column("source_count", sa.Integer(), nullable=True),
    )
    op.create_index("ix_doc_contributions_student_code", "doc_contributions", ["student_code"], unique=False)

    op.create_table(
        "presentation_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_code", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=True),
        sa.Column("milestone", sa.String(length=16), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("words", sa.Integer(), nullable=True),
        sa.Column("clarity_score", sa.Float(), nullable=True),
    )
    op.create_index("ix_presentation_records_student_code", "presentation_records", ["student_code"], unique=False)

    op.create_table(
        "activity_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_code", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=True),
        sa.Column("milestone", sa.String(length=16), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=True),
        sa.Column("happened_at", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
    )
    op.create_index("ix_activity_events_student_code", "activity_events", ["student_code"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_activity_events_student_code", table_name="activity_events")
    op.drop_table("activity_events")
    op.drop_index("ix_presentation_records_student_code", table_name="presentation_records")
    op.drop_table("presentation_records")
    op.drop_index("ix_doc_contributions_student_code", table_name="doc_contributions")
    op.drop_table("doc_contributions")
    op.drop_index("ix_chat_messages_student_code", table_name="chat_messages")
    op.drop_table("chat_messages")
